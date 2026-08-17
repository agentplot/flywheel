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

**A filter never writes.** The bolt loop's flip-consume, the intent loop's
handoff birth and compose are guards, and guards write. They appear here as
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
UNIT = "unit"
ELABORATION = "elaboration"
PLAN = "plan"
STALE = "stale"
TYPE_ASSERTION = "type:assertion"
TYPE_HANDOFF = "type:handoff"

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

INTENT_PREFIX = "intent/"
BOLT_PREFIX = "bolt/"
MILESTONE_PREFIXES = (INTENT_PREFIX, BOLT_PREFIX)


def milestone_slug(milestone):
    """`bolt/loop-server` -> `loop-server`. None for anything else."""
    for prefix in MILESTONE_PREFIXES:
        if milestone and milestone.startswith(prefix):
            return milestone[len(prefix):]
    return None


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
    def is_assertion(self):
        return TYPE_ASSERTION in self.labels

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
    intent guards test `parent_batch is None` — handoff birth for settled
    assertions, compose for orphan queued items — so without this every
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
    blocked_by: tuple = ()
    milestone: str = None     # bolt/<slug>, set by the planner at filing

    @property
    def slug(self):
        m = re.match(r"^\s*(?:Unit|Plan|Bolt):\s*([a-z0-9][a-z0-9-]*)\s*$",
                     self.title, re.IGNORECASE)
        return m.group(1) if m else None

    @property
    def bolt(self):
        """The bolt milestone this unit belongs to; falls back to the
        title slug for a card filed before milestones were the planner's."""
        if self.milestone and self.milestone.startswith(BOLT_PREFIX):
            return self.milestone
        return BOLT_PREFIX + self.slug if self.slug else None

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
                         blocked_by=tuple(i.get("blocked_by", ())),
                         milestone=i.get("milestone"))
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
    and handoff birth appear only in the INTENT loop's filter — so an intent
    whose last question just closed, leaving settled unbatched assertions
    but no ready item and no Ready batch, is a milestone with no job by the
    literal filter, and the loop that would birth its handoff is never
    started. The same goes for orphan `state:queued` items. Today's fleet
    driver covers this with its `compose_ms` proxy; a literal reading loses
    it. Queued as a question against the record rather than resolved here.

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
            # are containers, never composable work — counting them keeps a
            # job open forever (compose_plan skips them for the same reason).
            add(item.milestone, "run", f"#{item.number} queued and unbatched")
        elif (sweep and item.is_assertion and item.parent_batch is None
              and item.milestone.startswith(INTENT_PREFIX)):
            # over-approximation: handoff birth may have work here. The
            # blocker check is the loop's, not the server's.
            add(item.milestone, "run", f"#{item.number} unbatched assertion")

    for milestone in ready_batch_milestones:
        if milestone_slug(milestone) is not None:
            add(milestone, "run", "a batch at board Status Ready")

    # An approved plan card is a job for its bolt: the loop's first pass
    # expands it into the unit and its items.
    for card in snapshot.plan_cards:
        if card.at_ready and card.bolt:
            add(card.bolt, "run",
                f"plan card #{card.number} at Ready, awaiting expansion")

    for milestone in snapshot.closed_milestones:
        slug = milestone_slug(milestone)
        if slug is None:
            continue
        if changes is None or (changes / slug).exists():
            add(milestone, "archive", "closed milestone, change still in openspec/changes/")

    return sorted(jobs.values(), key=lambda j: (j.milestone, j.kind))


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
    full stop, and `tracker.md` invariant 6 uses "no open blockers" only for
    handoff birth. This returns exactly what the record says; `unblocked`
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


def unblocked(snapshot, items):
    """Those with no open blocker. Not part of the record's bolt filter —
    a convenience for the loop that wants it."""
    return tuple(i for i in items if not snapshot.open_blockers(i))


# ---------------------------------------------------------------------------
# 3 · intent loop
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HandoffPlan:
    action: str              # birth | amend
    assertions: tuple
    handoff_item: int = None


@dataclass
class IntentInbox:
    milestone: str
    ready: tuple = ()
    ready_units: tuple = ()
    queued_to_flip: tuple = ()
    handoff: HandoffPlan = None
    orphan_queued: tuple = ()
    to_collect: tuple = ()

    @property
    def empty(self):
        return not (self.ready or self.queued_to_flip or self.handoff
                    or self.orphan_queued or self.to_collect)


def handoff_plan(snapshot, slug):
    """`tracker.md` invariant 6, which is computable and so is computed.

        An assertion is settled and unbolted when its item is open on
        intent/<slug>, has no parent batch, and has no open blockers.
        Whenever such assertions exist at the queue, the loop births one
        type:handoff item naming exactly that set, or extends the open
        unstarted one — and while that handoff's unit still sits at Backlog,
        newcomers join it.

    Two branches, not one: BIRTH when there is no open handoff whose unit is
    still at Backlog, AMEND when there is. A filter that only ever births
    produces a second handoff for every newcomer and breaks invariant 2 —
    an item joins exactly one batch, ever.
    """
    milestone = f"{INTENT_PREFIX}{slug}"
    settled = tuple(
        i for i in snapshot.on(milestone)
        if i.is_open and i.is_assertion and i.parent_batch is None
        and not snapshot.open_blockers(i)
    )
    if not settled:
        return None

    for item in snapshot.on(milestone):
        if not (item.is_open and TYPE_HANDOFF in item.labels):
            continue
        batch = snapshot.batch(item.parent_batch) if item.parent_batch else None
        # "while that handoff's unit still sits at Backlog, newcomers join
        # it. The flip seals the batch." A handoff with no unit yet is
        # equally unsealed.
        if batch is None or batch.status == STATUS_BACKLOG:
            return HandoffPlan("amend", settled, item.number)
    return HandoffPlan("birth", settled)


def compose_plan(snapshot, slug, handoff=None):
    """Orphan `state:queued` items — queued work with no batch to release
    it. The loop composes them into a unit at Backlog; naming them is this
    module's job, composing them is the guard's.

    **The two sweeps are disjoint, and that is load-bearing.** An assertion
    handoff birth is already claiming is not also composed into a unit:
    invariant 2 says an item joins exactly one batch ever, and GitHub 422s
    the second attempt. Two guards writing to one item is also churn, which
    breaks the dry-cycle property the bolt's merge criteria test for. The
    fixture asserts the same split — `intent-tracker.json` annotates #202 as
    handoff birth's and #203 as compose's, one guard each.

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
    claimed = {i.number for i in (handoff.assertions if handoff else ())}
    return tuple(
        i for i in snapshot.on(milestone)
        if i.is_open and i.queued and i.parent_batch is None
        and i.number not in claimed
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
    """The bolt filter's shape on an intent milestone, plus the two guard
    sweeps the record names: handoff birth and compose."""
    milestone = f"{INTENT_PREFIX}{slug}"
    on_milestone = [i for i in snapshot.on(milestone) if i.is_open]
    units = tuple(
        b for b in snapshot.batches
        if b.at_ready and b.milestone in (None, milestone)
    )
    handoff = handoff_plan(snapshot, slug)
    return IntentInbox(
        milestone=milestone,
        ready=tuple(i for i in on_milestone if i.ready),
        ready_units=units,
        queued_to_flip=flip_consume_plan(snapshot, milestone),
        handoff=handoff,
        orphan_queued=compose_plan(snapshot, slug, handoff),
        to_collect=collect_plan(snapshot, slug),
    )


# ---------------------------------------------------------------------------
# 4 · dispatch
# ---------------------------------------------------------------------------

@dataclass
class DispatchInbox:
    triage: tuple = ()
    relay: tuple = ()

    @property
    def empty(self):
        return not (self.triage or self.relay)


def dispatch_inbox(snapshot):
    """Open issues with no milestone (triage), and open issues labelled
    `needs-operator` (relay).

    The relay half has **no milestone condition** — an escalation from a
    running bolt has a milestone and still needs relaying. Narrowing this to
    unmilestoned issues is a tempting tidy-up that silently breaks the one
    path the operator hears about live work on.

    For the same reason it has no *open* condition either, quite: it relays
    an item that is closed at `closed:merged`, because such an item is still
    in flight — its bolt has not landed — and the landing is exactly where a
    pause can now find every assertion already closed. A `needs-operator`
    nobody reads is the same silence as one never written. The condition
    stays bounded: the landing upgrades the reason to `closed:done`, and the
    item drops out of this filter for good.
    """
    live = [i for i in snapshot.items if i.is_open or i.merge_closed]
    return DispatchInbox(
        # A plan card is open and unmilestoned BY CONTRACT — it is the
        # planner's, awaiting board approval, and it is never triage.
        # Live fire: dispatch routed a fresh card onto a milestone with a
        # state label, which started phantom bolt loops.
        triage=tuple(i for i in live
                     if i.is_open and not i.milestone
                     and PLAN not in i.labels),
        relay=tuple(i for i in live if NEEDS_OPERATOR in i.labels),
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

    def snapshot(self, milestone=None, with_edges=True):
        """The picture the filters run over.

        Built per-milestone when a milestone is given, because the exact
        tests — invariant 6's open-blocker clause above all — need dependency
        and parentage edges, and those are per-issue calls. The server's pass
        wants none of that: it over-approximates on purpose and calls this
        with `with_edges=False`.

        Open issues **plus** the `closed:merged` ones, which are closed and
        still in flight — see `merge_closed_issues`.
        """
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
            # Blockers are only ever consulted for OPEN items (`unblocked`,
            # `handoff_plan` both filter on is_open), so a merge-closed
            # item's edges are a GET nobody reads.
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
                    sub_issues=tuple(self.sub_issues(item.number)) if with_edges else (),
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
                blocked_by=tuple(self.blocked_by(item.number)),
                milestone=item.milestone,
            ))

        # A batch's Ready flip is the approval, and a batch may sit on the
        # board without being an open issue we listed above.
        known = {b.number for b in batches}
        for number, row in board.items():
            if number in known or row.get("status") != STATUS_READY:
                continue
            if row.get("state") != "OPEN":
                continue
            batches.append(Batch(number=number, status=STATUS_READY,
                                 milestone=row.get("milestone")))

        items = backfill_parentage(items, batches)

        return TrackerSnapshot(
            items=items, batches=batches,
            closed_milestones=self.closed_milestones(),
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
        """The one item the intent loop ever creates is the handoff item.

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
        project_id, status_field_id, item_ids = meta
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
        return project["id"], field["id"], item_ids

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
            nodes { ... on ProjectV2SingleSelectField { id name } }
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
