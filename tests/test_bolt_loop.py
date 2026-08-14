"""#72 — the construction loop as a program: guards, stages, and STOP.

Every claim in the item is exercised against fakes: an injected tracker, an
injected runner, an injected subprocess and an injected clock. Nothing here
starts herdr, spawns `claude`, mints a token, touches the network or sleeps.

The two properties worth protecting, as in `tests/README.md`: the **dry
cycle** (applying the guards' plan empties it, so a second cycle against an
unchanged tracker writes nothing) and **outcomes read from the world** (a
stage is done because git and openspec say so, never because a session's
report said so).
"""

import json
import tempfile
import unittest
from pathlib import Path

from context import BIN, ROOT, inbox, sessions  # noqa: F401
import _flywheel_bolt_loop as loop  # noqa: E402

Item = inbox.Item
Batch = inbox.Batch
Snapshot = inbox.TrackerSnapshot
WaitState = sessions.WaitState


def item(number, *labels, **kw):
    kw.setdefault("milestone", "bolt/x")
    kw.setdefault("title", f"item {number}")
    return Item(number=number, labels=frozenset(labels), **kw)


# ---------------------------------------------------------------------------
# The seams
# ---------------------------------------------------------------------------

class Result:
    """A `CompletedProcess` stand-in, in the three fields we read."""

    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


class FakeTracker:
    """The tracker's read and write surface, recorded rather than performed."""

    def __init__(self, snapshot=None, comments=None, milestones=()):
        self._snapshot = snapshot or Snapshot()
        self._comments = comments or {}
        self._milestones = list(milestones)
        self.labels = {}
        self.writes = []

    # reads
    def snapshot(self, milestone=None, with_edges=True):
        return self._snapshot

    def comments(self, number):
        return list(self._comments.get(number, ()))

    def has_label(self, number, label):
        return label in self.labels.get(number, set())

    def milestones(self, state="all"):
        return self._milestones

    def milestone(self, title):
        return next((m for m in self._milestones if m.get("title") == title), None)

    # writes
    def add_label(self, number, label):
        self.labels.setdefault(number, set()).add(label)
        self.writes.append(("add_label", number, label))

    def remove_label(self, number, label):
        self.labels.setdefault(number, set()).discard(label)
        self.writes.append(("remove_label", number, label))

    def comment(self, number, body):
        self._comments.setdefault(number, []).append({"body": body})
        self.writes.append(("comment", number, body))

    def set_milestone(self, number, title):
        self.writes.append(("set_milestone", number, title))

    def clear_milestone(self, number):
        self.writes.append(("clear_milestone", number, ""))

    def close(self, number, comment=None):
        self.writes.append(("close", number, comment or ""))

    def create_item(self, title, body, labels=(), milestone=None):
        self.writes.append(("create_item", 0, title))
        return 999

    def kinds(self):
        return [w[0] for w in self.writes]


class ScriptedRunner:
    """A runner whose settles and pane reads are scripted, not simulated."""

    def __init__(self, states=(), reports=()):
        self.states = list(states) or [WaitState.SETTLED_DONE]
        self.reports = list(reports)
        self.launched, self.sent, self.keys, self.closed = [], [], [], []

    def launch(self, spec):
        self.launched.append(spec)
        return sessions.SessionHandle(name=spec.name, runner="fake",
                                      ref={"tab_id": "t1"})

    def wait(self, handle, timeout=None):
        return self.states.pop(0) if self.states else WaitState.SETTLED_DONE

    def send(self, handle, prompt):
        self.sent.append((handle.name, prompt))
        return True

    def send_keys(self, handle, *keys):
        self.keys.append((handle.name, keys))

    def collect(self, handle, lines=200):
        report = self.reports.pop(0) if self.reports else ""
        return sessions.Collected(state=WaitState.SETTLED_DONE, report=report)

    def close(self, handle):
        self.closed.append(handle.name)


class FakeClock:
    """Time moves only when something asks it to."""

    def __init__(self, now=1_000_000.0, step=1.0):
        self.now, self.step = now, step

    def __call__(self):
        self.now += self.step
        return self.now

    def advance(self, seconds):
        self.now += seconds


class FakeShell:
    """git / openspec / flywheel-batch, answered from a table."""

    def __init__(self, answers=None, default=Result(0)):
        self.answers = answers or {}
        self.default = default
        self.calls = []

    def __call__(self, argv, cwd=None, env=None, timeout=None):
        self.calls.append((tuple(argv), cwd))
        for prefix, result in self.answers.items():
            if tuple(argv)[:len(prefix)] == prefix:
                return result() if callable(result) else result
        # Built-in wt: the loop is the worktree orchestrator, so every test
        # meets `wt list` / `wt switch --create`. bolt/x pre-exists (topology
        # adopts, writes nothing — the dry-cycle property holds); build/*
        # exists once a recorded `wt switch --create` made it. All paths are
        # TREE, whose change directory the deliverable checks already use.
        if tuple(argv[:2]) == ("git", "merge-base"):
            return Result(1)   # not an ancestor: batches still need driving
        if tuple(argv[:2]) == ("wt", "list"):
            made = [a[3] if a[2] == "--create" else a[2]
                    for a, _ in self.calls
                    if a[:2] == ("wt", "switch") and len(a) > 2]
            rows = [{"branch": b, "path": str(TREE)}
                    for b in ["bolt/x", *made]]
            return Result(0, stdout=json.dumps(rows))
        return self.default


#: A worktree whose change directory exists, so guard 0 (scaffold-if-missing)
#: is a no-op everywhere except where a test wants it to fire.
_TREE = tempfile.TemporaryDirectory()
TREE = Path(_TREE.name)
(TREE / "openspec" / "changes" / "x").mkdir(parents=True, exist_ok=True)


def a_loop(tracker, runner=None, shell=None, clock=None, plan_mode=False,
           strategy="ff", **overrides):
    fields = dict(slug="x", org="o", repo="r", repo_dir=str(TREE),
                  bolt_worktree=str(TREE), type_name="bolt-quick",
                  plan_mode=plan_mode,
                  config=loop.LoopConfig(name="bolt-quick", strategy=strategy,
                                         plan_mode="available"))
    fields.update(overrides)
    runner = runner or ScriptedRunner()
    return loop.BoltLoop(loop.BoltParams(**fields), tracker,
                         runner_factory=lambda stage: runner,
                         run=shell or FakeShell(), clock=clock or FakeClock())


class SpecShortCircuitTest(unittest.TestCase):

    def test_a_change_that_already_validates_needs_no_spec_session(self):
        # A resumed batch re-drove a full spec session per restart for a
        # change that was already green.
        shell = FakeShell(answers={("openspec", "validate"): Result(0)})
        runner = ScriptedRunner([])
        l = a_loop(FakeTracker(), shell=shell, runner=runner)
        batch = loop.WorkBatch(slug="b1", items=(item(7, inbox.IN_PROGRESS),))
        outcome = l.spec_stage(batch)
        self.assertEqual(outcome.status, "done")
        self.assertEqual(runner.launched, [], "no session may be driven")


class DurableRepromptTest(unittest.TestCase):

    def test_a_predecessors_reprompt_marker_pauses_instead_of_reprompting(self):
        # The one-re-prompt rule must survive a process restart: the marker
        # is a tracker comment, and a successor that finds it pauses
        # (observed live: three re-prompts across three restarts, #140).
        marker = loop.SESSION_OPEN + " reprompt build-b1 -->"
        tracker = FakeTracker(Snapshot(), comments={7: [{"body": marker}]})
        l = a_loop(tracker)
        batch = loop.WorkBatch(slug="b1", items=(item(7, inbox.IN_PROGRESS),))
        outcome = l.reprompt_deliverables(
            batch, loop.StageOutcome("build", "done", handle=object()),
            ["no comment on #7"])
        self.assertEqual(outcome.status, "paused")
        self.assertIn(("add_label", 7, inbox.NEEDS_OPERATOR), tracker.writes)


class RelaunchOriginTest(unittest.TestCase):

    def test_a_fresh_launch_ignores_a_dead_sessions_marker(self):
        # #168: build relaunched after its predecessor died, inherited the
        # corpse's marker, and was judged stalled at 1276 minutes before
        # doing anything. Only a REUSED pane may inherit a marker.
        marker = f'{loop.SESSION_OPEN} name="build-b1" started="0" -->'
        tracker = FakeTracker(comments={7: [{"body": marker},
                                            {"body": "built it"}]})
        shell = FakeShell({("git", "rev-list"): Result(0, "3\n")})
        l = a_loop(tracker, shell=shell)   # ScriptedRunner: never reused
        batch = loop.WorkBatch(slug="b1", items=(item(7, inbox.IN_PROGRESS),))
        outcome = l.build_stage(batch)
        self.assertEqual(outcome.status, "done")

    def test_launch_origin_reads_the_latest_marker_for_the_name(self):
        first = f'{loop.SESSION_OPEN} name="build-b1" started="100" -->'
        again = f'{loop.SESSION_OPEN} name="build-b1" started="900" -->'
        tracker = FakeTracker(comments={7: [{"body": first},
                                            {"body": again}]})
        l = a_loop(tracker)
        self.assertEqual(l.launch_origin([7], "build-b1"), 900)


class ComposeAmendTest(unittest.TestCase):

    def test_bolt_compose_appends_to_the_open_backlog_unit(self):
        shell = FakeShell()
        snap = Snapshot(
            items=[item(120, inbox.QUEUED, inbox.UNIT, milestone="bolt/x")],
            batches=[Batch(120, kind=inbox.UNIT,
                           status=inbox.STATUS_BACKLOG, milestone="bolt/x")])
        l = a_loop(FakeTracker(snap), shell=shell)
        l.compose([item(7, inbox.QUEUED, milestone="bolt/x")], snap)
        call = next(a for a, _ in shell.calls if "flywheel-batch" in str(a[0]))
        self.assertIn("--into", call)
        self.assertEqual(call[call.index("--into") + 1], "120")


class StatelessResumeTest(unittest.TestCase):
    """A restarted loop re-adopts its own in-progress items (observed live:
    a restart saw only state:ready, found nothing, and stranded the bolt)."""

    def _snap(self):
        return Snapshot(items=[
            item(96, inbox.IN_PROGRESS, inbox.TYPE_ASSERTION,
                 milestone="bolt/x")])

    def test_an_unmerged_in_progress_item_is_re_driven_not_stranded(self):
        l = a_loop(FakeTracker(self._snap()))
        l.dry_run = True   # merge-base answers rc 1: not merged
        result = l.cycle(1)
        self.assertNotEqual(result.stopped,
                            "nothing is ready and the guards wrote nothing")

    def test_a_merged_in_progress_item_awaits_the_landing(self):
        shell = FakeShell(answers={("git", "merge-base"): Result(0),
                                   ("git", "rev-parse"): Result(0, "abc\n"),
                                   ("git", "rev-list"): Result(0, "1\n")})
        l = a_loop(FakeTracker(self._snap()), shell=shell)
        result = l.cycle(1)
        self.assertIn("awaiting the landing", result.stopped)
        box = inbox.bolt_inbox(self._snap(), "x")
        self.assertTrue(l.landing_wanted("auto", box,
                                         list(self._snap().items)))

    def test_an_empty_branch_is_nothing_to_merge_never_merged(self):
        # #164, observed live: build/stage-labels-133's tip was the very
        # commit it was cut at, so bare ancestry read the never-worked
        # branch as "merged" and the loop went looking for a landing.
        shell = FakeShell(answers={("git", "merge-base"): Result(0),
                                   ("git", "rev-parse"): Result(0, "abc\n"),
                                   ("git", "rev-list"): Result(0, "0\n")})
        l = a_loop(FakeTracker(self._snap()), shell=shell)
        result = l.cycle(1)
        self.assertNotIn("awaiting the landing", result.stopped or "")


class ContainerRoutingTest(unittest.TestCase):

    def test_a_unit_parent_is_never_routed(self):
        # Observed live: the loop composed discoveries into unit #120, then
        # the next cycle routed the container itself and the keep path
        # wrapped it in #121. A container is never work.
        snap = Snapshot(items=[
            item(120, inbox.QUEUED, inbox.UNIT, milestone="bolt/x"),
            item(7, inbox.QUEUED, milestone="bolt/x"),
        ])
        l = a_loop(FakeTracker())
        l.dry_run = True
        actions = []
        l.guard_route(snap, actions)
        said = " ".join(actions)
        self.assertIn("#7", said)
        self.assertNotIn("#120", said)


class WorktreeOrchestrationTest(unittest.TestCase):

    def test_an_existing_branch_without_a_worktree_gets_plain_switch(self):
        # FakeShell's default answers git rev-parse with rc 0: the branch
        # exists. --create on an existing branch errors in wt, so the loop
        # must attach with plain switch (the restart / session-got-there
        # -first case).
        shell = FakeShell()
        l = a_loop(FakeTracker(), shell=shell)
        path, created = l.worktree_for("bolt/y", "main")
        self.assertEqual(path, str(TREE))
        creates = [a for a, _ in shell.calls if a[:3] == ("wt", "switch", "--create")]
        self.assertFalse(creates, "an existing branch is attached, never --create'd")

    def test_a_branch_not_born_yet_is_created_from_its_base(self):
        shell = FakeShell(answers={("git", "rev-parse"): Result(1)})
        l = a_loop(FakeTracker(), shell=shell)
        path, created = l.worktree_for("build/z", "bolt/x")
        self.assertEqual(path, str(TREE))
        self.assertTrue(created)
        create = next(a for a, _ in shell.calls
                      if a[:3] == ("wt", "switch", "--create"))
        self.assertIn("--base", create)


# ---------------------------------------------------------------------------
# The type as a named loop config
# ---------------------------------------------------------------------------

class TypeConfigTest(unittest.TestCase):

    def test_each_shipped_type_declares_the_strategy_its_stages_run(self):
        # Read from the repo's own schemas, because openspec drops the block
        # and this parser is the only thing that reads it.
        wanted = {"bolt-quick": ("ff", ("/opsx:ff",)),
                  "bolt-default": ("new+ff", ("/opsx:new", "/opsx:ff")),
                  "bolt-adversarial": ("new+continue", ("/opsx:new", "/opsx:continue"))}
        for name, (strategy, invocations) in wanted.items():
            config = loop.load_type(name, ROOT)
            self.assertEqual(config.strategy, strategy, name)
            self.assertEqual(config.invocations, invocations, name)

    def test_the_hooks_a_type_declares_are_the_boundaries_its_strategy_creates(self):
        # ff is one command, so bolt-quick has no post-new to expose.
        self.assertNotIn("post-new", loop.load_type("bolt-quick", ROOT).hooks)
        self.assertIn("post-new", loop.load_type("bolt-default", ROOT).hooks)
        self.assertIn("post-artifact", loop.load_type("bolt-adversarial", ROOT).hooks)

    def test_plan_mode_is_available_on_bolt_quick_and_on_no_other_type(self):
        self.assertTrue(loop.load_type("bolt-quick", ROOT).plan_mode_available)
        self.assertFalse(loop.load_type("bolt-default", ROOT).plan_mode_available)
        self.assertFalse(loop.load_type("bolt-adversarial", ROOT).plan_mode_available)

    def test_a_plan_mode_declaration_against_a_type_that_forbids_it_is_refused(self):
        # The bolt type is the scrutiny the release approved; a program that
        # honoured this quietly would be downgrading it.
        with self.assertRaises(loop.LoopError):
            loop.resolve_plan_mode(True, loop.load_type("bolt-default", ROOT))
        self.assertTrue(
            loop.resolve_plan_mode(True, loop.load_type("bolt-quick", ROOT)))

    def test_the_bolt_declares_plan_mode_and_the_operators_flag_outranks_it(self):
        self.assertTrue(loop.plan_mode_declared({}, "bolt-quick, PLAN-MODE PATH: ..."))
        self.assertTrue(loop.plan_mode_declared({"plan_mode": "true"}, ""))
        self.assertFalse(loop.plan_mode_declared({}, "an ordinary bolt"))
        self.assertFalse(loop.plan_mode_declared({"plan_mode": "true"}, "", flag=False))

    def test_skip_specs_is_not_a_plan_mode_declaration(self):
        # Every bolt and intent change in this repo carries skip_specs: true,
        # bolt-default ones included — it says the RECORD has no spec deltas.
        # Reading it as the declaration ran a bolt-default bolt in plan mode.
        for path in sorted((ROOT / "openspec" / "changes").glob("*/.openspec.yaml")):
            binding = loop.read_binding(path.parent)
            if binding.get("schema") == "bolt-default":
                self.assertFalse(loop.plan_mode_declared(binding, ""), str(path))

    def test_an_unknown_strategy_is_named_rather_than_guessed(self):
        with self.assertRaises(loop.LoopError):
            loop.LoopConfig(name="t", strategy="wishful").invocations


# ---------------------------------------------------------------------------
# Guards — writes-only, idempotent, and the dry cycle
# ---------------------------------------------------------------------------

class GuardTest(unittest.TestCase):

    def snapshot_with_a_ready_unit(self):
        return Snapshot(
            items=[item(1, inbox.QUEUED), item(2, inbox.READY),
                   item(9, inbox.UNIT)],
            batches=[Batch(number=9, kind=inbox.UNIT, status=inbox.STATUS_READY,
                           sub_issues=(1,), milestone="bolt/x")],
            milestone="bolt/x")

    def test_a_ready_units_queued_sub_issue_is_flipped_and_the_write_is_recorded(self):
        tracker = FakeTracker(self.snapshot_with_a_ready_unit())
        actions, failure = a_loop(tracker).guards(tracker.snapshot())
        self.assertIsNone(failure)
        self.assertEqual(len(actions), 1)
        self.assertIn(("add_label", 1, inbox.READY), tracker.writes)
        self.assertIn(("remove_label", 1, inbox.QUEUED), tracker.writes)

    def test_the_second_cycle_against_an_unchanged_tracker_writes_nothing(self):
        # The dry cycle — the whole stateless-process design rests on it.
        snapshot = self.snapshot_with_a_ready_unit()
        tracker = FakeTracker(snapshot)
        program = a_loop(tracker)
        program.guards(snapshot)
        first = len(tracker.writes)

        after = Snapshot(items=[item(1, inbox.READY), item(2, inbox.READY),
                                item(9, inbox.UNIT)],
                         batches=snapshot.batches, milestone="bolt/x")
        actions, _ = program.guards(after)
        self.assertEqual(actions, [], "a check that changed nothing records nothing")
        self.assertEqual(len(tracker.writes), first, "and writes nothing")

    def test_an_item_with_a_parent_is_not_an_orphan_and_is_never_routed(self):
        snapshot = Snapshot(
            items=[item(1, inbox.QUEUED), item(9, inbox.UNIT)],
            batches=[Batch(number=9, kind=inbox.UNIT, status="Backlog",
                           sub_issues=(1,), milestone="bolt/x")],
            milestone="bolt/x")
        tracker = FakeTracker(snapshot)
        actions, _ = a_loop(tracker).guards(snapshot)
        self.assertEqual(actions, [])
        self.assertEqual(tracker.writes, [])

    def test_parentage_is_read_from_the_batches_because_the_field_is_not_filled(self):
        # `Tracker.snapshot` cannot fill `parent_batch` — GitHub's issue
        # payload has no such key — so an orphan test that read only the
        # field would call every live item an orphan.
        snapshot = Snapshot(
            items=[item(1, inbox.QUEUED)],
            batches=[Batch(number=9, kind=inbox.UNIT, status="Backlog",
                           sub_issues=(1,), milestone="bolt/x")])
        self.assertEqual(loop.parented(snapshot), {1})


class RoutingTest(unittest.TestCase):
    """Guard 2 — discovery routing, by the merge-criteria test."""

    def orphan_snapshot(self):
        return Snapshot(items=[item(5, inbox.QUEUED, title="a discovery")],
                        milestone="bolt/x")

    def routed(self, verdict, intents=("intent/y",)):
        snapshot = self.orphan_snapshot()
        tracker = FakeTracker(snapshot,
                              milestones=[{"title": t} for t in intents])
        runner = ScriptedRunner(reports=[verdict])
        program = a_loop(tracker, runner=runner)
        actions, failure = program.guards(snapshot)
        return tracker, actions, failure

    def test_a_discovery_the_bolt_can_land_without_moves_to_its_intent(self):
        tracker, actions, _ = self.routed("ROUTE: intent/y\nWHY: no criterion needs it")
        self.assertIn(("set_milestone", 5, "intent/y"), tracker.writes)
        self.assertTrue(any("moved to intent/y" in a for a in actions))

    def test_a_discovery_belonging_to_no_intent_is_left_for_dispatch(self):
        tracker, actions, _ = self.routed("ROUTE: unmilestoned\nWHY: nobody owns it")
        self.assertIn(("clear_milestone", 5, ""), tracker.writes)

    def test_a_discovery_the_criteria_need_stays_and_is_composed_at_backlog(self):
        tracker, actions, _ = self.routed("ROUTE: keep\nWHY: criterion two needs it")
        self.assertNotIn("set_milestone", tracker.kinds())
        self.assertNotIn("clear_milestone", tracker.kinds())
        self.assertTrue(any("composed" in a for a in actions), actions)

    def test_an_unreadable_verdict_moves_nothing(self):
        # Nothing leaves the bolt on a verdict the loop could not parse:
        # a kept item is visible in the queue, a wrongly-routed one is not.
        tracker, actions, _ = self.routed("I think it probably belongs elsewhere?")
        self.assertNotIn("set_milestone", tracker.kinds())
        self.assertNotIn("clear_milestone", tracker.kinds())

    def test_a_verdict_naming_a_milestone_that_is_not_an_open_intent_is_refused(self):
        tracker, _, _ = self.routed("ROUTE: intent/z\nWHY: guessing",
                                    intents=("intent/y",))
        self.assertNotIn("set_milestone", tracker.kinds())

    def test_the_composed_unit_is_born_at_backlog_and_never_at_ready(self):
        snapshot = self.orphan_snapshot()
        shell = FakeShell()
        tracker = FakeTracker(snapshot)
        program = a_loop(tracker, runner=ScriptedRunner(reports=["ROUTE: keep"]),
                         shell=shell)
        program.guards(snapshot)
        composed = [c for c, _ in shell.calls if "flywheel-batch" in c[0]]
        self.assertTrue(composed)
        self.assertIn("--kind", composed[0])
        self.assertNotIn("Ready", composed[0])


# ---------------------------------------------------------------------------
# Analyse — computed from the fields
# ---------------------------------------------------------------------------

class AnalyseTest(unittest.TestCase):

    def test_items_released_in_one_unit_ride_in_one_batch(self):
        snapshot = Snapshot(
            items=[item(1, inbox.READY), item(2, inbox.READY), item(3, inbox.READY)],
            batches=[Batch(number=9, kind=inbox.UNIT, status="Backlog",
                           sub_issues=(1, 2), milestone="bolt/x")])
        batches = loop.analyse(snapshot.items, snapshot, "x")
        self.assertEqual([b.numbers for b in batches], [(1, 2), (3,)])

    def test_a_batch_takes_the_change_name_its_items_agree_on(self):
        items = [item(1, inbox.READY, change="add-thing"),
                 item(2, inbox.READY, change="add-thing")]
        batch = loop.analyse(items, Snapshot(items=items), "x")[0]
        self.assertEqual(batch.slug, "add-thing")

    def test_a_batch_with_no_change_is_named_from_the_bolt_and_its_first_item(self):
        items = [item(7, inbox.READY)]
        self.assertEqual(loop.analyse(items, Snapshot(items=items), "x")[0].slug, "x-7")

    def test_a_session_name_never_outgrows_what_herdr_accepts(self):
        name = loop.session_name("spec-writing", "a" * 60)
        self.assertLessEqual(len(name), sessions.MAX_NAME)
        self.assertTrue(name.startswith("spec-writing-"))


# ---------------------------------------------------------------------------
# The cycle — STOP, halt, and the ready set
# ---------------------------------------------------------------------------

class CycleTest(unittest.TestCase):

    def test_stop_fires_when_nothing_is_ready_and_the_guards_wrote_nothing(self):
        tracker = FakeTracker(Snapshot(items=[item(1, inbox.QUEUED,
                                                   parent_batch=9)],
                                       milestone="bolt/x"))
        result = a_loop(tracker).cycle(1)
        self.assertIn("nothing is ready", result.stopped)
        self.assertEqual(tracker.writes, [])

    def test_a_failing_guard_halts_the_run_rather_than_looping(self):
        tracker = FakeTracker(Snapshot(milestone="bolt/x"))
        program = a_loop(tracker, runner=ScriptedRunner(states=[WaitState.GONE]),
                         bolt_worktree="/nowhere-at-all")
        report = program.run(land=False)
        self.assertTrue(report.halted)
        self.assertEqual(len(report.cycles), 1, "a failing cycle never loops")

    def test_a_ready_item_blocked_by_an_open_item_is_not_worked(self):
        snapshot = Snapshot(items=[item(1, inbox.READY, blocked_by=(2,)),
                                   item(2, inbox.QUEUED, parent_batch=9)],
                            milestone="bolt/x")
        result = a_loop(FakeTracker(snapshot)).cycle(1)
        self.assertIn("blocked", result.stopped)

    def test_an_andon_marker_on_an_item_pauses_its_batch_with_needs_operator(self):
        snapshot = Snapshot(items=[item(1, inbox.READY)], milestone="bolt/x")
        tracker = FakeTracker(snapshot, comments={
            1: [{"body": inbox.format_andon("the tree contradicts the claim")}]})
        result = a_loop(tracker).cycle(1)
        self.assertEqual([o.status for o in result.outcomes], ["paused"])
        self.assertIn(("add_label", 1, inbox.NEEDS_OPERATOR), tracker.writes)


# ---------------------------------------------------------------------------
# Stages — outcomes read from the world
# ---------------------------------------------------------------------------

class StageTest(unittest.TestCase):

    def batch(self, *numbers, change="add-thing"):
        return loop.WorkBatch(slug=change or "x-1", items=tuple(
            item(n, inbox.READY, change=change) for n in numbers))

    def test_a_spec_is_done_when_the_change_validates_not_when_the_session_says_so(self):
        tracker = FakeTracker()
        shell = FakeShell({("openspec", "validate"): Result(1)})
        outcome = a_loop(tracker, shell=shell).spec_stage(self.batch(1))
        self.assertEqual(outcome.status, "failed")
        self.assertIn("not green", outcome.detail)

    def test_the_strategy_decides_how_many_spec_commands_the_session_is_given(self):
        runner = ScriptedRunner(states=[WaitState.SETTLED_DONE] * 4)
        # not green before the session runs, green after — else the
        # short-circuit skips the session this test is about
        greens = iter([Result(1), Result(0), Result(0), Result(0)])
        shell = FakeShell({("openspec", "validate"): lambda: next(greens)})
        program = a_loop(FakeTracker(), runner=runner, strategy="new+ff",
                         shell=shell)
        program.spec_stage(self.batch(1))
        self.assertTrue(runner.launched[0].order.startswith("/opsx:new add-thing"))
        self.assertEqual(runner.sent[0][1], "/opsx:ff add-thing")

    def test_a_build_that_settles_without_deliverables_is_reprompted_exactly_once(self):
        tracker = FakeTracker()
        runner = ScriptedRunner(states=[WaitState.SETTLED_DONE] * 4)
        shell = FakeShell({("git", "rev-list"): Result(0, "0\n")})
        outcome = a_loop(tracker, runner=runner, shell=shell).build_stage(self.batch(1))
        self.assertEqual(outcome.status, "paused")
        self.assertEqual(len(runner.sent), 1, "one re-prompt, then the pause")
        self.assertIn(("add_label", 1, inbox.NEEDS_OPERATOR), tracker.writes)

    def test_a_build_with_its_deliverables_on_disk_is_done(self):
        tracker = FakeTracker(comments={1: [{"body": "built it"}]})
        shell = FakeShell({("git", "rev-list"): Result(0, "3\n")})
        outcome = a_loop(tracker, shell=shell).build_stage(self.batch(1))
        self.assertEqual(outcome.status, "done")

    def test_settle_never_clears_a_needs_operator_it_did_not_raise(self):
        # #165, observed live 4x: the andon's escalation was read as "my
        # stall notice already fired" and cleared when the next session
        # over the same items settled. A label this watch did not set
        # outlives its settle.
        tracker = FakeTracker(comments={1: [{"body": "built it"}]})
        tracker.add_label(1, inbox.NEEDS_OPERATOR)   # the andon's, not ours
        tracker.writes.clear()
        shell = FakeShell({("git", "rev-list"): Result(0, "3\n")})
        outcome = a_loop(tracker, shell=shell).build_stage(self.batch(1))
        self.assertEqual(outcome.status, "done")
        self.assertNotIn(("remove_label", 1, inbox.NEEDS_OPERATOR),
                         tracker.writes)

    def test_verify_pauses_the_item_when_the_same_finding_survives_two_rounds(self):
        tracker = FakeTracker(comments={1: [{"body": "built it"}]})
        runner = ScriptedRunner(
            states=[WaitState.SETTLED_DONE] * 8,
            reports=["FINDING: the spec asks for a flag that is not there",
                     "fixed it",
                     "FINDING: the spec asks for a flag that is not there"])
        shell = FakeShell({("git", "rev-list"): Result(0, "3\n")})
        build = loop.StageOutcome("build", "done", handle=sessions.SessionHandle(
            name="build-add-thing", runner="fake"))
        outcome = a_loop(tracker, runner=runner, shell=shell).verify_stage(
            self.batch(1), build)
        self.assertEqual(outcome.status, "paused")
        self.assertIn(("add_label", 1, inbox.NEEDS_OPERATOR), tracker.writes)

    def test_verify_is_clean_when_the_change_validates_and_nothing_is_reported(self):
        tracker = FakeTracker()
        runner = ScriptedRunner(reports=["No findings — the build matches the change."])
        outcome = a_loop(tracker, runner=runner).verify_stage(
            self.batch(1), loop.StageOutcome("build", "done"))
        self.assertEqual(outcome.status, "done")

    def test_verify_clean_closes_the_build_pane(self):
        # The pane's purpose — the build/verify conversation — ends at
        # clean; the session stays resumable by its id (#178).
        tracker = FakeTracker()
        runner = ScriptedRunner(reports=["No findings — the build matches the change."])
        build = loop.StageOutcome("build", "done", handle=sessions.SessionHandle(
            name="build-add-thing", runner="fake"))
        outcome = a_loop(tracker, runner=runner).verify_stage(self.batch(1), build)
        self.assertEqual(outcome.status, "done")
        self.assertIn("build-add-thing", runner.closed)

    def test_a_gone_pane_resumes_the_session_instead_of_pausing(self):
        # #178: a restart or a closed pane is never a reason to pause a
        # fix round — the deterministic id relaunches the conversation.
        tracker = FakeTracker(comments={1: [{"body": "built it"}]})
        runner = ScriptedRunner()
        shell = FakeShell({("git", "rev-list"): Result(0, "3\n")})
        program = a_loop(tracker, runner=runner, shell=shell)
        outcome = program.go_fix(self.batch(1),
                                 loop.StageOutcome("build", "done", handle=None),
                                 "FINDING: the flag is missing")
        self.assertEqual(outcome.status, "done")
        self.assertTrue(runner.launched, "a gone pane relaunches by id")
        self.assertNotIn(("add_label", 1, inbox.NEEDS_OPERATOR), tracker.writes)

    def test_spec_for_derives_a_stable_session_id(self):
        program = a_loop(FakeTracker())
        one = program.spec_for("build", "build-x-1", "/tmp/wt", "order")
        two = program.spec_for("build", "build-x-1", "/tmp/wt", "order")
        other = program.spec_for("build", "build-x-2", "/tmp/wt", "order")
        self.assertEqual(one.session_id, two.session_id)
        self.assertNotEqual(one.session_id, other.session_id)

    def test_verify_and_spec_are_skipped_on_the_plan_mode_path(self):
        program = a_loop(FakeTracker(), plan_mode=True)
        self.assertEqual(program.spec_stage(self.batch(1)).status, "skipped")
        self.assertEqual(
            program.verify_stage(self.batch(1), loop.StageOutcome("build", "done")).status,
            "skipped")

    def test_a_plan_returned_twice_pauses_the_batch_rather_than_bouncing_again(self):
        tracker = FakeTracker()
        runner = ScriptedRunner(
            states=[WaitState.SETTLED_BLOCKED] * 12,
            reports=["a plan"] * 12)
        program = a_loop(tracker, runner=runner, plan_mode=True)
        program.judge_plan = lambda batch, handle, pane: ("returned", "claim #1 dropped")
        outcome = program.plan_mode_build(self.batch(1, change=None), "build-x")
        self.assertEqual(outcome.status, "paused")
        self.assertIn(("add_label", 1, inbox.NEEDS_OPERATOR), tracker.writes)

    def test_an_approved_plan_is_driven_through_the_dialog_and_the_clock_restarts(self):
        tracker = FakeTracker()
        runner = ScriptedRunner(states=[WaitState.SETTLED_BLOCKED,
                                        WaitState.SETTLED_DONE],
                                reports=["a plan", "built it"])
        program = a_loop(tracker, runner=runner, plan_mode=True)
        verdicts = iter([("approved", "fine"), ("unreadable", "finished")])
        program.judge_plan = lambda *a: next(verdicts)
        outcome = program.plan_mode_build(self.batch(1, change=None), "build-x")
        self.assertEqual(runner.keys, [("build-x", ("enter",))])
        self.assertEqual(outcome.status, "done")

    def test_a_merge_is_done_only_when_git_says_the_branch_is_an_ancestor(self):
        ancestry = {"rc": 1}
        shell = FakeShell({("git", "merge-base"): lambda: Result(ancestry["rc"])})
        program = a_loop(FakeTracker(), shell=shell)
        self.assertEqual(program.merge_stage(self.batch(1)).status, "failed")
        ancestry["rc"] = 0
        self.assertEqual(program.merge_stage(self.batch(1)).status, "done")

    def test_the_merge_order_never_suppresses_the_gate(self):
        runner = ScriptedRunner()
        shell = FakeShell({("git", "merge-base"): Result(1)})
        a_loop(FakeTracker(), runner=runner, shell=shell).merge_stage(self.batch(1))
        order = runner.launched[0].order
        self.assertIn("wt merge build/add-thing --no-remove", order)
        for suppressor in ("--yes", "--no-hooks", "--no-verify"):
            self.assertIn(suppressor, order, "the order names what it forbids")


class LandingTest(unittest.TestCase):

    def snapshot(self):
        return Snapshot(items=[item(1, inbox.TYPE_ASSERTION, inbox.IN_PROGRESS),
                               item(2, inbox.TYPE_ASSERTION, inbox.IN_PROGRESS)],
                        milestone="bolt/x")

    def program(self, criteria, ancestor=0, runner=None, tracker=None):
        tracker = tracker or FakeTracker(self.snapshot())
        shell = FakeShell({("git", "merge-base"): Result(ancestor),
                           ("git", "rev-parse"): Result(0, "abc1234\n"),
                           ("git", "rev-list"): Result(0, "1\n")})
        program = a_loop(tracker, runner=runner or ScriptedRunner(), shell=shell)
        program.merge_criteria = lambda: criteria
        return program, tracker

    def test_a_work_less_bolt_branch_lands_nothing_and_closes_nothing(self):
        # #164, observed live: bolt/stage-labels carried only the scaffold,
        # already on main — ancestry was vacuously true, and the loop
        # declared "landed" and closed #96–#99 over a standing andon.
        tracker = FakeTracker(self.snapshot())
        shell = FakeShell({("git", "merge-base"): Result(0),
                           ("git", "rev-parse"): Result(0, "abc1234\n"),
                           ("git", "rev-list"): Result(0, "0\n")})
        program = a_loop(tracker, shell=shell)
        program.merge_criteria = lambda: "Landing: merge"
        outcome = program.land_stage(self.snapshot())
        self.assertEqual(outcome.status, "failed")
        self.assertIn("nothing to land", outcome.detail)
        self.assertEqual([w for w in tracker.writes if w[0] == "close"], [])

    def test_a_live_wait_on_any_item_holds_the_landing(self):
        snap = Snapshot(items=[item(1, inbox.TYPE_ASSERTION, inbox.IN_PROGRESS,
                                    inbox.NEEDS_OPERATOR)],
                        milestone="bolt/x")
        tracker = FakeTracker(snap)
        shell = FakeShell({("git", "merge-base"): Result(0),
                           ("git", "rev-parse"): Result(0, "abc1234\n"),
                           ("git", "rev-list"): Result(0, "1\n")})
        program = a_loop(tracker, shell=shell)
        program.merge_criteria = lambda: "Landing: merge"
        outcome = program.land_stage(snap)
        self.assertEqual(outcome.status, "paused")
        self.assertIn("#1", outcome.detail)
        self.assertEqual([w for w in tracker.writes if w[0] == "close"], [])

    def test_every_item_closes_with_the_landing_sha(self):
        program, tracker = self.program("Landing: merge", ancestor=0)
        outcome = program.land_stage(self.snapshot())
        self.assertEqual(outcome.status, "done")
        closed = [w for w in tracker.writes if w[0] == "close"]
        self.assertEqual([w[1] for w in closed], [1, 2])
        self.assertIn("abc1234", closed[0][2])

    def test_a_pull_request_landing_closes_nothing(self):
        program, tracker = self.program("Landing: pr", ancestor=1)
        outcome = program.land_stage(self.snapshot())
        self.assertEqual(outcome.status, "done")
        self.assertEqual([w for w in tracker.writes if w[0] == "close"], [])

    def test_the_default_landing_mode_is_merge(self):
        program, _ = self.program("Acceptance suites green on the bolt branch.")
        self.assertEqual(program.landing_mode(), "merge")

    def test_a_branch_that_did_not_land_closes_nothing_and_reports_the_failure(self):
        program, tracker = self.program("Landing: merge", ancestor=1)
        outcome = program.land_stage(self.snapshot())
        self.assertEqual(outcome.status, "failed")
        self.assertEqual([w for w in tracker.writes if w[0] == "close"], [])

    def test_an_andon_raised_by_the_landing_session_pauses_the_bolt(self):
        tracker = FakeTracker(self.snapshot(), comments={
            1: [{"body": inbox.format_andon("criterion two failed again")}]})
        program, tracker = self.program("Landing: merge", ancestor=1, tracker=tracker)
        outcome = program.land_stage(self.snapshot())
        self.assertEqual(outcome.status, "paused")
        self.assertIn(("add_label", 1, inbox.NEEDS_OPERATOR), tracker.writes)

    def test_a_run_that_merged_nothing_does_not_reach_for_a_landing(self):
        # An empty ready set is not the same fact as finished work: it is
        # also what a fresh process sees while a sibling's session builds.
        snapshot = self.snapshot()
        tracker = FakeTracker(snapshot)
        program = a_loop(tracker)
        box = inbox.bolt_inbox(snapshot, "x")
        open_items = [i for i in snapshot.items if i.is_open]
        self.assertFalse(program.landing_wanted("auto", box, open_items))
        self.assertTrue(program.landing_wanted("force", box, open_items))
        program._merged = 1
        self.assertTrue(program.landing_wanted("auto", box, open_items))

    def test_a_milestone_with_no_open_items_has_nothing_to_land(self):
        program = a_loop(FakeTracker())
        self.assertFalse(program.landing_wanted(
            "force", inbox.BoltInbox(milestone="bolt/x"), []))

    def test_a_landing_that_fails_twice_in_one_run_pauses_rather_than_retrying(self):
        program, tracker = self.program("Landing: merge", ancestor=1)
        program.land_stage(self.snapshot())
        outcome = program.land_stage(self.snapshot())
        self.assertEqual(outcome.status, "paused")


# ---------------------------------------------------------------------------
# The clock the program owns
# ---------------------------------------------------------------------------

class ClockTest(unittest.TestCase):

    def test_a_restarted_loop_measures_the_stall_from_the_launch_not_from_itself(self):
        # The marker on the item is the only carrier: herdr publishes no
        # timestamp, and a loop process is restarted freely.
        tracker = FakeTracker()
        program = a_loop(tracker)
        program.mark_launch([1], "build-x", 1_700_000_000)
        self.assertEqual(program.launch_origin([1], "build-x"), 1_700_000_000)
        self.assertIsNone(program.launch_origin([1], "build-y"))

    def test_half_a_marker_is_not_a_launch_record(self):
        tracker = FakeTracker(comments={1: [{"body": '<!-- flywheel:session name="b" -->'}]})
        self.assertIsNone(a_loop(tracker).launch_origin([1], "b"))

    def test_the_ninety_minute_notice_is_a_live_wait_and_is_cleared_on_settle(self):
        tracker = FakeTracker()
        clock = FakeClock(step=0.0)
        runner = ScriptedRunner(states=[WaitState.WORKING, WaitState.SETTLED_DONE])
        program = a_loop(tracker, runner=runner, clock=clock)
        original_wait = runner.wait

        def wait(handle, timeout=None):
            clock.advance(sessions.NOTIFY_AFTER_S)
            return original_wait(handle, timeout)

        runner.wait = wait
        outcome = program.settle("build", runner, sessions.SessionHandle(
            name="build-x", runner="fake"), [1], origin=clock.now)
        self.assertEqual(outcome.status, "done")
        self.assertIn(("add_label", 1, inbox.NEEDS_OPERATOR), tracker.writes)
        self.assertIn(("remove_label", 1, inbox.NEEDS_OPERATOR), tracker.writes)


# ---------------------------------------------------------------------------
# The trackers a run can be pointed at
# ---------------------------------------------------------------------------

class TrackerTest(unittest.TestCase):

    def test_a_dry_run_cannot_write_even_if_the_code_tried(self):
        guarded = loop.ReadOnlyTracker(FakeTracker())
        with self.assertRaises(loop.LoopError):
            guarded.add_label(1, inbox.READY)
        self.assertEqual(guarded.refused[0][0], "add_label")

    def test_a_fixture_file_can_be_the_tracker_for_a_whole_cycle(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bolt-tracker.json"
            path.write_text(json.dumps({
                "milestone": "bolt/x",
                "items": [{"number": 1, "title": "one", "labels": ["state:queued"],
                           "blocked_by": [], "parent_batch": None}],
                "batches": [{"number": 9, "kind": "unit", "status": "Ready",
                             "sub_issues": [1]}]}))
            tracker = loop.FixtureTracker(path)
            snapshot = tracker.snapshot("bolt/x")
            actions, _ = a_loop(tracker).guards(snapshot)
            self.assertEqual(len(actions), 1)
            again, _ = a_loop(tracker).guards(tracker.snapshot("bolt/x"))
            self.assertEqual(again, [], "the second pass over the same file writes nothing")
            self.assertIn("state:ready", json.loads(path.read_text())["items"][0]["labels"])


# ---------------------------------------------------------------------------
# Small readings
# ---------------------------------------------------------------------------

class ReadingTest(unittest.TestCase):

    def test_the_same_finding_is_the_same_text_and_nothing_cleverer(self):
        self.assertEqual(loop._finding_key("A  finding\n"), loop._finding_key("a finding"))
        self.assertNotEqual(loop._finding_key("a finding"), loop._finding_key("another"))

    def test_a_verify_report_that_says_it_found_nothing_is_read_as_clean(self):
        self.assertTrue(loop._no_findings("No findings."))
        self.assertTrue(loop._no_findings(""))
        self.assertFalse(loop._no_findings("FINDING: the flag is missing"))

    def test_the_merge_criteria_section_is_read_from_the_record_on_disk(self):
        record = ROOT / "openspec" / "changes" / "loop-server" / "bolt.md"
        if not record.exists():                      # a fresh worktree may lack it
            self.skipTest("this bolt's record is not in this tree")
        program = a_loop(FakeTracker(), slug="loop-server",
                         bolt_worktree=str(ROOT))
        self.assertIn("Landing: merge", program.merge_criteria())
        self.assertEqual(program.landing_mode(), "merge")


if __name__ == "__main__":
    unittest.main()
