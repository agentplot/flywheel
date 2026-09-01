"""The design loop, as an ordinary program.

`design/loop-programs.md`, "The intent loop":

    query+guards (flip-consume, ready-consume, compose) ->
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

**Completion is the operator's, and the signal is `stage:done`.** The loop
writes `stage:in-session` on each item of a batch as it dispatches, and the
OPERATOR flips `stage:done` — in the pane (the session writes it to its own
item and settles) or on GitHub directly, one flip either way. That label is
the loop's only completion filter: there is nothing to configure and no state
in which completion is *unknown*. A session settling is NOT completion — the
operator may iterate a plannotator or lavish round as often as they like.

Each item's stages advance independently: the loop collects, marks
`stage:collected` and closes every item carrying `stage:done`, whether or not
its siblings in the same session do. Merging the session's `sess/*` branch and
closing its pane are properties of the SESSION and wait for the last item —
a branch merged mid-session merges a half-finished tree, and a pane closed
under a running session destroys the work in it.
"""

import json
import os
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _flywheel_inbox import (CLOSED_DONE, DISPATCH_STANDING, ELABORATION,  # noqa: E501
                             INTENT_PREFIX,
                             resolve_change_id,
                             IN_PROGRESS, NEEDS_OPERATOR, QUEUED, READY,
                             STAGE_COLLECTED, STAGE_DONE, STAGE_IN_SESSION,
                             STATUS_BACKLOG, Tracker,
                             TrackerSnapshot, clear_needs_operator,
                             find_andon, intent_inbox, parse_andon,
                             set_needs_operator, set_stage, unblocked)
from _flywheel_ledger import NullLedger
from _flywheel_sessions import (MAX_NAME, SessionHandle, SessionSpec,
                                WaitState, runner_for,
                                supervise, work_order)


class LoopStop(Exception):
    """A cycle that cannot go on. The run stops with this in its report.

    "a cycle that cannot read the tracker, mint its token, or resolve its
    parameters STOPS THE RUN with the failure in the report; a failing cycle
    never loops."
    """


# ---------------------------------------------------------------------------
# The five design types — one enumeration, and this is it
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DesignType:
    """A design session type and its launch mechanics.

    `profile` follows the single rule in
    `openspec/specs/flywheel-inception-skill/spec.md`: does this session's
    BATCH WORK build a lavish surface? Interactive's does and takes
    `flywheel-interactive-session`; the other four take
    `flywheel-design-session`. The dispatch plan every type may end
    with is not part of the basis. No second basis is admitted.

    `model` is the default column of
    `openspec/specs/flywheel-session-type-skills/spec.md`.

    `alone` is the schema's "prototypes always alone" — each is its own
    experiment.

    Two former fields are now properties of every design session and
    carry no per-type information: each launches in its own worktree
    (the close writes `decisions/` and `close/` files; an unchanged
    worktree costs nothing at teardown) and each is an operator-round
    session (any may end with a dispatch plan the operator takes as
    long as they like — the 4-hour auto-stall is traded for the
    surviving 90-minute notify).
    """

    name: str
    profile: str
    model: str
    alone: bool = False


TYPES = {t.name: t for t in (
    DesignType("planning", "flywheel-design-session", "fable"),
    DesignType("interactive", "flywheel-interactive-session", "fable"),
    DesignType("research", "flywheel-design-session", "opus[1m]"),
    DesignType("prototype", "flywheel-design-session", "opus", alone=True),
    DesignType("writeback", "flywheel-design-session", "opus"),
)}


def type_of(item):
    """The item's `type:` label, without its prefix, or None.

    Invariant 4: "`type:*` is the session type that works the item." There is
    NO default here, and that is deliberate — a fallback type would hand
    any mistyped item to whatever session that type charges. An item the
    loop cannot type is reported, not guessed at.
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
    kind: str          # label | body | comment | issue | sub-issue | close | command
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
        self.writes = []
        self._added = {}
        self._removed = {}
        self.created = []   # issue numbers born this cycle, for wait_listed
        self.snapshot = snapshot

    # -- the snapshot, and the cache that may not outlive it ----------------

    @property
    def snapshot(self):
        return self._snapshot

    @snapshot.setter
    def snapshot(self, snapshot):
        """Replacing the snapshot invalidates **both** halves of the cache.

        A re-read is the loop learning what the world now says, so a cache of
        this writer's own earlier writes must not survive it. `_removed`
        outliving a re-read would re-report a label as absent; `_added`
        outliving one makes the surface answer from a state that no longer
        exists — on the normal pane path, dispatch writes `stage:in-session`,
        the pane's own `stage:done` removes it on GitHub, and a stale
        addition then sends one redundant `--remove-label` per collect.

        Both directions go together because a cache with one direction
        invalidated is a cache whose rule nobody can state.
        """
        self._snapshot = snapshot
        self._added = {}
        self._removed = {}

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
        if label in self._removed.get(number, set()):
            return False           # this cycle took it off; the snapshot is stale
        if self.snapshot is not None:
            item = self.snapshot.item(number)
            if item is not None:
                return label in item.labels
        if self.tracker is not None:
            return self.tracker.has_label(number, label)
        return False

    def add_label(self, number, label):
        self._added.setdefault(number, set()).add(label)
        self._removed.get(number, set()).discard(label)
        self._record("label", f"#{number}", f"+{label}")
        if self.apply and self.tracker:
            self.tracker.add_label(number, label)

    def remove_label(self, number, label):
        self._added.get(number, set()).discard(label)
        self._removed.setdefault(number, set()).add(label)
        self._record("label", f"#{number}", f"-{label}")
        if self.apply and self.tracker:
            self.tracker.remove_label(number, label)

    def clear_status(self, number):
        self._record("clear_status", f"#{number}", "board Status consumed")
        if self.apply and self.tracker is not None and hasattr(
                self.tracker, "clear_board_status"):
            self.tracker.clear_board_status(number)

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

def apply_ready_consume(writer, numbers):
    """A spent approval leaves the Ready column.

    The bolt loop consumes a card's Ready at expansion; this is the intent
    side's same move, one pass after the flip. A batch still at Ready with
    its work released is how a later joiner inherits an approval the
    operator never gave it (observed live: #265)."""
    for number in numbers:
        writer.clear_status(number)


def apply_flip_consume(writer, numbers):
    """`state:queued` -> `state:ready`, for the sub-issues a Ready batch releases.

    The plan is `_flywheel_inbox.flip_consume_plan`'s and it only ever names
    sub-issues of a batch the OPERATOR moved to Ready. Idempotent by
    construction: an item already `state:ready` is not in the plan, so applying
    the plan empties it.
    """
    for number in numbers:
        writer.relabel(number, remove=[QUEUED], add=[READY])


def compose_batch(writer, config, kind, title, numbers, into=None):
    """One `flywheel-batch` call — THE definition of composing or joining.

    `flywheel-batch` is the whole move in one command: it creates the
    parent (or, with `--into`, refuses a non-open one and appends), attaches
    the sub-issues, adds the parent to the org Project and defaults its
    fields, skips an item that already belongs to a batch, and comments the
    newcomers on an amended parent. Reimplementing any of that in this
    module would be a second definition of what a batch looks like — the
    handoff amend once spoke to the sub-issue endpoint directly and got
    none of those checks.

    A created parent's number is captured into `writer.created` so
    `wait_listed` gives BOTH release paths read-your-writes, not just
    compose.
    """
    if not numbers:
        return
    argv = [
        str(config.batch_cmd),
        "--org", config.org,
        "--repo", config.repo,
        "--kind", kind,
        "--milestone", config.milestone,
        "--title", title,
        "--project", config.project,
    ]
    if into is not None:
        argv += ["--into", str(into)]
    argv += [str(n) for n in numbers]
    result = writer.command(argv, cwd=config.repo_dir, what="flywheel-batch")
    if result is not None:
        match = re.search(r"^(?:unit|elaboration) #(\d+):",
                          (result.stdout or ""), re.MULTILINE)
        if match:
            writer.created.append(int(match.group(1)))


def compose_unit(writer, config, title, numbers, into=None):
    """One `unit` parent over these items, through `flywheel-batch`.

    It puts the parent at **Backlog** and never writes Ready — on this path
    the operator's flip is the approval, and a batch born at Ready would
    make the loop the approver of its own work. The one release where
    the parent IS born at Ready is the operator's born-ready release at
    triage, where their word is itself the approval; that move is made by
    the release path with `flywheel-board`, not from inside this loop.

    `into` appends late-arriving items to the unit that already
    exists, through the same command.
    """
    compose_batch(writer, config, "unit", title, numbers, into=into)


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
    # AMEND, not a second birth: while an open elaboration for this
    # milestone sits at Backlog, newcomers JOIN it — a new batch per
    # sweep fragments the queue into near-identical containers (observed
    # live: #131/#132, #109/#114/#129).
    into = None
    if snapshot is not None:
        for b in sorted(snapshot.batches, key=lambda b: b.number):
            if (b.kind == ELABORATION and b.status == STATUS_BACKLOG
                    and b.milestone == config.milestone):
                into = b.number
                break
    compose_batch(writer, config, "elaboration",
                  f"Elaboration: {config.slug}",
                  [i.number for i in sorted(items, key=lambda i: i.number)],
                  into=into)


def wait_listed(tracker, numbers, milestone, tries=8, pause=5,
                sleep=time.sleep):
    """Read-your-writes over an eventually consistent list.

    GitHub's issue list can lag a fresh creation, and the next cycle's
    snapshot IS that list — a birth invisible to it births again
    (observed live: #128/#130, #131/#132). A cycle
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


def apply_board_place(writer, config, snapshot):
    """An open elaboration parent with NO board Status goes to Backlog.

    Every Backlog predicate — the round derivation, the server's poke,
    the operator's own board — keys on Status, and a parent filed
    without the board write is invisible to all of them: the willdan
    fleet sat with five elaborations nobody's round ever carried
    (problem 12 residual, 2026-09-01). Placement is a repair, not an
    approval — Backlog is exactly where a filed-and-unapproved batch
    belongs, and the operator's flip is still the only release.
    """
    if snapshot is None or writer.tracker is None:
        return
    place = getattr(writer.tracker, "set_board_status", None)
    if place is None:
        return
    for batch in snapshot.batches:
        if (batch.kind == ELABORATION and batch.status is None
                and batch.milestone == config.milestone
                and batch.milestone_state == "open"):
            if writer.apply and place(batch.number, STATUS_BACKLOG):
                writer._record("board", f"#{batch.number}",
                               "placed at Backlog")


def run_guards(writer, inbox, snapshot, config):
    """All four, every cycle, in order, each idempotent. Returns its writes."""
    mark = writer.mark()
    apply_flip_consume(writer, inbox.queued_to_flip)
    apply_ready_consume(writer, getattr(inbox, "spent_ready", ()))
    apply_compose(writer, inbox.orphan_queued, config, snapshot)
    apply_board_place(writer, config, snapshot)
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
    """`<type>-<topic>-<first item>` — the name IS the classification plus
    the batch, and herdr caps it at 32 characters.

    Deterministic, because a stateless loop process restarts freely and
    `HerdrRunner.launch` reuses an agent already running under the name. A
    name that moved between runs would launch a second session onto the
    same work — and a name shared BETWEEN batches did the opposite: round
    two reused round one's idle pane, the reuse path sent no new order,
    and the loop marked work settled that no session ever saw (observed
    live: the site intent's #301 and #302). The batch's first item number
    makes the name per-batch: same batch, same pane; new batch, new pane
    and a real prompt.
    """
    stem = f"{batch.type}-{slug}"
    suffix = f"-{batch.first}"
    return stem[:MAX_NAME - len(suffix)] + suffix


def session_order(batch, config):
    """One prompt, the summary line first.

    Design types have NO canonical slash-command invocation — the profile
    loads the type skill the work order names — so the first line is a
    plain summary rather than an invented `/flywheel:<type>`.
    """
    nums = ", ".join(f"#{n}" for n in batch.numbers)
    invocation = f"{batch.type} session for intent {config.slug} - items {nums}"
    brief = "\n".join([
        f"Change: {config.change_id}. Session type: {batch.type}. "
        f"Items: {nums}.",
        "",
        config.goal or (
            "Work the items: read each item body and the change's records, "
            "close what the batch can close, and report what it cannot."
        ),
        "",
        f"Your session directory is "
        f"openspec/changes/{config.change_id}/sessions/<date>-<topic>/ and you are "
        "its sole writer. Write your records (decisions, questions, "
        "the session README) in your worktree; queue your own "
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


def _dispatch_markers(comments):
    """Every dispatch marker in these comments, as parsed field dicts.

    The one reader of the marker format. `session_named` and
    `parse_dispatch` both consume it, so a change to the fields cannot
    update one and silently starve the other — a `session_named` that
    stopped matching would skip a whole session group at teardown, the
    stranded-deliverables failure `resume_collect` exists to prevent.
    """
    for comment in comments or ():
        body = comment.get("body") if isinstance(comment, dict) else comment
        found = _DISPATCH.search(body or "")
        if not found:
            continue
        yield dict(pair.split("=", 1)
                   for pair in found.group("fields").split() if "=" in pair)


def session_named(comments):
    """The session name an item's dispatch marker records, or None.

    The counterpart to `format_dispatch`, and what lets the loop answer
    "which items does this session carry" — a question it could not ask
    before, so the session-scoped teardown was keyed on the batch (which a
    later batch of the same type is not) and on type+slug (which is a name,
    not a membership).
    """
    latest = None
    for fields in _dispatch_markers(comments):
        latest = fields.get("name") or latest
    return latest


def session_members(tracker, snapshot, milestone, name, fallback=()):
    """Every open item whose dispatch marker names this session.

    Falls back to the caller's set when there is no tracker to ask — a
    dry run or a fixture — so the teardown is never wider than what it
    can actually see.
    """
    if tracker is None:
        return list(fallback)
    found = [i.number for i in snapshot.on(milestone)
             if i.is_open and session_named(tracker.comments(i.number)) == name]
    return found or list(fallback)


def parse_dispatch(comments, name=None):
    """(origin, notified) recovered from the item's comments, or (None, False).

    `supervise` takes a WALL clock and an `origin` for a stated reason: loop
    processes are stateless and restart freely, and a session handed a fresh
    four-hour budget on every restart never stalls at all. herdr carries no
    timestamp to recover it from — so the tracker does, which it can, because
    the tracker is the only bus by construction.
    """
    latest = (None, False)
    for fields in _dispatch_markers(comments):
        if name is not None and fields.get("name") != name:
            continue
        try:
            latest = (float(fields.get("origin")),
                      fields.get("notified") == "1")
        except (TypeError, ValueError):
            continue
    return latest


# ---------------------------------------------------------------------------
# Completion — one label, per item
# ---------------------------------------------------------------------------

def is_done(number, snapshot):
    """Has the OPERATOR marked THIS item done?

    Two-valued on purpose. The loop has one filter — the `stage:done` label
    — and there is no configuration to name it, so the state in which no
    signal is configured and completion is therefore *unknown* rather than
    false does not exist.

    Never inferred from the session settling: "the operator may iterate a
    plannotator or lavish round as many times as they want", and a loop that
    read a settled pane as a finished session would collect half a decision.
    Never read off the board either: the board's Status is the operator's
    batch-approval surface, and per-item session state lives in labels with
    every other signal the loops read.
    """
    item = snapshot.item(number)
    if item is None:
        return False                   # not on this snapshot; nothing to collect
    return STAGE_DONE in item.labels


def is_collected(number, snapshot):
    """Whether this item's deliverables were already gathered.

    The guard against collecting twice, and it is exactly the label that
    says the gathering happened.
    """
    item = snapshot.item(number)
    return item is not None and STAGE_COLLECTED in item.labels


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
    apply: bool = True
    fixture: str = None
    max_cycles: int = 20
    plugin_bin: Path = Path(__file__).resolve().parent

    @property
    def milestone(self):
        return f"{INTENT_PREFIX}{self.slug}"

    @property
    def change_id(self):
        """The openspec change id the intent's record lives under —
        kind-prefixed (`intent-<slug>`) unless a bare-slug directory
        predates the prefix, which is adopted rather than renamed."""
        return resolve_change_id(
            Path(self.repo_dir) / "openspec" / "changes", self.milestone)

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
    """Flip the items in progress and in session, record the origin, launch.

    Idempotent. `stage:in-session` names the whole span in which the
    operator iterates — however many plannotator or lavish rounds it holds.
    The rounds themselves are not stages: a stage exists only if a loop
    filter consumes it or the operator's eye needs it.
    """
    name = session_name(batch, config.slug)
    # Every design type carries a worktree and holds an operator round:
    # any session may end with a dispatch plan, whose close writes
    # decisions/ and close/ files and whose round the operator takes as
    # long as they like.
    cwd = ensure_worktree(writer, config, name)
    spec = SessionSpec(
        name=name,
        cwd=str(cwd),
        order=session_order(batch, config),
        profile=TYPES[batch.type].profile,
        model=TYPES[batch.type].model,
        operator_round=True,
    )
    for item in batch.items:
        if READY in item.labels:
            writer.relabel(item.number, remove=[READY], add=[IN_PROGRESS])
        # Never walk the operator's flip back. A resumed batch may hold an
        # item already at `stage:done`, and writing `stage:in-session` over
        # it would erase the one signal the completion filter reads.
        if not (writer.has_label(item.number, STAGE_DONE)
                or writer.has_label(item.number, STAGE_COLLECTED)):
            set_stage(writer, item.number, STAGE_IN_SESSION)
    # **On every item, not just the first.** The dispatch marker is the only
    # record of which session an item belongs to, and the loop's
    # session-scoped acts — the `sess/*` merge and the pane close — need
    # that set. Keying them on type+slug instead made a second same-type
    # batch land inside the running session, and its completion tore down
    # the pane and branch under items still at `stage:in-session`.
    origin = clock()
    for number in batch.numbers:
        writer.comment(number, format_dispatch(name, origin))
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


def run(config, tracker=None, runner=None, clock=time.time, writer=None,
        ledger=None):
    """The loop. Returns a `Report`; raises nothing a caller must catch."""
    report = Report(slug=config.slug)
    led = ledger or NullLedger()
    fault = config_fault(config)
    if fault:
        report.status = "stopped"
        report.failure = fault
        return report

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
            ready_numbers = [i.number for i in inbox.ready]
            led.precondition(
                ("ready " + ", ".join(f"#{n}" for n in ready_numbers))
                if ready_numbers else "nothing ready")

            writes_before = len(writer.writes)
            guard_writes = run_guards(writer, inbox, snapshot, config)
            for index, write in enumerate(writer.writes[writes_before:]):
                # Guards write as they check — recorded, never gated.
                step = f"guard:{cycle + 1}.{index}"
                led.expect(step, "idempotent repair", str(write))
                led.actual(step, str(write))
            if guard_writes and config.apply:
                if writer.created:
                    wait_listed(tracker, writer.created, config.milestone)
                    writer.created = []
                continue               # the tracker moved; re-query before working

            # A flip the loop was not there to see. Collected BEFORE the
            # ready set is worked, so a restarted process finishes what it
            # left behind before starting anything new. The ghost reset
            # runs first: an in-session item whose session is gone must
            # rejoin the ready set this same run.
            if resume_in_session(writer, runner, config, snapshot, report):
                continue               # the tracker moved; re-query
            if collect_settled(writer, runner, config, snapshot, report):
                continue               # the tracker moved; re-query
            if resume_collect(inbox, writer, runner, config, snapshot, report):
                continue               # the tracker moved; re-query
            if close_finished_batches(writer, config, snapshot, report):
                continue               # the tracker moved; re-query

            batches, undispatchable = batch_ready(snapshot, inbox.ready)
            for item, kind in undispatchable:
                set_needs_operator(
                    writer, item.number,
                    f"The intent loop cannot dispatch this item: its type is "
                    f"`{kind or 'missing'}`, which is not one of the five "
                    f"design types ({', '.join(sorted(TYPES))}). "
                    f"Set a type label — the loop will not guess one.",
                )
            if not batches:
                break                  # nothing ready, guards dry: STOP

            plan = [{
                "step": f"session:{session_name(batch, config.slug)}",
                "trigger": ", ".join(f"#{n}" for n in batch.numbers) + " ready",
                "expected": f"a {batch.type} session is charged and supervised",
            } for batch in batches]
            led.write_plan(plan)       # the expectation record, never a gate

            # Every batch launches before any is waited on: the sessions run in
            # parallel, the WAITING is the loop's and is serial, and so is the
            # merging that follows it — one writer to the base branch at a time.
            live = []
            for batch, row in zip(batches, plan):
                led.expect(row["step"], row["trigger"], row["expected"])
                spec, handle = dispatch_batch(batch, writer, runner, config, clock)
                led.actual(row["step"],
                           "session launched" if handle else "planned only",
                           ok=True)
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
    if report.failure:
        led.note(report.failure)
    path = led.write_report()
    hook = os.environ.get("FLYWHEEL_OBSERVER")
    if path and hook:
        try:
            subprocess.run([hook, str(path)], check=False)
        except OSError:
            pass
    return report


def resume_in_session(writer, runner, config, snapshot, report):
    """Reset the in-session ghosts a dead process left behind. True if
    it wrote.

    A loop killed mid-charge leaves items at `state:in-progress` +
    `stage:in-session` that no session owns — invisible to the ready
    filter, to `collect_plan`, and to every other reader, so they sit
    forever until the operator resets them by hand (problem 13, willdan
    fleet: #24/#25). The membership is recoverable — the dispatch marker
    names the session — and the roster answers whether that session is
    live. GONE with no `stage:done` means the work never finished and
    nobody is doing it: back to `state:ready`, stage label dropped, so
    the next cycle redispatches. The deterministic session id then
    resumes the same conversation warm — nothing is lost but the wait.

    A live or blocked session is left strictly alone, and so is anything
    the operator has touched (`stage:done`, `needs-operator`): this
    reconciles abandonment, never judgment.
    """
    if not config.apply or writer.tracker is None or runner is None:
        return False
    state_of = getattr(runner, "state", None)
    if state_of is None:
        return False
    wrote = False
    for item in snapshot.on(config.milestone):
        if not item.is_open or STAGE_IN_SESSION not in item.labels:
            continue
        if (writer.has_label(item.number, STAGE_DONE)
                or writer.has_label(item.number, STAGE_COLLECTED)
                or writer.has_label(item.number, NEEDS_OPERATOR)):
            continue
        name = session_named(writer.tracker.comments(item.number))
        if not name or state_of(name) != WaitState.GONE:
            continue
        writer.relabel(item.number,
                       remove=[IN_PROGRESS, STAGE_IN_SESSION], add=[READY])
        writer.comment(item.number, (
            f"The loop found this item marked in-session for "
            f"`{name}`, but no such session is on the roster — a "
            f"restart stranded it. Reset to ready; the next cycle "
            f"redispatches, resuming the session's conversation by its "
            f"deterministic id."))
        report.notes += (f"#{item.number} was in-session for a session "
                         f"that is gone (`{name}`) — reset to ready.",)
        wrote = True
    return wrote


def collect_settled(writer, runner, config, snapshot, report):
    """Flip the settled sessions no cycle is watching. True if it wrote.

    `land` collects a session that settles inside the run that launched
    it — but a design session outlives its 60-second run as a rule, and
    the flow then expects the session to write `stage:done` to its own
    item before settling. One that delivered without flipping leaves its
    item `stage:in-session` beside an idle pane no path reads:
    `resume_in_session` reconciles only GONE sessions, `collect_plan`
    only `stage:done`. The pane sits forever and the item never closes
    (observed live 2026-09-01: #11, #86, #70 — three delivered planning
    sessions idle for hours, reaped by hand).

    A raised andon pauses instead, mirroring `land`; a working or
    blocked session is left strictly alone. The write is `stage:done`
    plus the pane's report tail, and the next pass's `resume_collect`
    closes the item, merges the `sess/*` branch, and reaps the pane
    through the machinery that already exists.
    """
    if not config.apply or writer.tracker is None or runner is None:
        return False
    state_of = getattr(runner, "state", None)
    if state_of is None:
        return False
    wrote = False
    for entry in snapshot.on(config.milestone):
        if not entry.is_open or STAGE_IN_SESSION not in entry.labels:
            continue
        if (writer.has_label(entry.number, STAGE_DONE)
                or writer.has_label(entry.number, STAGE_COLLECTED)
                or writer.has_label(entry.number, NEEDS_OPERATOR)):
            continue
        comments = writer.tracker.comments(entry.number)
        name = session_named(comments)
        if not name or state_of(name) != WaitState.SETTLED_DONE:
            continue
        collected = runner.collect(
            SessionHandle(name=name, runner=getattr(runner, "kind", "herdr")))
        raised = find_andon(comments) or parse_andon(collected.report or "")
        if raised:
            set_needs_operator(
                writer, entry.number,
                f"`{name}` settled with the andon standing: {raised.reason}. "
                "Nothing is collected under it.")
            report.notes += (f"#{entry.number}: `{name}` settled under its "
                             f"andon — paused, not collected.",)
            wrote = True
            continue
        evidence = (collected.report or "").strip().splitlines()
        tail = evidence[-1][:200] if evidence else "no pane report"
        set_stage(writer, entry.number, STAGE_DONE)
        writer.comment(entry.number, (
            f"`{name}` settled without flipping this item — the loop read "
            f"the settled pane and flipped it. {tail}"))
        report.notes += (f"#{entry.number}: `{name}` settled un-flipped — "
                         f"stage:done written from the pane.",)
        wrote = True
    return wrote


def close_finished_batches(writer, config, snapshot, report):
    """Close an elaboration parent whose every member is closed.

    Members close one by one through the collect path, and nothing ever
    closed the container: the finished parent sat open at board Backlog
    and every dispatch round re-derived it as an approvals row, so the
    operator was shown the same finished elaborations round after round
    (willdan round 17, observed 2026-09-01). A parent still carrying
    `dispatch:standing` holds an unconsumed payload and is dispatch's to
    retire; one under `needs-operator` is the operator's; a parent whose
    membership was not fetched is left alone. True if it wrote.
    """
    if not config.apply or writer.tracker is None:
        return False
    open_items = {i.number: i for i in snapshot.items if i.is_open}
    finished = [
        batch for batch in snapshot.batches
        if batch.kind == ELABORATION and batch.sub_issues
        and batch.milestone in (None, config.milestone)
        and (parent := open_items.get(batch.number)) is not None
        and DISPATCH_STANDING not in parent.labels
        and NEEDS_OPERATOR not in parent.labels
        and not any(n in open_items for n in batch.sub_issues)]
    for batch in finished:
        writer.close_issue(
            batch.number,
            comment=("Every member of this elaboration is closed; the loop "
                     "closes the finished container so no dispatch round "
                     "re-offers it."),
            reason=CLOSED_DONE)
        report.notes += (f"closed finished elaboration #{batch.number} — "
                         f"every member already closed.",)
    return bool(finished)


def resume_collect(inbox, writer, runner, config, snapshot, report):
    """Collect items flipped while no loop was watching. True if it wrote.

    The pane path is handled inside `land`, which re-reads the tracker
    after its session settles. This is the other half: an item whose
    session is over — the process died, or the operator flipped long after
    the pane was gone — sits `state:in-progress` with `stage:done` and is
    invisible to the ready filter forever. `collect_plan` names that set;
    this consumes it.

    **Nothing is re-launched.** A session that already settled has left its
    deliverables where they belong — the session directory and the `sess/*`
    branch, both on disk — and `runner.collect` only ever supplied the
    pane's last line for the closing comment. Starting a fresh session on
    an item the operator has already called done would redo finished work,
    so the comment says plainly that there was no pane to read rather than
    inventing one.

    **The `sess/*` branch IS merged**, once every item of that session has
    been collected. The earlier reading — that which session an item
    belonged to is not recoverable once its pane is gone — was wrong:
    `session_name` is deterministic in the type and the slug precisely so a
    restarted process finds the same name, and a lone type appends the item
    it rides alone with. Leaving the branch unmerged made the tracker half
    complete and the work invisible: the item closed, the deliverables
    stranded on a branch nobody would look for. That is the failure this
    whole capability exists to prevent, arriving by a quieter route.

    The pane is closed with it when a runner is on hand, and left open when
    one is not — an orphan pane is visible to the operator and costs
    nothing, where an unmerged branch is lost work.
    """
    if not inbox.to_collect or not config.apply:
        return False
    # Idempotent within the run as well as across cycles: this path ends
    # with a `continue`, so an item whose write the next snapshot has not
    # caught up with yet must not be collected and closed twice.
    numbers = [i.number for i in inbox.to_collect
               if not writer.has_label(i.number, STAGE_COLLECTED)
               and not writer.has_label(i.number, NEEDS_OPERATOR)]
    # Defence in depth on the stronger signal: `collect_plan` excludes a
    # paused item by its label, and an andon raised without one still stops
    # this. A raised andon is a pause, and nothing is collected under it.
    if numbers and writer.tracker is not None:
        numbers = [n for n in numbers
                   if not find_andon(writer.tracker.comments(n))]
    if not numbers:
        return False
    for number in numbers:
        set_stage(writer, number, STAGE_COLLECTED)
        writer.close_issue(
            number,
            comment=("Collected by the intent loop after its session had "
                     "ended — the operator's `stage:done` was flipped with "
                     "no pane to read, so this comment carries no session "
                     "report. The deliverables are the session directory "
                     "and its `sess/*` branch."),
            reason=CLOSED_DONE)
    report.notes += (
        "collected after the fact: " + ", ".join(f"#{n}" for n in numbers)
        + " carried stage:done with no live session.",)
    merge_resumed(inbox, writer, runner, config, snapshot, report, numbers)
    return True


def merge_resumed(inbox, writer, runner, config, snapshot, report, collected):
    """Merge the `sess/*` branch of every session this pass finished.

    Session-scoped, exactly as it is on the live path: a branch is merged
    only once EVERY item that session carries has reached
    `stage:collected`, because a branch merged while siblings are still
    open merges a half-finished tree.

    Membership is reconstructed the way the name is — from the type and the
    slug — so what is merged is the branch the dispatch would have named,
    never a guess.
    """
    done = set(collected)
    tracker = writer.tracker
    # Group by the session each item's dispatch marker NAMES, not by
    # type+slug. Two same-type batches share a name but not a membership,
    # and merging on the name alone would cut the second one off.
    names = {}
    for item in inbox.to_collect:
        if item.number not in done:
            continue
        found = session_named(tracker.comments(item.number)) if tracker else None
        if found:
            names.setdefault(found, []).append(item.number)
    for name, mine in sorted(names.items()):
        kind = next((k for k in TYPES if name.startswith(f"{k}-")), None)
        if kind is None:
            continue
        members = session_members(tracker, snapshot, config.milestone, name,
                                  fallback=mine)
        outstanding = [n for n in members
                       if n not in done
                       and not writer.has_label(n, STAGE_COLLECTED)]
        if outstanding:
            report.notes += (
                f"`sess/{name}` is not merged yet — "
                + ", ".join(f"#{n}" for n in outstanding) + " still open.",)
            continue
        # The two session-scoped acts are INDEPENDENT, exactly as they are
        # on the live path: the merge acts on the branch when it exists,
        # the pane close is unconditional. Gating both behind one test
        # left a session's pane open forever — and because `session_name`
        # is deterministic and `launch` reuses a running agent, the next
        # batch is dispatched into an orphaned, already-settled pane.
        worktree = worktree_path(config.repo_dir, f"sess/{name}",
                                 run=writer._run)
        if worktree:
            merge_session(writer, config, worktree)
        else:
            report.notes += (f"no worktree for `sess/{name}` — nothing to "
                             f"merge for the {kind} session.",)
        if runner is not None:
            try:
                # By NAME: this path runs in a process that never launched
                # the pane, so a synthesized handle carries no tab_id and a
                # `close(handle)` on it was a silent no-op — the pane it
                # meant to reap stayed open forever.
                runner.close_named(name)
            except Exception:            # a pane already gone is not a fault
                pass


def land(batch, spec, handle, writer, runner, tracker, config, snapshot,
         clock, report):
    """Supervise, then collect/close per item and merge/close per session.

    The per-item half acts on every item carrying `stage:done`, whether or
    not its siblings do; the session half — the `sess/*` merge and the pane
    close — waits until every item the session carries has reached
    `stage:collected`.
    """
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
        # Mark EVERY item, not none: `collect_plan` excludes a paused item
        # by its `needs-operator` label, so a stall that labelled nothing
        # left the next cycle free to collect and close a flipped sibling
        # of the stalled batch.
        for number in batch.numbers:
            set_needs_operator(
                writer, number,
                f"`{spec.name}` stalled after {result.elapsed / 3600:.1f} h "
                "without settling. Its pane is left open — a stalled session "
                "is evidence — and nothing on this batch is collected, "
                "merged or closed until you say so.")
        report.notes += (f"{spec.name} stalled after "
                         f"{result.elapsed / 3600:.1f} h; its pane is left "
                         "open — a stalled session is evidence.",)
        return

    raised = batch_andon(batch, tracker)
    if raised:
        number, andon = raised
        # The whole batch, not just the item that raised it. A raised andon
        # pauses the BATCH — the spec says "nothing is merged or closed" —
        # and the label is what the next cycle's collect filter reads, so
        # marking only the raiser left its flipped siblings collectable.
        for member in batch.numbers:
            set_needs_operator(
                writer, member,
                f"Andon raised by `{spec.name}` on #{number}: {andon.reason}. "
                "The batch is paused; nothing merged and nothing closed.",
            )
        report.notes += (f"{spec.name} raised the andon on #{number}: "
                         f"{andon.reason}",)
        return

    # **Re-read before asking who is done.** The operator's flip lands
    # DURING the session — that is the whole point of the pane path, where
    # the session writes `stage:done` to its own item and settles — so the
    # picture this cycle opened with, taken before the session was even
    # launched, cannot contain it. Asking the stale snapshot means the pane
    # path can never see its own write, and there is no next pass to catch
    # it: the item left the ready set when dispatch flipped it in-progress.
    if tracker is not None or config.fixture:
        snapshot = read_snapshot(config, tracker)
        writer.snapshot = snapshot

    fresh = [n for n in batch.numbers
             if is_done(n, snapshot) and not is_collected(n, snapshot)]
    if fresh:
        collected = runner.collect(handle)
        evidence = (collected.report or "").strip().splitlines()
        tail = evidence[-1][:200] if evidence else "no pane report"
        for number in fresh:
            set_stage(writer, number, STAGE_COLLECTED)
            writer.close_issue(
                number,
                comment=f"Collected from `{spec.name}`. {tail}",
                reason=CLOSED_DONE)

    # `writer.has_label` answers from the snapshot plus what this cycle just
    # wrote, so an item collected on an earlier pass counts here too.
    # The session's items, not this batch's. `launch` is idempotent and
    # reuses an agent already running under the name, so a later batch of
    # the same type joins THIS pane and THIS branch; tearing them down on
    # this batch's completion would cut that batch off mid-flight.
    members = session_members(tracker, snapshot, config.milestone, spec.name,
                              fallback=batch.numbers)
    outstanding = [n for n in members
                   if not writer.has_label(n, STAGE_COLLECTED)]
    if outstanding:
        report.notes += (
            f"{spec.name} settled; " + ", ".join(f"#{n}" for n in outstanding)
            + " not yet marked done by the operator — its pane stays open.",)
        return

    # Every item collected: the session's own resources may be torn down.
    merge_session(writer, config, spec.cwd)
    runner.close(handle)
