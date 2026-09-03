"""The four inbox filters — the tracker is the only bus.

No session, loop, or server ever messages another. Everything moves through
GitHub issues, and each consumer has an exact filter: `server_inbox`,
`bolt_inbox`, `intent_inbox`, `dispatch_inbox`. A discovery is an issue, an
escalation is a label, a completion is item state; anything not expressible
in these filters is a design smell (`design/loop-programs.md`, "Inboxes").

Import from a sibling script:

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _flywheel_inbox import Tracker, bolt_inbox, find_andon

**The filters are pure functions over a snapshot.** Reads live in `Tracker`;
no filter touches the network. That is not tidiness — it is what lets the
loops be unit-tested at all, and it is the difference between a coordination
model implemented in code and one implemented in an agent's judgment.

**A filter never writes.** The bolt loop's flip-consume and the intent
loop's compose are guards, and guards write. They appear here as
PLANS — pure functions returning what the loop should write — so that the
writes stay in the loop's guard stage and the plan stays testable. The
dry-cycle property the bolt's merge criteria demand ("two consecutive cycles
against an unchanged tracker produce the same tracker state, and the second
writes nothing") is exactly the statement that applying a plan empties it,
and it is a unit test rather than an inference because of this split.

Zero dependencies, stdlib only, beside `_flywheel_gh.py`.
"""

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# The vocabulary. One enumeration, the `LABELS` table in bin/flywheel-setup.
# ---------------------------------------------------------------------------

READY = "state:ready"
IN_PROGRESS = "state:in-progress"
QUEUED = "state:queued"
NEEDS_OPERATOR = "needs-operator"
#: Dispatch has something to assemble here — a published round payload's
#: anchor, or a close-ready unit parent. The label is only the signal;
#: the marker comment on the item says what kind of standing thing it is.
DISPATCH_STANDING = "dispatch:standing"
UNIT = "unit"
ELABORATION = "elaboration"
PLAN = "plan"
#: A chore card or batch: work with no new behavior — deletions, doc and
#: docstring corrections, supersession headers, renames, status fixes.
#: The label buys compact rendering on the round (one line per chore,
#: one approval for the lot); the pipeline underneath is the ordinary
#: card -> expansion -> items machinery, unchanged.
CHORE = "chore"
STALE = "stale"

#: The stage names. A `stage:*` label is ADDITIONAL to the item's `state:*`
#: label and never a substitute for it — every one of the four inbox filters
#: reads `state:*`, so an item whose state label was displaced would go
#: invisible to the loop that owns it. An item carries at most one `stage:*`
#: at a time, naming its leading edge.
STAGE_PLANNED = "stage:planned"
STAGE_BUILT = "stage:built"
STAGE_VERIFIED = "stage:verified"
STAGE_MERGED = "stage:merged"
STAGE_IN_SESSION = "stage:in-session"
STAGE_DONE = "stage:done"
STAGE_COLLECTED = "stage:collected"

#: The bolt loop's four, in the order its cycle reaches them. The order is
#: read by the stage reconciliation, which must never walk a label BACK past
#: a stage the tree cannot witness.
CONSTRUCTION_STAGES = (STAGE_PLANNED, STAGE_BUILT, STAGE_VERIFIED,
                       STAGE_MERGED)

#: The intent loop's two, plus the operator's `stage:done` between them.
DESIGN_STAGES = (STAGE_IN_SESSION, STAGE_DONE, STAGE_COLLECTED)

#: Every stage name there is — what "remove any other stage label" sweeps.
STAGE_LABELS = CONSTRUCTION_STAGES + DESIGN_STAGES


def stage_of(labels, among=STAGE_LABELS):
    """The one stage label a set of labels carries, or None.

    `among` narrows it to a phase — the bolt loop asks about its four and
    is not confused by a design stage left over from the item's life on an
    intent milestone.
    """
    for stage in among:
        if stage in labels:
            return stage
    return None


CLOSED_DONE = "closed:done"
#: Merged to the bolt branch, awaiting the landing. A construction
#: sub-issue closes here so the unit parent's native bar — which counts
#: CLOSED sub-issues — advances at merge rather than at the landing, and
#: the landing upgrades the reason to `closed:done` with the SHA. Invariant
#: 5 stands verbatim: exactly one `closed:*` reason, at every moment.
CLOSED_MERGED = "closed:merged"
CLOSED_DECLINED = "closed:declined"
CLOSED_SUPERSEDED = "closed:superseded"
CLOSED_PARKED = "closed:parked"

CLOSED_REASONS = (CLOSED_DONE, CLOSED_MERGED, CLOSED_DECLINED,
                  CLOSED_SUPERSEDED, CLOSED_PARKED)

STATUS_BACKLOG = "Backlog"
STATUS_READY = "Ready"
STATUS_DONE = "Done"
#: Approved and picked up — where a consumed Ready goes, so the board
#: reads "in flight" rather than bouncing the card back to Backlog.
STATUS_IN_PROGRESS = "In Progress"

INTENT_PREFIX = "intent/"
BOLT_PREFIX = "bolt/"
MILESTONE_PREFIXES = (INTENT_PREFIX, BOLT_PREFIX)


def milestone_slug(milestone):
    """`bolt/loop-server` -> `loop-server`. None for anything else."""
    for prefix in MILESTONE_PREFIXES:
        if milestone and milestone.startswith(prefix):
            return milestone[len(prefix):]
    return None


def change_id(milestone):
    """The kind-prefixed openspec change id a milestone's record uses:
    `bolt/loop-server` -> `bolt-loop-server`, `intent/x` -> `intent-x`.
    The prefix keeps the two kinds apart at a glance in the records
    repo's openspec/changes/. None for anything else."""
    for prefix in MILESTONE_PREFIXES:
        if milestone and milestone.startswith(prefix):
            return prefix.rstrip("/") + "-" + milestone[len(prefix):]
    return None


def resolve_change_id(changes_root, milestone):
    """The change id a milestone's record actually lives under.

    An existing bare-slug directory is adopted — renaming a live change
    would rewrite openspec bookkeeping under open sessions — so only
    records scaffolded after the prefix landed carry it."""
    slug = milestone_slug(milestone)
    prefixed = change_id(milestone)
    if slug is None:
        return None
    if changes_root is not None and (Path(changes_root) / slug).is_dir():
        return slug
    return prefixed


# ---------------------------------------------------------------------------
# The objects
# ---------------------------------------------------------------------------

_CHANGE_LINE = re.compile(r"^Change:\s*`?([A-Za-z0-9._/-]+)`?\s*$", re.MULTILINE)
_AFTER_LINE = re.compile(r"^After:\s*(.+?)\s*$", re.MULTILINE)


def body_change(body):
    """The `Change: <slug>` line an expanded plan task's item carries —
    the one spec-driven change the item is. Absent on discovery items."""
    match = _CHANGE_LINE.search(body or "")
    return match.group(1) if match else None


def body_after(body):
    """The `After: …` line, as raw comma-separated tokens — the plan's
    task-level chain, carried into the item at expansion."""
    match = _AFTER_LINE.search(body or "")
    if not match:
        return ()
    return tuple(t.strip().strip("`") for t in match.group(1).split(",")
                 if t.strip())


@dataclass(frozen=True)
class Item:
    number: int
    title: str = ""
    body: str = ""
    labels: frozenset = frozenset()
    milestone: str = None
    milestone_state: str = "open"
    state: str = "open"
    blocked_by: tuple = ()
    parent_batch: int = None
    record: str = None
    change: str = None
    after: tuple = ()

    @property
    def is_open(self):
        return self.state == "open"

    @property
    def ready(self):
        return READY in self.labels

    @property
    def queued(self):
        return QUEUED in self.labels

    @property
    def in_progress(self):
        return IN_PROGRESS in self.labels

    @property
    def is_container(self):
        """A unit or elaboration parent — a batch, never work.

        Every per-item sweep excludes containers, or a release's own parent
        is re-run through composition, routing or staging (observed live as
        #120 -> #121). One definition, so the next sweep cannot forget it
        by copying the set literal wrong.
        """
        return bool({UNIT, ELABORATION} & self.labels)

    @property
    def merge_closed(self):
        """Closed at merge-back and still in flight until the bolt lands.

        Not `is_open`, and not finished either — the landing still owes it
        an upgrade to `closed:done` and the landing SHA.
        """
        return not self.is_open and CLOSED_MERGED in self.labels

    @classmethod
    def from_fixture(cls, raw, milestone=None):
        """The field names in `workflows/fixtures/*-tracker.json` are the
        contract, and this reads them verbatim."""
        return cls(
            number=raw["number"],
            title=raw.get("title", ""),
            body=raw.get("body", ""),
            labels=frozenset(raw.get("labels", ())),
            milestone=raw.get("milestone", milestone),
            milestone_state=raw.get("milestone_state", "open"),
            state=raw.get("state", "open"),
            blocked_by=tuple(raw.get("blocked_by", ())),
            parent_batch=raw.get("parent_batch"),
            record=raw.get("record"),
            change=raw.get("change") or body_change(raw.get("body", "")),
            after=tuple(raw.get("after", ())) or body_after(raw.get("body", "")),
        )

    @classmethod
    def from_api(cls, raw):
        """One issue as `gh api /repos/{o}/{r}/issues` returns it."""
        milestone = raw.get("milestone") or {}
        return cls(
            number=raw["number"],
            title=raw.get("title", ""),
            body=raw.get("body") or "",
            labels=frozenset(
                label["name"] for label in raw.get("labels", ())
                if isinstance(label, dict) and "name" in label
            ),
            milestone=milestone.get("title"),
            milestone_state=milestone.get("state", "open"),
            state=raw.get("state", "open"),
            blocked_by=tuple(raw.get("blocked_by", ())),
            parent_batch=raw.get("parent_batch"),
            change=body_change(raw.get("body") or ""),
            after=body_after(raw.get("body") or ""),
        )


def backfill_parentage(items, batches):
    """Fill each item's `parent_batch` from the batches that claim it.

    **The API does not carry this field and the guards key on it.** Measured on
    the live tracker, 2026-08-13: `gh api /repos/agentplot/flywheel/issues/73`
    returns `sub_issues_summary` and no parent of any kind, so
    `Item.from_api`'s `raw.get("parent_batch")` is always `None` there. Both
    intent compose guard tests `parent_batch is None` for orphan queued
    items — so without this every
    already-batched item on a live milestone reads as an orphan: a second batch
    per cycle, a 422 on the re-attach GitHub refuses (an item joins exactly one
    batch, ever), and a cycle that is never dry.

    The fixtures state the field directly, which is why the filter tests pass
    over the hole; parentage is only ever *derived* on the live path, from the
    `sub_issues` the snapshot already fetches per batch.

    An item that already carries a parent keeps it — this fills, it never
    overrides — and the first batch claiming an item wins, since a second
    claim is the state GitHub forbids anyway.
    """
    parent = {}
    for batch in batches:
        for number in batch.sub_issues:
            parent.setdefault(number, batch.number)
    if not parent:
        return list(items)
    filled = []
    for item in items:
        if item.parent_batch is None and item.number in parent:
            item = Item(**{**item.__dict__, "parent_batch": parent[item.number]})
        filled.append(item)
    return filled


@dataclass(frozen=True)
class Batch:
    number: int
    kind: str = None          # unit | elaboration
    status: str = None        # board Status: Backlog | Ready
    chore: bool = False       # label `chore`: a chore batch, rendered lean
    sub_issues: tuple = ()
    milestone: str = None
    milestone_state: str = "open"

    @property
    def at_ready(self):
        return self.status == STATUS_READY


@dataclass(frozen=True)
class PlanCard:
    """One proposed unit: a `plan`-labeled issue on its bolt's milestone,
    whose body is the unit's plan document. The planner creates the
    milestone and files the card onto it; the card becomes the unit at
    expansion, so its number is stable across the whole bolt."""

    number: int
    title: str = ""
    body: str = ""
    status: str = None        # board Status: Backlog | Ready | None
    team: str = None
    stale: bool = False
    chore: bool = False       # label `chore`: rendered one line per change
    blocked_by: tuple = ()
    milestone: str = None     # bolt/<slug>, set by the planner at filing
    milestone_state: str = "open"

    @property
    def slug(self):
        """The unit name the card's title carries. Still the card's parsed
        name — for the change id and the log line — but no longer a source
        of milestones: see `bolt`."""
        m = re.match(r"^\s*(?:Unit|Plan|Bolt):\s*([a-z0-9][a-z0-9-]*)\s*$",
                     self.title, re.IGNORECASE)
        return m.group(1) if m else None

    @property
    def bolt(self):
        """The bolt milestone this unit belongs to: the one the planner
        filed the card onto, and nothing else.

        No fallback to the title slug. The planner creates the milestone
        and files the card onto it, so a card arrives already knowing where
        it belongs; a name synthesized from a title is not a milestone the
        tracker holds, and routing work to one starts a loop on a milestone
        that does not exist while the card's own bolt goes unstarted. A card
        with no `bolt/*` milestone answers `None` and is routed nowhere.
        """
        if self.milestone and self.milestone.startswith(BOLT_PREFIX):
            return self.milestone
        return None

    @property
    def system(self):
        m = re.search(r"^System:\s*(\S+)\s*$", self.body, re.MULTILINE)
        return m.group(1) if m else None

    @property
    def derived_from(self):
        """(book sha, specs sha) the plan recorded, or (None, None)."""
        m = re.search(r"Derived from:\s*book\s+([0-9a-f]+)\s*[·,]\s*specs\s+"
                      r"([0-9a-f]+)", self.body)
        return (m.group(1), m.group(2)) if m else (None, None)

    @property
    def at_ready(self):
        return self.status == STATUS_READY


def plan_tasks(body):
    """The plan document's task table, as dicts keyed by its header row.

    The format is the bolt-planning skill's: a pipe table whose header
    carries at least `change`; `delivers`, `chapters` and `after` ride
    along when present. Rows outside a recognized table are ignored, so a
    stray pipe elsewhere in the document costs nothing.
    """
    lines = body.splitlines()
    header, tasks = None, []
    for line in lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            lowered = [c.lower() for c in cells]
            if line.strip().startswith("|") and "change" in lowered:
                header = lowered
            continue
        if set(line.strip()) <= {"|", "-", " ", ":"}:
            continue
        if not line.strip().startswith("|"):
            header = None
            continue
        row = dict(zip(header, cells))
        change = row.get("change", "").strip("`")
        if not change or change == "<change-slug>":
            continue
        after = row.get("after", "").strip().strip("`")
        tasks.append({
            "change": change,
            "delivers": row.get("delivers", ""),
            "chapters": row.get("chapters", ""),
            "after": "" if after in ("", "—", "-", "none") else after,
        })
    return tasks


@dataclass
class TrackerSnapshot:
    """Everything the filters read, and nothing they do not."""

    items: tuple = ()
    batches: tuple = ()
    closed_milestones: tuple = ()
    milestone: str = None
    plan_cards: tuple = ()

    def __post_init__(self):
        self.items = tuple(self.items)
        self.batches = tuple(self.batches)
        self.closed_milestones = tuple(self.closed_milestones)
        self.plan_cards = tuple(self.plan_cards)

    def item(self, number):
        for candidate in self.items:
            if candidate.number == number:
                return candidate
        return None

    def batch(self, number):
        for candidate in self.batches:
            if candidate.number == number:
                return candidate
        return None

    def on(self, milestone):
        return [i for i in self.items if i.milestone == milestone]

    def open_blockers(self, item):
        """Blockers still open. A blocker we cannot see is treated as open —
        the safe direction, because the alternative starts blocked work."""
        blockers = []
        for number in item.blocked_by:
            blocker = self.item(number)
            if blocker is None or blocker.is_open:
                blockers.append(number)
        return blockers

    @classmethod
    def from_fixture(cls, path):
        """Read `workflows/fixtures/{bolt,intent}-tracker.json`.

        The fixtures are the repo's own declared contract for a cycle's
        query result, so the filters are exercised against the same shape
        the loops will hand them rather than against a shape invented here.
        """
        raw = json.loads(Path(path).read_text())
        milestone = raw.get("milestone")
        return cls(
            items=[Item.from_fixture(i, milestone) for i in raw.get("items", ())],
            batches=[
                Batch(number=b["number"], kind=b.get("kind"),
                      status=b.get("status"),
                      chore=b.get("chore", False),
                      sub_issues=tuple(b.get("sub_issues", ())),
                      milestone=b.get("milestone", milestone),
                      milestone_state=b.get("milestone_state", "open"))
                for b in raw.get("batches", ())
            ],
            closed_milestones=raw.get("closed_milestones", ()),
            milestone=milestone,
            plan_cards=[
                PlanCard(number=i["number"], title=i.get("title", ""),
                         body=i.get("body", ""), status=i.get("status"),
                         team=i.get("team"),
                         stale=STALE in i.get("labels", ()),
                         chore=CHORE in i.get("labels", ()),
                         blocked_by=tuple(i.get("blocked_by", ())),
                         milestone=i.get("milestone", milestone),
                         milestone_state=i.get("milestone_state", "open"))
                for i in raw.get("items", ())
                if PLAN in i.get("labels", ())
                and i.get("state", "open") == "open"
            ],
        )


# ---------------------------------------------------------------------------
# 1 · server — milestones with a job
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Job:
    milestone: str
    kind: str      # run | archive
    why: str = ""


def server_inbox(snapshot, changes_dir=None, sweep=True):
    """Milestones with a job, per `design/loop-programs.md`:

        any open intent/* or bolt/* milestone holding an open item labelled
        state:ready or state:in-progress, or a batch at board Status Ready;
        plus closed milestones whose change still sits in openspec/changes/.

    **`sweep` covers a hole in that filter, and the hole is real.** Compose
    appears only in the INTENT loop's filter — so orphan `state:queued`
    items on a milestone with no ready item and no Ready batch name no job
    by the literal filter. Today's fleet driver covers this with its
    `compose_ms` proxy; a literal reading loses it. Queued as a question
    against the record rather than resolved here.

    The asymmetry that makes the sweep safe is worth stating, because the
    whole design leans on it: **a server filter may over-approximate; a loop
    filter must be exact.** The record already licenses the cost — the loop
    STOPs "when nothing is ready and the guards wrote nothing" — so a false
    positive costs one process start and a clean exit, while a false
    negative costs work that never happens. `sweep=False` gives the record
    verbatim, for anyone who wants to see the difference.
    """
    changes = Path(changes_dir) if changes_dir else None
    jobs = {}

    def add(milestone, kind, why):
        jobs.setdefault((milestone, kind), Job(milestone, kind, why))

    # Bounded by the milestone being open — the same test the per-item loop
    # below makes. Without it a unit parent left open at Ready keeps its
    # milestone reporting a job on every sweep: before the landing, after it,
    # and after the operator closes the milestone, where it collides with the
    # `archive` job this same sweep adds for that milestone.
    ready_batch_milestones = {
        b.milestone for b in snapshot.batches
        if b.at_ready and b.milestone and b.milestone_state == "open"
    }

    # An approved plan card is a job for its bolt: the loop's first pass
    # expands it into the unit and its items.
    #
    # **First, so the card's reason wins.** `add` is `setdefault`, so the
    # first reason for a milestone is the one reported — and a Ready card
    # also reaches this pass as a synthetic Ready `Batch` out of
    # `Tracker.snapshot`, which would otherwise claim the milestone with
    # "a batch at board Status Ready". The reason is what the run record
    # prints and what the restart backoff fingerprints, so the card has to
    # be legible as the thing the loop was started for.
    #
    # Bounded by the milestone being open, the same test the Ready-batch set
    # above and the per-item loop below make, and for the same reason: a run
    # job on a closed milestone collides with the `archive` job this same
    # sweep adds for it.
    #
    # `card.bolt` is the milestone the planner filed the card onto, or None.
    # A card naming no `bolt/*` milestone yields nothing: the server does not
    # synthesize a milestone name from a card's title.
    for card in snapshot.plan_cards:
        if card.at_ready and card.bolt and card.milestone_state == "open":
            add(card.bolt, "run",
                f"plan card #{card.number} at Ready, awaiting expansion")

    # Before the per-item loop, so the operator's approval is the reason a
    # held loop sees. `add` is setdefault and the backoff releases a hold
    # only when a job's reason CHANGES — with the item loop first, a
    # milestone held on "#N queued and unbatched" kept that reason through
    # a Ready flip, and the operator's approval waited out the full hold
    # (observed live: three elaborations approved, sessions ~11 minutes
    # late).
    for milestone in ready_batch_milestones:
        if milestone_slug(milestone) is not None:
            add(milestone, "run", "a batch at board Status Ready")

    for item in snapshot.items:
        if item.milestone_state != "open":
            # The operator's close on a bolt milestone RELEASES the landing:
            # merged items still awaiting their upgrade keep the loop's job
            # alive until the landing has run and closed them done — and so
            # does the born-ready fix item a failed landing files, or the
            # close strands its own repair.
            if item.milestone and item.milestone.startswith(BOLT_PREFIX):
                if item.merge_closed:
                    add(item.milestone, "run",
                        f"#{item.number} merged; the close released the landing")
                elif item.is_open and (item.ready or item.in_progress):
                    add(item.milestone, "run",
                        f"#{item.number} ready on the closed milestone — "
                        f"a landing's fix item")
            continue
        if milestone_slug(item.milestone) is None:
            continue
        if item.merge_closed:
            # Closed at merge-back and NOT finished: its bolt still has to
            # land, and the landing is what upgrades the reason and comments
            # the SHA. Without this a loop killed between the last merge and
            # the landing is never restarted, because every other test here
            # reads open items.
            #
            # Bolt milestones only. `closed:merged` is the construction
            # loop's label and the landing is a bolt's act; an intent
            # milestone has no landing to wait for, so a stray one there
            # must not keep an intent loop alive forever.
            if item.milestone.startswith(BOLT_PREFIX):
                add(item.milestone, "run",
                    f"#{item.number} merged, awaiting the landing")
            continue
        if not item.is_open:
            continue
        if item.ready or item.in_progress:
            add(item.milestone, "run", f"#{item.number} {item.state or ''}".strip())
        elif (sweep and item.queued and item.parent_batch is None
              and not item.is_container):
            # over-approximation: compose may have work here. Batch parents
            # are containers, not work — counting one keeps a job open
            # forever (compose_plan skips them for the same reason).
            add(item.milestone, "run", f"#{item.number} queued and unbatched")
        elif (sweep and item.is_container
              and item.milestone.startswith(INTENT_PREFIX)):
            # A finished elaboration container names no work by the
            # literal filter — every member closed, nothing ready — so
            # its milestone never ran the reconciler that closes the
            # container, and #72/#74 sat open on the board for a day.
            # Over-approximate per the sweep's stated asymmetry: a
            # container with nothing to reconcile costs one process
            # start and a clean exit, then the backoff holds it.
            add(item.milestone, "run",
                f"#{item.number} open container awaiting reconciliation")

    for milestone in snapshot.closed_milestones:
        slug = milestone_slug(milestone)
        if slug is None:
            continue
        if changes is None or (changes / resolve_change_id(changes, milestone)).exists():
            add(milestone, "archive", "closed milestone, change still in openspec/changes/")

    return sorted(jobs.values(), key=lambda j: (j.milestone, j.kind))


def operator_waits(snapshot, jobs=()):
    """The "waiting on the operator" lines of `flywheel status`, as strings.

    Pure over `(snapshot, jobs)` — the same pair the status pass already
    holds — so the report is testable without a tracker, and so `status`
    keeps its one promise: it reads, it starts nothing, it writes nothing.

    Three kinds of thing wait on the operator, in one list:

    - a **batch at Backlog**, which the flip to Ready releases;
    - an **unexpanded plan card**, which is now the whole approval surface
      for construction work. A card at Ready on an open milestone is
      already counted — its milestone carries a `run` job naming it — so
      it is not repeated here. A card at Backlog is what stands between a
      planned bolt and its construction, and a card the filter declines to
      route is reported with its defect named rather than dropped silently;
    - an open item labelled `needs-operator`.

    `jobs` decides *whether* a Ready card is listed — a card whose milestone
    already appears in the job rows is not repeated — while the card's own
    state names *why* it is not there.
    """
    routed = {j.milestone for j in jobs if j.kind == "run"}
    lines = []
    for batch in snapshot.batches:
        if batch.status == STATUS_BACKLOG:
            where = f" on {batch.milestone}" if batch.milestone else ""
            lines.append(
                f"batch #{batch.number} at Backlog{where} — flip to Ready to release")
    for card in snapshot.plan_cards:
        if card.bolt is None:
            lines.append(
                f"plan card #{card.number} names no bolt milestone — "
                f"the server yields no job for it")
        elif card.status == STATUS_BACKLOG:
            lines.append(
                f"plan card #{card.number} at Backlog on {card.bolt} — "
                f"flip to Ready to release")
        elif card.at_ready:
            # Counted by its milestone's job row — unless that milestone has
            # no `run` job, which means nothing will expand the card and this
            # line is the only place it can surface.
            if card.bolt not in routed:
                why = ("its milestone is closed"
                       if card.milestone_state != "open" else "no job names it")
                lines.append(
                    f"plan card #{card.number} at Ready on {card.bolt} — {why}")
        elif card.status is None:
            # Every open card is outstanding work on its bolt, so a card that
            # is on no board row is reported rather than falling through both
            # surfaces: it yields no job, and the arms above enumerate only
            # Backlog and Ready.
            lines.append(
                f"plan card #{card.number} on {card.bolt} is not on the board — "
                f"it has no Status, so nothing releases it")
        else:
            # On the board, in some third column. `Backlog` and `Ready` are
            # the only Status values this module names, but the board's
            # single-select holds whatever the Project defines — the default
            # `Todo`/`In Progress`/`Done` sit alongside them. Such a card is
            # placed, so telling the operator to place it would name a cause
            # that is not the cause; say where it actually sits instead.
            lines.append(
                f"plan card #{card.number} on {card.bolt} at Status "
                f"{card.status} — only Ready releases it")
    for item in snapshot.items:
        if item.is_open and NEEDS_OPERATOR in item.labels:
            lines.append(f"#{item.number} needs-operator — "
                         f"{getattr(item, 'title', '')[:60]}")
    return tuple(lines)


# ---------------------------------------------------------------------------
# 2 · bolt loop
# ---------------------------------------------------------------------------

@dataclass
class BoltInbox:
    milestone: str
    ready: tuple = ()
    in_progress: tuple = ()   # the loop's own half-done items, for re-adoption
    ready_units: tuple = ()
    queued_to_flip: tuple = ()

    @property
    def empty(self):
        return not (self.ready or self.queued_to_flip)


def flip_consume_plan(snapshot, milestone=None):
    """The sub-issues a Ready unit releases — a PLAN, not a write.

    **Invariant 5 is the whole point of the guard**: "only the operator's
    word makes ready — the flip to Ready on the board for a batch". So a
    `state:queued` item becomes ready ONLY as a sub-issue of a batch the
    operator has moved to board Status Ready. A plan that relabels queued
    items because *some* Ready batch exists on the milestone has quietly
    made the loop the approver, which is the one thing the state ladder
    exists to prevent.

    Idempotent by construction: an item already `state:ready` is not in the
    plan, so applying the plan empties it. That is the dry-cycle property.
    """
    numbers = []
    for batch in snapshot.batches:
        if not batch.at_ready:
            continue
        if milestone is not None and batch.milestone not in (None, milestone):
            continue
        for number in batch.sub_issues:
            item = snapshot.item(number)
            if item is None or not item.is_open:
                continue
            if item.queued:
                numbers.append(number)
    return tuple(sorted(set(numbers)))


def bolt_inbox(snapshot, slug):
    """Open items on `bolt/<slug>` labelled `state:ready`, plus that bolt's
    units at board Status Ready.

    The record's filter is **silent on blockers** — it says `state:ready`,
    full stop. This returns exactly what the record says; `unblocked`
    below is offered beside it so a caller that wants the stricter set does
    not have to re-derive it. The silence is noted on #76 rather than
    resolved by inference.
    """
    milestone = f"{BOLT_PREFIX}{slug}"
    on_milestone = [i for i in snapshot.on(milestone) if i.is_open]
    # `ready` stays exactly the record's filter. `in_progress` rides
    # beside it because the loop itself flips ready -> in-progress when a
    # batch starts, and a STATELESS RESTART must re-adopt its half-done
    # items — but which of them still need driving is git's to say (a
    # batch whose build branch is an ancestor of the bolt branch awaits
    # only the landing), so the split is the loop's, not this filter's.
    ready = tuple(i for i in on_milestone if i.ready)
    in_progress = tuple(i for i in on_milestone if i.in_progress)
    units = tuple(
        b for b in snapshot.batches
        if b.at_ready and b.kind == UNIT and b.milestone in (None, milestone)
    )
    return BoltInbox(
        milestone=milestone,
        ready=ready,
        in_progress=in_progress,
        ready_units=units,
        queued_to_flip=flip_consume_plan(snapshot, milestone),
    )


def ready_consume_plan(snapshot, milestone=None):
    """Batches whose board Ready is spent — a PLAN, not a write.

    The operator's Ready is an approval, and an approval is consumed by
    the work it starts: once none of a batch's sub-issues is still
    `state:queued`, everything the Ready covered has been released, and
    the batch leaving the Ready column is what keeps the board honest —
    Ready shows only approvals not yet picked up, and nothing that joins
    a batch later inherits a spent approval. Idempotent: a batch with no
    board Status is not in the plan.
    """
    numbers = []
    for batch in snapshot.batches:
        if not batch.at_ready or not batch.sub_issues:
            continue
        if milestone is not None and batch.milestone not in (None, milestone):
            continue
        subs = [snapshot.item(n) for n in batch.sub_issues]
        if any(i is not None and i.is_open and i.queued for i in subs):
            continue                      # flip first; consume next pass
        numbers.append(batch.number)
    return tuple(numbers)


def unblocked(snapshot, items):
    """Those with no open blocker. Not part of the record's bolt filter —
    a convenience for the loop that wants it."""
    return tuple(i for i in items if not snapshot.open_blockers(i))


# ---------------------------------------------------------------------------
# 3 · intent loop
# ---------------------------------------------------------------------------

@dataclass
class IntentInbox:
    milestone: str
    ready: tuple = ()
    ready_units: tuple = ()
    queued_to_flip: tuple = ()
    spent_ready: tuple = ()
    orphan_queued: tuple = ()
    to_collect: tuple = ()

    @property
    def empty(self):
        return not (self.ready or self.queued_to_flip
                    or self.orphan_queued or self.to_collect)


def compose_plan(snapshot, slug):
    """Orphan `state:queued` items — queued work with no batch to release
    it. The loop composes them into a unit at Backlog; naming them is this
    module's job, composing them is the guard's.

    **A batch is not composable work, and the live tracker is what proves it.**
    Measured on `intent/relay-delivery`, 2026-08-13: #46 is an `elaboration`
    parent at Backlog holding #43 and #45, and it is itself an open
    `state:queued` issue with no parent of its own — so the literal reading
    proposes batching the batch. That never converges: the parent this guard
    would create is another queued orphan, which the next cycle composes in
    turn, for as long as the loop runs. The `unit`/`elaboration` labels are
    what distinguish a container from the work inside it, so they are what the
    sweep skips.
    """
    milestone = f"{INTENT_PREFIX}{slug}"
    return tuple(
        i for i in snapshot.on(milestone)
        if i.is_open and i.queued and i.parent_batch is None
        and not i.is_container
    )


def collect_plan(snapshot, slug):
    """Items the operator flipped that the loop has not yet collected.

    **The ready filter cannot see these, and that is the hole.** Dispatch
    relabels an item `state:in-progress`, so once a session is launched the
    item is out of `ready` for good. A process killed between that dispatch
    and the collect — or one whose operator flips long after the pane is
    gone — leaves an item `state:in-progress` carrying `stage:done`, which
    no filter here would name and no cycle would work. The flip would never
    be consumed, and the milestone would keep a job forever.

    `flywheel-design-session-completion` requires the opposite in so many
    words: the loop "consumes the flip on its next pass", and an item
    flipped "on a later pass" is collected then. This names that set.

    **A paused item is not in it.** `needs-operator` marks a live wait —
    the andon the session raised, or a stall, or a question — and the same
    spec says a stalled or andon-raising session is untouched: "its pane is
    left open and nothing is merged or closed". `land` honours that by
    returning, but returning is not a halt: the run's next cycle reaches
    this filter first, and without the exclusion it would collect and close
    a flipped sibling out from under the very batch `land` had just paused,
    with a comment claiming the session had ended while its pane is open.
    The exclusion belongs here rather than at the call site because this is
    the function that says what "collectable" means.
    """
    milestone = f"{INTENT_PREFIX}{slug}"
    return tuple(
        i for i in snapshot.on(milestone)
        if i.is_open and i.in_progress
        and STAGE_DONE in i.labels and STAGE_COLLECTED not in i.labels
        and NEEDS_OPERATOR not in i.labels
    )


def intent_inbox(snapshot, slug):
    """The bolt filter's shape on an intent milestone, plus the compose
    sweep for orphan queued items."""
    milestone = f"{INTENT_PREFIX}{slug}"
    on_milestone = [i for i in snapshot.on(milestone) if i.is_open]
    units = tuple(
        b for b in snapshot.batches
        if b.at_ready and b.milestone in (None, milestone)
    )
    return IntentInbox(
        milestone=milestone,
        ready=tuple(i for i in on_milestone if i.ready),
        ready_units=units,
        queued_to_flip=flip_consume_plan(snapshot, milestone),
        spent_ready=ready_consume_plan(snapshot, milestone),
        orphan_queued=compose_plan(snapshot, slug),
        to_collect=collect_plan(snapshot, slug),
    )


# ---------------------------------------------------------------------------
# 4 · dispatch
# ---------------------------------------------------------------------------

@dataclass
class DispatchInbox:
    triage: tuple = ()
    relay: tuple = ()
    #: board work awaiting the operator's approval — batch parents and
    #: plan cards at Status Backlog on open milestones. They carry a
    #: milestone and no standing label, so neither queue above ever
    #: matched them: elaborations and bolt cards parked at Backlog were
    #: invisible to dispatch and no round was ever poked for them.
    round: tuple = ()

    @property
    def empty(self):
        return not (self.triage or self.relay or self.round)


def dispatch_inbox(snapshot):
    """Open issues with no milestone (triage), open issues labelled
    `needs-operator` (relay), and Backlog board objects awaiting
    approval (round).

    The relay half has **no milestone condition** — an escalation from a
    running bolt has a milestone and still needs relaying. Narrowing this to
    unmilestoned issues is a tempting tidy-up that silently breaks the one
    path the operator hears about live work on.

    For the same reason it has no *open* condition either, quite: it relays
    an item that is closed at `closed:merged`, because such an item is still
    in flight — its bolt has not landed — and the landing is exactly where a
    pause can now find every work item already closed. A `needs-operator`
    nobody reads is the same silence as one never written. The condition
    stays bounded: the landing upgrades the reason to `closed:done`, and the
    item drops out of this filter for good.
    """
    live = [i for i in snapshot.items if i.is_open or i.merge_closed]
    # The same predicate the round derivation uses (`round_inbox`), so
    # the poke and the round can never disagree about what stands. The
    # rows are the underlying issues, looked up by number, because the
    # delivery payload wants number+title.
    parked = {b.number for b in snapshot.batches
              if b.status == STATUS_BACKLOG and b.milestone_state == "open"}
    parked |= {c.number for c in snapshot.plan_cards
               if c.status == STATUS_BACKLOG and c.milestone_state == "open"}
    return DispatchInbox(
        # A plan card is open and unmilestoned BY CONTRACT — it is the
        # planner's, awaiting board approval, and it is never triage.
        # Live fire: dispatch routed a fresh card onto a milestone with a
        # state label, which started phantom bolt loops.
        # `dispatch:standing` items — published round payloads, close-ready
        # unit parents — join triage: the round is triage's own plan,
        # widened, not a parallel queue.
        triage=tuple(i for i in live
                     if (i.is_open and not i.milestone
                         and PLAN not in i.labels)
                     or (i.is_open and DISPATCH_STANDING in i.labels)),
        # One wait, one surface: an item standing for the round is
        # assembled into the plan, never ALSO relayed as a DM — two
        # deliveries of one wait carry two contradictory imperatives.
        relay=tuple(i for i in live if NEEDS_OPERATOR in i.labels
                    and DISPATCH_STANDING not in i.labels),
        round=tuple(i for i in live if i.number in parked),
    )


# ---------------------------------------------------------------------------
# The andon cord — code, not judgment
# ---------------------------------------------------------------------------

ANDON_OPEN = "<!-- flywheel:andon -->"
ANDON_CLOSE = "<!-- /flywheel:andon -->"
ANDON_ANSWERED = "<!-- flywheel:andon-answered -->"
_ANDON_ANSWERED = re.compile(
    r"^" + re.escape(ANDON_ANSWERED) + r"[ \t]*$", re.MULTILINE)

_ANDON = re.compile(
    r"^" + re.escape(ANDON_OPEN) + r"[ \t]*$(?P<body>.*?)^" + re.escape(ANDON_CLOSE),
    re.DOTALL | re.MULTILINE,
)
_REASON = re.compile(r"^ANDON:[ \t]*(?P<reason>\S.*?)[ \t]*$", re.MULTILINE)


@dataclass(frozen=True)
class Andon:
    reason: str
    body: str = ""


def format_andon(reason):
    """The marker a session writes in its item comment when it raises the
    cord. One canonical form, because the recognizer is code."""
    reason = " ".join((reason or "").split())
    if not reason:
        raise ValueError("an andon needs its reason — what is wrong, in one line")
    return f"{ANDON_OPEN}\nANDON: {reason}\n{ANDON_CLOSE}"


def parse_andon(comment_body):
    """The marker, or None. Never a judgment about prose.

    Strict on three axes, each for a reason:

    - **The delimiters start their own lines**, so a marker quoted inside a
      sentence is not one.
    - **The closing delimiter is required.** A truncated comment is not a
      stop signal; half a marker means something went wrong with the writing,
      not with the work.
    - **The payload must carry `ANDON: <reason>`.** This is what makes prose
      un-matchable: a comment saying "this is the andon cord, expected
      behaviour" has no marker and no payload and returns None, which is the
      entire difference between recognizing a signal and interpreting a
      sentence.

    Two marker pairs in one comment — a session quoting a prior andon —
    resolve **first wins** rather than refuse. The action an andon triggers
    is pause plus `needs-operator`, so erring toward pausing is the safe
    direction; refusing would let a real stop hide behind a quotation.
    """
    if not comment_body:
        return None
    match = _ANDON.search(comment_body)
    if not match:
        return None
    body = match.group("body")
    reason = _REASON.search(body)
    if not reason:
        return None
    return Andon(reason=reason.group("reason").strip(), body=body.strip())


def find_andon(comments):
    """The first raised andon among an item's comments, or None.

    Called on the item the loop is already working — never as a repo-wide
    sweep of comment bodies. **The marker is the payload; the signal is the
    label and the item state.** A comment body is not expressible in any of
    the four filters, and the record is explicit that anything not
    expressible in the filters is a design smell. So the loop learns that a
    session stopped from `needs-operator` and item state the way it learns
    everything else, and reads the marker only to find out why.

    An `ANDON_ANSWERED` marker retires every andon raised before it — the
    operator (or their proxy) writes it in the comment that answers, and
    the batch resumes; without it an answered andon re-pauses the batch on
    every cycle forever (#166). Same strictness: a literal marker line,
    never prose. An answer comment that quotes the old andon does not
    re-raise it.
    """
    found = None
    for comment in comments or ():
        body = comment.get("body") if isinstance(comment, dict) else comment
        if body and _ANDON_ANSWERED.search(body):
            found = None
            continue
        if found is None:
            found = parse_andon(body)
    return found


# ---------------------------------------------------------------------------
# 5 · the round — derived, never annotated
# ---------------------------------------------------------------------------

@dataclass
class RoundInbox:
    """What stands for the operator's round, DERIVED from the snapshot.

    The round is a pure function of the tracker, like the server's job
    list: no writer has to remember a label for its work to appear, and
    a label wrongly present or absent cannot invent or hide a decision.
    The one annotated thing is a published payload — genuinely new
    information the snapshot cannot derive — and even there the label
    only nominates anchors; the marker comment is the payload.
    """

    #: bolt milestones whose every work item is merge-closed, with no
    #: open plan card and nothing ready — the close releases the landing.
    close_ready: tuple = ()
    #: elaboration/unit batch parents sitting at board Backlog — pending
    #: operator approvals the board would otherwise carry alone.
    backlog_batches: tuple = ()
    #: plan cards sitting at board Backlog — proposed bolts/units
    #: awaiting the same approval.
    backlog_cards: tuple = ()
    #: open items labelled `dispatch:standing` — nominated payload
    #: anchors; the caller reads each anchor's latest unretired
    #: round-payload marker for the address.
    payload_anchors: tuple = ()
    #: open items labelled `needs-operator` — andons and pauses. The plan
    #: is the ONE routing surface put before the operator, so the set the
    #: fleet is waiting on rides every round beside the approvals; a
    #: relay DM is a poke, not a surface.
    needs_operator: tuple = ()

    @property
    def empty(self):
        return not (self.close_ready or self.backlog_batches
                    or self.backlog_cards or self.payload_anchors
                    or self.needs_operator)


def round_inbox(snapshot):
    """Everything standing for a round, computed from the snapshot.

    Close-ready is the SAME predicate the bolt loop's close-ready mark
    uses — every non-container work item on an open bolt milestone
    closed `closed:merged`, none ready, and no open plan card holding
    the landing — re-derived rather than read back from the labels the
    loop writes, so the round cannot drift from the loop's own truth.
    """
    live = [i for i in snapshot.items if i.is_open or i.merge_closed]
    holding = {c.milestone for c in snapshot.plan_cards
               if c.milestone and c.milestone_state == "open"}
    close_ready = []
    bolt_milestones = sorted({
        i.milestone for i in live
        if i.milestone and i.milestone.startswith(BOLT_PREFIX)
        and i.milestone_state == "open"})
    for milestone in bolt_milestones:
        if milestone in holding:
            continue
        work = [i for i in live if i.milestone == milestone
                and not i.is_container]
        if not work:
            continue
        if any(READY in i.labels and i.is_open for i in work):
            continue
        if all(i.merge_closed for i in work):
            close_ready.append(milestone)
    # The approval's one effect on a Backlog batch is releasing its queued
    # members. A batch whose known members hold nothing queued — released
    # already, or every member closed and gone from the snapshot — has
    # nothing an approval could do, and offering it anyway is how the same
    # finished elaborations re-rendered round after round (willdan round
    # 17, observed 2026-09-01). Empty `sub_issues` means membership was
    # not fetched, and an unknown batch still stands.
    queued = {i.number for i in snapshot.items if i.is_open
              and QUEUED in i.labels}
    return RoundInbox(
        close_ready=tuple(close_ready),
        backlog_batches=tuple(b for b in snapshot.batches
                              if b.status == STATUS_BACKLOG
                              and b.milestone_state == "open"
                              and (not b.sub_issues
                                   or queued & set(b.sub_issues))),
        backlog_cards=tuple(c for c in snapshot.plan_cards
                            if c.status == STATUS_BACKLOG
                            and c.milestone_state == "open"),
        # A close-ready bolt's parents carry the standing label for
        # visibility and the poke; they nominate no payload, so the
        # derived close row covers them and they are not shortfalls.
        payload_anchors=tuple(i for i in snapshot.items
                              if i.is_open and DISPATCH_STANDING in i.labels
                              and i.milestone not in close_ready),
        needs_operator=tuple(i for i in snapshot.items
                             if i.is_open and NEEDS_OPERATOR in i.labels),
    )


# ---------------------------------------------------------------------------
# The round's markers — published payloads and close-ready milestones
# ---------------------------------------------------------------------------

ROUND_PAYLOAD_OPEN = "<!-- flywheel:round-payload -->"
ROUND_PAYLOAD_CLOSE = "<!-- /flywheel:round-payload -->"
ROUND_CONSUMED = "<!-- flywheel:round-consumed -->"
_ROUND_CONSUMED = re.compile(
    r"^" + re.escape(ROUND_CONSUMED) + r"[ \t]*$", re.MULTILINE)
_ROUND_PAYLOAD = re.compile(
    r"^" + re.escape(ROUND_PAYLOAD_OPEN)
    + r"[ \t]*$(?P<body>.*?)^" + re.escape(ROUND_PAYLOAD_CLOSE),
    re.DOTALL | re.MULTILINE,
)
_PAYLOAD_LINE = re.compile(
    r"^PAYLOAD:[ \t]*repo=(?P<repo>\S+)[ \t]+sha=(?P<sha>[0-9a-f]{40})"
    r"[ \t]+dir=(?P<dir>\S+)[ \t]*$", re.MULTILINE)
_ORIGIN_LINE = re.compile(r"^ORIGIN:[ \t]*(?P<origin>\S+)[ \t]*$",
                          re.MULTILINE)

CLOSE_READY_OPEN = "<!-- flywheel:close-ready -->"
CLOSE_READY_CLOSE = "<!-- /flywheel:close-ready -->"
_CLOSE_READY = re.compile(
    r"^" + re.escape(CLOSE_READY_OPEN)
    + r"[ \t]*$(?P<body>.*?)^" + re.escape(CLOSE_READY_CLOSE),
    re.DOTALL | re.MULTILINE,
)
_CLOSE_READY_LINE = re.compile(
    r"^CLOSE-READY:[ \t]*milestone=(?P<milestone>\S+)"
    r"[ \t]+branch=(?P<branch>\S+)[ \t]+main=(?P<main>\S+)[ \t]*$",
    re.MULTILINE)


@dataclass(frozen=True)
class RoundPayload:
    repo: str
    sha: str
    dir: str
    origin: str = ""


@dataclass(frozen=True)
class CloseReady:
    milestone: str
    branch: str
    main: str


def format_round_payload(repo, sha, dir, origin):
    """The marker an origin actor writes on its anchor item at publish.
    The label (`dispatch:standing`) is the signal; this is the payload —
    the committed files' address, pinned by SHA so what dispatch renders
    is exactly what the origin committed."""
    for name, value in (("repo", repo), ("sha", sha), ("dir", dir),
                        ("origin", origin)):
        if not (value or "").strip():
            raise ValueError(f"a round payload needs its {name}")
    return (f"{ROUND_PAYLOAD_OPEN}\n"
            f"PAYLOAD: repo={repo} sha={sha} dir={dir}\n"
            f"ORIGIN: {origin}\n"
            f"{ROUND_PAYLOAD_CLOSE}")


def parse_round_payload(comment_body):
    """The marker, or None — andon-grade strictness: own-line delimiters,
    closing delimiter required, the PAYLOAD line required with a full
    40-hex sha, so prose can never match."""
    if not comment_body:
        return None
    match = _ROUND_PAYLOAD.search(comment_body)
    if not match:
        return None
    body = match.group("body")
    payload = _PAYLOAD_LINE.search(body)
    if not payload:
        return None
    origin = _ORIGIN_LINE.search(body)
    return RoundPayload(repo=payload.group("repo"), sha=payload.group("sha"),
                        dir=payload.group("dir"),
                        origin=origin.group("origin") if origin else "")


def find_round_payload(comments):
    """The standing payload among an item's comments, or None.

    A `ROUND_CONSUMED` marker retires every payload published before it —
    dispatch writes it as its apply's last act for the payload — so a
    round never re-offers what an earlier round applied, even where the
    label removal raced. Latest unretired payload wins: a republish after
    a send-back supersedes the earlier address."""
    found = None
    for comment in comments or ():
        body = comment.get("body") if isinstance(comment, dict) else comment
        if body and _ROUND_CONSUMED.search(body):
            found = None
            continue
        parsed = parse_round_payload(body)
        if parsed is not None:
            found = parsed
    return found


def format_close_ready(milestone, branch, main):
    """The machine half of the loop's close-ready comment. The prose half
    stays beside it for the human; this block is what lets an actor with
    only API access enumerate closable milestones — `needs-operator` on a
    container also means pauses and andons, so the label alone cannot."""
    return (f"{CLOSE_READY_OPEN}\n"
            f"CLOSE-READY: milestone={milestone} branch={branch} "
            f"main={main}\n"
            f"{CLOSE_READY_CLOSE}")


def parse_close_ready(comment_body):
    """The close-ready facts, or None. There is no withdrawn marker: the
    loop removes the labels when new cards hold the landing, and label
    off means not offered — the marker only carries the facts while the
    label stands. Latest marker wins at the caller (scan newest-last)."""
    if not comment_body:
        return None
    match = _CLOSE_READY.search(comment_body)
    if not match:
        return None
    line = _CLOSE_READY_LINE.search(match.group("body"))
    if not line:
        return None
    return CloseReady(milestone=line.group("milestone"),
                      branch=line.group("branch"), main=line.group("main"))


# ---------------------------------------------------------------------------
# The two writes this module owns: the label that means a live wait
# ---------------------------------------------------------------------------

def set_needs_operator(tracker, number, comment=None):
    """Add `needs-operator`, idempotently, with the reason as a comment.

    Invariant 7: the label marks a LIVE wait, applied at the moment of
    blocking. Returns True when it wrote.
    """
    if tracker.has_label(number, NEEDS_OPERATOR):
        return False
    if comment:
        tracker.comment(number, comment)
    tracker.add_label(number, NEEDS_OPERATOR)
    return True


def set_stage(tracker, number, stage, labels=None):
    """Move an item to one `stage:*` label, removing any other. True on a write.

    An item carries exactly ONE stage label, naming its **leading edge** —
    the shape the tracker already uses for `state:*` — so that "the items at
    `stage:built`" is a question with an answer rather than a set that also
    holds everything further along.

    **Both loops write through here**, which is what makes the vocabulary
    one vocabulary: the bolt loop owns four of the names, the intent loop
    two and the operator one, and a rule about the set that only one loop
    obeyed would be a rule about that loop instead.

    Nothing here touches a `closed:*` label. `stage:merged` and
    `closed:merged` are written at the same boundary but are not the same
    act, and the closure vocabulary has its own writer.

    Idempotent, and reports whether it wrote: an item already at the target
    **and carrying no other stage** is left alone and nothing is recorded,
    which is what keeps a second cycle over an unchanged tracker writing
    nothing.

    The early return is deliberately narrow. Returning on the target alone
    would assume every stage label on the tracker was written through here,
    and that assumption is not one this function is entitled to: the
    capability explicitly permits the operator to add `stage:done` by hand on
    GitHub, which sweeps nothing. So the sweep runs whenever the item's stage
    set is not already exactly the target, and an item carrying the target
    plus another ends carrying the target alone.

    Takes any of the four-method label surfaces — `Tracker`, `BoltTracker`,
    the intent loop's `Writer` — as its other two writes here do, and uses
    two optional extras where the surface offers them: a callable `labels`
    answers "what does the item carry" in ONE read instead of one probe per
    stage name (against the live tracker each probe is a full issue GET),
    and `swap_label` makes the move without a moment in which the item
    carries no stage at all. A surface with neither — the test fakes —
    gets the probe-and-two-writes behaviour unchanged. Callers already
    holding the item's labels pass them as `labels` and no read happens.
    """
    if labels is None:
        reader = getattr(tracker, "labels", None)
        if callable(reader):
            labels = reader(number)
        else:
            labels = {l for l in STAGE_LABELS if tracker.has_label(number, l)}
    carried = set(labels) & set(STAGE_LABELS)
    if carried == {stage}:
        return False
    stale = [l for l in STAGE_LABELS if l in carried and l != stage]
    add_needed = stage not in carried
    swap = getattr(tracker, "swap_label", None)
    if add_needed and callable(swap):
        swap(number, add=stage, remove=stale.pop(0) if stale else None)
        add_needed = False
    for other in stale:
        tracker.remove_label(number, other)
    if add_needed:
        tracker.add_label(number, stage)
    return True


def clear_needs_operator(tracker, number):
    """Remove it. "Whoever applies the answer removes the label."

    The counterpart to the 90-minute notice in
    `_flywheel_sessions.supervise`: a supervision that notified and a
    completion that never clears leaves the label on forever, and the
    operator's waiting-on-me view — and dispatch's relay filter — are wrong
    from then on.
    """
    if not tracker.has_label(number, NEEDS_OPERATOR):
        return False
    tracker.remove_label(number, NEEDS_OPERATOR)
    return True


# ---------------------------------------------------------------------------
# The reads
# ---------------------------------------------------------------------------

class Tracker:
    """The tracker's read side, and the small label writes above.

    `gh` and `graphql` are injected so the filters can be exercised against
    fixtures; by default they are `_flywheel_gh`'s, which is the one
    credential seam — the token is minted by the app and passed only through
    a copied environment, never ambient.
    """

    def __init__(self, token, org, repo, project_title=None,
                 gh=None, graphql=None):
        self.token = token
        self.org = org
        self.repo = repo
        self.project_title = project_title
        if gh is None or graphql is None:
            import sys
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from _flywheel_gh import gh as _gh, graphql as _graphql
            gh = gh or _gh
            graphql = graphql or _graphql
        self._gh = self._with_refresh(gh)
        self._graphql = graphql

    def _with_refresh(self, raw):
        """Retry exactly once with a re-minted token on Bad credentials.

        Installation tokens live one hour and flywheel-token's cache
        refreshes five minutes before expiry — but a long-lived process
        holding the token STRING in memory sails past the hour (observed
        live: a loop 401'd on the deliverables check after waiting out a
        30-minute build; the server daemon would hit the same wall). The
        wrapper ignores the stale first argument and re-resolves through
        flywheel-token, whose cache makes the refresh cheap.
        """
        def call(token, *args, **kw):
            try:
                return raw(token, *args, **kw)
            except SystemExit as err:
                if "Bad credentials" not in str(err):
                    raise
                os.environ.pop("GH_TOKEN", None)   # never re-read a stale copy
                from _flywheel_gh import resolve_token
                self.token = resolve_token(self.org)
                return raw(self.token, *args, **kw)
        return call

    # -- reads -------------------------------------------------------------

    def open_issues(self):
        """Every open issue. Pull requests are not issues for our purposes
        and are filtered out here rather than in each caller."""
        pages = self._gh(
            self.token, "api",
            f"/repos/{self.org}/{self.repo}/issues?state=open&per_page=100",
            "--paginate", "--slurp",
        )
        return [
            raw for page in pages for raw in page
            if "pull_request" not in raw
        ]

    def merge_closed_issues(self):
        """Closed issues carrying `closed:merged` — work still in flight.

        Closing an item at merge-back takes it out of `open_issues()`, and
        every filter downstream reads that. But a merge-closed item is not
        finished: its bolt has not landed, the landing still has to upgrade
        its reason and comment the SHA, and the server still has to start a
        loop for its milestone. So the snapshot carries them beside the open
        ones, and the filters that must not see them — every one built on
        `is_open`, the ready set above all — are unaffected.
        """
        pages = self._gh(
            self.token, "api",
            f"/repos/{self.org}/{self.repo}/issues"
            f"?state=closed&labels={CLOSED_MERGED}&per_page=100",
            "--paginate", "--slurp",
        )
        return [
            raw for page in pages for raw in page
            if "pull_request" not in raw
        ]

    def retired_issues(self, milestone):
        """Items on `milestone` closed by any reason BUT `closed:merged`.

        The snapshot carries open items and merge-closed ones and nothing
        else, on purpose — a declined, superseded or parked item is out of
        the work. But a session cut for that item does not close itself:
        a batch paused on an andon keeps its pane open for the operator to
        read, and when the operator's answer is to retire the item, the
        pane (and the batch's build worktree) outlive every tracker fact
        that could have reaped them. This is the read that finds them,
        scoped by milestone number so a long-lived org's closed history is
        never paged through.
        """
        pages = self._gh(
            self.token, "api",
            f"/repos/{self.org}/{self.repo}/milestones?state=all&per_page=100",
            "--paginate", "--slurp",
        )
        number = next((m["number"] for page in pages for m in page
                       if m.get("title") == milestone), None)
        if number is None:
            return []
        pages = self._gh(
            self.token, "api",
            f"/repos/{self.org}/{self.repo}/issues"
            f"?state=closed&milestone={number}&per_page=100",
            "--paginate", "--slurp",
        )
        return [
            Item.from_api(raw) for page in pages for raw in page
            if "pull_request" not in raw
            and not any(l.get("name") == CLOSED_MERGED
                        for l in raw.get("labels", ()))
        ]

    def closed_milestones(self):
        pages = self._gh(
            self.token, "api",
            f"/repos/{self.org}/{self.repo}/milestones?state=closed&per_page=100",
            "--paginate", "--slurp",
        )
        return [m["title"] for page in pages for m in page]

    def board_items(self):
        """(issue number, Status, Team, milestone) for every board row."""
        if not self.project_title:
            return []
        rows, cursor = [], None
        while True:
            data = self._graphql(self.token, _BOARD_QUERY, {
                "org": self.org, "title": self.project_title, "after": cursor,
            })
            projects = data["organization"]["projectsV2"]["nodes"]
            project = next(
                (p for p in projects if p["title"] == self.project_title), None)
            if project is None:
                return rows
            page = project["items"]
            for node in page["nodes"]:
                content = node.get("content") or {}
                if not content.get("number"):
                    continue
                status = (node.get("status") or {}).get("name")
                team = (node.get("team") or {}).get("name")
                milestone = (content.get("milestone") or {}).get("title")
                rows.append({
                    "number": content["number"], "status": status,
                    "team": team, "milestone": milestone,
                    "state": content.get("state", "OPEN"),
                })
            if not page["pageInfo"]["hasNextPage"]:
                return rows
            cursor = page["pageInfo"]["endCursor"]

    def blocked_by(self, number):
        """GitHub's dependency edges, read from the API, never inferred."""
        rows = self._gh(
            self.token, "api",
            f"/repos/{self.org}/{self.repo}/issues/{number}/dependencies/blocked_by",
        )
        return [row["number"] for row in rows or () if "number" in row]

    def sub_issues(self, number):
        rows = self._gh(
            self.token, "api",
            f"/repos/{self.org}/{self.repo}/issues/{number}/sub_issues",
        )
        return [row["number"] for row in rows or () if "number" in row]

    def comments(self, number):
        """One item's comments. Per-item on purpose — see `find_andon`."""
        return self._gh(
            self.token, "api",
            f"/repos/{self.org}/{self.repo}/issues/{number}/comments?per_page=100",
        ) or []

    # -- assembly ----------------------------------------------------------

    def snapshot(self, milestone=None, with_edges=True, with_batch_edges=None):
        """The picture the filters run over.

        Built per-milestone when a milestone is given, because the exact
        tests — invariant 6's open-blocker clause above all — need dependency
        and parentage edges, and those are per-issue calls. The server's pass
        wants none of that: it over-approximates on purpose and calls this
        with `with_edges=False`.

        `with_batch_edges` narrows that trade for the round: batch
        containers still get their `sub_issues` (one call per batch — a
        handful) while items skip the per-issue blocker calls. It defaults
        to `with_edges`, so existing callers are unchanged.

        Open issues **plus** the `closed:merged` ones, which are closed and
        still in flight — see `merge_closed_issues`.
        """
        batch_edges = with_edges if with_batch_edges is None else with_batch_edges
        all_raws = self.open_issues() + self.merge_closed_issues()
        raws = all_raws
        if milestone:
            raws = [r for r in raws
                    if (r.get("milestone") or {}).get("title") == milestone]

        board = {row["number"]: row for row in self.board_items()}
        items, batches = [], []
        for raw in raws:
            item = Item.from_api(raw)
            labels = item.labels
            # Blockers are only ever consulted for OPEN items (`unblocked`
            # filters on is_open), so a merge-closed item's edges are a GET
            # nobody reads.
            if with_edges and item.is_open:
                item = Item(
                    **{**item.__dict__,
                       "blocked_by": tuple(self.blocked_by(item.number))}
                )
            items.append(item)
            if UNIT in labels or ELABORATION in labels:
                row = board.get(item.number, {})
                batches.append(Batch(
                    number=item.number,
                    kind=UNIT if UNIT in labels else ELABORATION,
                    status=row.get("status"),
                    chore=CHORE in labels,
                    sub_issues=tuple(self.sub_issues(item.number)) if batch_edges else (),
                    milestone=item.milestone,
                    milestone_state=item.milestone_state,
                ))

        cards = []
        for raw in all_raws:
            item = Item.from_api(raw)
            if PLAN not in item.labels or not item.is_open:
                continue
            row = board.get(item.number, {})
            cards.append(PlanCard(
                number=item.number, title=item.title, body=item.body,
                status=row.get("status"), team=row.get("team"),
                stale=STALE in item.labels,
                chore=CHORE in item.labels,
                # Gated like the item block above: the one reader of a card's
                # blockers is the expansion guard, which runs under
                # `snapshot(milestone)` with edges on. The server's sweep and
                # `status` pass `with_edges=False` precisely to avoid a
                # per-issue GET, and this was making one per open plan card.
                blocked_by=(tuple(self.blocked_by(item.number))
                            if with_edges else ()),
                milestone=item.milestone,
                milestone_state=item.milestone_state,
            ))

        # A batch's Ready flip is the approval, and a batch may sit on the
        # board without being an open issue we listed above.
        #
        # `milestone_state` is carried from the same closed-milestone list
        # this snapshot reports, not defaulted. A Ready plan card reaches
        # `server_inbox` twice — as a card and as one of these synthetic
        # batches — and the card block declines a closed milestone while the
        # Ready-batch set would not have known to. Left defaulting to "open"
        # the backfill re-adds the very `run` job the card block declined,
        # colliding with the `archive` job the same sweep adds for that
        # milestone: the exact collision both other guards exist to prevent.
        closed = self.closed_milestones()
        known = {b.number for b in batches}
        for number, row in board.items():
            if number in known or row.get("status") != STATUS_READY:
                continue
            if row.get("state") != "OPEN":
                continue
            row_milestone = row.get("milestone")
            batches.append(Batch(
                number=number, status=STATUS_READY,
                milestone=row_milestone,
                milestone_state=("closed" if row_milestone in closed else "open"),
            ))

        # A blocker closed as COMPLETED is in neither fetched set, so
        # `open_blockers` — whose unseen-is-open default is the right
        # safety for a blocker it truly cannot read — would hold its
        # dependents forever (observed live 2026-09-01: #70 blocked_by
        # the closed #71, silently undispatchable, #73 stalled behind
        # it). Resolve every unseen blocker number explicitly; one that
        # still cannot be read stays treated as open.
        seen = {i.number for i in items}
        unseen = sorted(
            ({n for i in items for n in i.blocked_by}
             | {n for c in cards for n in c.blocked_by}) - seen)
        for number in unseen:
            try:
                raw = self._gh(self.token, "api",
                               f"/repos/{self.org}/{self.repo}/issues/{number}")
            except (Exception, SystemExit):
                # gh failures surface as SystemExit; an unreadable blocker
                # keeps the unseen-is-open treatment.
                continue
            if raw and "number" in raw:
                items.append(Item.from_api(raw))

        items = backfill_parentage(items, batches)

        return TrackerSnapshot(
            items=items, batches=batches,
            closed_milestones=closed,
            milestone=milestone, plan_cards=cards,
        )

    # -- the small writes --------------------------------------------------

    def labels(self, number):
        """Every label on the item, as a set of names. One read.

        `has_label` is the four-method surface's question and answers one
        name at a time; a caller that wants to *name* what an item carries —
        `flywheel-stage` reporting which stage it replaced — would otherwise
        ask once per candidate or reach past this class for the payload.
        """
        raw = self._gh(self.token, "api",
                       f"/repos/{self.org}/{self.repo}/issues/{number}")
        return {l.get("name") for l in raw.get("labels", ())}

    def has_label(self, number, label):
        return label in self.labels(number)

    def closed_with(self, number, label):
        """Is this item CLOSED and carrying `label`? One read, both fields.

        Closing is two writes — the reason label, then the state — so
        "already closed with this reason" is a two-field question, and
        asking only the label half calls a torn close finished. The same
        payload carries both, so this costs exactly what `has_label` costs.
        """
        raw = self._gh(self.token, "api",
                       f"/repos/{self.org}/{self.repo}/issues/{number}")
        return (raw.get("state") == "closed"
                and any(l.get("name") == label for l in raw.get("labels", ())))

    def closed(self, number):
        """Is this item closed, whatever the reason? One read.

        A distinct question from `closed_with`, which asks whether a
        *particular* close already happened and is the right test for a
        write that would otherwise be made twice. A caller asking "is this
        blocker's work behind us" wants any close: a predecessor closed
        `closed:superseded` or `closed:declined` is as finished as one
        closed `closed:done`, and testing a single reason would hold its
        dependent forever.
        """
        raw = self._gh(self.token, "api",
                       f"/repos/{self.org}/{self.repo}/issues/{number}")
        return raw.get("state") == "closed"

    def add_label(self, number, label):
        self._gh(self.token, "issue", "edit", str(number),
                 "--repo", f"{self.org}/{self.repo}", "--add-label", label)

    def remove_label(self, number, label):
        self._gh(self.token, "issue", "edit", str(number),
                 "--repo", f"{self.org}/{self.repo}", "--remove-label", label)

    def swap_label(self, number, add, remove=None):
        """Put one label on and take another off in ONE call.

        For the invariants written "at every moment": a label pair swapped
        by `add_label` then `remove_label` is two API calls with a window
        between them, and in that window the item carries both — or, done
        the other way round, neither. `gh issue edit` accepts both flags
        and applies them in a single PATCH, so the window does not exist.

        `remove` may be None or equal to `add`, in which case this is a
        plain add — the caller does not have to special-case it.
        """
        args = ["issue", "edit", str(number),
                "--repo", f"{self.org}/{self.repo}", "--add-label", add]
        if remove and remove != add:
            args += ["--remove-label", remove]
        self._gh(self.token, *args)

    def comment(self, number, body):
        self._gh(self.token, "issue", "comment", str(number),
                 "--repo", f"{self.org}/{self.repo}", "--body", body)

    def set_body(self, number, body):
        self._gh(self.token, "issue", "edit", str(number),
                 "--repo", f"{self.org}/{self.repo}", "--body", body)

    def create_issue(self, title, body, labels=(), milestone=None):
        """Create one tracker item and return its number.

        `gh issue create` prints the URL rather than JSON, so the number comes
        off the end of it; a URL we cannot parse is not fatal — the guard's
        write happened, and the next cycle reads the item back from the
        tracker like everything else.
        """
        args = ["issue", "create", "--repo", f"{self.org}/{self.repo}",
                "--title", title, "--body", body]
        for label in labels:
            args += ["--label", label]
        if milestone:
            args += ["--milestone", milestone]
        out = self._gh(self.token, *args)
        text = out if isinstance(out, str) else str(out or "")
        tail = text.strip().rsplit("/", 1)[-1]
        return int(tail) if tail.isdigit() else None

    def create_milestone(self, title):
        """Create the milestone if it does not exist; idempotent by title."""
        pages = self._gh(self.token, "api",
                         f"/repos/{self.org}/{self.repo}/milestones"
                         "?state=all&per_page=100", "--paginate", "--slurp")
        for page in pages or ():
            for m in page:
                if m.get("title") == title:
                    return m.get("number")
        made = self._gh(self.token, "api", "-X", "POST",
                        f"/repos/{self.org}/{self.repo}/milestones",
                        "-f", f"title={title}")
        return (made or {}).get("number")

    def set_milestone(self, number, title):
        self._gh(self.token, "issue", "edit", str(number),
                 "--repo", f"{self.org}/{self.repo}", "--milestone", title)

    def issue_id(self, number):
        raw = self._gh(self.token, "api",
                       f"/repos/{self.org}/{self.repo}/issues/{number}")
        return (raw or {}).get("id")

    def attach_sub_issue(self, parent, child):
        child_id = self.issue_id(child)
        if not child_id:
            return
        self._gh(self.token, "api", "-X", "POST",
                 f"/repos/{self.org}/{self.repo}/issues/{parent}/sub_issues",
                 "-F", f"sub_issue_id={child_id}")

    def clear_board_status(self, number):
        """Consume an approval: clear the board Status on the issue's row.

        Field and item ids come from the same project the board query
        reads; a card off the board is a no-op, not an error.
        """
        meta = self._project_meta()
        if not meta:
            return
        project_id, status_field_id, item_ids, _options = meta
        item_id = item_ids.get(number)
        if not item_id:
            return
        self._graphql(self.token, _CLEAR_STATUS_MUTATION, {
            "project": project_id, "item": item_id,
            "field": status_field_id,
        })

    def _project_meta(self):
        if not self.project_title:
            return None
        data = self._graphql(self.token, _PROJECT_META_QUERY, {
            "org": self.org, "title": self.project_title,
        })
        projects = data["organization"]["projectsV2"]["nodes"]
        project = next(
            (p for p in projects if p["title"] == self.project_title), None)
        if project is None:
            return None
        field = next((f for f in project["fields"]["nodes"]
                      if f.get("name") == "Status"), None)
        if field is None:
            return None
        item_ids = {}
        cursor = None
        while True:
            page = self._graphql(self.token, _PROJECT_ITEM_IDS_QUERY, {
                "org": self.org, "title": self.project_title, "after": cursor,
            })
            node = next(
                (p for p in page["organization"]["projectsV2"]["nodes"]
                 if p["title"] == self.project_title), None)
            if node is None:
                break
            items = node["items"]
            for row in items["nodes"]:
                content = row.get("content") or {}
                if content.get("number"):
                    item_ids[content["number"]] = row["id"]
            if not items["pageInfo"]["hasNextPage"]:
                break
            cursor = items["pageInfo"]["endCursor"]
        options = {o["name"]: o["id"] for o in field.get("options") or ()}
        return project["id"], field["id"], item_ids, options

    def set_board_status(self, number, name):
        """Place an issue's board row at a Status option, by name.

        Adds the issue to the project first when it has no row — a
        parent filed without any board write is exactly as invisible to
        the Backlog predicates as one parked wrong, and the placement
        guard exists for that case. A missing project, field, or option
        is a no-op, not an error: placement is a repair, never a gate.
        """
        meta = self._project_meta()
        if not meta:
            return False
        project_id, field_id, item_ids, options = meta
        option_id = options.get(name)
        if not option_id:
            return False
        item_id = item_ids.get(number)
        if not item_id:
            raw = self._gh(self.token, "api",
                           f"/repos/{self.org}/{self.repo}/issues/{number}")
            content_id = (raw or {}).get("node_id")
            if not content_id:
                return False
            added = self._graphql(self.token, _ADD_ITEM_MUTATION, {
                "project": project_id, "content": content_id})
            item_id = added["addProjectV2ItemById"]["item"]["id"]
        self._graphql(self.token, _SET_STATUS_MUTATION, {
            "project": project_id, "item": item_id,
            "field": field_id, "option": option_id})
        return True

    def close_issue(self, number, comment=None, reason=CLOSED_DONE):
        if reason:
            self.add_label(number, reason)
        args = ["issue", "close", str(number),
                "--repo", f"{self.org}/{self.repo}"]
        if comment:
            args += ["--comment", comment]
        self._gh(self.token, *args)


_PROJECT_META_QUERY = """
  query($org: String!, $title: String!) {
    organization(login: $org) {
      projectsV2(first: 10, query: $title) {
        nodes {
          id title
          fields(first: 30) {
            nodes { ... on ProjectV2SingleSelectField {
              id name options { id name } } }
          }
        }
      }
    }
  }"""

_PROJECT_ITEM_IDS_QUERY = """
  query($org: String!, $title: String!, $after: String) {
    organization(login: $org) {
      projectsV2(first: 10, query: $title) {
        nodes {
          title
          items(first: 100, after: $after) {
            pageInfo { hasNextPage endCursor }
            nodes { id content { ... on Issue { number } } }
          }
        }
      }
    }
  }"""

_CLEAR_STATUS_MUTATION = """
  mutation($project: ID!, $item: ID!, $field: ID!) {
    clearProjectV2ItemFieldValue(input: {
      projectId: $project, itemId: $item, fieldId: $field
    }) { projectV2Item { id } }
  }"""

_SET_STATUS_MUTATION = """
  mutation($project: ID!, $item: ID!, $field: ID!, $option: String!) {
    updateProjectV2ItemFieldValue(input: {
      projectId: $project, itemId: $item, fieldId: $field,
      value: { singleSelectOptionId: $option }
    }) { projectV2Item { id } }
  }"""

_ADD_ITEM_MUTATION = """
  mutation($project: ID!, $content: ID!) {
    addProjectV2ItemById(input: {
      projectId: $project, contentId: $content
    }) { item { id } }
  }"""

_BOARD_QUERY = """
  query($org: String!, $title: String!, $after: String) {
    organization(login: $org) {
      projectsV2(first: 10, query: $title) {
        nodes {
          id title
          items(first: 100, after: $after) {
            pageInfo { hasNextPage endCursor }
            nodes {
              status: fieldValueByName(name: "Status") {
                ... on ProjectV2ItemFieldSingleSelectValue { name } }
              team: fieldValueByName(name: "Team") {
                ... on ProjectV2ItemFieldSingleSelectValue { name } }
              content { ... on Issue { number state milestone { title } } }
            }
          }
        }
      }
    }
  }"""
