"""The design loop, as an ordinary program.

`design/loop-programs.md`, "The intent loop":

    query+guards (flip-consume, handoff birth, compose) ->
    typed design sessions -> collect deliverables ->
    merge sess/* branches -> re-query ... STOP

This module is the driver; `bin/flywheel-intent-loop` is its command. The
filters and their guard PLANS are `_flywheel_inbox`'s, the launching and
waiting are `_flywheel_sessions`'s, and what is here is the part neither of
them can be: the cycle, the guards' writes, the batching, the dispatch, and
the landing.

Import from a sibling script:

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _flywheel_intent import Config, run

**Every mutation goes through one `Writer`.** Tracker writes, `flywheel-batch`,
`wt`, worktree teardown — all of it. That is what makes `--dry-run` and
`--fixture` a single branch instead of a branch at each call site, and it is
what lets a test assert the property the whole stateless-process design rests
on: a second cycle against an unchanged tracker writes nothing.

**Completion is the operator's, and R1 is open.** `design/loop-programs.md`
leaves "the exact GitHub signal for *operator marks a design session done*" to
the operator (R1). All three candidates are implemented below and none is the
default: without `--completion-signal` the loop runs everything up to and
including supervision and then stops before collecting, saying so. A session
settling is NOT completion — the operator may iterate a plannotator or lavish
round as often as they like.
"""

import json
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _flywheel_inbox import (CLOSED_DONE, ELABORATION, INTENT_PREFIX,
                             IN_PROGRESS, NEEDS_OPERATOR, QUEUED, READY,
                             STATUS_BACKLOG, TYPE_ASSERTION, Tracker,
                             TrackerSnapshot, clear_needs_operator,
                             find_andon, intent_inbox, set_needs_operator,
                             unblocked)
from _flywheel_sessions import (MAX_NAME, SessionSpec, WaitState, runner_for,
                                supervise, work_order)


class LoopStop(Exception):
    """A cycle that cannot go on. The run stops with this in its report.

    "a cycle that cannot read the tracker, mint its token, or resolve its
    parameters STOPS THE RUN with the failure in the report; a failing cycle
    never loops."
    """


# ---------------------------------------------------------------------------
# The six design types — one enumeration, and this is it
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DesignType:
    """A design session type and its launch mechanics.

    `profile` follows the single rule in
    `openspec/specs/flywheel-inception-skill/spec.md`: does this session build
    a lavish surface? Interactive does and takes
    `flywheel-interactive-session`; the other five take
    `flywheel-design-session`. No second basis is admitted.

    `model` is the default column of
    `openspec/specs/flywheel-session-type-skills/spec.md`.

    `operator_round` is the intent schema's LIMITS paragraph: planning,
    interactive and handoff hold operator rounds by design, so they notify at
    90 minutes like everything else but never auto-stall.

    `worktree` is herdr.md's "a session that edits no files gets no worktree —
    skip the `wt switch`, start it in the launch directory, and skip the merge
    and teardown too". Research is the type that reads: "the finding is the
    item comment and the report; nothing is built."

    `alone` is the schema's "prototypes always alone" — each is its own
    experiment.
    """

    name: str
    profile: str
    model: str
    operator_round: bool
    worktree: bool
    alone: bool = False


TYPES = {t.name: t for t in (
    DesignType("planning", "flywheel-design-session", "fable", True, True),
    DesignType("interactive", "flywheel-interactive-session", "fable", True, True),
    DesignType("handoff", "flywheel-design-session", "opus", True, True),
    DesignType("research", "flywheel-design-session", "opus[1m]", False, False),
    DesignType("prototype", "flywheel-design-session", "opus", False, True, alone=True),
    DesignType("writeback", "flywheel-design-session", "opus", False, True),
)}


def type_of(item):
    """The item's `type:` label, without its prefix, or None.

    Invariant 4: "`type:*` is the session type that works the item." There is
    NO default here, and that is deliberate — the compiled fixture
    (`workflows/fixtures/flywheel-intent.compiled.js`) falls back to
    `type:research`, which would hand a released assertion to a research
    session. An item the loop cannot type is reported, not guessed at.
    """
    for label in sorted(item.labels):
        if label.startswith("type:"):
            return label[len("type:"):]
    return None


# ---------------------------------------------------------------------------
# The one seam every mutation passes through
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Write:
    kind: str          # label | body | comment | issue | close | command
    target: str
    detail: str = ""

    def __str__(self):
        detail = f" — {self.detail}" if self.detail else ""
        return f"{self.kind} {self.target}{detail}"


def _subprocess_run(argv, cwd=None, timeout=None):
    return subprocess.run(argv, cwd=cwd, timeout=timeout,
                          capture_output=True, text=True)


class Writer:
    """Records every mutation, and performs it when `apply` is set.

    The read half — `has_label` — is answered from the cycle's snapshot plus
    whatever this writer has already added, which is what keeps
    `_flywheel_inbox.set_needs_operator`'s idempotence honest in dry-run and
    fixture modes where there is no tracker to ask. The four-method surface
    (`has_label`/`add_label`/`remove_label`/`comment`) is deliberately the one
    `set_needs_operator` and `clear_needs_operator` already take, so those are
    reused rather than reimplemented.
    """

    def __init__(self, tracker=None, apply=True, run=None, snapshot=None):
        self.tracker = tracker
        self.apply = apply
        self._run = run or _subprocess_run
        self.snapshot = snapshot
        self.writes = []
        self._added = {}
        self.created = []   # issue numbers born this cycle, for wait_listed

    # -- bookkeeping -------------------------------------------------------

    def _record(self, kind, target, detail=""):
        self.writes.append(Write(kind, str(target), detail))

    def mark(self):
        """A cursor into the write log, for 'what did THIS cycle write'."""
        return len(self.writes)

    def since(self, mark):
        return tuple(self.writes[mark:])

    # -- the tracker surface `set_needs_operator` expects -------------------

    def has_label(self, number, label):
        if label in self._added.get(number, set()):
            return True
        if self.snapshot is not None:
            item = self.snapshot.item(number)
            if item is not None:
                return label in item.labels
        if self.tracker is not None:
            return self.tracker.has_label(number, label)
        return False

    def add_label(self, number, label):
        self._added.setdefault(number, set()).add(label)
        self._record("label", f"#{number}", f"+{label}")
        if self.apply and self.tracker:
            self.tracker.add_label(number, label)

    def remove_label(self, number, label):
        self._added.get(number, set()).discard(label)
        self._record("label", f"#{number}", f"-{label}")
        if self.apply and self.tracker:
            self.tracker.remove_label(number, label)

    def comment(self, number, body):
        self._record("comment", f"#{number}", body.splitlines()[0][:80])
        if self.apply and self.tracker:
            self.tracker.comment(number, body)

    # -- the rest ----------------------------------------------------------

    def relabel(self, number, remove=(), add=()):
        for label in remove:
            self.remove_label(number, label)
        for label in add:
            self.add_label(number, label)

    def set_body(self, number, body):
        self._record("body", f"#{number}", "rewrite")
        if self.apply and self.tracker:
            self.tracker.set_body(number, body)

    def create_issue(self, title, body, labels=(), milestone=None):
        self._record("issue", title, " ".join(labels))
        if self.apply and self.tracker:
            number = self.tracker.create_issue(title, body, labels, milestone)
            if number:
                self.created.append(number)
            return number
        return None

    def close_issue(self, number, comment=None, reason=CLOSED_DONE):
        self._record("close", f"#{number}", reason or "")
        if self.apply and self.tracker:
            self.tracker.close_issue(number, comment, reason)

    def command(self, argv, cwd=None, what=""):
        """A subprocess that changes the world — `flywheel-batch`, `wt`, herdr
        teardown. Reads never come through here."""
        self._record("command", what or Path(argv[0]).name,
                     " ".join(shlex.quote(a) for a in argv[1:6]))
        if not self.apply:
            return None
        result = self._run(argv, cwd=str(cwd) if cwd else None)
        if result.returncode != 0:
            raise LoopStop(
                f"{what or argv[0]} failed: "
                f"{(result.stderr or '').strip() or (result.stdout or '').strip()}"
            )
        return result


# ---------------------------------------------------------------------------
# Guard 1 — flip-consume
# ---------------------------------------------------------------------------

def apply_flip_consume(writer, numbers):
    """`state:queued` -> `state:ready`, for the sub-issues a Ready batch releases.

    The plan is `_flywheel_inbox.flip_consume_plan`'s and it only ever names
    sub-issues of a batch the OPERATOR moved to Ready. Idempotent by
    construction: an item already `state:ready` is not in the plan, so applying
    the plan empties it.
    """
    for number in numbers:
        writer.relabel(number, remove=[QUEUED], add=[READY])


# ---------------------------------------------------------------------------
# Guard 2 — handoff birth and amend
# ---------------------------------------------------------------------------

HANDOFF_SET_OPEN = "<!-- flywheel:handoff-set -->"
HANDOFF_SET_CLOSE = "<!-- /flywheel:handoff-set -->"

_HANDOFF_SET = re.compile(
    re.escape(HANDOFF_SET_OPEN) + r"(?P<body>.*?)" + re.escape(HANDOFF_SET_CLOSE),
    re.DOTALL,
)


def format_handoff_set(numbers):
    listing = " ".join(f"#{n}" for n in sorted(numbers))
    return f"{HANDOFF_SET_OPEN}\n{listing}\n{HANDOFF_SET_CLOSE}"


def parse_handoff_set(body):
    """The assertion set an existing handoff item names, or None.

    This is what makes an amend SILENT when nothing changed, and a silent
    amend is the dry-cycle property: birth on cycle N is seen as amend on
    cycle N+1 forever after, because the assertions stay open and unbatched on
    the milestone until the handoff SESSION makes the custody move. An amend
    that rewrote an unchanged body would make every cycle wet, and the loop
    would never quiet.
    """
    found = _HANDOFF_SET.search(body or "")
    if not found:
        return None
    return tuple(sorted(int(n) for n in re.findall(r"#(\d+)", found.group("body"))))


def handoff_body(slug, numbers):
    return "\n".join([
        f"Settled, unbolted assertions on `{INTENT_PREFIX}{slug}` — assertions "
        "open on this milestone with no parent batch and no open blocker.",
        "",
        format_handoff_set(numbers),
        "",
        "Born by the intent loop's handoff-birth guard. The handoff session "
        "that works this item plans the bolt and makes the custody move; the "
        "loop creates the item and never moves a milestone itself.",
    ])


def apply_handoff(writer, plan, snapshot, slug):
    """Ensure ONE open `type:handoff` item names exactly the settled set.

    Two branches, `_flywheel_inbox.handoff_plan`'s: BIRTH when no open handoff
    sits unsealed, AMEND when one does. The guard creates the ITEM and attaches
    no sub-issues — the assertions leave this milestone when the handoff
    session moves them to `bolt/<slug>`, and that move is the bolting.
    """
    if plan is None:
        return
    numbers = tuple(sorted(i.number for i in plan.assertions))
    if plan.action == "amend":
        item = snapshot.item(plan.handoff_item)
        current = parse_handoff_set(item.body if item else "")
        if current == numbers:
            return                      # unchanged — write nothing
        writer.set_body(plan.handoff_item, handoff_body(slug, numbers))
        writer.comment(
            plan.handoff_item,
            "The settled, unbolted set moved: now "
            + " ".join(f"#{n}" for n in numbers)
            + ". Amended by the intent loop's handoff-birth guard.",
        )
        return
    writer.create_issue(
        title=f"Plan the bolt for the settled assertions on {slug}",
        body=handoff_body(slug, numbers),
        labels=["type:handoff", QUEUED],
        milestone=f"{INTENT_PREFIX}{slug}",
    )


# ---------------------------------------------------------------------------
# Guard 3 — compose
# ---------------------------------------------------------------------------

def apply_compose(writer, items, config, snapshot=None):
    """Orphan `state:queued` items into one proposed batch at Backlog.

    Composing is not releasing — `flywheel-batch` puts the parent at Backlog
    and never writes Ready; the operator's flip is the release. "By thread"
    with no thread signal available on the tracker reduces to one batch: the
    loop never splits by guess.
    """
    if not items:
        return
    argv = [
        str(config.batch_cmd),
        "--org", config.org,
        "--repo", config.repo,
        "--kind", "elaboration",
        "--milestone", config.milestone,
        "--title", f"Work the queued design items on {config.slug}",
        "--project", config.project,
    ]
    # AMEND, like handoff birth: while an open elaboration for this
    # milestone sits at Backlog, newcomers JOIN it — a new batch per
    # sweep fragments the queue into near-identical containers (observed
    # live: #131/#132, #109/#114/#129).
    if snapshot is not None:
        for b in sorted(snapshot.batches, key=lambda b: b.number):
            if (b.kind == ELABORATION and b.status == STATUS_BACKLOG
                    and b.milestone == config.milestone):
                argv += ["--into", str(b.number)]
                break
    argv += [str(i.number) for i in sorted(items, key=lambda i: i.number)]
    result = writer.command(argv, cwd=config.repo_dir, what="flywheel-batch")
    if result is not None:
        match = re.search(r"^(?:unit|elaboration) #(\d+):",
                          (result.stdout or ""), re.MULTILINE)
        if match:
            writer.created.append(int(match.group(1)))


def wait_listed(tracker, numbers, milestone, tries=8, pause=5,
                sleep=time.sleep):
    """Read-your-writes over an eventually consistent list.

    GitHub's issue list can lag a fresh creation, and the next cycle's
    snapshot IS that list — a birth invisible to it births again
    (observed live: handoffs #128/#130, elaborations #131/#132). A cycle
    that created something does not proceed until its creations are
    listed, so no successor ever reads a pre-write list.
    """
    missing = set(numbers)
    for _ in range(tries):
        snap = tracker.snapshot(milestone=milestone)
        missing -= {i.number for i in snap.items}
        if not missing:
            return True
        sleep(pause)
    return False


def run_guards(writer, inbox, snapshot, config):
    """All three, every cycle, in order, each idempotent. Returns its writes."""
    mark = writer.mark()
    apply_flip_consume(writer, inbox.queued_to_flip)
    apply_handoff(writer, inbox.handoff, snapshot, config.slug)
    apply_compose(writer, inbox.orphan_queued, config, snapshot)
    return writer.since(mark)


# ---------------------------------------------------------------------------
# Batching — one session type per batch, prototypes alone
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DesignBatch:
    type: str
    items: tuple

    @property
    def numbers(self):
        return tuple(i.number for i in self.items)

    @property
    def first(self):
        return self.items[0].number


def batch_ready(snapshot, items):
    """(batches, undispatchable) from the ready set.

    "batch the ready items by their type label - one session type per batch,
    prototypes always alone. A batch runs only when every blocked_by of every
    item in it is closed - computed from the field, not reasoned."

    `type:assertion` is never dispatched: it is a released claim, guard 2's
    business and construction's, not a design session's.
    """
    groups, undispatchable = {}, []
    for item in sorted(unblocked(snapshot, items), key=lambda i: i.number):
        kind = type_of(item)
        if kind not in TYPES:
            undispatchable.append((item, kind))
            continue
        key = (kind, item.number if TYPES[kind].alone else -1)
        groups.setdefault(key, []).append(item)
    batches = tuple(
        DesignBatch(kind, tuple(members))
        for (kind, _), members in sorted(groups.items())
    )
    return batches, tuple(undispatchable)


def session_name(batch, slug):
    """`<type>-<topic>` — the name IS the classification, and herdr caps it at
    32 characters.

    Deterministic, because a stateless loop process restarts freely and
    `HerdrRunner.launch` reuses an agent already running under the name. A name
    that moved between runs would launch a second session onto the same work.
    """
    stem = f"{batch.type}-{slug}"
    if TYPES[batch.type].alone:
        suffix = f"-{batch.first}"
        return stem[:MAX_NAME - len(suffix)] + suffix
    return stem[:MAX_NAME]


def session_order(batch, config):
    """One prompt, the summary line first.

    Design types have NO canonical slash-command invocation — the profile
    loads the type skill the work order names — so the first line is the
    repo's own compiled shape rather than an invented `/flywheel:<type>`.
    """
    nums = ", ".join(f"#{n}" for n in batch.numbers)
    invocation = f"{batch.type} session for intent {config.slug} - items {nums}"
    brief = "\n".join([
        f"Change: {config.slug}. Session type: {batch.type}. "
        f"Items: {nums}.",
        "",
        config.goal or (
            "Work the items: read each item body and the change's records, "
            "close what the batch can close, and report what it cannot."
        ),
        "",
        f"Your session directory is "
        f"openspec/changes/{config.slug}/sessions/<date>-<topic>/ and you are "
        "its sole writer. Write your records (decisions, questions, "
        "assertions, the session README) in your worktree; queue your own "
        "discoveries as items — whoever finds queues; comment each item you "
        "worked; never close your own items.",
        "",
        f'Tracker writes run as the app: '
        f'GH_TOKEN=$("{config.plugin_bin}/flywheel-token" --org {config.org}); '
        "if the token cannot mint, stop and report failed — never ambient "
        "credentials.",
        "",
        "Deliver by settling: comment your items, print your report as your "
        "final message, and settle. Never wait on the loop.",
    ])
    return work_order(invocation, brief)


# ---------------------------------------------------------------------------
# The dispatch record — how a restarted loop recovers a session's clock
# ---------------------------------------------------------------------------

DISPATCH_OPEN = "<!-- flywheel:dispatch "
_DISPATCH = re.compile(
    re.escape(DISPATCH_OPEN) + r"(?P<fields>[^>]*?)-->", re.DOTALL)


def format_dispatch(name, origin, notified=False):
    return (f"{DISPATCH_OPEN}name={name} origin={origin:.0f} "
            f"notified={1 if notified else 0} -->\n"
            f"Dispatched design session `{name}`.")


def parse_dispatch(comments, name=None):
    """(origin, notified) recovered from the item's comments, or (None, False).

    `supervise` takes a WALL clock and an `origin` for a stated reason: loop
    processes are stateless and restart freely, and a session handed a fresh
    four-hour budget on every restart never stalls at all. herdr carries no
    timestamp to recover it from — so the tracker does, which it can, because
    the tracker is the only bus by construction.
    """
    latest = (None, False)
    for comment in comments or ():
        body = comment.get("body") if isinstance(comment, dict) else comment
        found = _DISPATCH.search(body or "")
        if not found:
            continue
        fields = dict(
            pair.split("=", 1)
            for pair in found.group("fields").split()
            if "=" in pair
        )
        if name is not None and fields.get("name") != name:
            continue
        try:
            latest = (float(fields.get("origin")),
                      fields.get("notified") == "1")
        except (TypeError, ValueError):
            continue
    return latest


# ---------------------------------------------------------------------------
# Completion — the R1 seam. Three candidates, no default.
# ---------------------------------------------------------------------------

R1_UNRESOLVED = (
    'R1 unresolved: the operator has not named the signal for "design session '
    'done" (design/loop-programs.md, R1 — a state label, a board Status, or '
    "closing the items). Pass --completion-signal to name it. Sessions were "
    "dispatched and supervised; nothing was collected, merged or closed."
)


@dataclass
class CompletionContext:
    snapshot: object
    board: dict = field(default_factory=dict)
    done_label: str = None
    done_status: str = None


def _done_closed(batch, ctx):
    """Every item in the batch is closed on the tracker."""
    for number in batch.numbers:
        item = ctx.snapshot.item(number)
        if item is not None and item.is_open:
            return False
    return True


def _done_label(batch, ctx):
    """Every item carries the label the operator sets to mean done."""
    if not ctx.done_label:
        raise LoopStop("--completion-signal label needs --done-label")
    for number in batch.numbers:
        item = ctx.snapshot.item(number)
        if item is None:               # closed items satisfy any signal
            continue
        if ctx.done_label not in item.labels:
            return False
    return True


def _done_board(batch, ctx):
    """Every item's board row is at the done Status."""
    if not ctx.done_status:
        raise LoopStop("--completion-signal board needs --done-status")
    for number in batch.numbers:
        item = ctx.snapshot.item(number)
        if item is None:
            continue
        if (ctx.board.get(number) or {}).get("status") != ctx.done_status:
            return False
    return True


COMPLETION_SIGNALS = {
    "closed": _done_closed,
    "label": _done_label,
    "board": _done_board,
}


def is_complete(batch, config, ctx):
    """Has the OPERATOR marked this session done?

    Never inferred from the session settling: "the operator may iterate a
    plannotator or lavish round as many times as they want", and a loop that
    read a settled pane as a finished session would collect half a decision.
    """
    signal = COMPLETION_SIGNALS.get(config.completion_signal)
    if signal is None:
        return None                    # R1 unresolved — not False, unknown
    return signal(batch, ctx)


# ---------------------------------------------------------------------------
# Worktrees and the merge
# ---------------------------------------------------------------------------

APPROVAL_BLOCK = "Cannot prompt for approval in non-interactive environment"


def worktree_path(repo_dir, branch, run=None):
    """Where `wt` put the worktree for a branch, read from git rather than
    parsed out of `wt`'s prose."""
    run = run or _subprocess_run
    result = run(["git", "worktree", "list", "--porcelain"], cwd=str(repo_dir))
    if result.returncode != 0:
        return None
    path = None
    for line in (result.stdout or "").splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree "):].strip()
        elif line.strip() == f"branch refs/heads/{branch}":
            return path
    return None


def ensure_worktree(writer, config, name):
    """`sess/<name>`, cut from the base branch, idempotently."""
    branch = f"sess/{name}"
    existing = worktree_path(config.repo_dir, branch, run=writer._run)
    if existing:
        return existing
    writer.command(
        ["wt", "switch", "--create", branch, "--base", config.base_branch,
         "--no-cd"],
        cwd=config.repo_dir, what="wt switch",
    )
    return worktree_path(config.repo_dir, branch, run=writer._run) or branch


def merge_session(writer, config, worktree):
    """Through the gate, never around it.

    `wt merge` runs the repo's three `[pre-merge]` hooks on every shape that
    does not suppress them, so the green claim is the tool's rather than
    ours: no `--yes`, no `--no-hooks`, no `--no-verify`, and hand-running the
    three scripts is not a substitute. The merge driver runs in the repo's
    main checkout; a work session gets a worktree, a merge stage never does.
    Serialized by construction — this loop merges one batch at a time.
    """
    try:
        writer.command(["wt", "merge", "--no-remove", "-C", str(worktree)],
                       cwd=config.repo_dir, what="wt merge")
    except LoopStop as stop:
        if APPROVAL_BLOCK in str(stop):
            raise LoopStop(
                f"{stop} — the gate needs an approval this run cannot give. "
                "That is a work stoppage for the operator, not something to "
                "route around."
            )
        raise


# ---------------------------------------------------------------------------
# Config and report
# ---------------------------------------------------------------------------

@dataclass
class Config:
    slug: str
    org: str = "agentplot"
    repo: str = "flywheel"
    project: str = "Flywheel"
    repo_dir: Path = Path(".")
    base_branch: str = "main"
    goal: str = None
    completion_signal: str = None
    done_label: str = None
    done_status: str = None
    apply: bool = True
    fixture: str = None
    max_cycles: int = 20
    plugin_bin: Path = Path(__file__).resolve().parent

    @property
    def milestone(self):
        return f"{INTENT_PREFIX}{self.slug}"

    @property
    def batch_cmd(self):
        return Path(self.plugin_bin) / "flywheel-batch"

    @classmethod
    def from_mapping(cls, raw):
        """Defensive parse (#29): an args object arriving as a JSON string is
        parsed, never trusted as-is."""
        if isinstance(raw, str):
            raw = json.loads(raw)
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in dict(raw).items() if k in known})


@dataclass
class Report:
    slug: str
    status: str = "ok"                 # ok | stopped
    failure: str = None
    cycles: int = 0
    writes: tuple = ()
    dispatched: tuple = ()
    resting: tuple = ()
    notes: tuple = ()

    def render(self):
        lines = [f"intent loop · {self.slug} · {self.status} · "
                 f"{self.cycles} cycle(s)"]
        if self.failure:
            lines += ["", f"STOPPED: {self.failure}"]
        if self.dispatched:
            lines += ["", "dispatched:"] + [f"  {d}" for d in self.dispatched]
        if self.writes:
            lines += ["", f"writes ({len(self.writes)}):"]
            lines += [f"  {w}" for w in self.writes]
        else:
            lines += ["", "writes: none"]
        lines += ["", "the queue at rest:"]
        lines += [f"  {r}" for r in self.resting] or ["  (empty)"]
        if self.notes:
            lines += [""] + [f"note: {n}" for n in self.notes]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# The cycle
# ---------------------------------------------------------------------------

def config_fault(config):
    """Why this run cannot start, or None. Checked before anything is read —
    "a cycle that cannot resolve its parameters STOPS THE RUN"."""
    if not config.slug:
        return "no intent slug — the loop runs one milestone"
    signal = config.completion_signal
    if signal is not None and signal not in COMPLETION_SIGNALS:
        return (f"unknown completion signal {signal!r} — one of "
                f"{', '.join(sorted(COMPLETION_SIGNALS))}")
    if signal == "label" and not config.done_label:
        return "--completion-signal label needs --done-label"
    if signal == "board" and not config.done_status:
        return "--completion-signal board needs --done-status"
    return None


def read_snapshot(config, tracker):
    if config.fixture:
        return TrackerSnapshot.from_fixture(config.fixture)
    if tracker is None:
        raise LoopStop("no tracker and no fixture — nothing to read")
    return tracker.snapshot(milestone=config.milestone)


def resting_queue(inbox, snapshot, undispatchable):
    """One line per batch and unbatched item — the report the record asks for.

    "An empty ready set with a full queue is the correct resting state."
    """
    lines = []
    for batch in snapshot.batches:
        if batch.milestone in (None, inbox.milestone):
            lines.append(f"batch #{batch.number} [{batch.kind or 'batch'}] "
                         f"{batch.status or 'unplaced'} — "
                         f"{len(batch.sub_issues)} item(s)")
    for item in sorted(snapshot.on(inbox.milestone), key=lambda i: i.number):
        if not item.is_open or item.parent_batch is not None:
            continue
        state = next((l for l in sorted(item.labels)
                      if l.startswith("state:")), "unstated")
        lines.append(f"#{item.number} [{type_of(item) or 'untyped'}] {state} — "
                     f"{item.title[:60]}")
    for item, kind in undispatchable:
        lines.append(f"#{item.number} NOT DISPATCHED — "
                     f"type {kind or 'missing'} is not a design type")
    return tuple(lines)


def dispatch_batch(batch, writer, runner, config, clock):
    """Flip the items in progress, record the origin, launch. Idempotent."""
    name = session_name(batch, config.slug)
    cwd = config.repo_dir
    if TYPES[batch.type].worktree:
        cwd = ensure_worktree(writer, config, name)
    spec = SessionSpec(
        name=name,
        cwd=str(cwd),
        order=session_order(batch, config),
        profile=TYPES[batch.type].profile,
        model=TYPES[batch.type].model,
        operator_round=TYPES[batch.type].operator_round,
    )
    for item in batch.items:
        if READY in item.labels:
            writer.relabel(item.number, remove=[READY], add=[IN_PROGRESS])
    writer.comment(batch.first, format_dispatch(name, clock()))
    handle = runner.launch(spec) if writer.apply else None
    return spec, handle


def batch_andon(batch, tracker):
    """The first andon raised on any item of the batch, or None.

    The loop recognizes the marker — code, not judgment — and reads it only on
    an item it is already working.
    """
    if tracker is None:
        return None
    for number in batch.numbers:
        found = find_andon(tracker.comments(number))
        if found:
            return number, found
    return None


def run(config, tracker=None, runner=None, clock=time.time, writer=None):
    """The loop. Returns a `Report`; raises nothing a caller must catch."""
    report = Report(slug=config.slug)
    fault = config_fault(config)
    if fault:
        report.status = "stopped"
        report.failure = fault
        return report
    if config.completion_signal is None:
        report.notes += (R1_UNRESOLVED,)

    writer = writer or Writer(tracker=tracker, apply=config.apply)
    dispatched = []
    inbox = undispatchable = None
    snapshot = None

    try:
        for cycle in range(config.max_cycles):
            report.cycles = cycle + 1
            snapshot = read_snapshot(config, tracker)
            writer.snapshot = snapshot
            inbox = intent_inbox(snapshot, config.slug)

            guard_writes = run_guards(writer, inbox, snapshot, config)
            if guard_writes and config.apply:
                if writer.created:
                    wait_listed(tracker, writer.created, config.milestone)
                    writer.created = []
                continue               # the tracker moved; re-query before working

            batches, undispatchable = batch_ready(snapshot, inbox.ready)
            for item, kind in undispatchable:
                set_needs_operator(
                    writer, item.number,
                    f"The intent loop cannot dispatch this item: its type is "
                    f"`{kind or 'missing'}`, which is not one of the six "
                    f"design types ({', '.join(sorted(TYPES))}). "
                    f"{'An assertion is guard 2 and construction' if kind == 'assertion' else 'Set a type label'}"
                    f" — the loop will not guess one.",
                )
            if not batches:
                break                  # nothing ready, guards dry: STOP

            # Every batch launches before any is waited on: the sessions run in
            # parallel, the WAITING is the loop's and is serial, and so is the
            # merging that follows it — one writer to the base branch at a time.
            live = []
            for batch in batches:
                spec, handle = dispatch_batch(batch, writer, runner, config, clock)
                dispatched.append(
                    f"{spec.name} — {', '.join(f'#{n}' for n in batch.numbers)}")
                live.append((batch, spec, handle))

            if not config.apply:
                # A dry run plans exactly one cycle. Re-querying a tracker it
                # never wrote to would replay the same plan forever.
                break

            for batch, spec, handle in live:
                land(batch, spec, handle, writer, runner, tracker, config,
                     snapshot, clock, report)
    except LoopStop as stop:
        report.status = "stopped"
        report.failure = str(stop)

    report.writes = tuple(str(w) for w in writer.writes)
    report.dispatched = tuple(dispatched)
    if inbox is not None and snapshot is not None:
        report.resting = resting_queue(inbox, snapshot, undispatchable or ())
    return report


def land(batch, spec, handle, writer, runner, tracker, config, snapshot,
         clock, report):
    """Supervise, then collect/merge/close — the second half behind R1."""
    if handle is None or runner is None:
        return
    origin, notified = (None, False)
    if tracker is not None:
        origin, notified = parse_dispatch(tracker.comments(batch.first),
                                          spec.name)

    def on_notify(_handle, elapsed):
        set_needs_operator(
            writer, batch.first,
            f"`{spec.name}` has been working for {elapsed / 3600:.1f} h with "
            "no settle. A live wait — the loop is still waiting.",
        )

    result = supervise(runner, handle, operator_round=spec.operator_round,
                       on_notify=on_notify, clock=clock, origin=origin,
                       notified=notified)
    if result.notified and result.state != WaitState.STALLED:
        clear_needs_operator(writer, batch.first)
    if result.state == WaitState.STALLED:
        report.notes += (f"{spec.name} stalled after "
                         f"{result.elapsed / 3600:.1f} h; its pane is left "
                         "open — a stalled session is evidence.",)
        return

    raised = batch_andon(batch, tracker)
    if raised:
        number, andon = raised
        set_needs_operator(
            writer, number,
            f"Andon raised by `{spec.name}`: {andon.reason}. The batch is "
            "paused; nothing merged and nothing closed.",
        )
        report.notes += (f"{spec.name} raised the andon on #{number}: "
                         f"{andon.reason}",)
        return

    ctx = CompletionContext(
        snapshot=snapshot,
        board={row["number"]: row for row in (tracker.board_items() if tracker else ())},
        done_label=config.done_label,
        done_status=config.done_status,
    )
    complete = is_complete(batch, config, ctx)
    if complete is None:
        report.notes += (f"{spec.name} settled; {R1_UNRESOLVED}",)
        return
    if not complete:
        report.notes += (f"{spec.name} settled but the operator has not "
                         "marked it done; its pane stays open.",)
        return

    collected = runner.collect(handle)
    if TYPES[batch.type].worktree:
        merge_session(writer, config, spec.cwd)
    evidence = (collected.report or "").strip().splitlines()
    tail = evidence[-1][:200] if evidence else "no pane report"
    for number in batch.numbers:
        writer.close_issue(number,
                           comment=f"Merged from `{spec.name}`. {tail}",
                           reason=CLOSED_DONE)
    runner.close(handle)
