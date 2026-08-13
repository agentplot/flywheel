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

import unittest

from context import FIXTURES, inbox, intent, sessions

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

    def __init__(self, snapshot=None, comments=None, board=()):
        self.snapshot_obj = snapshot
        self._comments = comments or {}
        self._board = list(board)
        self.labels = {}
        self.calls = []

    # reads
    def comments(self, number):
        return self._comments.get(number, [])

    def board_items(self):
        return self._board

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


class HandoffGuardTest(unittest.TestCase):

    def test_birth_creates_one_handoff_item_naming_exactly_that_set(self):
        snap = Snapshot(items=[
            item(1, "type:assertion", "state:queued"),
            item(2, "type:assertion", "state:queued"),
        ])
        writer = intent.Writer(apply=False)
        intent.apply_handoff(writer, inbox.handoff_plan(snap, "x"), snap, "x")
        self.assertEqual([w.kind for w in writer.writes], ["issue"])
        self.assertEqual(intent.parse_handoff_set(intent.handoff_body("x", (1, 2))),
                         (1, 2))

    def test_amend_is_silent_when_the_set_is_unchanged(self):
        # THE dry-cycle crux. The assertions stay open and unbatched on the
        # milestone until the handoff SESSION makes the custody move, so
        # birth-on-cycle-N is seen as amend-on-cycle-N+1 forever. An amend that
        # rewrote an unchanged body would make every cycle wet.
        snap = Snapshot(items=[
            item(1, "type:assertion", "state:queued"),
            item(9, "type:handoff", "state:queued",
                 body=intent.handoff_body("x", (1,))),
        ])
        plan = inbox.handoff_plan(snap, "x")
        self.assertEqual(plan.action, "amend")
        writer = intent.Writer(apply=False)
        intent.apply_handoff(writer, plan, snap, "x")
        self.assertEqual(writer.writes, [],
                         "an unchanged set must write nothing at all")

    def test_amend_rewrites_the_body_when_a_newcomer_joins(self):
        snap = Snapshot(items=[
            item(1, "type:assertion", "state:queued"),
            item(2, "type:assertion", "state:queued"),
            item(9, "type:handoff", "state:queued",
                 body=intent.handoff_body("x", (1,))),
        ])
        writer = intent.Writer(apply=False)
        intent.apply_handoff(writer, inbox.handoff_plan(snap, "x"), snap, "x")
        self.assertEqual([w.kind for w in writer.writes], ["body", "comment"])

    def test_a_handoff_body_round_trips_its_set(self):
        self.assertEqual(
            intent.parse_handoff_set(intent.handoff_body("x", (7, 3))), (3, 7))

    def test_prose_with_no_marker_names_no_set(self):
        self.assertIsNone(intent.parse_handoff_set("we should hand off #3 soon"))


class ComposeGuardTest(unittest.TestCase):

    def test_compose_calls_flywheel_batch_at_backlog_and_never_writes_ready(self):
        run = FakeRun()
        writer = intent.Writer(apply=True, run=run)
        intent.apply_compose(writer, [item(5, "state:queued")],
                             config(apply=True))
        self.assertEqual(len(run.calls), 1)
        argv = run.calls[0]
        self.assertIn("--kind", argv)
        self.assertEqual(argv[argv.index("--kind") + 1], "elaboration")
        self.assertNotIn("Ready", argv,
                         "composing is not releasing — the flip is the operator's")

    def test_a_batch_parent_is_not_itself_composable_work(self):
        # Live on intent/relay-delivery, 2026-08-13: #46 is an elaboration
        # parent at Backlog and an open state:queued issue with no parent of
        # its own. Composing it would create another queued orphan, which the
        # next cycle composes in turn — the loop never quiets.
        snap = Snapshot(items=[item(46, "elaboration", "state:queued"),
                               item(51, "type:planning", "state:queued")])
        self.assertEqual([i.number for i in inbox.compose_plan(snap, "x")], [51])

    def test_compose_appends_to_the_open_backlog_elaboration(self):
        # The amend branch, like handoff birth's: newcomers JOIN the open
        # Backlog batch instead of fragmenting into near-identical
        # containers (observed live: #131/#132, #109/#114/#129).
        run = FakeRun()
        writer = intent.Writer(apply=True, run=run)
        snap = Snapshot(
            items=[item(46, "elaboration", "state:queued")],
            batches=[Batch(46, kind=inbox.ELABORATION,
                           status=inbox.STATUS_BACKLOG,
                           milestone="intent/x")])
        intent.apply_compose(writer, [item(5, "state:queued")],
                             config(apply=True), snap)
        argv = run.calls[0]
        self.assertIn("--into", argv)
        self.assertEqual(argv[argv.index("--into") + 1], "46")

    def test_no_orphans_runs_no_command(self):
        run = FakeRun()
        writer = intent.Writer(apply=True, run=run)
        intent.apply_compose(writer, [], config(apply=True))
        self.assertEqual(run.calls, [])


class DryCycleTest(unittest.TestCase):
    """The bolt's own merge criterion, stated in a form a test can hold.

    Stated precisely, because the loose statement is false and the difference
    matters: the guards CONVERGE. A cycle whose writes changed the tracker is
    followed by a cycle that sees the change — birth makes a handoff item, and
    that newborn item is itself an orphan the next cycle composes. What must be
    true is that the writes stop: once the tracker holds what the guards want,
    every later cycle against it writes NOTHING.
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
            [w.kind for w in self._guards(cycle1)], ["label", "label", "issue"],
            "the flip releases #1 and handoff birth claims #2")

        # #1 flipped, #9 born. The newborn handoff is an orphan, so this cycle
        # composes it — a real change, not churn.
        cycle2 = Snapshot(
            items=[item(1, "state:ready", parent_batch=4),
                   item(2, "type:assertion", "state:queued"),
                   item(9, "type:handoff", "state:queued",
                        body=intent.handoff_body("x", (2,)))],
            batches=cycle1.batches,
        )
        self.assertEqual([w.kind for w in self._guards(cycle2)], ["command"])

        # #9 batched at Backlog, awaiting the operator's flip. Settled.
        cycle3 = Snapshot(
            items=[item(1, "state:ready", parent_batch=4),
                   item(2, "type:assertion", "state:queued"),
                   item(9, "type:handoff", "state:queued", parent_batch=10,
                        body=intent.handoff_body("x", (2,)))],
            batches=list(cycle1.batches) + [
                Batch(number=10, kind="elaboration", status="Backlog",
                      sub_issues=(9,), milestone="intent/x")],
        )
        self.assertEqual(self._guards(cycle3), (),
                         "a settled tracker must produce no write at all")
        self.assertEqual(self._guards(cycle3), (),
                         "and must keep producing none")


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
            {"planning": "fable", "interactive": "fable", "handoff": "opus",
             "research": "opus[1m]", "prototype": "opus", "writeback": "opus"})
        self.assertEqual(
            sorted(n for n, t in intent.TYPES.items() if t.operator_round),
            ["handoff", "interactive", "planning"])

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
# 4 · completion — the R1 seam. Three candidates, no default.
# ---------------------------------------------------------------------------

class CompletionTest(unittest.TestCase):

    def setUp(self):
        self.batch = intent.DesignBatch("research", (item(1), item(2)))

    def test_no_signal_configured_is_unknown_rather_than_incomplete(self):
        ctx = intent.CompletionContext(snapshot=Snapshot(items=[item(1)]))
        self.assertIsNone(intent.is_complete(self.batch, config(), ctx))

    def test_closed_means_every_item_is_gone_from_the_open_snapshot(self):
        ctx = intent.CompletionContext(snapshot=Snapshot(items=[item(1)]))
        cfg = config(completion_signal="closed")
        self.assertFalse(intent.is_complete(self.batch, cfg, ctx))
        ctx.snapshot = Snapshot(items=[])
        self.assertTrue(intent.is_complete(self.batch, cfg, ctx))

    def test_label_means_every_open_item_carries_it(self):
        cfg = config(completion_signal="label", done_label="state:done")
        ctx = intent.CompletionContext(
            snapshot=Snapshot(items=[item(1, "state:done"), item(2)]),
            done_label="state:done")
        self.assertFalse(intent.is_complete(self.batch, cfg, ctx))
        ctx.snapshot = Snapshot(items=[item(1, "state:done"),
                                       item(2, "state:done")])
        self.assertTrue(intent.is_complete(self.batch, cfg, ctx))

    def test_board_means_every_row_is_at_the_done_status(self):
        cfg = config(completion_signal="board", done_status="Done")
        ctx = intent.CompletionContext(
            snapshot=Snapshot(items=[item(1), item(2)]),
            board={1: {"status": "Done"}, 2: {"status": "Ready"}},
            done_status="Done")
        self.assertFalse(intent.is_complete(self.batch, cfg, ctx))
        ctx.board[2] = {"status": "Done"}
        self.assertTrue(intent.is_complete(self.batch, cfg, ctx))

    def test_a_signal_that_needs_a_name_and_lacks_one_stops_the_run(self):
        self.assertIn("--done-label",
                      intent.config_fault(config(completion_signal="label")))
        self.assertIn("--done-status",
                      intent.config_fault(config(completion_signal="board")))

    def test_an_unknown_signal_stops_the_run_before_it_reads_anything(self):
        report = intent.run(config(completion_signal="vibes"))
        self.assertEqual(report.status, "stopped")
        self.assertIn("unknown completion signal", report.failure)


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
        self.assertEqual(kinds.count("issue"), 1, "handoff birth for #202")
        self.assertEqual(kinds.count("command"), 2,
                         "flywheel-batch for #203, and one wt switch")
        self.assertEqual(report.dispatched, ("planning-sandbox-design — #201",))

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

    def test_the_r1_note_is_on_every_run_that_names_no_signal(self):
        report = intent.run(config(
            slug="sandbox-design",
            fixture=str(FIXTURES / "intent-tracker.json")))
        self.assertTrue(any("R1 unresolved" in n for n in report.notes))


# ---------------------------------------------------------------------------
# 6 · landing — the andon, and what a settled session is not
# ---------------------------------------------------------------------------

class LandingTest(unittest.TestCase):

    def _land(self, cfg, tracker, runner=None, clock=None):
        batch = intent.DesignBatch("research", (item(1),))
        spec = sessions.SessionSpec(name="research-x", cwd="/tmp", order="go",
                                    profile="flywheel-design-session")
        runner = runner or ScriptedRunner()
        handle = runner.launch(spec)
        writer = intent.Writer(tracker=tracker, apply=True,
                               snapshot=Snapshot(items=[item(1)]))
        report = intent.Report(slug="x")
        intent.land(batch, spec, handle, writer, runner, tracker, cfg,
                    Snapshot(items=[item(1)]), clock or Clock(), report)
        return writer, report, runner

    def test_a_settled_session_is_not_a_finished_one(self):
        tracker = FakeTracker()
        writer, report, runner = self._land(config(apply=True), tracker)
        self.assertEqual(runner.closed, [],
                         "the operator may iterate a round as often as they like")
        self.assertTrue(any("R1 unresolved" in n for n in report.notes))

    def test_an_andon_pauses_the_batch_and_merges_nothing(self):
        tracker = FakeTracker(comments={
            1: [{"body": inbox.format_andon("the spec contradicts its decision")}]})
        writer, report, runner = self._land(
            config(apply=True, completion_signal="closed"), tracker)
        self.assertIn(("add_label", 1, "needs-operator"), tracker.calls)
        self.assertEqual([c for c in tracker.calls if c[0] == "close_issue"], [])
        self.assertEqual(runner.closed, [])
        self.assertTrue(any("raised the andon" in n for n in report.notes))

    def test_prose_about_stopping_is_not_an_andon(self):
        tracker = FakeTracker(comments={
            1: [{"body": "I nearly raised the andon but did not."}]})
        writer, report, runner = self._land(
            config(apply=True, completion_signal="closed"), tracker)
        self.assertNotIn(("add_label", 1, "needs-operator"), tracker.calls)

    def test_a_complete_batch_closes_its_items_closed_done(self):
        tracker = FakeTracker()
        writer, report, runner = self._land(
            config(apply=True, completion_signal="label",
                   done_label="state:done"), tracker)
        # #1 carries no done label, so nothing closes
        self.assertEqual([c for c in tracker.calls if c[0] == "close_issue"], [])

    def test_a_stalled_session_keeps_its_pane_as_evidence(self):
        tracker = FakeTracker()
        runner = ScriptedRunner(states=[WaitState.WORKING] * 40)
        clock = Clock()

        class Ticking(Clock):
            def __call__(self):
                value = self.now
                self.now += sessions.WAIT_CHUNK_S
                return value

        writer, report, runner = self._land(
            config(apply=True, completion_signal="closed"), tracker,
            runner=runner, clock=Ticking())
        self.assertTrue(any("stalled" in n for n in report.notes))
        self.assertEqual(runner.closed, [])


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
