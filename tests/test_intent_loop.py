"""#73 — the design loop as its own program: guards, typed sessions, the R1 seam.

`design/loop-programs.md` claims the loops are "ordinary Python … unit-testable,
no agent asked to behave like code". These tests are what makes that claim
checkable: nothing here starts herdr, spawns `claude`, mints a token, touches
GitHub, or sleeps. The tracker is a `FakeTracker`, the subprocesses are a
`FakeRun`, the clock is a counter, and the snapshots are the repo's own
`workflows/fixtures/intent-tracker.json` plus small inline literals.

The property worth protecting is the DRY CYCLE: applying a cycle's writes and
running the next cycle against the resulting tracker writes nothing. The whole
stateless-process design rests on it — `flywheel server` restarts these
processes freely.
"""

import tempfile
import unittest
from pathlib import Path

from context import FIXTURES, inbox, intent, ledger as obs, sessions

Item = inbox.Item
Batch = inbox.Batch
Snapshot = inbox.TrackerSnapshot
Config = intent.Config
WaitState = sessions.WaitState


def item(number, *labels, **kw):
    kw.setdefault("milestone", "intent/x")
    return Item(number=number, labels=frozenset(labels), **kw)


def config(**kw):
    kw.setdefault("slug", "x")
    kw.setdefault("apply", False)
    return Config(**kw)


class Result:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


class FakeRun:
    """Every subprocess the loop would spawn, recorded and answered."""

    def __init__(self, returncode=0, stdout=""):
        self.calls = []
        self.returncode, self.stdout = returncode, stdout

    def __call__(self, argv, cwd=None, timeout=None):
        self.calls.append(list(argv))
        return Result(self.returncode, self.stdout)


class FakeTracker:
    """The four-method write surface, plus the reads the loop makes."""

    def __init__(self, snapshot=None, comments=None):
        self.snapshot_obj = snapshot
        self._comments = comments or {}
        self.labels = {}
        self.calls = []

    # reads
    def snapshot(self, milestone=None, with_edges=True):
        """The loop re-reads the tracker mid-cycle, so the double must be
        the source of truth rather than a bag of writes."""
        return self.snapshot_obj if self.snapshot_obj is not None else Snapshot()

    def comments(self, number):
        return self._comments.get(number, [])

    # writes
    def has_label(self, number, label):
        return label in self.labels.get(number, set())

    def add_label(self, number, label):
        self.labels.setdefault(number, set()).add(label)
        self.calls.append(("add_label", number, label))

    def remove_label(self, number, label):
        self.labels.setdefault(number, set()).discard(label)
        self.calls.append(("remove_label", number, label))

    def comment(self, number, body):
        self.calls.append(("comment", number, body))

    def set_body(self, number, body):
        self.calls.append(("set_body", number, body))

    def create_issue(self, title, body, labels=(), milestone=None):
        self.calls.append(("create_issue", title, tuple(labels), milestone))
        return 999

    def close_issue(self, number, comment=None, reason=None):
        self.calls.append(("close_issue", number, reason))


class ScriptedRunner:
    """A session runner with no session behind it."""

    def __init__(self, states=(), report="the report"):
        self.states = list(states) or [WaitState.SETTLED_DONE]
        self.report = report
        self.launched, self.closed = [], []

    def launch(self, spec):
        self.launched.append(spec)
        return sessions.SessionHandle(name=spec.name, runner="fake")

    def wait(self, handle, timeout=None):
        return self.states.pop(0) if self.states else WaitState.SETTLED_DONE

    def collect(self, handle):
        return sessions.Collected(state=WaitState.SETTLED_DONE,
                                  report=self.report)

    def close(self, handle):
        self.closed.append(handle.name)


class Clock:
    def __init__(self, now=1000.0):
        self.now = now

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


# ---------------------------------------------------------------------------
# 1 · the guards, and the dry cycle
# ---------------------------------------------------------------------------

class FlipConsumeTest(unittest.TestCase):

    def test_the_flip_writes_one_relabel_per_released_sub_issue(self):
        writer = intent.Writer(apply=False)
        intent.apply_flip_consume(writer, (11, 12))
        self.assertEqual(
            [(w.kind, w.target, w.detail) for w in writer.writes],
            [("label", "#11", "-state:queued"), ("label", "#11", "+state:ready"),
             ("label", "#12", "-state:queued"), ("label", "#12", "+state:ready")])

    def test_an_empty_plan_writes_nothing(self):
        writer = intent.Writer(apply=False)
        intent.apply_flip_consume(writer, ())
        self.assertEqual(writer.writes, [])


class DryCycleTest(unittest.TestCase):
    """The bolt's own merge criterion, stated in a form a test can hold.

    Stated precisely, because the loose statement is false and the difference
    matters: the guards CONVERGE. A cycle whose writes changed the tracker is
    followed by a cycle that sees the change. What must be true is that the
    writes stop: once the tracker holds what the guards want, every later
    cycle against it writes NOTHING.
    """

    def _guards(self, snapshot):
        writer = intent.Writer(apply=False, snapshot=snapshot)
        return intent.run_guards(
            writer, inbox.intent_inbox(snapshot, "x"), snapshot, config())

    def test_the_guards_converge_and_then_write_nothing_forever(self):
        cycle1 = Snapshot(
            items=[item(1, "state:queued", parent_batch=4),
                   item(2, "type:assertion", "state:queued")],
            batches=[Batch(number=4, kind="unit", status="Ready",
                           sub_issues=(1,), milestone="intent/x")],
        )
        self.assertEqual(
            [w.kind for w in self._guards(cycle1)],
            ["label", "label"],
            "the flip releases #1; the settled assertion #2 sits uncomposed "
            "— construction's work is born by the planner, never here")

        # #1 flipped. The assertion stays where it is, claimed by nothing.
        cycle2 = Snapshot(
            items=[item(1, "state:ready", parent_batch=4),
                   item(2, "type:assertion", "state:queued")],
            batches=list(cycle1.batches),
        )
        # The one write left is the spent approval leaving the board:
        # batch #4's Ready released everything it covered, so the consume
        # fires once...
        self.assertEqual([w.kind for w in self._guards(cycle2)],
                         ["clear_status"],
                         "a spent Ready is consumed, and nothing else moves")

        # ...and with the status gone, the tracker is settled for good.
        cycle3 = Snapshot(
            items=list(cycle2.items),
            batches=[Batch(number=4, kind="unit", status=None,
                           sub_issues=(1,), milestone="intent/x")],
        )
        self.assertEqual(self._guards(cycle3), (),
                         "a settled tracker must produce no write at all")
        self.assertEqual(self._guards(cycle3), (),
                         "and must keep producing none")


class ResumeCollectTest(unittest.TestCase):
    """A flip the loop was not there to see.

    Dispatch takes an item out of the ready set for good, so without this
    an item flipped after its session ended is invisible to every filter
    and its milestone keeps a job forever.
    """

    def flipped(self):
        return Snapshot(items=[
            item(1, "type:research", inbox.IN_PROGRESS, "stage:done"),
            item(2, "type:research", inbox.IN_PROGRESS, "stage:in-session"),
        ])

    def test_the_filter_names_a_flipped_in_progress_item(self):
        box = inbox.intent_inbox(self.flipped(), "x")
        self.assertEqual([i.number for i in box.to_collect], [1])
        self.assertEqual(box.ready, (), "it is not ready, and never will be")
        self.assertFalse(box.empty)

    def test_an_already_collected_item_is_not_named_again(self):
        snap = Snapshot(items=[item(1, "type:research", inbox.IN_PROGRESS,
                                    "stage:collected")])
        self.assertEqual(inbox.collect_plan(snap, "x"), ())

    def test_it_collects_closes_and_says_there_was_no_pane(self):
        snap = self.flipped()
        tracker = FakeTracker(snapshot=snap)
        writer = intent.Writer(tracker=tracker, apply=True, snapshot=snap)
        report = intent.Report(slug="x")
        wrote = intent.resume_collect(inbox.intent_inbox(snap, "x"), writer, None,
                                      config(apply=True), snap, report)
        self.assertTrue(wrote)
        self.assertIn(("add_label", 1, "stage:collected"), tracker.calls)
        self.assertIn(("close_issue", 1, "closed:done"), tracker.calls)
        self.assertEqual([c for c in tracker.calls
                          if c[0] == "close_issue" and c[1] == 2], [],
                         "#2 is not flipped and is untouched")
        self.assertTrue(any("no pane" in n or "after the fact" in n
                            for n in report.notes))

    def test_it_writes_nothing_when_no_item_is_flipped(self):
        snap = Snapshot(items=[item(1, "type:research", inbox.IN_PROGRESS,
                                    "stage:in-session")])
        writer = intent.Writer(apply=False, snapshot=snap)
        report = intent.Report(slug="x")
        self.assertFalse(intent.resume_collect(
            inbox.intent_inbox(snap, "x"), writer, None, config(), snap, report))
        self.assertEqual(writer.writes, [])

    def test_dispatch_never_walks_the_operators_flip_back(self):
        # A resumed batch may hold an item already at stage:done; writing
        # stage:in-session over it would erase the completion signal.
        flipped = item(1, "type:research", inbox.READY, "stage:done")
        snap = Snapshot(items=[flipped])
        writer = intent.Writer(apply=False, snapshot=snap)
        intent.dispatch_batch(intent.DesignBatch("research", (flipped,)),
                              writer, None, config(), Clock())
        self.assertNotIn("+stage:in-session",
                         [w.detail for w in writer.writes])
        self.assertNotIn("-stage:done", [w.detail for w in writer.writes])


class PausedBatchTest(unittest.TestCase):
    """A pause must survive the next cycle.

    `land` returns on a stall or an andon and closes nothing — but
    returning is not a halt. These drive `run` across cycles, which is the
    pass the earlier tests never reached: they called `land` directly, so
    the next cycle's `resume_collect` was never exercised.
    """

    def paused(self):
        # #1 flipped by the operator; #3 raised the andon, so the batch is
        # paused and every item on it carries needs-operator.
        return Snapshot(items=[
            item(1, "type:research", inbox.IN_PROGRESS, "stage:done",
                 inbox.NEEDS_OPERATOR),
            item(3, "type:research", inbox.IN_PROGRESS, inbox.NEEDS_OPERATOR),
        ])

    def test_a_flipped_sibling_of_a_paused_batch_is_not_collectable(self):
        self.assertEqual(inbox.collect_plan(self.paused(), "x"), ())
        self.assertEqual(inbox.intent_inbox(self.paused(), "x").to_collect, ())

    def test_a_run_over_a_paused_batch_closes_nothing(self):
        snap = self.paused()
        tracker = FakeTracker(snapshot=snap)
        report = intent.run(config(slug="x", apply=True), tracker=tracker,
                            runner=ScriptedRunner(), clock=Clock())
        self.assertEqual([c for c in tracker.calls if c[0] == "close_issue"], [],
                         "the pane is open and the batch is paused")
        self.assertEqual([c for c in tracker.calls
                          if c[0] == "add_label" and c[2] == "stage:collected"],
                         [])
        self.assertEqual(report.status, "ok")

    def test_an_andon_stops_the_collect_even_with_no_needs_operator(self):
        # The stronger signal, in case the label write did not land.
        snap = Snapshot(items=[item(1, "type:research", inbox.IN_PROGRESS,
                                    "stage:done")])
        tracker = FakeTracker(snapshot=snap, comments={
            1: [{"body": inbox.format_andon("the spec contradicts its decision")}]})
        writer = intent.Writer(tracker=tracker, apply=True, snapshot=snap)
        wrote = intent.resume_collect(inbox.intent_inbox(snap, "x"), writer, None,
                                      config(apply=True), snap,
                                      intent.Report(slug="x"))
        self.assertFalse(wrote)
        self.assertEqual([c for c in tracker.calls if c[0] == "close_issue"], [])

    def test_an_unpaused_flip_is_still_collected(self):
        # The exclusion must not swallow the case it was added for.
        snap = Snapshot(items=[item(1, "type:research", inbox.IN_PROGRESS,
                                    "stage:done")])
        tracker = FakeTracker(snapshot=snap)
        writer = intent.Writer(tracker=tracker, apply=True, snapshot=snap)
        self.assertTrue(intent.resume_collect(
            inbox.intent_inbox(snap, "x"), writer, None, config(apply=True),
            snap, intent.Report(slug="x")))
        self.assertIn(("close_issue", 1, "closed:done"), tracker.calls)


class ResumeMergeTest(unittest.TestCase):
    """The staggered flip must not strand the session's branch.

    `land` runs only for batches dispatched in the same cycle, and a
    dispatched item never re-enters the ready set — so a flip arriving
    later is `resume_collect`'s. Collecting the item without merging its
    branch made the tracker read finished while the deliverables sat on a
    branch nobody would look for.
    """

    def session_of(self, *items, name="writeback-x"):
        snap = Snapshot(items=list(items))
        run = FakeRun(stdout="worktree /tmp/sess-x\nbranch refs/heads/sess/writeback-x\n")
        # PRODUCTION SHAPE: dispatch writes its marker on every item, and
        # that marker is the only record of which session an item belongs
        # to. A fixture without it pins a state the loop cannot produce.
        tracker = FakeTracker(snapshot=snap, comments={
            i.number: [{"body": intent.format_dispatch(name, 1000.0)}]
            for i in items})
        writer = intent.Writer(tracker=tracker, apply=True, run=run,
                               snapshot=snap)
        report = intent.Report(slug="x")
        runner = ScriptedRunner()
        intent.resume_collect(inbox.intent_inbox(snap, "x"), writer, runner,
                              config(apply=True), snap, report)
        return run, report, runner

    def test_the_last_flip_merges_the_session_branch_and_closes_the_pane(self):
        run, report, runner = self.session_of(
            item(1, "type:writeback", inbox.IN_PROGRESS, "stage:done"))
        merges = [c for c in run.calls if c[:2] == ["wt", "merge"]]
        self.assertEqual(len(merges), 1, run.calls)
        for suppressor in ("--yes", "--no-hooks", "--no-verify"):
            self.assertNotIn(suppressor, merges[0])
        self.assertEqual(runner.closed, ["writeback-x"])

    def test_a_half_flipped_session_merges_nothing(self):
        # Session-scoped, exactly as on the live path: a branch merged
        # while a sibling is still open merges a half-finished tree.
        run, report, runner = self.session_of(
            item(1, "type:writeback", inbox.IN_PROGRESS, "stage:done"),
            item(2, "type:writeback", inbox.IN_PROGRESS, "stage:in-session"))
        self.assertEqual([c for c in run.calls if c[:2] == ["wt", "merge"]], [])
        self.assertEqual(runner.closed, [])
        self.assertTrue(any("#2 still open" in n for n in report.notes),
                        report.notes)

    def test_a_type_that_gets_no_worktree_merges_nothing(self):
        # Research edits no files, so it gets no worktree and there is no
        # branch to merge — the resume path must not invent one.
        self.assertFalse(intent.TYPES["research"].worktree)
        run, report, runner = self.session_of(
            item(1, "type:research", inbox.IN_PROGRESS, "stage:done"),
            name="research-x")
        self.assertEqual([c for c in run.calls if c[:2] == ["wt", "merge"]], [])

    def test_a_type_that_gets_no_worktree_still_has_its_pane_closed(self):
        """No branch to merge is not no pane to close.

        The two session-scoped acts are independent: the merge is
        conditional on the type having a worktree, the close never is.
        `land` gets this right on the live path — `if
        TYPES[batch.type].worktree: merge_session(...)` and then
        `runner.close(handle)` unconditionally — and the resume path was
        gating BOTH behind the same `continue`.

        `session_name` is deterministic and `launch` reuses a running
        agent, so an unclosed pane is not merely untidy: the next research
        batch is dispatched into an orphaned, already-settled pane.
        """
        run, report, runner = self.session_of(
            item(1, "type:research", inbox.IN_PROGRESS, "stage:done"),
            name="research-x")
        self.assertEqual(runner.closed, ["research-x"],
                         "the pane closes even though nothing merged")

    def test_a_half_flipped_no_worktree_session_keeps_its_pane_open(self):
        # The close is unconditional on TYPE, never on completeness: a
        # session with an item still open keeps its pane, worktree or not.
        run, report, runner = self.session_of(
            item(1, "type:research", inbox.IN_PROGRESS, "stage:done"),
            item(2, "type:research", inbox.IN_PROGRESS, "stage:in-session"),
            name="research-x")
        self.assertEqual(runner.closed, [])
        self.assertTrue(any("#2 still open" in n for n in report.notes),
                        report.notes)


class SessionMembershipTest(unittest.TestCase):
    """The loop must be able to name the set of items a session carries.

    Both defects here had one root: the session-scoped teardown was keyed
    on the batch (which a later batch of the same type is not) and on
    type+slug (which is a NAME, not a membership). The dispatch marker is
    now written on every item, and is that membership.
    """

    def test_dispatch_records_the_session_on_every_item(self):
        items = [item(1, "type:writeback", inbox.READY),
                 item(2, "type:writeback", inbox.READY)]
        snap = Snapshot(items=items)
        tracker = FakeTracker(snapshot=snap)
        writer = intent.Writer(tracker=tracker, apply=True, snapshot=snap)
        intent.dispatch_batch(intent.DesignBatch("writeback", tuple(items)),
                              writer, ScriptedRunner(), config(apply=True),
                              Clock())
        marked = [c[1] for c in tracker.calls if c[0] == "comment"]
        self.assertEqual(sorted(marked), [1, 2], "not just batch.first")

    def test_the_marker_round_trips_its_session_name(self):
        body = intent.format_dispatch("writeback-x", 1000.0)
        self.assertEqual(intent.session_named([{"body": body}]), "writeback-x")
        self.assertIsNone(intent.session_named([{"body": "no marker here"}]))

    def test_a_later_batch_in_the_same_session_holds_the_teardown(self):
        # `launch` is idempotent and reuses the agent running under the
        # name, so a second same-type batch joins THIS pane and branch.
        # Tearing them down on the first batch's completion cut it off.
        first = item(1, "type:writeback", inbox.IN_PROGRESS, "stage:done")
        later = item(2, "type:writeback", inbox.IN_PROGRESS, "stage:in-session")
        snap = Snapshot(items=[first, later])
        tracker = FakeTracker(snapshot=snap, comments={
            n: [{"body": intent.format_dispatch("writeback-x", 1000.0)}]
            for n in (1, 2)})
        run = FakeRun()
        runner = ScriptedRunner()
        spec = sessions.SessionSpec(name="writeback-x", cwd="/tmp", order="go",
                                    profile="flywheel-design-session")
        handle = runner.launch(spec)
        writer = intent.Writer(tracker=tracker, apply=True, run=run,
                               snapshot=snap)
        report = intent.Report(slug="x")
        intent.land(intent.DesignBatch("writeback", (first,)), spec, handle,
                    writer, runner, tracker, config(apply=True), snap,
                    Clock(), report)
        self.assertEqual(runner.closed, [],
                         "#2 is still in session; the pane is not ours to close")
        self.assertEqual([c for c in run.calls if c[:2] == ["wt", "merge"]], [],
                         "and its branch is not ours to merge")
        self.assertTrue(any("#2" in n for n in report.notes), report.notes)


class PauseMarksTheBatchTest(unittest.TestCase):
    """A pause must mark every item, because the label IS the guard.

    `collect_plan` excludes a paused item by its `needs-operator` label. A
    pause that labelled only the raising item — or, on a stall, nothing —
    left the next cycle free to collect and close a flipped sibling of the
    very batch it had paused.
    """

    def _land(self, items, states=(), comments=None):
        snap = Snapshot(items=items)
        tracker = FakeTracker(snapshot=snap, comments=comments or {})
        runner = ScriptedRunner(states=list(states))
        spec = sessions.SessionSpec(name="research-x", cwd="/tmp", order="go",
                                    profile="flywheel-design-session")
        handle = runner.launch(spec)
        writer = intent.Writer(tracker=tracker, apply=True, snapshot=snap)
        clock = Clock()
        if states:
            class Ticking(Clock):
                def __call__(s):
                    v = s.now
                    s.now += sessions.WAIT_CHUNK_S
                    return v
            clock = Ticking()
        intent.land(intent.DesignBatch("research", tuple(items)), spec, handle,
                    writer, runner, tracker, config(apply=True), snap, clock,
                    intent.Report(slug="x"))
        return tracker

    def paused_items(self, tracker):
        return sorted(c[1] for c in tracker.calls
                      if c[0] == "add_label" and c[2] == inbox.NEEDS_OPERATOR)

    def test_an_andon_pauses_every_item_of_the_batch(self):
        items = [item(1, "type:research", inbox.IN_PROGRESS, "stage:done"),
                 item(3, "type:research", inbox.IN_PROGRESS)]
        tracker = self._land(items, comments={
            3: [{"body": inbox.format_andon("the spec contradicts its decision")}]})
        self.assertEqual(self.paused_items(tracker), [1, 3],
                         "the flipped sibling must be paused too, or the next "
                         "cycle collects it")

    def test_a_stall_pauses_every_item_of_the_batch(self):
        items = [item(1, "type:research", inbox.IN_PROGRESS, "stage:done"),
                 item(3, "type:research", inbox.IN_PROGRESS)]
        tracker = self._land(items, states=[WaitState.WORKING] * 40)
        self.assertEqual(self.paused_items(tracker), [1, 3])

    def test_the_pause_then_makes_the_sibling_uncollectable(self):
        # The two halves together: the label the pause writes is exactly
        # what `collect_plan` reads.
        paused = Snapshot(items=[
            item(1, "type:research", inbox.IN_PROGRESS, "stage:done",
                 inbox.NEEDS_OPERATOR),
            item(3, "type:research", inbox.IN_PROGRESS, inbox.NEEDS_OPERATOR)])
        self.assertEqual(inbox.collect_plan(paused, "x"), ())


class ReleasedAssertionsTest(unittest.TestCase):
    """A released assertion never escalates.

    Assertions are construction's, never a design session's: the planner
    cards their work from the book. `batch_ready` reports them
    undispatchable — correctly, they are not a design type — and the loop
    must not write `needs-operator` on each.
    """

    def released(self):
        return Snapshot(
            items=[item(2, "type:assertion", inbox.READY, parent_batch=10),
                   item(3, "type:assertion", inbox.READY, parent_batch=10)],
            batches=[Batch(number=10, kind="unit", status=inbox.STATUS_READY,
                           sub_issues=(2, 3), milestone="intent/x")])

    def test_the_assertions_arrive_undispatchable_by_design(self):
        snap = self.released()
        batches, undispatchable = intent.batch_ready(snap, snap.items)
        self.assertEqual(list(batches), [])
        self.assertEqual(sorted(k for _, k in undispatchable), ["assertion"] * 2)

    def test_released_assertions_escalate_nothing(self):
        snap = self.released()
        tracker = FakeTracker(snapshot=snap)
        intent.run(config(slug="x", apply=True), tracker=tracker,
                   runner=ScriptedRunner(), clock=Clock())
        self.assertEqual(
            [c for c in tracker.calls
             if c[0] == "add_label" and c[2] == inbox.NEEDS_OPERATOR], [],
            "the assertions are construction's, not a fault")

    def test_a_genuinely_untyped_item_is_still_escalated(self):
        # The exclusion is for assertions only; an item the loop cannot
        # type at all is still the operator's to answer.
        snap = Snapshot(items=[item(1, inbox.READY)])
        tracker = FakeTracker(snapshot=snap)
        intent.run(config(slug="x", apply=True), tracker=tracker,
                   runner=ScriptedRunner(), clock=Clock())
        self.assertIn(("add_label", 1, inbox.NEEDS_OPERATOR), tracker.calls)


class ParentageTest(unittest.TestCase):
    """The live API carries no parent; the guards key on one."""

    def test_parentage_is_backfilled_from_the_batches(self):
        items = [item(1), item(2)]
        batches = [Batch(number=4, kind="unit", sub_issues=(1,),
                         milestone="intent/x")]
        filled = {i.number: i.parent_batch
                  for i in inbox.backfill_parentage(items, batches)}
        self.assertEqual(filled, {1: 4, 2: None})

    def test_an_already_batched_item_is_not_composed(self):
        # Without the back-fill this is the live-tracker failure: every batched
        # item reads as an orphan, the loop composes a second batch every
        # cycle, and GitHub 422s the re-attach.
        raw = [item(1, "state:queued"), item(2, "state:queued")]
        batches = [Batch(number=4, kind="unit", sub_issues=(1,),
                         milestone="intent/x")]
        snap = Snapshot(items=inbox.backfill_parentage(raw, batches),
                        batches=batches)
        self.assertEqual(
            [i.number for i in inbox.compose_plan(snap, "x")], [2])

    def test_a_parent_the_api_did_supply_is_kept(self):
        filled = inbox.backfill_parentage(
            [item(1, parent_batch=7)],
            [Batch(number=4, sub_issues=(1,), milestone="intent/x")])
        self.assertEqual(filled[0].parent_batch, 7)


# ---------------------------------------------------------------------------
# 2 · batching — one session type per batch, prototypes alone
# ---------------------------------------------------------------------------

class BatchingTest(unittest.TestCase):

    def test_ready_items_group_by_their_type_label(self):
        snap = Snapshot(items=[item(1, "type:research", "state:ready"),
                               item(2, "type:research", "state:ready"),
                               item(3, "type:writeback", "state:ready")])
        batches, _ = intent.batch_ready(snap, snap.items)
        self.assertEqual([(b.type, b.numbers) for b in batches],
                         [("research", (1, 2)), ("writeback", (3,))])

    def test_prototypes_always_ride_alone(self):
        snap = Snapshot(items=[item(1, "type:prototype", "state:ready"),
                               item(2, "type:prototype", "state:ready")])
        batches, _ = intent.batch_ready(snap, snap.items)
        self.assertEqual([b.numbers for b in batches], [(1,), (2,)],
                         "each prototype is its own experiment")

    def test_a_batch_with_an_open_blocker_does_not_run(self):
        snap = Snapshot(items=[item(1, "type:research", "state:ready",
                                    blocked_by=(2,)),
                               item(2, "type:research", "state:ready")])
        batches, _ = intent.batch_ready(snap, snap.items)
        self.assertEqual([b.numbers for b in batches], [(2,)])

    def test_an_assertion_is_never_dispatched_to_a_design_session(self):
        snap = Snapshot(items=[item(1, "type:assertion", "state:ready")])
        batches, undispatchable = intent.batch_ready(snap, snap.items)
        self.assertEqual(batches, ())
        self.assertEqual([i.number for i, _ in undispatchable], [1])

    def test_an_untyped_item_is_reported_rather_than_defaulted(self):
        # workflows/fixtures/flywheel-intent.compiled.js falls back to
        # type:research here. A fixture reviewed and never run does not
        # outrank "batch the ready items by their type label".
        snap = Snapshot(items=[item(1, "state:ready")])
        batches, undispatchable = intent.batch_ready(snap, snap.items)
        self.assertEqual(batches, ())
        self.assertEqual(undispatchable[0][1], None)

    def test_the_untyped_item_raises_needs_operator_once_and_not_twice(self):
        snap = Snapshot(items=[item(1, "state:ready")])
        writer = intent.Writer(apply=False, snapshot=snap)
        for _ in range(2):
            inbox.set_needs_operator(writer, 1, "no type label")
        self.assertEqual([w.detail for w in writer.writes if w.kind == "label"],
                         ["+needs-operator"])


# ---------------------------------------------------------------------------
# 3 · the session specs
# ---------------------------------------------------------------------------

class SessionSpecTest(unittest.TestCase):

    def test_every_type_carries_its_profile_model_and_round(self):
        self.assertEqual(intent.TYPES["interactive"].profile,
                         "flywheel-interactive-session")
        self.assertTrue(all(
            t.profile == "flywheel-design-session"
            for name, t in intent.TYPES.items() if name != "interactive"),
            "one rule: does this session build a lavish surface?")
        self.assertEqual(
            {n: t.model for n, t in intent.TYPES.items()},
            {"planning": "fable", "interactive": "fable",
             "research": "opus[1m]", "prototype": "opus", "writeback": "opus"})
        self.assertEqual(
            sorted(n for n, t in intent.TYPES.items() if t.operator_round),
            ["interactive", "planning"])

    def test_research_gets_no_worktree_and_so_skips_the_merge(self):
        self.assertFalse(intent.TYPES["research"].worktree)
        self.assertTrue(all(t.worktree for n, t in intent.TYPES.items()
                            if n != "research"))

    def test_a_session_name_is_stable_and_fits_herdrs_cap(self):
        batch = intent.DesignBatch("planning", (item(1, "type:planning"),))
        first = intent.session_name(batch, "a-very-long-intent-slug-indeed")
        second = intent.session_name(batch, "a-very-long-intent-slug-indeed")
        self.assertEqual(first, second,
                         "a name that moved would launch a second session")
        self.assertLessEqual(len(first), sessions.MAX_NAME)

    def test_a_lone_prototype_keeps_its_item_number_in_the_name(self):
        batch = intent.DesignBatch("prototype", (item(42, "type:prototype"),))
        name = intent.session_name(batch, "a-very-long-intent-slug-indeed")
        self.assertTrue(name.endswith("-42"))
        self.assertLessEqual(len(name), sessions.MAX_NAME)

    def test_the_work_order_is_one_prompt_with_its_summary_line_first(self):
        batch = intent.DesignBatch("research", (item(1), item(2)))
        order = intent.session_order(batch, config(slug="lamp"))
        self.assertEqual(order.splitlines()[0],
                         "research session for intent lamp - items #1, #2")
        self.assertIn("Deliver by settling", order)

    def test_a_dispatch_comment_carries_the_origin_a_restart_recovers(self):
        body = intent.format_dispatch("research-x", 1786000000.0)
        self.assertEqual(intent.parse_dispatch([{"body": body}], "research-x"),
                         (1786000000.0, False))

    def test_a_dispatch_for_another_session_is_not_this_ones_clock(self):
        body = intent.format_dispatch("planning-x", 1786000000.0)
        self.assertEqual(intent.parse_dispatch([{"body": body}], "research-x"),
                         (None, False))


# ---------------------------------------------------------------------------
# 4 · completion — one label, per item, nothing to configure
# ---------------------------------------------------------------------------

class CompletionTest(unittest.TestCase):

    def test_the_operators_stage_done_is_what_the_filter_reads(self):
        snap = Snapshot(items=[item(1, "stage:done"), item(2)])
        self.assertTrue(intent.is_done(1, snap))
        self.assertFalse(intent.is_done(2, snap))

    def test_an_item_off_the_snapshot_is_not_read_as_done(self):
        self.assertFalse(intent.is_done(7, Snapshot(items=[item(1)])))

    def test_stage_collected_is_what_guards_a_second_collect(self):
        snap = Snapshot(items=[item(1, "stage:done", "stage:collected"),
                               item(2, "stage:done")])
        self.assertTrue(intent.is_collected(1, snap))
        self.assertFalse(intent.is_collected(2, snap))

    def test_the_board_is_not_consulted_for_completion(self):
        # Per-item session state lives in labels; the board's Status is the
        # operator's batch-approval surface and nothing else. The filter
        # takes no board at all, so no Status can make an item complete.
        import inspect
        self.assertEqual(list(inspect.signature(intent.is_done).parameters),
                         ["number", "snapshot"])

    def test_the_intent_loop_moves_the_leading_edge_like_the_bolt_loop(self):
        # One vocabulary means one rule about the set: writing a stage
        # removes the previous one, in BOTH loops. Accumulating them made
        # `stage_of(..., DESIGN_STAGES)` answer `stage:in-session` for a
        # finished item, because it returns the first match in order.
        snap = Snapshot(items=[item(1, "stage:in-session", "stage:done")])
        writer = intent.Writer(apply=False, snapshot=snap)
        intent.set_stage(writer, 1, "stage:collected")
        self.assertEqual([w.detail for w in writer.writes],
                         ["-stage:in-session", "-stage:done",
                          "+stage:collected"])
        self.assertTrue(writer.has_label(1, "stage:collected"))
        self.assertFalse(writer.has_label(1, "stage:in-session"),
                         "the writer must not report a label it just removed")

    def test_moving_to_a_stage_the_item_already_holds_writes_nothing(self):
        snap = Snapshot(items=[item(1, "stage:collected")])
        writer = intent.Writer(apply=False, snapshot=snap)
        self.assertFalse(intent.set_stage(writer, 1, "stage:collected"))
        self.assertEqual(writer.writes, [])

    def test_nothing_names_a_completion_signal_any_more(self):
        # The state in which no signal is configured, and completion is
        # therefore *unknown* rather than false, has ceased to exist.
        self.assertFalse(hasattr(intent, "COMPLETION_SIGNALS"))
        self.assertFalse(hasattr(intent, "R1_UNRESOLVED"))
        self.assertNotIn("completion_signal", Config.__dataclass_fields__)
        self.assertNotIn("done_label", Config.__dataclass_fields__)
        self.assertNotIn("done_status", Config.__dataclass_fields__)
        self.assertIsNone(intent.config_fault(config()))


# ---------------------------------------------------------------------------
# 5 · a whole cycle
# ---------------------------------------------------------------------------

class CycleTest(unittest.TestCase):

    def test_the_repo_fixture_fires_exactly_the_guards_it_annotates(self):
        report = intent.run(config(
            slug="sandbox-design",
            fixture=str(FIXTURES / "intent-tracker.json")))
        self.assertEqual(report.status, "ok")
        kinds = [w.split()[0] for w in report.writes]
        self.assertEqual(kinds.count("issue"), 0,
                         "the loop births nothing — #202 sits uncomposed")
        self.assertEqual(kinds.count("command"), 2,
                         "flywheel-batch for #203, and one wt switch")
        self.assertEqual(report.dispatched,
                         ("planning-sandbox-design-201 — #201",),
                         "the name is per-batch: a new round gets a fresh "
                         "pane and a real prompt")

    def test_dispatch_puts_the_batchs_items_in_session(self):
        report = intent.run(config(
            slug="sandbox-design",
            fixture=str(FIXTURES / "intent-tracker.json")))
        self.assertIn("label #201 — +stage:in-session", report.writes)

    def test_a_dry_run_records_its_plan_and_performs_none_of_it(self):
        tracker = FakeTracker()
        report = intent.run(
            config(slug="sandbox-design",
                   fixture=str(FIXTURES / "intent-tracker.json")),
            tracker=tracker)
        self.assertTrue(report.writes)
        self.assertEqual(tracker.calls, [],
                         "a dry run plans every write and applies none")

    def test_an_empty_milestone_stops_with_no_writes_at_all(self):
        writer = intent.Writer(apply=False, snapshot=Snapshot())
        report = intent.run(config(slug="x"), writer=writer)
        self.assertEqual(report.status, "stopped")
        self.assertIn("nothing to read", report.failure)

    def test_the_resting_report_names_the_queue_it_left(self):
        report = intent.run(config(
            slug="sandbox-design",
            fixture=str(FIXTURES / "intent-tracker.json")))
        self.assertTrue(any("#202" in line for line in report.resting))
        self.assertTrue(any("batch #204" in line for line in report.resting))

    def test_a_run_naming_no_signal_reports_no_unresolved_note(self):
        # There is one filter and nothing to configure, so a run against a
        # milestone with no completion signal named anywhere is ordinary.
        report = intent.run(config(
            slug="sandbox-design",
            fixture=str(FIXTURES / "intent-tracker.json")))
        self.assertEqual(report.status, "ok")
        self.assertFalse(any("unresolved" in n.lower() for n in report.notes),
                         report.notes)


# ---------------------------------------------------------------------------
# 6 · landing — the andon, and what a settled session is not
# ---------------------------------------------------------------------------

class LandingTest(unittest.TestCase):

    def _land(self, cfg, tracker, runner=None, clock=None, items=None,
              batch=None):
        items = items or [item(1)]
        batch = batch or intent.DesignBatch("research", tuple(items))
        spec = sessions.SessionSpec(name="research-x", cwd="/tmp", order="go",
                                    profile="flywheel-design-session")
        runner = runner or ScriptedRunner()
        handle = runner.launch(spec)
        snapshot = Snapshot(items=items)
        if tracker.snapshot_obj is None:
            tracker.snapshot_obj = snapshot
        writer = intent.Writer(tracker=tracker, apply=True, snapshot=snapshot)
        report = intent.Report(slug="x")
        intent.land(batch, spec, handle, writer, runner, tracker, cfg,
                    snapshot, clock or Clock(), report)
        return writer, report, runner

    def test_a_settled_session_is_not_a_finished_one(self):
        # A settled pane is still not a finished session — and it is now
        # `stage:done` that decides.
        tracker = FakeTracker()
        writer, report, runner = self._land(config(apply=True), tracker)
        self.assertEqual(runner.closed, [],
                         "the operator may iterate a round as often as they like")
        self.assertEqual([c for c in tracker.calls if c[0] == "close_issue"], [])
        self.assertTrue(any("not yet marked done" in n for n in report.notes))

    def test_an_andon_pauses_the_batch_and_merges_nothing(self):
        tracker = FakeTracker(comments={
            1: [{"body": inbox.format_andon("the spec contradicts its decision")}]})
        writer, report, runner = self._land(
            config(apply=True), tracker, items=[item(1, "stage:done")])
        self.assertIn(("add_label", 1, "needs-operator"), tracker.calls)
        self.assertEqual([c for c in tracker.calls if c[0] == "close_issue"], [])
        self.assertEqual(runner.closed, [])
        self.assertTrue(any("raised the andon" in n for n in report.notes))

    def test_prose_about_stopping_is_not_an_andon(self):
        tracker = FakeTracker(comments={
            1: [{"body": "I nearly raised the andon but did not."}]})
        writer, report, runner = self._land(config(apply=True), tracker)
        self.assertNotIn(("add_label", 1, "needs-operator"), tracker.calls)

    def test_a_flipped_item_is_collected_marked_and_closed(self):
        tracker = FakeTracker()
        writer, report, runner = self._land(
            config(apply=True), tracker, items=[item(1, "stage:done")])
        self.assertIn(("add_label", 1, "stage:collected"), tracker.calls)
        self.assertIn(("close_issue", 1, "closed:done"), tracker.calls)
        self.assertEqual(runner.closed, ["research-x"],
                         "every item collected, so the session may be torn down")

    def test_a_worktree_bearing_session_merges_once_when_its_last_item_lands(self):
        # `land`'s other completion tests all use `research`, whose type has
        # no worktree, so `merge_session` is never reached on this path —
        # only on the resume path. A writeback session bears one, so the
        # teardown merge and the pane close both have to fire, exactly once.
        only = item(1, "type:writeback", inbox.IN_PROGRESS, "stage:done")
        snap = Snapshot(items=[only])
        tracker = FakeTracker(snapshot=snap, comments={
            1: [{"body": intent.format_dispatch("writeback-x", 1000.0)}]})
        run = FakeRun()
        runner = ScriptedRunner()
        spec = sessions.SessionSpec(name="writeback-x", cwd="/tmp/wt-x", order="go",
                                    profile="flywheel-design-session")
        handle = runner.launch(spec)
        writer = intent.Writer(tracker=tracker, apply=True, run=run, snapshot=snap)
        report = intent.Report(slug="x")

        intent.land(intent.DesignBatch("writeback", (only,)), spec, handle,
                    writer, runner, tracker, config(apply=True), snap,
                    Clock(), report)

        merges = [c for c in run.calls if c[:2] == ["wt", "merge"]]
        self.assertEqual(len(merges), 1, f"exactly one merge, got {merges}")
        self.assertIn("/tmp/wt-x", merges[0], "and it merges the session's worktree")
        self.assertEqual(runner.closed, ["writeback-x"])
        self.assertIn(("add_label", 1, "stage:collected"), tracker.calls)

    def test_the_flip_written_during_the_session_is_seen(self):
        """The pane path, which is the primary one.

        The session writes `stage:done` to its own item and settles WHILE
        the loop is blocked in `supervise`, so the picture the cycle opened
        with cannot contain it. Reading the stale snapshot meant the pane
        path could never see its own write — and there is no next pass,
        because dispatch already took the item out of the ready set.
        """
        before = Snapshot(items=[item(1, "stage:in-session")])
        after = Snapshot(items=[item(1, "stage:in-session", "stage:done")])
        tracker = FakeTracker(snapshot=after)          # the tracker as it is NOW
        batch = intent.DesignBatch("research", (item(1, "stage:in-session"),))
        spec = sessions.SessionSpec(name="research-x", cwd="/tmp", order="go",
                                    profile="flywheel-design-session")
        runner = ScriptedRunner()
        handle = runner.launch(spec)
        writer = intent.Writer(tracker=tracker, apply=True, snapshot=before)
        report = intent.Report(slug="x")
        intent.land(batch, spec, handle, writer, runner, tracker,
                    config(apply=True), before, Clock(), report)
        self.assertIn(("close_issue", 1, "closed:done"), tracker.calls)
        self.assertIn(("add_label", 1, "stage:collected"), tracker.calls)
        self.assertEqual(runner.closed, ["research-x"],
                         "the session is torn down once its item is collected")

    def test_an_unflipped_item_is_still_not_collected_after_the_re_read(self):
        # The re-read must not turn "not done" into "done".
        unchanged = Snapshot(items=[item(1, "stage:in-session")])
        tracker = FakeTracker(snapshot=unchanged)
        writer, report, runner = self._land(
            config(apply=True), tracker, items=[item(1, "stage:in-session")])
        self.assertEqual([c for c in tracker.calls if c[0] == "close_issue"], [])
        self.assertEqual(runner.closed, [])

    def test_a_collected_item_ends_carrying_one_stage_label(self):
        tracker = FakeTracker()
        writer, report, runner = self._land(
            config(apply=True), tracker,
            items=[item(1, "stage:in-session", "stage:done")])
        self.assertIn(("remove_label", 1, "stage:in-session"), tracker.calls)
        self.assertIn(("remove_label", 1, "stage:done"), tracker.calls)
        self.assertEqual(tracker.labels[1] & {"stage:in-session", "stage:done",
                                              "stage:collected"},
                         {"stage:collected"})

    def test_two_of_three_flipped_collects_exactly_those_two(self):
        tracker = FakeTracker()
        items = [item(1, "stage:done"), item(2, "stage:done"), item(3)]
        writer, report, runner = self._land(config(apply=True), tracker,
                                            items=items)
        closed = [c[1] for c in tracker.calls if c[0] == "close_issue"]
        self.assertEqual(closed, [1, 2])
        self.assertNotIn(("add_label", 3, "stage:collected"), tracker.calls)

    def test_the_session_scoped_acts_wait_for_the_third_item(self):
        run = FakeRun()
        tracker = FakeTracker()
        items = [item(1, "stage:done"), item(2, "stage:done"), item(3)]
        runner = ScriptedRunner()
        writer, report, runner = self._land(
            config(apply=True), tracker, runner=runner, items=items)
        self.assertEqual(runner.closed, [],
                         "a pane closed under a running session destroys it")
        self.assertEqual([w for w in writer.writes if w.kind == "command"], [],
                         "a branch merged mid-session merges a half tree")
        self.assertTrue(any("#3" in n for n in report.notes))

    def test_an_already_collected_item_is_not_collected_twice(self):
        tracker = FakeTracker()
        items = [item(1, "stage:done", "stage:collected")]
        writer, report, runner = self._land(config(apply=True), tracker,
                                            items=items)
        self.assertEqual([c for c in tracker.calls if c[0] == "close_issue"], [])
        self.assertEqual(runner.closed, ["research-x"],
                         "already collected still completes the session")

    def test_a_stalled_session_keeps_its_pane_as_evidence(self):
        tracker = FakeTracker()
        runner = ScriptedRunner(states=[WaitState.WORKING] * 40)

        class Ticking(Clock):
            def __call__(self):
                value = self.now
                self.now += sessions.WAIT_CHUNK_S
                return value

        writer, report, runner = self._land(
            config(apply=True), tracker,
            runner=runner, clock=Ticking(), items=[item(1, "stage:done")])
        self.assertTrue(any("stalled" in n for n in report.notes))
        self.assertEqual(runner.closed, [])
        self.assertEqual([c for c in tracker.calls if c[0] == "close_issue"], [])


# ---------------------------------------------------------------------------
# 7 · the merge is never routed around
# ---------------------------------------------------------------------------

class MergeTest(unittest.TestCase):

    def test_the_merge_runs_through_the_gate_and_suppresses_nothing(self):
        run = FakeRun()
        writer = intent.Writer(apply=True, run=run)
        intent.merge_session(writer, config(apply=True), "/tmp/sess")
        argv = run.calls[0]
        self.assertEqual(argv[:2], ["wt", "merge"])
        for suppressor in ("--yes", "--no-hooks", "--no-verify"):
            self.assertNotIn(suppressor, argv)

    def test_an_approval_prompt_is_a_work_stoppage_not_a_workaround(self):
        run = FakeRun(returncode=1, stdout=intent.APPROVAL_BLOCK)
        writer = intent.Writer(apply=True, run=run)
        with self.assertRaises(intent.LoopStop) as raised:
            intent.merge_session(writer, config(apply=True), "/tmp/sess")
        self.assertIn("work stoppage", str(raised.exception))


# ---------------------------------------------------------------------------
# 8 · args, parsed defensively
# ---------------------------------------------------------------------------

class ConfigTest(unittest.TestCase):

    def test_an_args_object_arriving_as_a_json_string_is_parsed(self):
        cfg = Config.from_mapping('{"slug": "lamp", "org": "agentplot"}')
        self.assertEqual((cfg.slug, cfg.org), ("lamp", "agentplot"))

    def test_unknown_keys_do_not_blow_up_the_run(self):
        self.assertEqual(Config.from_mapping({"slug": "x", "nonsense": 1}).slug,
                         "x")

    def test_a_run_with_no_slug_stops_before_reading_anything(self):
        self.assertIn("no intent slug", intent.config_fault(config(slug="")))


class WriterCacheTest(unittest.TestCase):
    """A cached label surface may not outlive the snapshot behind it.

    `Writer.has_label` answers from the cycle's snapshot plus what this
    writer has already written. Both halves of that cache are invalidated
    when the snapshot is replaced, because a re-read is the loop learning
    what the world now says.
    """

    def test_an_addition_does_not_survive_a_re_read(self):
        # The normal pane path: dispatch writes `stage:in-session`, the pane
        # session's own `stage:done` removes it on GitHub. A stale addition
        # makes the surface answer from a state that no longer exists, and
        # sends one redundant `--remove-label` per collect.
        writer = intent.Writer(tracker=None, apply=False,
                               snapshot=Snapshot(items=[item(1)]))
        writer.add_label(1, "stage:in-session")
        self.assertTrue(writer.has_label(1, "stage:in-session"))

        writer.snapshot = Snapshot(items=[item(1, "stage:done")])
        self.assertFalse(writer.has_label(1, "stage:in-session"),
                         "the re-read is what the surface answers from now")
        self.assertTrue(writer.has_label(1, "stage:done"))

    def test_a_removal_does_not_survive_a_re_read_either(self):
        # The direction that was already invalidated. Both go together: a
        # cache with one direction invalidated is a cache whose rule nobody
        # can state.
        writer = intent.Writer(tracker=None, apply=False,
                               snapshot=Snapshot(items=[item(1, "needs-operator")]))
        writer.remove_label(1, "needs-operator")
        self.assertFalse(writer.has_label(1, "needs-operator"))

        writer.snapshot = Snapshot(items=[item(1, "needs-operator")])
        self.assertTrue(writer.has_label(1, "needs-operator"),
                        "the operator put it back; the cycle's own write is stale")

    def test_within_one_snapshot_the_cache_still_answers(self):
        # The invalidation must not cost the read-your-writes property the
        # dry cycle depends on.
        writer = intent.Writer(tracker=None, apply=False,
                               snapshot=Snapshot(items=[item(1)]))
        writer.add_label(1, "stage:collected")
        self.assertTrue(writer.has_label(1, "stage:collected"))
        writer.remove_label(1, "stage:collected")
        self.assertFalse(writer.has_label(1, "stage:collected"))


class ObservedRunTest(unittest.TestCase):
    """The run ledger and the expectation gate on the intent loop."""

    def a_ready_batch(self):
        return Snapshot(items=[item(1, "type:research", inbox.READY)])

    def observed(self, snap, root, gate_mode="gate"):
        led = obs.RunLedger(root, "intent-x", gate_mode=gate_mode)
        tracker = FakeTracker(snapshot=snap)
        runner = ScriptedRunner()
        report = intent.run(config(slug="x", apply=True), tracker=tracker,
                            runner=runner, clock=Clock(), ledger=led)
        return report, runner

    def test_an_unapproved_pass_gates_before_any_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            report, runner = self.observed(self.a_ready_batch(), tmp)
            self.assertEqual(report.status, "stopped")
            self.assertIn("gated", report.failure)
            self.assertEqual(runner.launched, [], "nothing may be charged")
            scope = Path(tmp) / "intent-x"
            self.assertTrue((scope / "pending.json").exists())
            self.assertTrue(list(scope.glob("*.plan.md")))

    def test_an_approved_plan_dispatches(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.observed(self.a_ready_batch(), tmp)
            obs.approve(tmp, "intent-x")
            report, runner = self.observed(self.a_ready_batch(), tmp)
            self.assertEqual(report.status, "ok", report.failure)
            self.assertTrue(runner.launched)
            report_doc = list((Path(tmp) / "intent-x").glob("*.report.md"))
            self.assertTrue(report_doc)
            self.assertIn("session:research-x", report_doc[-1].read_text())

    def test_a_changed_plan_regates(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.observed(self.a_ready_batch(), tmp)
            obs.approve(tmp, "intent-x")
            other = Snapshot(items=[item(2, "type:planning", inbox.READY)])
            report, runner = self.observed(other, tmp)
            self.assertIn("gated", report.failure)
            self.assertEqual(runner.launched, [])

    def test_a_dry_run_writes_the_plan_and_never_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            led = obs.RunLedger(tmp, "intent-x", gate_mode="gate")
            report = intent.run(
                config(slug="sandbox-design",
                       fixture=str(FIXTURES / "intent-tracker.json")),
                ledger=led)
            self.assertEqual(report.status, "ok")
            self.assertTrue(report.dispatched, "the dry plan still plans")
            self.assertTrue(list((Path(tmp) / "intent-x").glob("*.plan.md")))
            self.assertFalse((Path(tmp) / "intent-x" / "pending.json").exists())


if __name__ == "__main__":
    unittest.main()
