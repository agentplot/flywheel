"""One session abstraction for the flywheel loop programs.

`launch(spec)` / `wait(handle)` / `collect(handle)` / `close(handle)`, over
three runners:

- **herdr** — a pane; supervised; anything the operator might watch or answer.
  Plannotator and lavish run here.
- **headless** — `claude -p` from the program; reuses the CLI login;
  unsupervised work only.
- **cloud** — future managed agents; the same interface, a stub today.

Import from a sibling script:

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _flywheel_sessions import SessionSpec, runner_for, supervise

Two properties this module exists to guarantee, both from
`design/loop-programs.md`, "Sessions and runners":

**Launches are idempotent.** An agent already running under the name is
reused and its work order is never re-sent. Loop processes are stateless and
restart freely — the reconcile that starts one twice must not produce two
sessions doing the same work.

**The PROGRAM owns all waiting, with real clocks.** `wait()` is a single
bounded wait and never loops; `supervise()` is the loop, and it holds the
clock: notify at 90 minutes via `needs-operator`, stall at 4 hours, and
operator-round sessions never auto-stall because an operator taking their
time is not a stalled session.

Zero dependencies, stdlib only, like every other script in `bin/`. Every
subprocess goes through an injected `run=` callable and every clock through an
injected `clock=`, so the loops that import this are unit-testable without
herdr, without `claude`, and without sleeping.
"""

import enum
import json
import os
import re
import shlex
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# The clocks. Real seconds, not chunk counts: the program owns the waiting.
# ---------------------------------------------------------------------------

NOTIFY_AFTER_S = 90 * 60      # comment + needs-operator, then keep waiting
STALL_AFTER_S = 4 * 60 * 60   # give up waiting; the pane is left open
WAIT_CHUNK_S = 600            # one bounded wait, ten real minutes

#: A cold claude start regularly needs more than two minutes — devenv init,
#: MCP servers, a large project index — and the fleet driver already grants
#: 300s (`bin/flywheel`). The runner granting less was the direct source of
#: `timeout — timed out waiting for agent startup` on every busy day.
START_TIMEOUT_MS = 300_000

#: Startup failures that are transient by construction: the pane's shell is
#: still initializing (pane_busy), claude is booting slower than the wait
#: (not_ready / timed out). A retry against the same pane is safe — the
#: session name and id are deterministic — and far cheaper than failing the
#: stage and burning a whole cycle.
_RETRYABLE_START = ("pane_busy", "not_ready", "timed out", "timeout")

# herdr caps agent names at 32 characters (skills/_reference/herdr.md).
MAX_NAME = 32

# A stable namespace so a headless session's id is DERIVED from its name
# rather than remembered. A restarted loop process recomputes the same id
# and can find — or resume — the session it already started.
FLYWHEEL_NS = uuid.UUID("3f9a2b1c-6f7c-5d2e-9a4b-1c8db1e0a5f3")


class SessionError(Exception):
    """A runner could not do what it was asked."""


class RunnerUnavailable(SessionError):
    """The runner exists in the interface but not yet in the world."""


class WaitState(str, enum.Enum):
    WORKING = "working"                  # still going; wait again
    SETTLED_DONE = "settled_done"        # idle or done
    SETTLED_BLOCKED = "settled_blocked"  # blocked — a question or a permission ask
    GONE = "gone"                        # the agent no longer exists
    STALLED = "stalled"                  # supervise() only: the clock ran out


# ---------------------------------------------------------------------------
# The work order
# ---------------------------------------------------------------------------

def work_order(invocation, brief):
    """One prompt, invocation first line.

    From herdr.md: "A slash command buried mid-body never loads the skill …
    and a command sent bare with the brief chasing it as a second prompt is
    the same defect mirrored." So the shape is enforced here rather than
    trusted to each caller.
    """
    invocation = (invocation or "").strip()
    if not invocation:
        raise ValueError("a work order needs its invocation")
    if "\n" in invocation:
        raise ValueError("the invocation is one line, and it is the first")
    brief = (brief or "").strip()
    return f"{invocation}\n\n{brief}" if brief else invocation


# ---------------------------------------------------------------------------
# Specs and handles
# ---------------------------------------------------------------------------

def claude_transcript_exists(cwd, session_id):
    """Does Claude Code hold a transcript for this session in this cwd?

    Transcripts live under ~/.claude/projects/<slug>/<id>.jsonl, where the
    slug is the cwd with every non-alphanumeric character turned into a
    dash (measured against real project dirs: /, . and _ all become -).
    """
    slug = re.sub(r"[^A-Za-z0-9-]", "-", str(cwd))
    return (Path.home() / ".claude" / "projects" / slug
            / f"{session_id}.jsonl").exists()


def seed_workspace_trust(cwd, config_path=None):
    """Accept Claude Code's trust dialog for `cwd` before it is ever shown.

    Claude Code blocks its first launch in an unseen directory at an
    interactive trust dialog, which reads as `blocked`/`not ready` to the
    launcher — every fresh build worktree failed its first launch until the
    operator hand-seeded the path. The dialog's answer is one key in
    `~/.claude.json`, so the launcher writes it up front. Best-effort and
    idempotent: an unreadable or unwritable config is not a launch failure,
    it just means the dialog may appear.
    """
    config = Path(config_path) if config_path else Path.home() / ".claude.json"
    try:
        data = json.loads(config.read_text())
    except (OSError, json.JSONDecodeError):
        data = {}
    if not isinstance(data, dict):
        return False
    project = data.setdefault("projects", {}).setdefault(str(cwd), {})
    if project.get("hasTrustDialogAccepted"):
        return False
    project["hasTrustDialogAccepted"] = True
    try:
        # Atomic replace: claude itself rewrites this file, and a torn
        # write here would cost far more than the dialog ever did.
        tmp = config.with_name(config.name + ".flywheel-tmp")
        tmp.write_text(json.dumps(data))
        tmp.replace(config)
    except OSError:
        return False
    return True


@dataclass(frozen=True)
class SessionSpec:
    """What to launch. Runner choice is per stage, by supervision need, and
    is config — see `choose_runner`."""

    name: str
    cwd: str
    order: str
    profile: str
    model: str = None
    runner: str = "herdr"
    plan_mode: bool = False
    skip_permissions: bool = True
    operator_round: bool = False
    env: dict = None
    #: Deterministic Claude session id (the caller derives it from the
    #: session name). The pane is disposable; the session is durable: a
    #: fresh launch pins this id with --session-id, and a later launch
    #: whose pane is gone resumes the same warm conversation with
    #: --resume. Empty means neither flag is passed.
    session_id: str = ""

    def __post_init__(self):
        if not self.name:
            raise ValueError("a session needs a name — the name IS the classification")
        if len(self.name) > MAX_NAME:
            raise ValueError(
                f"herdr caps agent names at {MAX_NAME} characters; "
                f"{self.name!r} is {len(self.name)}"
            )
        if not self.cwd:
            raise ValueError(f"{self.name}: a session needs a working directory")
        if not (self.order or "").strip():
            raise ValueError(f"{self.name}: a session needs its work order")

    @property
    def permission_flag(self):
        """The permission mode is the launcher's to set (herdr.md).

        Plan mode is the no-spec path: every edit blocked until the plan,
        checked against the item's claim, is approved through the dialog.
        """
        if self.plan_mode:
            return ["--permission-mode", "plan"]
        return ["--dangerously-skip-permissions"] if self.skip_permissions else []


@dataclass
class SessionHandle:
    name: str
    runner: str
    ref: dict = field(default_factory=dict)
    reused: bool = False


@dataclass
class Collected:
    state: WaitState
    report: str
    raw: str = ""


@dataclass
class Supervision:
    state: WaitState
    elapsed: float
    notified: bool = False
    waits: int = 0


# ---------------------------------------------------------------------------
# The subprocess seam
# ---------------------------------------------------------------------------

def _subprocess_run(argv, cwd=None, env=None, timeout=None):
    return subprocess.run(argv, cwd=cwd, env=env, timeout=timeout,
                          capture_output=True, text=True)


#: The plugin that carries every `flywheel-*` agent profile a spec names.
FLYWHEEL_PLUGIN = "flywheel@flywheel"


def seed_plugin_install(cwd, run=_subprocess_run, plugins_path=None):
    """Install the flywheel plugin for `cwd` before claude first boots there.

    A repo's `.claude/settings.json` can enable the plugin, but claude only
    loads it where an install record exists for that exact project path —
    and a fresh worktree has none. Claude then boots without the flywheel
    agent profiles, `--agent flywheel-…` dies at the shell, and the
    launcher times out on an agent that never existed (observed live on
    every switchboard-kit build worktree, 2026-09-01). Best-effort and
    idempotent, like the trust seed: a failed install is not a launch
    failure — the launch itself will say what is wrong.
    """
    path = (Path(plugins_path) if plugins_path
            else Path.home() / ".claude" / "plugins" / "installed_plugins.json")
    try:
        records = json.loads(path.read_text())["plugins"][FLYWHEEL_PLUGIN]
        if any(r.get("projectPath") == str(cwd) for r in records):
            return False
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        pass
    try:
        result = run(["claude", "plugin", "install", FLYWHEEL_PLUGIN,
                      "--scope", "local"], cwd=str(cwd), timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


#: `terminal_title_stripped` is not stripped while an agent is working.
#: Measured on the live roster, 2026-08-13: an idle agent reads `dispatch`,
#: a working one reads `◑ build-substrate` — the spinner glyph survives. So
#: herdr.md's "poll .terminal_title_stripped until it is <name>" is unreliable
#: exactly when the agent is busy, which is the state a delivered work order
#: puts it in. Compare on the name, not on the decoration.
_GLYPH = re.compile(r"^[^\w]+")


def strip_glyph(title):
    return _GLYPH.sub("", (title or "")).strip()


class Runner:
    """launch / wait / collect / close — the four verbs the abstraction is
    named for — plus `send`.

    `send` is here because the record's own bolt loop cannot be written
    without it: verify's findings are handled by "the loop re-prompts the
    SAME build session — 'go fix these'", a relayed operator answer goes to
    the session that asked, and a plan-mode approval drives a dialog in a
    session already alive. Four verbs can launch and reap a session but
    cannot say a second thing to one. The gap is the item's enumeration
    being shorter than the record's stages, and it is noted on #75 rather
    than papered over.
    """

    kind = "abstract"

    def launch(self, spec):
        raise NotImplementedError

    def wait(self, handle, timeout=WAIT_CHUNK_S):
        """ONE bounded wait. Never loops — that is `supervise`'s job."""
        raise NotImplementedError

    def send(self, handle, prompt):
        """Say a second thing to a session already alive."""
        raise NotImplementedError

    def collect(self, handle):
        raise NotImplementedError

    def close(self, handle):
        raise NotImplementedError

    def close_named(self, name):
        """Reap a finished session by its deterministic name.

        `close` needs the launch handle, which only the process that
        launched the session holds — a restarted loop has no handle to a
        pane its predecessor opened, and the pane outlives the process.
        Best-effort: a name with nothing behind it is a no-op."""

# ---------------------------------------------------------------------------
# herdr — the supervised pane
# ---------------------------------------------------------------------------

class HerdrRunner(Runner):
    """A pane the operator can watch and answer.

    Mechanics are herdr.md's, with one deliberate improvement carried from
    the fleet driver (`bin/flywheel:start_actor`): the name is set at launch
    with `-n`, so there is no rename to race with the work order. There is
    no typed `/rename` fallback — the title is cosmetic, the roster keys on
    the start name first, and anything typed for a title can strand in the
    composer and swallow the work order.
    """

    kind = "herdr"

    def __init__(self, run=_subprocess_run, sleep=time.sleep, env=None,
                 start_attempts=12, ready_attempts=30, submit_attempts=8,
                 poll_s=4, transcript_exists=None, seed_trust=None,
                 seed_plugin=None, settle_reads=3, settle_gap_s=10):
        self._run = run
        self._sleep = sleep
        self._env = env
        self._transcript_exists = transcript_exists or claude_transcript_exists
        self._seed_trust = seed_workspace_trust if seed_trust is None else seed_trust
        self._seed_plugin = ((lambda cwd: seed_plugin_install(cwd, run=run))
                             if seed_plugin is None else seed_plugin)
        self.start_attempts = start_attempts
        self.ready_attempts = ready_attempts
        self.submit_attempts = submit_attempts
        self.poll_s = poll_s
        self.settle_reads = settle_reads
        self.settle_gap_s = settle_gap_s

    # -- plumbing ----------------------------------------------------------

    def _herdr(self, *args, timeout=None):
        try:
            return self._run(["herdr", *args], env=self._env, timeout=timeout)
        except subprocess.TimeoutExpired:
            # A wedged herdr call is a failed call, not a crashed loop: the
            # callers all read returncode/stderr and re-derive state from
            # the roster, which is exactly the right recovery.
            return subprocess.CompletedProcess(
                ["herdr", *args], 124, stdout="",
                stderr=f"herdr {' '.join(args[:3])} timed out after {timeout}s")

    def _herdr_json(self, *args, timeout=None):
        out = self._herdr(*args, timeout=timeout)
        if out.returncode != 0:
            raise SessionError(
                f"herdr {' '.join(args[:3])} failed: "
                f"{(out.stderr or '').strip() or (out.stdout or '').strip()}"
            )
        try:
            return json.loads(out.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise SessionError(f"herdr {' '.join(args[:3])} returned unparseable output: {exc}")

    def agents(self):
        """{name: agent row}. Keyed on the name or the stripped title, the
        way the fleet driver keys it — an agent named before its title
        converged is findable under either."""
        rows = self._herdr_json("agent", "list").get("result", {}).get("agents", [])
        return {
            (row.get("name") or strip_glyph(row.get("terminal_title_stripped"))): row
            for row in rows
            if isinstance(row, dict)
        }

    # -- the four verbs ----------------------------------------------------

    def launch(self, spec):
        """Idempotent: an agent already under this name is reused, and its
        work order is NOT re-sent. Reuse is health-checked first: a live
        classified agent — working, settled, or blocked at a real question
        its composer already reached — is the session this launch wants; a
        row that never reached its composer is a corpse from an earlier
        failed launch, and adopting it wedges the stage (the order is never
        re-sent), so it is reaped and the launch proceeds fresh."""
        existing = self.agents().get(spec.name)
        if existing:
            status = existing.get("agent_status")
            usable = (status in ("working", "idle", "done")
                      or (status == "blocked"
                          and existing.get("interactive_ready")))
            if usable:
                return SessionHandle(
                    name=spec.name, runner=self.kind, reused=True,
                    ref={"pane_id": existing.get("pane_id"),
                         "tab_id": existing.get("tab_id"),
                         "workspace_id": existing.get("workspace_id")},
                )
            self._close_tab(existing.get("tab_id"))

        # Answer the trust dialog before claude can ask it: a fresh build
        # worktree otherwise blocks its first launch at an interactive
        # prompt no loop can drive. Same for the plugin install record —
        # without it claude boots agentless and the launch times out.
        self._seed_trust(spec.cwd)
        self._seed_plugin(spec.cwd)
        tab = self._herdr_json("tab", "create", "--cwd", str(spec.cwd),
                               "--label", spec.name, "--no-focus")
        result = tab.get("result", {})
        tab_id = (result.get("tab", {}).get("tab_id")
                  or result.get("tab", {}).get("id"))
        pane = result.get("root_pane", {}).get("pane_id")
        if not pane:
            self._close_tab(tab_id)
            raise SessionError(
                f"{spec.name}: tab create returned no root_pane.pane_id: "
                f"{json.dumps(result)[:200]}"
            )

        argv = ["agent", "start", spec.name, "--kind", "claude",
                "--pane", str(pane), "--timeout", str(START_TIMEOUT_MS),
                "--", "--agent", spec.profile, "-n", spec.name]
        argv += spec.permission_flag
        if spec.model:
            argv += ["--model", spec.model]
        if spec.session_id:
            # A transcript under this id means an earlier pane died with
            # the conversation intact — resume it warm rather than start
            # cold. Otherwise pin the id so a future launch can.
            if self._transcript_exists(spec.cwd, spec.session_id):
                argv += ["--resume", spec.session_id]
            else:
                argv += ["--session-id", spec.session_id]

        # A fresh tab's shell can take a while to reach its prompt (devenv
        # init) and herdr reports pane_busy until it does; a slow claude
        # boot reads as not_ready or a start timeout. All transient — retry
        # with backoff rather than failing the stage and burning a cycle.
        start = None
        started = False
        for attempt in range(self.start_attempts):
            start = self._herdr(*argv)
            if start.returncode == 0:
                started = True
                break
            # The agent can come up BEHIND a failed start: a startup
            # timeout returns while claude is still booting, and every
            # later attempt then reads pane_busy — busy with the very
            # claude this launch asked for. The roster is the truth.
            if self.agents().get(spec.name):
                started = True
                break
            stderr = start.stderr or ""
            if not any(token in stderr for token in _RETRYABLE_START):
                break
            if attempt < self.start_attempts - 1:
                self._sleep(min(30, 10 + 5 * attempt))
        if not started:
            self._close_tab(tab_id)
            raise SessionError(
                f"{spec.name}: agent start failed: "
                f"{(start.stderr or '').strip() if start else 'no result'}"
            )

        handle = SessionHandle(
            name=spec.name, runner=self.kind,
            ref={"pane_id": pane, "tab_id": tab_id},
        )
        if not self._await_ready(spec.name):
            # Typing into a pane that never reached its composer is how
            # keystrokes buffer and land glued once claude comes up.
            self._herdr("agent", "rename", spec.name, f"{spec.name}-notready")
            raise SessionError(
                f"{spec.name}: claude never reached its composer — the pane "
                f"is left open for inspection as {spec.name}-notready")
        self._ensure_named(spec.name)
        if not self._deliver(spec.name, spec.order):
            # Release the NAME while keeping the pane: launch is idempotent
            # by name and deliberately never re-sends an order, so a corpse
            # under this name wedges every later launch (#169, observed
            # live on spec-writing-stage-labels-133).
            self._herdr("agent", "rename", spec.name,
                        f"{spec.name}-undelivered")
            raise SessionError(
                f"{spec.name}: the work order never submitted — the pane is "
                f"left open for inspection as {spec.name}-undelivered")
        return handle

    def wait(self, handle, timeout=WAIT_CHUNK_S):
        """A SINGLE `herdr agent wait`, bounded.

        Without `--until` it matches idle, done or blocked — which is what
        "tell me when it needs me" means. A wait pinned to `--until idle`
        never fires on an agent that settled at `done`, and `done` is exactly
        what a finished agent shows when its tab was never focused.
        """
        args = ["agent", "wait", handle.name]
        if timeout:
            args += ["--timeout", str(int(timeout * 1000))]
        self._herdr(*args, timeout=(timeout + 30) if timeout else None)
        state = self.state(handle.name)
        # A momentary idle between two turns reads exactly like a finished
        # session — build-codebuild-fleet's branch was collected and merged
        # 25 minutes before its session printed its report. One status read
        # is a hint, not a verdict: settled-done must hold across
        # `settle_reads` spaced reads before it is believed. Blocked and
        # gone return as seen — neither is a between-turns blip.
        for _ in range(self.settle_reads - 1):
            if state != WaitState.SETTLED_DONE:
                break
            self._sleep(self.settle_gap_s)
            state = self.state(handle.name)
        return state

    def send(self, handle, prompt):
        """Re-prompt a live pane — verify's go-fix round, a relayed answer."""
        return self._deliver(handle.name, prompt)

    def send_keys(self, handle, *keys):
        """Drive a dialog. The plan-mode approval is arrows plus enter."""
        return self._herdr("agent", "send-keys", handle.name, *keys)

    def state(self, name):
        row = self.agents().get(name)
        if row is None:
            return WaitState.GONE
        status = row.get("agent_status")
        if status in ("idle", "done"):
            return WaitState.SETTLED_DONE
        if status == "blocked":
            return WaitState.SETTLED_BLOCKED
        return WaitState.WORKING

    def collect(self, handle, lines=200):
        """Read the pane.

        Composer ghost text is NOT input: a read renders whatever sits at the
        prompt, including Claude Code's suggestions, which look exactly like
        typed-but-unsent messages. Callers act only on what the session
        actually produced.
        """
        out = self._herdr("agent", "read", handle.name,
                          "--source", "recent-unwrapped", "--lines", str(lines))
        raw = out.stdout or ""
        text = raw
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            pass
        else:
            result = data.get("result", data)
            if isinstance(result, dict):
                for key in ("text", "output", "content", "lines"):
                    if key in result:
                        value = result[key]
                        text = "\n".join(value) if isinstance(value, list) else str(value)
                        break
        return Collected(state=self.state(handle.name), report=text.strip(), raw=raw)

    def close(self, handle):
        """Close means FINISHED.

        A settled pane left open makes the roster lie — but a session the
        loop will re-prompt (a plan-mode build awaiting approval, a review
        awaiting a bounce) KEEPS its pane. Callers close only what is done
        — and the same still-working guard `close_named` carries holds
        here too, so a caller whose settle verdict was a between-turns
        blip cannot reap a live session. The roster's tab_id wins over the
        handle's: a handle synthesized without a ref still closes the
        right tab.
        """
        row = self.agents().get(handle.name)
        if row is not None and row.get("agent_status") == "working":
            return
        self._close_tab((row or {}).get("tab_id") or handle.ref.get("tab_id"))

    def close_named(self, name):
        row = self.agents().get(name)
        if row is not None and row.get("agent_status") != "working":
            self._close_tab(row.get("tab_id"))

    # -- internals ---------------------------------------------------------

    def _close_tab(self, tab_id):
        if tab_id:
            self._herdr("tab", "close", str(tab_id))

    def _await_ready(self, name):
        """The pane's claude takes tens of seconds to reach its composer; a
        prompt sent earlier strands unsubmitted or is lost outright."""
        for _ in range(self.ready_attempts):
            if self.agents().get(name, {}).get("interactive_ready"):
                return True
            self._sleep(self.poll_s)
        return False

    def _named(self, name):
        row = self.agents().get(name, {})
        return strip_glyph(row.get("terminal_title_stripped")) == name

    def _ensure_named(self, name):
        """`-n` set the title at launch; the title field only lags it. Wait
        for convergence and never type. The old `/rename` fallback is how a
        work order gets swallowed: the dance could exit on `-n`'s own late
        convergence with the unsubmitted `/rename` still in the composer,
        where the next order pasted straight onto it and submitted as one
        garbage line (`/rename scaffold-…/opsx:new …`, observed live on
        bolt/matches-the-book). The title is cosmetic either way — the
        roster keys on the start name first — so a title that never
        converges costs nothing beyond this False."""
        for _ in range(3):
            if self._named(name):
                return True
            self._sleep(self.poll_s)
        return False

    def _deliver(self, name, order):
        """Deliver the order and verify it submitted.

        A multi-line prompt can land in the composer as a pasted block
        without submitting — the pane shows `[Pasted text …]` and the agent
        stays settled. One Enter submits a stuck composer.
        """
        # A clean composer first: esc clears anything stranded — an
        # unsubmitted rename, ghost text — that would otherwise prefix
        # this order. Harmless on an empty composer.
        self._herdr("agent", "send-keys", name, "esc")
        sent = self._herdr("agent", "prompt", name, order)
        if sent.returncode != 0:
            raise SessionError(
                f"{name}: prompt failed: {(sent.stderr or '').strip()}")
        for _ in range(self.submit_attempts):
            self._sleep(self.poll_s)
            if self.agents().get(name, {}).get("agent_status") == "working":
                return True
            self._herdr("agent", "send-keys", name, "enter")
        return False


# ---------------------------------------------------------------------------
# headless — `claude -p`, unsupervised
# ---------------------------------------------------------------------------

def _state_dir():
    root = os.environ.get("XDG_STATE_HOME")
    base = Path(root) if root else Path.home() / ".local" / "state"
    return base / "flywheel" / "sessions"


def derived_session_id(name):
    """A session id computed from the name, never remembered.

    Loop processes are stateless: a restart re-reads tracker and records, and
    must also be able to find the session it already started rather than
    launch a twin. Deriving the id makes that possible with no memory at all.
    """
    return str(uuid.uuid5(FLYWHEEL_NS, name))


def _alive(pid):
    try:
        os.kill(int(pid), 0)
    except (OSError, TypeError, ValueError):
        return False
    return True


class HeadlessRunner(Runner):
    """`claude -p` straight from the program, reusing the CLI login.

    Unsupervised work only — there is no pane for the operator to answer
    into, so anything that might ask a question belongs on the herdr runner.
    No credential is injected: the environment is inherited exactly as the
    program received it, which is what "reuses the CLI login" means.
    """

    kind = "headless"

    def __init__(self, run=None, popen=subprocess.Popen, state_dir=None,
                 alive=_alive, clock=time.monotonic, seed_trust=None,
                 seed_plugin=None):
        self._run = run or _subprocess_run
        self._popen = popen
        self._state_dir = Path(state_dir) if state_dir else _state_dir()
        self._alive = alive
        self._clock = clock
        self._seed_trust = seed_workspace_trust if seed_trust is None else seed_trust
        self._seed_plugin = ((lambda cwd: seed_plugin_install(cwd, run=self._run))
                             if seed_plugin is None else seed_plugin)

    def _registry(self, name):
        return self._state_dir / f"{name}.json"

    def _read_registry(self, name):
        path = self._registry(name)
        try:
            return json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            return None

    def argv(self, spec, resume=False):
        session_id = derived_session_id(spec.name)
        argv = ["claude", "-p", spec.order, "--agent", spec.profile]
        if spec.model:
            argv += ["--model", spec.model]
        argv += spec.permission_flag
        argv += ["--resume", session_id] if resume else ["--session-id", session_id]
        return argv

    def launch(self, spec):
        """Idempotent in both halves: a live recorded pid is reused as-is; a
        dead one is resumed by its derived session id rather than restarted
        from the top."""
        if spec.plan_mode:
            # Plan mode is approved "through the plan dialog" — an
            # interactive affordance. A headless session has no pane for an
            # approver to drive, so a plan-mode spec sent here would block
            # forever with nothing to approve it. Refuse loudly at launch
            # rather than at four hours.
            raise RunnerUnavailable(
                f"{spec.name}: the plan-mode path needs a pane the approver "
                "can drive — launch it on the herdr runner")
        recorded = self._read_registry(spec.name)
        if recorded and self._alive(recorded.get("pid")):
            return SessionHandle(name=spec.name, runner=self.kind, reused=True,
                                 ref=dict(recorded))

        self._seed_trust(spec.cwd)
        self._seed_plugin(spec.cwd)
        self._state_dir.mkdir(parents=True, exist_ok=True)
        log = self._state_dir / f"{spec.name}.log"
        argv = self.argv(spec, resume=bool(recorded))
        # The environment is INHERITED. Nothing is added: the CLI login is
        # the credential, and a program that injects one has fallen back to
        # ambient auth by another name.
        env = dict(os.environ, **(spec.env or {})) if spec.env else None
        handle_log = open(log, "w")
        try:
            proc = self._popen(argv, cwd=str(spec.cwd), env=env,
                               stdout=handle_log, stderr=subprocess.STDOUT)
        finally:
            handle_log.close()
        ref = {"pid": proc.pid, "log": str(log),
               "session_id": derived_session_id(spec.name),
               "argv": " ".join(shlex.quote(a) for a in argv)}
        self._registry(spec.name).write_text(json.dumps(ref, indent=2))
        handle = SessionHandle(name=spec.name, runner=self.kind, ref=ref)
        handle.ref["proc"] = proc
        return handle

    def wait(self, handle, timeout=WAIT_CHUNK_S):
        """ONE bounded wait on the process."""
        proc = handle.ref.get("proc")
        if proc is not None:
            try:
                proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                return WaitState.WORKING
            return WaitState.SETTLED_DONE
        pid = handle.ref.get("pid")
        deadline = self._clock() + (timeout or 0)
        while self._alive(pid):
            if self._clock() >= deadline:
                return WaitState.WORKING
            time.sleep(1)
        return WaitState.SETTLED_DONE

    def send(self, handle, prompt):
        """`claude -p --resume <id>` — the same conversation, a second turn."""
        session_id = handle.ref.get("session_id") or derived_session_id(handle.name)
        out = self._run(["claude", "-p", prompt, "--resume", session_id],
                        cwd=handle.ref.get("cwd"))
        if out.returncode != 0:
            raise SessionError(
                f"{handle.name}: resume failed: {(out.stderr or '').strip()}")
        return out.stdout

    def collect(self, handle):
        try:
            raw = Path(handle.ref["log"]).read_text()
        except (OSError, KeyError):
            raw = ""
        return Collected(state=self.state(handle), report=raw.strip(), raw=raw)

    def state(self, handle):
        if self._alive(handle.ref.get("pid")):
            return WaitState.WORKING
        return WaitState.SETTLED_DONE

    def close(self, handle):
        proc = handle.ref.get("proc")
        if proc is not None and proc.poll() is None:
            proc.terminate()
        self._registry(handle.name).unlink(missing_ok=True)

    def close_named(self, name):
        recorded = self._read_registry(name)
        if recorded and self._alive(recorded.get("pid")):
            return  # still working — a name is not proof it settled
        self._registry(name).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# cloud — the stub
# ---------------------------------------------------------------------------

class CloudRunner(Runner):
    """Future managed agents; the same interface.

    A stub on purpose rather than an omission: the third runner is named in
    the decision record, and a loop that reaches for it should fail with that
    sentence rather than with an AttributeError.
    """

    kind = "cloud"

    _WHY = ("the cloud runner is a stub — managed agents are not wired yet; "
            "choose the herdr runner for supervised work or headless for "
            "unsupervised (design/loop-programs.md, Sessions and runners)")

    def launch(self, spec):
        raise RunnerUnavailable(self._WHY)

    def wait(self, handle, timeout=WAIT_CHUNK_S):
        raise RunnerUnavailable(self._WHY)

    def send(self, handle, prompt):
        raise RunnerUnavailable(self._WHY)

    def collect(self, handle):
        raise RunnerUnavailable(self._WHY)

    def close(self, handle):
        raise RunnerUnavailable(self._WHY)


# ---------------------------------------------------------------------------
# Runner choice is per stage, by supervision need, and is config
# ---------------------------------------------------------------------------

RUNNERS = {
    "herdr": HerdrRunner,
    "headless": HeadlessRunner,
    "cloud": CloudRunner,
}

#: The default map. Supervised where the operator might watch or answer;
#: headless only where there is genuinely nothing to answer. The fallback for
#: an unnamed stage is `herdr`, because a stage wrongly run headless has no
#: pane for the question it turns out to have.
DEFAULT_STAGE_RUNNERS = {
    "spec": "herdr",
    "build": "herdr",
    "verify": "herdr",
    "merge": "herdr",      # the gate can ask for an approval
    "land": "herdr",
    "design": "herdr",
    "plannotator": "herdr",
    "lavish": "herdr",
    "query": "headless",
    "guards": "headless",
    "bookkeeping": "headless",
}


def choose_runner(stage, config=None):
    """Which runner a stage uses. Config wins; the default map is the floor."""
    if config and stage in config:
        return config[stage]
    return DEFAULT_STAGE_RUNNERS.get(stage, "herdr")


def runner_for(name, **kwargs):
    try:
        return RUNNERS[name](**kwargs)
    except KeyError:
        raise SessionError(
            f"unknown runner {name!r} — one of {', '.join(sorted(RUNNERS))}")


# ---------------------------------------------------------------------------
# The waiting — the program's, with a real clock
# ---------------------------------------------------------------------------

def supervise(runner, handle, operator_round=False, on_notify=None,
              clock=time.time, notify_after=NOTIFY_AFTER_S,
              stall_after=STALL_AFTER_S, chunk=WAIT_CHUNK_S,
              origin=None, notified=False):
    """Wait on a session until it settles, notifying and stalling on a clock.

    - At `notify_after` (90 min) `on_notify(handle, elapsed)` fires ONCE —
      the caller comments on the items and adds `needs-operator` — and the
      waiting continues. A live wait is what that label means.
    - At `stall_after` (4 h) the wait gives up and returns STALLED. The pane
      is left open on purpose: a stalled session is evidence.
    - An `operator_round` session NEVER auto-stalls — and every design
      session is one, since any may end with a dispatch plan. A round —
      plannotator, lavish, the close plan — is the operator's to take as
      long as they like, and a program that calls that a stall is
      measuring the wrong thing. It still notifies at 90 minutes: the
      record excepts the stall, not the notice.

    **`origin` is why this takes a wall clock and not a monotonic one.**
    Loop processes are stateless and a 60s reconcile restarts them freely.
    With the origin defaulting to now, a loop that dies at 80 minutes and
    restarts hands a hung session a fresh four-hour budget, and on a
    flapping server the session never stalls at all. herdr cannot fix this
    for us — measured on the live roster, `herdr agent list` returns no
    timestamp of any kind, only the monotonic counters `revision` and
    `state_change_seq`. So the caller passes the origin it recovered from
    the tracker (the dispatch comment on the item is the natural carrier,
    and the tracker is the only bus by construction). Omit it and you get
    from-now behaviour, which is right for a fresh launch and wrong for a
    rehydrated one.

    `notified` is passed back in for the same reason: a restart must not
    re-notify, because `needs-operator` marks a live wait and a second
    comment on every restart is exactly the pollution invariant 7 forbids.

    **The caller owes the counterpart.** If this returns `notified=True` and
    the session then settles, the label it added has to come off —
    "whoever applies the answer removes the label" (tracker.md invariant 7).
    `_flywheel_inbox.clear_needs_operator` is its other half; a supervision
    that notified and a completion that never clears leaves the operator's
    waiting-on-me view permanently wrong.

    Calling this once per PROMPT rather than once per session is what
    expresses "the clock restarts after a plan approval": the approval is a
    new prompt, the next call is a new origin, and there is no counter to
    reset by hand.
    """
    started = clock() if origin is None else origin
    waits = 0
    while True:
        # Poll BEFORE judging the clock: a rehydrated origin can be hours
        # old while the session already settled — a stall verdict issued
        # without one look at the pane wedged finished work behind a
        # marker from the previous launch (observed live, twice). The
        # budgets only ever measure a session seen still working.
        state = runner.wait(handle, timeout=chunk)
        waits += 1
        if state != WaitState.WORKING:
            return Supervision(state, clock() - started, notified, waits)
        elapsed = clock() - started
        if not notified and elapsed >= notify_after:
            notified = True
            if on_notify is not None:
                on_notify(handle, elapsed)
        if not operator_round and elapsed >= stall_after:
            return Supervision(WaitState.STALLED, elapsed, notified, waits)
