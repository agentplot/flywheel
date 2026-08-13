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
# The vocabulary. One enumeration, bin/flywheel-setup:57-90.
# ---------------------------------------------------------------------------

READY = "state:ready"
IN_PROGRESS = "state:in-progress"
QUEUED = "state:queued"
NEEDS_OPERATOR = "needs-operator"
UNIT = "unit"
ELABORATION = "elaboration"
TYPE_ASSERTION = "type:assertion"
TYPE_HANDOFF = "type:handoff"

CLOSED_DONE = "closed:done"
CLOSED_DECLINED = "closed:declined"
CLOSED_SUPERSEDED = "closed:superseded"
CLOSED_PARKED = "closed:parked"

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
            change=raw.get("change"),
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

    @property
    def at_ready(self):
        return self.status == STATUS_READY


@dataclass
class TrackerSnapshot:
    """Everything the filters read, and nothing they do not."""

    items: tuple = ()
    batches: tuple = ()
    closed_milestones: tuple = ()
    milestone: str = None

    def __post_init__(self):
        self.items = tuple(self.items)
        self.batches = tuple(self.batches)
        self.closed_milestones = tuple(self.closed_milestones)

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
                      milestone=b.get("milestone", milestone))
                for b in raw.get("batches", ())
            ],
            closed_milestones=raw.get("closed_milestones", ()),
            milestone=milestone,
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

    ready_batch_milestones = {
        b.milestone for b in snapshot.batches if b.at_ready and b.milestone
    }

    for item in snapshot.items:
        if not item.is_open or item.milestone_state != "open":
            continue
        if milestone_slug(item.milestone) is None:
            continue
        if item.ready or item.in_progress:
            add(item.milestone, "run", f"#{item.number} {item.state or ''}".strip())
        elif sweep and item.queued and item.parent_batch is None:
            # over-approximation: compose may have work here
            add(item.milestone, "run", f"#{item.number} queued and unbatched")
        elif (sweep and item.is_assertion and item.parent_batch is None
              and item.milestone.startswith(INTENT_PREFIX)):
            # over-approximation: handoff birth may have work here. The
            # blocker check is the loop's, not the server's.
            add(item.milestone, "run", f"#{item.number} unbatched assertion")

    for milestone in ready_batch_milestones:
        if milestone_slug(milestone) is not None:
            add(milestone, "run", "a batch at board Status Ready")

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
    ready = tuple(i for i in on_milestone if i.ready)
    units = tuple(
        b for b in snapshot.batches
        if b.at_ready and b.kind == UNIT and b.milestone in (None, milestone)
    )
    return BoltInbox(
        milestone=milestone,
        ready=ready,
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

    @property
    def empty(self):
        return not (self.ready or self.queued_to_flip
                    or self.handoff or self.orphan_queued)


def handoff_plan(snapshot, slug):
    """`tracker.md` invariant 6, which is computable and so is computed.

        An assertion is settled and unbolted when its item is open on
        intent/<slug>, has no parent batch, and has no open blockers.
        Whenever such assertions exist at the queue, the conductor births one
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
        and not ({UNIT, ELABORATION} & i.labels)
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
    """
    open_items = [i for i in snapshot.items if i.is_open]
    return DispatchInbox(
        triage=tuple(i for i in open_items if not i.milestone),
        relay=tuple(i for i in open_items if NEEDS_OPERATOR in i.labels),
    )


# ---------------------------------------------------------------------------
# The andon cord — code, not judgment
# ---------------------------------------------------------------------------

ANDON_OPEN = "<!-- flywheel:andon -->"
ANDON_CLOSE = "<!-- /flywheel:andon -->"

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
    """
    for comment in comments or ():
        body = comment.get("body") if isinstance(comment, dict) else comment
        found = parse_andon(body)
        if found:
            return found
    return None


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
        self._gh = gh
        self._graphql = graphql

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
        """
        raws = self.open_issues()
        if milestone:
            raws = [r for r in raws
                    if (r.get("milestone") or {}).get("title") == milestone]

        board = {row["number"]: row for row in self.board_items()}
        items, batches = [], []
        for raw in raws:
            item = Item.from_api(raw)
            labels = item.labels
            if with_edges:
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
            milestone=milestone,
        )

    # -- the small writes --------------------------------------------------

    def has_label(self, number, label):
        raw = self._gh(self.token, "api",
                       f"/repos/{self.org}/{self.repo}/issues/{number}")
        return any(l.get("name") == label for l in raw.get("labels", ()))

    def add_label(self, number, label):
        self._gh(self.token, "issue", "edit", str(number),
                 "--repo", f"{self.org}/{self.repo}", "--add-label", label)

    def remove_label(self, number, label):
        self._gh(self.token, "issue", "edit", str(number),
                 "--repo", f"{self.org}/{self.repo}", "--remove-label", label)

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

    def close_issue(self, number, comment=None, reason=CLOSED_DONE):
        if reason:
            self.add_label(number, reason)
        args = ["issue", "close", str(number),
                "--repo", f"{self.org}/{self.repo}"]
        if comment:
            args += ["--comment", comment]
        self._gh(self.token, *args)


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
