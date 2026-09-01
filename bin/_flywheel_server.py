"""#74 — the server: one loop process per milestone with a job.

`design/loop-programs.md`, "Decision":

    There are no conductor agents. `flywheel server` is a daemon the
    operator starts on any host they want in the fleet; it runs the
    reconcile pass every 60s and starts or stops one loop process per
    milestone with a job. ... no job -> the loop process stops; a job ->
    a stateless process starts and re-reads tracker + records; a closed
    milestone -> a one-shot archive run.

`bin/flywheel server` is the command; this is what it runs. It decides
nothing: the job list is `_flywheel_inbox.server_inbox`, the processes are
`bin/flywheel-bolt-loop` and `bin/flywheel-intent-loop`, and everything
between them is arithmetic over manifest + tracker + the live registry.

**The pass splits into a pure planner and an impure executor**, the same
split `_flywheel_inbox` makes and for the same reason: `plan()` is a
function of (jobs, teams, host, running, backoff) with no network, no
clock and no process in it, so every claim this server makes is a unit
test rather than an inference.

**Stateless downward, stateful nowhere else.** The loops hold no state
between runs, so a stopped or killed one loses nothing and a restarted one
rehydrates from the tracker and the records. The server's own registry is
in-memory on purpose: a server restart costs at most one extra process
start and a clean exit, which is the cost the record already licenses when
it says a server filter may over-approximate.

Import from a sibling script:

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _flywheel_server import Server, ServerConfig, plan

Zero dependencies, stdlib only, beside `_flywheel_gh.py` and
`_flywheel_inbox.py`.
"""

import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _flywheel_inbox as inbox  # noqa: E402
import _flywheel_ledger as obs   # noqa: E402

# ---------------------------------------------------------------------------
# The clocks and the one command table
# ---------------------------------------------------------------------------

INTERVAL_S = 60          # the record's number, and the default
BACKOFF_BASE_S = 60      # after a loop exits having found nothing to do
BACKOFF_MAX_S = 900      # ... doubling to a fifteen-minute ceiling
STOP_GRACE_S = 10        # SIGTERM, then SIGKILL, on teardown

LOOP_COMMANDS = {
    inbox.BOLT_PREFIX: "flywheel-bolt-loop",
    inbox.INTENT_PREFIX: "flywheel-intent-loop",
}


def milestone_kind(milestone):
    """`bolt/x` -> `bolt`. None for a milestone no loop owns."""
    for prefix in LOOP_COMMANDS:
        if milestone and milestone.startswith(prefix):
            return prefix.rstrip("/")
    return None


# ---------------------------------------------------------------------------
# Where a host keeps its server's state
#
# Computed, never written down: `scripts/check-paths.mjs` fails the build for
# a literal home directory in anything under bin/, and it is right to — a path
# baked in here resolves on one laptop and nowhere else.
# ---------------------------------------------------------------------------

def state_dir(org, environ=None, home=None):
    environ = os.environ if environ is None else environ
    base = environ.get("XDG_STATE_HOME")
    root = Path(base) if base else Path(home or Path.home()) / ".local" / "state"
    return root / "flywheel" / org


def server_log(org, **kw):
    return state_dir(org, **kw) / "server.log"


def loop_log(org, kind, slug, **kw):
    return state_dir(org, **kw) / "loops" / f"{kind}-{slug}.log"


def pid_path(org, **kw):
    return state_dir(org, **kw) / "server.pid"


def running_pid(org, alive=None, **kw):
    """The pid of a server already running for this org here, or None.

    A pidfile left by a killed server is not a running server, so the pid is
    probed rather than trusted — one server per org per host is a property
    worth actually having, since two would start every loop twice.
    """
    alive = alive or _alive
    path = pid_path(org, **kw)
    try:
        pid = int(path.read_text().strip())
    except (OSError, ValueError):
        return None
    return pid if alive(pid) else None


def _alive(pid):
    try:
        os.kill(pid, 0)
    except (OSError, ProcessLookupError):
        return False
    return True


def spawn_detached(argv, log_path, popen=subprocess.Popen):
    """Start the server in its own session, output appended to its log.

    `start_new_session=True` is the detach: the daemon outlives the shell
    that ran `flywheel up`, which is the whole point of `up` starting it.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(log_path, "a")  # noqa: SIM115 — owned by the child
    proc = popen(argv, stdout=handle, stderr=handle,
                 stdin=subprocess.DEVNULL, start_new_session=True)
    return proc.pid


# ---------------------------------------------------------------------------
# The plan — pure
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Want:
    milestone: str
    kind: str            # run | archive
    slug: str = ""
    argv: tuple = ()
    why: str = ""


@dataclass(frozen=True)
class ServerPlan:
    start: tuple = ()        # Want
    stop: tuple = ()         # (milestone, kind)
    keep: tuple = ()         # (milestone, kind)
    elsewhere: tuple = ()    # (milestone, host)
    waiting: tuple = ()      # (milestone, seconds left)

    @property
    def quiet(self):
        return not (self.start or self.stop)


@dataclass
class Backoff:
    """Why a restarted loop is not restarted immediately, every time.

    `server_inbox` hands out a `run` job for a milestone holding an item at
    `state:in-progress`, and a loop STOPs when nothing is *ready*. Nothing in
    that pair is wrong, but together they are a 60-second restart loop
    against the GitHub API for any milestone parked mid-flight. So a loop
    that exits against an unchanged job description waits, doubling, and a
    job description that CHANGES releases the wait at once — the tracker
    moving is the signal that there is new work, which is the same signal
    everything else in this design reads.

    This is not in the record. It is named on #74 for review rather than
    smuggled in.
    """

    fingerprint: str = ""
    exits: int = 0
    last_exit: float = 0.0

    def record_exit(self, fingerprint, now):
        if fingerprint == self.fingerprint and self.exits:
            self.exits += 1
        else:
            self.fingerprint, self.exits = fingerprint, 1
        self.last_exit = now

    def wait_left(self, now, fingerprint):
        if not self.exits or fingerprint != self.fingerprint:
            return 0
        delay = min(BACKOFF_BASE_S * (2 ** (self.exits - 1)), BACKOFF_MAX_S)
        return max(0, (self.last_exit + delay) - now)


def plan(jobs, *, teams=None, host=None, running=(), board_teams=None,
         now=0.0, backoff=None, argv_for=None):
    """What this host should start, stop and leave alone. No I/O.

    `running` is the set of `(milestone, kind)` keys with a live process
    here. A job routed to another host is reported and never started — and
    if one is running here for it, it is STOPPED, because re-teaming work is
    exactly how the operator moves a loop between hosts.
    """
    teams = teams or {}
    board_teams = board_teams or {}
    backoff = backoff or {}
    running = set(running)

    start, keep, elsewhere, waiting = [], [], [], []
    ours = set()

    for job in sorted(jobs, key=lambda j: (j.milestone, j.kind)):
        key = (job.milestone, job.kind)
        if milestone_kind(job.milestone) is None:
            continue
        team = board_teams.get(job.milestone)
        # A Team value is an address, `<operator>@<host>` — the value
        # carries its own routing. A bare value falls back to the legacy
        # translation map so an un-migrated board still routes.
        if team and "@" in team:
            want_host = team.rsplit("@", 1)[1]
        elif team:
            want_host = teams.get(team, host)
        else:
            want_host = host
        if host is not None and want_host != host:
            elsewhere.append((job.milestone, want_host))
            continue
        ours.add(key)
        if key in running:
            keep.append(key)
            continue
        held = backoff.get(key)
        left = held.wait_left(now, job.why) if held else 0
        if left > 0:
            waiting.append((job.milestone, int(left)))
            continue
        start.append(Want(
            milestone=job.milestone, kind=job.kind,
            slug=inbox.milestone_slug(job.milestone) or "",
            argv=tuple(argv_for(job)) if argv_for else (),
            why=job.why,
        ))

    stop = [key for key in sorted(running) if key not in ours]

    return ServerPlan(start=tuple(start), stop=tuple(stop), keep=tuple(keep),
                      elsewhere=tuple(elsewhere), waiting=tuple(waiting))


def _sha_match(recorded, current):
    """Shas from different `--format` widths still name the same commit."""
    if not recorded or not current:
        return False
    return recorded.startswith(current) or current.startswith(recorded)


def git_heads(binding, run=None):
    """(book sha, book last-commit epoch, specs sha) for one binding.

    Subtree commits, not repo HEAD: a book inside a larger repo goes stale
    only when a commit touches the book, and specs only when a commit
    touches `openspec/specs/`.
    """
    run = run or _run
    book = str(binding["book"])
    repo = str(binding["repo"])
    got = run(["git", "-C", book, "log", "-1", "--format=%h %ct", "--", "."])
    if got.returncode != 0 or not got.stdout.strip():
        return None
    book_sha, _, epoch = got.stdout.strip().partition(" ")
    got = run(["git", "-C", repo, "log", "-1", "--format=%h", "--",
               "openspec/specs"])
    if got.returncode != 0:
        return None
    specs_sha = got.stdout.strip() or "none"
    try:
        return book_sha, int(epoch), specs_sha
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# The executor
# ---------------------------------------------------------------------------

def _run(argv, cwd=None, env=None, timeout=None):
    return subprocess.run(argv, cwd=cwd, env=env, timeout=timeout,
                          capture_output=True, text=True)


@dataclass(frozen=True)
class ServerConfig:
    org: str = "agentplot"
    repo: str = "flywheel"
    project: str = "Flywheel"
    host: str = None
    loops_cwd: Path = None
    teams: dict = field(default_factory=dict)
    interval: int = INTERVAL_S
    bin_dir: Path = None
    state: Path = None
    operator: str = ""
    # system name -> {"book": Path, "repo": Path, "team": str,
    #                 "settle_minutes": int}. The homing rule as a fact on
    # disk: only bound systems get planning runs.
    books: dict = field(default_factory=dict)

    @property
    def changes_dir(self):
        if not self.loops_cwd:
            return None
        return Path(self.loops_cwd) / "openspec" / "changes"

    @property
    def commands(self):
        return Path(self.bin_dir or Path(__file__).resolve().parent)


@dataclass
class LoopProcess:
    key: tuple
    want: Want
    proc: object
    log_path: Path = None
    started: float = 0.0
    terminated: bool = False


class Server:
    """The reconcile pass, and the daemon that repeats it."""

    def __init__(self, config, tracker=None, gate=None, dispatch=None,
                 run=_run, popen=subprocess.Popen, clock=time.time,
                 sleep=time.sleep, log=None, dry_run=False, opener=None,
                 ledger=None, planner=None, heads=None):
        self.config = config
        self.tracker = tracker
        self.gate = gate            # injected: bin/flywheel's gate_readiness
        # injected: a factory yielding one per-pass session with
        # .relay(items)/.triage(items), each returning {"delivered", "reason"?}
        # — the dispatch MCP server, in production.
        self.dispatch = dispatch
        self.ledger = ledger or obs.NullLedger()
        self.planner = planner      # injected: charge one planning run
        self._deliveries = {}
        self._delivered_sets = {}   # kind -> frozenset of item numbers
        self._plan_charges = 0
        self.heads = heads or git_heads
        self.run = run
        self.popen = popen
        self.clock = clock
        self.sleep = sleep
        self.dry_run = dry_run
        self.opener = opener or self._open_log
        self.log = log or (lambda message: print(message, flush=True))
        self.processes = {}         # (milestone, kind) -> LoopProcess
        self.backoff = {}           # (milestone, kind) -> Backoff
        self.stopping = False

    # -- reads -------------------------------------------------------------

    def board_teams(self):
        """milestone -> Team, a Ready row's answer preferred.

        Ready first because a batch's Ready flip is the approval and so the
        most deliberate statement of where work belongs; any other row is a
        fallback so loose ready items are routable too.
        """
        ready, other = {}, {}
        for row in self.tracker.board_items() or ():
            milestone, team = row.get("milestone"), row.get("team")
            if not milestone or not team:
                continue
            table = ready if row.get("status") == inbox.STATUS_READY else other
            table.setdefault(milestone, team)
        return {**other, **ready}

    def argv_for(self, job):
        """The loop process's command line.

        **Nothing here names a completion signal, because there is nothing
        to name.** The intent loop consumes one label — the operator's
        `stage:done` — and has no parameter selecting between candidates, so
        a daemon cannot answer that question on the operator's behalf by
        accident or otherwise.

        `--repo-dir` is the RECORDS repo — `loops_cwd`, where the
        milestone's openspec change lives. A bolt job also gets the
        fleet's book bindings as one JSON argument, system name → built
        repo and book paths: the loop resolves each unit's built repo from
        its card's `System:` line against this map, so the manifest stays
        the server's to read and the loop never opens fleet.yaml. The bolt
        branch and its worktrees are the loop's to cut and adopt, in the
        built repos — the server passes no worktree.
        """
        slug = inbox.milestone_slug(job.milestone) or ""
        kind = milestone_kind(job.milestone)
        command = self.config.commands / LOOP_COMMANDS[f"{kind}/"]
        argv = [str(command), "--slug", slug,
                "--org", self.config.org, "--repo", self.config.repo,
                "--project", self.config.project,
                "--repo-dir", str(self.config.loops_cwd)]
        if kind == "bolt" and self.config.books:
            bindings = {name: {"repo": str(b["repo"]), "book": str(b["book"])}
                        for name, b in self.config.books.items()
                        if b.get("repo") and b.get("book")}
            if bindings:
                argv += ["--bindings-json",
                         json.dumps(bindings, sort_keys=True)]
        return tuple(argv)

    # -- the pass ----------------------------------------------------------

    def pass_once(self):
        """One reconcile. Never raises: a daemon that dies on a 502 is worse
        than one that logs it and takes the next tick.

        `_flywheel_gh.gh()` exits the process on any gh failure, which is
        right for a one-shot command and fatal for this one, so `SystemExit`
        is caught by name beside everything else. This is the same rule
        `gate_readiness` already states for itself — "fail closed, never fail
        loudly ... least of all a reconcile daemon".
        """
        try:
            return self._pass()
        except SystemExit as error:
            self.log(f"pass failed: {error}")
            return 1
        except Exception as error:  # noqa: BLE001 — deliberate, see above
            self.log(f"pass failed: {error.__class__.__name__}: {error}")
            return 1

    def _pass(self):
        self.reap()
        snapshot = self.tracker.snapshot(with_edges=False)
        jobs = inbox.server_inbox(snapshot, changes_dir=self.config.changes_dir)
        current = plan(
            jobs, teams=self.config.teams, host=self.config.host,
            running=set(self.processes), board_teams=self.board_teams(),
            now=self.clock(), backoff=self.backoff, argv_for=self.argv_for,
        )

        failures = 0
        for key in current.stop:
            self.stop(key, "no job on the tracker")
        for want in current.start:
            if not self.start(want, snapshot):
                failures += 1
        for milestone, host in current.elsewhere:
            self.log(f"{milestone}: routed to {host} — not this host")
        for milestone, left in current.waiting:
            self.log(f"{milestone}: holding {left}s — it exited with the "
                     "tracker unchanged")
        for milestone, kind in current.keep:
            self.log(f"{milestone}: {kind} already running")
        self.write_state(current)

        failures += self.relay(snapshot)
        failures += self.plan_runs(snapshot)
        if current.quiet and not current.keep:
            self.log("nothing actionable on the tracker")
        return 1 if failures else 0

    def write_state(self, current):
        """A per-pass snapshot for `flywheel status` — the daemon's answer
        to run-vs-held, which the tracker alone cannot say."""
        rows = {}
        for want in current.start:
            rows[getattr(want, "milestone", "?")] = {
                "state": "run", "detail": "started this pass"}
        for milestone, kind in current.keep:
            rows[milestone] = {"state": "run", "detail": "loop active"}
        for milestone, left in current.waiting:
            rows[milestone] = {"state": "held",
                               "detail": f"dry; retry in {int(left)}s"}
        for milestone, host in current.elsewhere:
            rows[milestone] = {"state": "elsewhere", "detail": host}
        path = state_dir(self.config.org) / "state.json"
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(
                {"written_unix": self.clock(), "loops": rows}) + "\n")
        except OSError:
            pass

    def relay(self, snapshot):
        """Dispatch's queues, handed over as tool calls — the one standing
        agent, reached only through the dispatch MCP server. Triage and
        relay need a mind and a Discord channel; everything else here is a
        process.

        The queues are serviced in one pass, one tool call each, relay
        first — escalations outrank intake — with the round queue
        (Backlog board work awaiting approval) last. The composition of what
        dispatch actually reads is the proxy's; this pass owes it items,
        not prose. A non-delivery is a ledgered divergence with its
        reason and a pass failure — dispatch absent is a fact now, never
        a silent success.

        One delivery per queue STATE: a standing item leaves triage only
        when a round consumes it, so an unchanged queue re-delivered every
        pass is an endless poke on material dispatch already holds. The
        set delivered last is remembered per kind; only a changed set is
        delivered again, a failed delivery is retried next pass, and an
        emptied queue forgets — the same numbers standing anew are news."""
        box = inbox.dispatch_inbox(snapshot)
        if not self.dispatch:
            return 0
        if box.empty:
            self._delivered_sets.clear()
            return 0
        if self.dry_run:
            for kind, items in (("relay", box.relay), ("triage", box.triage),
                                ("round", box.round)):
                if items:
                    self.log(f"would {kind}: "
                             + ", ".join(f"#{i.number}" for i in items))
            return 0
        failures = 0
        with self.dispatch() as d:
            for kind, call, items in (("relay", d.relay, box.relay),
                                      ("triage", d.triage, box.triage),
                                      ("round", d.round, box.round)):
                if not items:
                    self._delivered_sets.pop(kind, None)
                    continue
                current = frozenset(i.number for i in items)
                if self._delivered_sets.get(kind) == current:
                    continue
                if self._deliver(kind, call, items):
                    failures += 1
                else:
                    self._delivered_sets[kind] = current
        return failures

    def _deliver(self, kind, call, items):
        payload = [{"number": i.number, "title": i.title or "",
                    "url": (f"https://github.com/{self.config.org}/"
                            f"{self.config.repo}/issues/{i.number}")}
                   for i in items]
        nums = ", ".join(f"#{i.number}" for i in items)
        self._deliveries[kind] = self._deliveries.get(kind, 0) + 1
        step = f"{kind}:{self._deliveries[kind]}"
        self.ledger.expect(step, f"dispatch {kind} queue non-empty",
                           f"{kind} delivered — {nums}")
        result = call(payload) or {}
        delivered = bool(result.get("delivered"))
        reason = result.get("reason") or "no reason given"
        self.ledger.actual(step, "delivered" if delivered
                           else f"delivery failed — {reason}", ok=delivered)
        return 0 if delivered else 1

    # -- planning runs -----------------------------------------------------

    def plan_runs(self, snapshot):
        """The bolt planner's triggers, one bound system at a time.

        Staleness is marked whenever an unapproved card's recorded input
        commits no longer match the current heads; a run is charged when a
        system's standing cards are missing or all stale AND the book has
        been quiet for the settle window. A landing needs no code of its
        own: the archive advances `openspec/specs/`, the specs head moves,
        the cards go stale, and the next quiet pass charges the run.
        """
        failures = 0
        for name, binding in sorted((self.config.books or {}).items()):
            try:
                failures += self._plan_run(name, binding, snapshot)
            except (Exception, SystemExit) as error:  # noqa: BLE001 — a
                self.log(f"plan {name}: {error.__class__.__name__}: {error}")
                failures += 1           # binding must not kill the pass
                                        # (gh raises SystemExit on failure)
        return failures

    def _plan_run(self, name, binding, snapshot):
        heads = self.heads(binding, self.run)
        if not heads:
            self.log(f"plan {name}: heads unreadable — skipped")
            return 0
        book_sha, book_epoch, specs_sha = heads

        cards = [c for c in snapshot.plan_cards if c.system == name]
        standing = [c for c in cards if not c.at_ready]
        fresh = []
        for card in standing:
            book_rec, specs_rec = card.derived_from
            current = (_sha_match(book_rec, book_sha)
                       and _sha_match(specs_rec, specs_sha))
            if current:
                fresh.append(card)
            elif not card.stale:
                if self.dry_run:
                    self.log(f"plan {name}: would mark #{card.number} stale")
                else:
                    self.tracker.add_label(card.number, inbox.STALE)
                    self.ledger.note(
                        f"#{card.number} marked stale — inputs moved "
                        f"(book {book_sha}, specs {specs_sha}) — Kanban")

        settle_s = int(binding.get("settle_minutes", 90)) * 60
        quiet = (self.clock() - book_epoch) >= settle_s
        if fresh or not quiet or not self.planner:
            return 0

        key = (f"plan/{name}", "planner")
        held = self.backoff.get(key)
        why = f"cards {'stale' if standing else 'missing'}, book settled"
        if held and held.wait_left(self.clock(), why) > 0:
            return 0

        order = (f"bolt planning for {name} — book {binding['book']}, "
                 f"repo {binding['repo']}, mode: board, tracker "
                 f"{self.config.org}/{self.config.repo}, team "
                 f"{binding.get('team', '')}")
        if self.dry_run:
            self.log(f"plan {name}: would charge a planning run — {why}")
            return 0
        self._plan_charges += 1
        step = f"plan:{name}:{self._plan_charges}"
        self.ledger.expect(step, why, "plan cards filed at Backlog")
        charged = bool(self.planner(name, binding, order))
        self.ledger.actual(step, "charged" if charged else "charge failed",
                           ok=charged)
        self.backoff.setdefault(key, Backoff()).record_exit(why, self.clock())
        return 0 if charged else 1

    # -- processes ---------------------------------------------------------

    def _open_log(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        return open(path, "a")  # noqa: SIM115 — owned by the child process

    def start(self, want, snapshot=None):
        if want.kind == "archive":
            return self.archive(want, snapshot)
        if self.dry_run:
            self.log(f"would start {want.milestone} ({want.why})")
            return True
        if self.gate and self.config.loops_cwd:
            check = self.gate(Path(self.config.loops_cwd))
            if check is not None and not getattr(check, "ok", True):
                self.log(f"{want.milestone}: not started — its repo's merge "
                         "gate is not runnable")
                return False
        kind = milestone_kind(want.milestone)
        path = loop_log(self.config.org, kind, want.slug)
        handle = self.opener(path)
        try:
            proc = self.popen(list(want.argv), stdout=handle, stderr=handle,
                              stdin=subprocess.DEVNULL,
                              cwd=str(self.config.loops_cwd))
        except OSError as error:
            self.log(f"{want.milestone}: start failed: {error}")
            return False
        self.processes[(want.milestone, want.kind)] = LoopProcess(
            key=(want.milestone, want.kind), want=want, proc=proc,
            log_path=path, started=self.clock())
        self.log(f"started {want.milestone} (pid {getattr(proc, 'pid', '?')}) "
                 f"· {want.why} · log {path}")
        return True

    def reap(self):
        """Collect finished loops. An exit is not a failure — a loop that
        found nothing ready and stopped is the design working."""
        for key, loop in list(self.processes.items()):
            code = loop.proc.poll()
            if code is None:
                continue
            del self.processes[key]
            held = self.backoff.setdefault(key, Backoff())
            held.record_exit(loop.want.why, self.clock())
            ran = int(self.clock() - loop.started)
            self.log(f"{key[0]}: exited rc={code} after {ran}s · "
                     f"{loop.log_path}")

    def stop(self, key, why=""):
        """SIGTERM, and SIGKILL if it is still there on the next pass.

        Killing a loop mid-cycle is safe by construction and not by luck: the
        loops hold no state between runs, their guards are idempotent, and a
        later job starts a fresh process that re-reads the tracker and the
        records.
        """
        loop = self.processes.get(key)
        if loop is None:
            return
        if self.dry_run:
            self.log(f"would stop {key[0]}: {why}")
            return
        if loop.terminated:
            loop.proc.kill()
            self.log(f"killed {key[0]}: it ignored SIGTERM")
            return
        loop.proc.terminate()
        loop.terminated = True
        self.log(f"stopping {key[0]}: {why}")

    def stop_all(self):
        for key in list(self.processes):
            self.stop(key, "the server is shutting down")
        # Counted rounds, not a wall clock: the grace period must end whether
        # or not the clock it was given moves, and a teardown that can spin
        # forever is worse than one that kills a second early.
        for _round in range(STOP_GRACE_S):
            if not self.processes:
                break
            self.sleep(1)
            self.reap()
        for key, loop in list(self.processes.items()):
            loop.proc.kill()
            self.log(f"killed {key[0]}: it outlived the grace period")
            del self.processes[key]

    # -- the archive one-shot ----------------------------------------------

    def archive(self, want, snapshot=None):
        """A closed milestone whose change is still on disk.

        `openspec archive <slug> --yes --json` is deterministic and cannot
        prompt: measured against openspec 1.8.0, whose `archive.js` says JSON
        mode "never prompts at all" and turns every decision point into an
        `ArchiveBlockedError` carrying a machine-readable diagnostic and a
        non-zero exit. So the mechanism is code — and the one decision the
        code cannot take goes to the operator as a label, which is the same
        andon shape the loops use.
        """
        slug, cwd = want.slug, str(self.config.loops_cwd)
        change = inbox.resolve_change_id(self.config.changes_dir, want.milestone)
        if self.dry_run:
            self.log(f"would archive {change} ({want.milestone})")
            return True
        if want.milestone.startswith(inbox.BOLT_PREFIX):
            # The close released the landing; the archive follows it. A bolt
            # branch still un-landed means the loop has work first — retry
            # on a later pass, no flag: this is sequencing, not a defect.
            branch = f"bolt/{slug}"
            exists = self.run(["git", "rev-parse", "-q", "--verify", branch],
                              cwd=cwd)
            if getattr(exists, "returncode", 1) == 0:
                landed = self.run(
                    ["git", "merge-base", "--is-ancestor", branch, "main"],
                    cwd=cwd)
                if getattr(landed, "returncode", 1) != 0:
                    self.log(f"{want.milestone}: closed but not landed — "
                             f"the landing runs first; archive follows")
                    return False
        out = self.run(["openspec", "archive", change, "--yes", "--json"],
                       cwd=cwd)
        if getattr(out, "returncode", 1) != 0:
            why = _diagnostic(out)
            self.log(f"{want.milestone}: archive blocked — {why}")
            self.flag(want.milestone, snapshot, f"archive blocked: {why}")
            return False
        merging = self.run(["git", "rev-parse", "-q", "--verify", "MERGE_HEAD"],
                           cwd=cwd)
        if getattr(merging, "returncode", 1) == 0:
            why = "the checkout is mid-merge; the archive is not committed"
            self.log(f"{want.milestone}: {why}")
            self.flag(want.milestone, snapshot, why)
            return False
        status = self.run(["git", "status", "--porcelain", "--", "openspec/"],
                          cwd=cwd)
        if not (status.stdout or "").strip():
            self.log(f"{want.milestone}: archived {change}, nothing to commit")
            return True
        self.run(["git", "add", "--", "openspec/"], cwd=cwd)
        commit = self.run(
            ["git", "commit", "-m", f"chore(openspec): archive {change}",
             "--", "openspec/"], cwd=cwd)
        if getattr(commit, "returncode", 1) != 0:
            why = (commit.stderr or commit.stdout or "").strip()[:200]
            self.log(f"{want.milestone}: archive commit failed — {why}")
            self.flag(want.milestone, snapshot, f"archive commit failed: {why}")
            return False
        self.log(f"{want.milestone}: archived {change} and committed")
        return True

    def flag(self, milestone, snapshot, why):
        """Route a decision this server cannot take to the operator.

        `set_needs_operator` writes only when the label is absent, so a
        blocked archive re-read every 60 seconds stays a dry cycle.
        """
        if snapshot is None or self.tracker is None:
            return
        open_items = [i for i in snapshot.on(milestone) if i.is_open]
        if not open_items:
            self.log(f"  {milestone} has no open item to flag — "
                     "the operator reads this in the server log")
            return
        for item in open_items:
            inbox.set_needs_operator(self.tracker, item.number, why)

    # -- the daemon --------------------------------------------------------

    def install_signals(self, handler=signal.signal):
        """SIGINT and SIGTERM end the pass and take the children down.

        The first signal handling in this repo, so it is small on purpose:
        the handler sets a flag and nothing else, and every teardown decision
        is taken on the main path where it can be logged.
        """
        def stop(_signum, _frame):
            self.stopping = True

        for sig in (signal.SIGINT, signal.SIGTERM):
            handler(sig, stop)

    def serve(self, interval=None, once=False):
        interval = self.config.interval if interval is None else interval
        rc = 0
        while not self.stopping:
            rc = self.pass_once()
            if once or self.stopping:
                break
            self.log(f"-- next pass in {interval}s --")
            self.nap(interval)
        if not once:
            self.stop_all()
        return rc

    def nap(self, seconds):
        """Sleep in one-second bites so a signal lands within a second."""
        for _second in range(int(seconds)):
            if self.stopping:
                return
            self.sleep(1)


def _diagnostic(out):
    """openspec's machine-readable reason, or its first line of stderr."""
    for stream in (getattr(out, "stdout", ""), getattr(out, "stderr", "")):
        for line in (stream or "").splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            found = _find_message(data)
            if found:
                return found
    text = (getattr(out, "stderr", "") or getattr(out, "stdout", "") or "").strip()
    return text.splitlines()[0][:200] if text else "no reason given"


def _find_message(data):
    if isinstance(data, dict):
        if isinstance(data.get("message"), str) and data.get("code"):
            return data["message"]
        for value in data.values():
            found = _find_message(value)
            if found:
                return found
    elif isinstance(data, list):
        for value in data:
            found = _find_message(value)
            if found:
                return found
    return None
