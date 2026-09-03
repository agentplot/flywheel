"""The round's ear, kept OUTSIDE the dispatch pane.

A lavish page is answered through `lavish-axi poll`, which blocks until
the operator sends feedback. Run inside dispatch's own turn, that poll
cannot survive the fleet: herdr's prompt delivery interrupts whatever
tool the pane is running to reach the composer, and every server poke
— a new card, a relay, a re-render — killed the poll 45 seconds before
it landed (round 28, 2026-09-02, three times over). A round nobody is
polling is a round nobody is listening to, and the operator's answers
sat queued in lavish for a day.

So the poll lives here, in a process the pane's turns cannot kill, and
feedback is handed INTO the pane through the same door the pokes use:
written to a file beside the plan and delivered as a prompt naming it,
once the pane has settled. Lavish keeps feedback queued until a poll
consumes it, so a listener started late still delivers everything.

Pure function `listen(plan, poll, deliver)` for the loop; the CLI wraps
it with the real poll, the settled-pane delivery, a pidfile so a second
start is a no-op, and a detached child so dispatch's turn returns.
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _flywheel_herdr as herdr         # noqa: E402

SETTLED = ("idle", "done")
#: The poll's structured reply when the operator ended the session from
#: the page (`Send & End`): `{"status": "ended", "ended_by": "user"}`.
#: Matched on the JSON, never on prose — lavish's own boilerplate says
#: "ends the session" on every poll.
_ENDED = re.compile(r"\"status\"\s*:\s*\"ended\"")
#: The poll's error reply — a YAML-ish `error: …` / `code: …` block —
#: lavish's server hiccuping (measured: "poll response was interrupted",
#: SERVER_ERROR, delivered into the pane as if it were the operator's
#: word). Retried, never delivered.
_ERROR = re.compile(r"^\s*error:\s*\S", re.MULTILINE)
#: The banner every poll prints before it blocks; not feedback.
_BANNER = re.compile(r"^\[lavish-axi\] Long-polling.*$", re.MULTILINE)
RETRY_S = (15, 30, 60, 120)


def feedback_path(plan, n):
    return plan.parent / "feedback" / f"{n:03d}.md"


def write_feedback(plan, n, text):
    path = feedback_path(plan, n)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def order(plan, n, path):
    return (f"lavish feedback on {plan.parent.name}, delivery {n}: the "
            f"operator answered the round on the page. Read {path} "
            f"completely — it is their word on the round — and apply it in "
            f"the protocol's order, then say per object what you filed.")


def session_ended(text):
    return bool(_ENDED.search(text or ""))


def feedback_in(text):
    """The poll's reply with the banner stripped; empty when nothing
    but the banner came back."""
    return _BANNER.sub("", text or "").strip()


def poll_errored(text):
    return bool(_ERROR.search(feedback_in(text)))


def listen(plan, poll, deliver, log=print, alive=lambda: True,
           sleep=time.sleep):
    """Poll until the session ends; every delivery goes into the pane.

    `poll()` -> `(returncode, output)`; `deliver(text)` -> bool;
    `alive()` says whether the page's URL still answers. Returns the
    number of deliveries made.

    Three replies are not feedback and are never delivered: nothing but
    the banner (poll again), an `error:` block (lavish hiccuped — wait
    and poll again while the page still answers; stop when it does
    not), and a non-zero exit with nothing to say (lavish refusing: the
    session closed from the page and not reopenable — stop).
    """
    made, errors = 0, 0
    while True:
        rc, out = poll()
        body = feedback_in(out)
        if not body:
            if rc != 0:
                log(f"poll exited {rc} with nothing — stopping")
                return made
            continue
        if poll_errored(out):
            errors += 1
            if not alive():
                log(f"poll error and the page no longer answers — stopping: "
                    f"{body.splitlines()[0]}")
                return made
            wait = RETRY_S[min(errors, len(RETRY_S)) - 1]
            log(f"poll error ({body.splitlines()[0]}) — retrying in {wait}s")
            sleep(wait)
            continue
        errors = 0
        made += 1
        path = write_feedback(plan, made, out)
        if not deliver(order(plan, made, path)):
            log(f"delivery {made} could not be handed to the pane — "
                f"it stands at {path}")
        else:
            log(f"delivery {made} → pane ({path})")
        if session_ended(out) or rc != 0:
            log("the operator ended the session — stopping")
            return made


def url_answers(plan):
    """Does the round's recorded URL (`url.txt` beside the plan) still
    answer? Unknown (no file) reads as alive: the listener then trusts
    the poll alone."""
    import urllib.request
    try:
        url = (plan.parent / "url.txt").read_text().strip()
    except OSError:
        return True
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return resp.status < 500
    except Exception:  # noqa: BLE001 — any failure is "does not answer"
        return False


def poll_lavish(plan, run=subprocess.run):
    out = run(["npx", "-y", "lavish-axi", "poll", str(plan)],
              cwd=str(plan.parent), capture_output=True, text=True)
    return out.returncode, (out.stdout or "") + (out.stderr or "")


def deliver_settled(agent, text, env, sleep=time.sleep, attempts=120,
                    log=print):
    """Prompt the pane only once it has settled: a prompt into a working
    pane interrupts its tool, which is the very failure this module
    exists to avoid. Waits up to `attempts` × 30s for the turn to end."""
    for _ in range(attempts):
        try:
            status = herdr.herdr_agents(env).get(agent, {}).get("agent_status")
        except RuntimeError as error:
            log(f"roster unreadable: {error}")
            status = None
        if status in SETTLED:
            delivered, reason = herdr.send_prompt(agent, text, env)
            if delivered:
                return True
            log(reason)
        elif status is None:
            log(f"{agent} is not on the roster — waiting")
        sleep(30)
    return False


def standing_round(plans_dir, answers=None):
    """The round that stands: the newest `<plans_dir>/*/plan.html` whose
    recorded URL still answers, as `(plan_path, url)`, else None.

    A command rather than a shell recipe on purpose: the dispatch pane's
    `ls` is aliased (eza), `ls -t` there errors out, and a recycled
    dispatch concluded "no plans directory" beside sixty rounds
    (2026-09-03). Newest by the directory's own mtime, so a re-render
    keeps the round current without renaming anything."""
    answers = answers or url_answers
    plans = Path(plans_dir)
    if not plans.is_dir():
        return None
    candidates = sorted((p for p in plans.glob("*/plan.html")),
                        key=lambda p: p.parent.stat().st_mtime, reverse=True)
    for plan in candidates:
        try:
            url = (plan.parent / "url.txt").read_text().strip()
        except OSError:
            continue
        if url and answers(plan):
            return plan, url
    return None


def pid_alive(path):
    try:
        pid = int(path.read_text().strip())
        os.kill(pid, 0)
        return pid
    except (OSError, ValueError):
        return None


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(prog="flywheel-dispatch-listen")
    parser.add_argument("plan", nargs="?", help="the round's plan.html")
    parser.add_argument("--agent", default="dispatch",
                        help="the pane feedback is handed to")
    parser.add_argument("--foreground", action="store_true",
                        help="run the loop here (the detached child does)")
    parser.add_argument("--standing", metavar="PLANS_DIR",
                        help="print the round that stands under PLANS_DIR "
                             "(newest plan.html whose url.txt answers) "
                             "and exit")
    args = parser.parse_args(argv)
    if args.standing:
        found = standing_round(args.standing)
        if not found:
            print("none")
            return 1
        plan, url = found
        print(f"standing {plan} {url}")
        return 0
    if not args.plan:
        parser.error("plan.html is required unless --standing is given")
    plan = Path(args.plan).resolve()
    if not plan.is_file():
        sys.exit(f"flywheel-dispatch-listen: {plan} is not a file")
    pidfile = plan.parent / ".listen.pid"
    alive = pid_alive(pidfile)
    if alive:
        print(f"already listening on {plan.parent.name} (pid {alive})")
        return 0
    if not args.foreground:
        log = open(plan.parent / "listen.log", "a")
        child = subprocess.Popen(
            [sys.executable, __file__, str(plan), "--agent", args.agent,
             "--foreground"],
            stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
            start_new_session=True, env=dict(os.environ))
        print(f"listening on {plan.parent.name} (pid {child.pid}) → "
              f"{args.agent}; feedback lands in {plan.parent}/feedback/")
        return 0
    pidfile.write_text(f"{os.getpid()}\n")
    env = dict(os.environ)

    def log(message):
        print(time.strftime("%Y-%m-%dT%H:%M:%S ") + message, flush=True)

    try:
        listen(plan, poll=lambda: poll_lavish(plan),
               deliver=lambda text: deliver_settled(args.agent, text, env,
                                                    log=log),
               log=log, alive=lambda: url_answers(plan))
    finally:
        pidfile.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
