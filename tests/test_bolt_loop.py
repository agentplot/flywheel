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
        self.closed = set()
        self.reasons = []

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

    def close(self, number, comment=None, reason=inbox.CLOSED_DONE):
        self.labels.setdefault(number, set()).add(reason)
        self.closed.add(number)
        self.writes.append(("close", number, comment or ""))
        self.reasons.append((number, reason))

    def reclose(self, number, comment=None, was=None, now=inbox.CLOSED_DONE):
        self.labels.setdefault(number, set()).add(now)
        if was and was != now:
            self.labels[number].discard(was)
        self.closed.add(number)
        self.writes.append(("reclose", number, comment or ""))
        self.reasons.append((number, now))

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

    def test_the_three_older_types_declare_no_stages_and_run_them_all(self):
        # `bolt-direct` is expressed as config, so the types that predate it
        # must be untouched by its arrival: no `stages:` key, and the
        # default sequence.
        for name in ("bolt-quick", "bolt-default", "bolt-adversarial"):
            self.assertEqual(loop.load_type(name, ROOT).stages,
                             loop.DEFAULT_STAGES, name)

    def test_bolt_direct_declares_the_stage_set_it_runs_and_verify_is_not_in_it(self):
        config = loop.load_type("bolt-direct", ROOT)
        self.assertEqual(config.stages, ("spec", "build", "merge", "land"))
        self.assertFalse(config.runs("verify"))
        self.assertTrue(all(config.runs(s) for s in ("spec", "build", "merge")))

    def test_bolt_direct_declares_no_boundary_its_stages_never_create(self):
        # A hook naming a boundary that never occurs is a review point
        # nothing can ever attach to.
        self.assertNotIn("post-verify", loop.load_type("bolt-direct", ROOT).hooks)
        for name in ("bolt-quick", "bolt-default", "bolt-adversarial"):
            self.assertIn("post-verify", loop.load_type(name, ROOT).hooks)

    def test_plan_mode_is_not_reachable_on_bolt_direct_either(self):
        with self.assertRaises(loop.LoopError):
            loop.resolve_plan_mode(True, loop.load_type("bolt-direct", ROOT))

    def test_an_unknown_stage_name_is_named_rather_than_silently_skipped(self):
        # `strategy` has raised on an unknown value since this config
        # existed; `stages` did not, so `[spec, buld, merge, land]` was a
        # type that silently skips build — the same downgrade a per-bolt
        # declaration is refused for.
        with self.assertRaises(loop.LoopError) as raised:
            loop.LoopConfig(name="t", stages=("spec", "buld")).validate()
        self.assertIn("buld", str(raised.exception))
        with self.assertRaises(loop.LoopError):
            loop.LoopConfig(name="t", stages=()).validate()

    def test_every_shipped_type_validates(self):
        for name in ("bolt-quick", "bolt-default", "bolt-adversarial",
                     "bolt-direct"):
            self.assertIs(loop.load_type(name, ROOT).validate().name and True, True)

    def test_a_per_bolt_stage_declaration_is_refused_not_ignored(self):
        # Symmetric with resolve_plan_mode: the bolt type is the scrutiny
        # the release approved, so skipping verify is bolt-direct's property
        # and not something a binding can ask for on another type.
        default = loop.load_type("bolt-default", ROOT)
        for key in loop.STAGE_DECLARATION_KEYS:
            with self.assertRaises(loop.LoopError, msg=key):
                loop.refuse_stage_declaration({key: "false"}, default)

    def test_a_clean_binding_passes_the_config_through(self):
        default = loop.load_type("bolt-default", ROOT)
        self.assertIs(
            loop.refuse_stage_declaration({"schema": "bolt-default"}, default),
            default)

    def test_a_block_style_declaration_is_seen_and_so_can_be_refused(self):
        # A key the binding parser cannot SEE is a key nothing can refuse.
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".openspec.yaml").write_text(
                "schema: bolt-default\ncreated: 2026-08-13\n"
                "stages:\n  - spec\n  - build\n")
            binding = loop.read_binding(tmp)
        self.assertEqual(binding["schema"], "bolt-default")
        self.assertEqual(binding["stages"], ["spec", "build"])
        with self.assertRaises(loop.LoopError):
            loop.refuse_stage_declaration(
                binding, loop.load_type("bolt-default", ROOT))

    def test_an_empty_declaration_is_still_a_declaration(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".openspec.yaml").write_text(
                "schema: bolt-default\nverify:\n")
            binding = loop.read_binding(tmp)
        with self.assertRaises(loop.LoopError):
            loop.refuse_stage_declaration(
                binding, loop.load_type("bolt-default", ROOT))

    def test_the_binding_parser_still_reads_every_binding_on_disk(self):
        # Flow lists and scalars must survive the block-list addition.
        for path in sorted((ROOT / "openspec" / "changes").glob("*/.openspec.yaml")):
            binding = loop.read_binding(path.parent)
            self.assertIn("schema", binding, str(path))
            self.assertIsInstance(binding["schema"], str, str(path))

    def test_the_refusal_holds_on_bolt_direct_too(self):
        # Even where the declaration would agree with the bound type: the
        # stage set has one writer, and it is the schema.
        with self.assertRaises(loop.LoopError):
            loop.refuse_stage_declaration(
                {"stages": "spec, build, merge, land"},
                loop.load_type("bolt-direct", ROOT))

    def test_no_schema_still_calls_the_loop_block_a_stub(self):
        # It is read — least stubbily on bolt-direct, whose whole reason to
        # exist is that read_schema_config reads its stage set.
        for path in sorted((ROOT / "schemas").glob("bolt-*/schema.yaml")):
            self.assertNotIn("STUB", path.read_text(), str(path))

    def test_every_schema_keeps_the_warning_that_openspec_strips_the_block(self):
        # The part of that comment which is still load-bearing.
        for path in sorted((ROOT / "schemas").glob("bolt-*/schema.yaml")):
            text = path.read_text()
            self.assertIn("MUST read schema.yaml itself", text, str(path))
            self.assertIn("schema fork", text, str(path))

    def test_no_schema_still_describes_the_landing_as_the_only_close(self):
        # The merge boundary closes `closed:merged`; the landing upgrades.
        for path in sorted((ROOT / "schemas").glob("bolt-*/schema.yaml")):
            text = path.read_text()
            self.assertIn("closed:merged", text, str(path))
            self.assertNotIn("close it `closed:done`", text, str(path))

    def test_install_schemas_would_publish_the_new_type_with_the_others(self):
        # `bin/install-schemas` copies every directory under schemas/ that
        # holds a schema.yaml — so a new type needs no change to it.
        published = sorted(d.name for d in (ROOT / "schemas").iterdir()
                           if (d / "schema.yaml").is_file())
        self.assertIn("bolt-direct", published)
        self.assertEqual(published, ["bolt-adversarial", "bolt-default",
                                     "bolt-direct", "bolt-quick",
                                     "flywheel-intent"])


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
        program = a_loop(FakeTracker(), runner=runner, strategy="new+ff")
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


class StageLabelTest(unittest.TestCase):
    """#96 — a label at each boundary, one at a time, re-derived from git."""

    #: A tree that says: the item's branch holds commits, and (by default)
    #: is an ancestor of the bolt branch.
    def shell(self, commits="3\n", ancestor=0):
        return FakeShell({("git", "rev-list"): Result(0, commits),
                          ("git", "merge-base"): Result(ancestor)})

    def worked(self, tracker, **overrides):
        runner = ScriptedRunner(states=[WaitState.SETTLED_DONE] * 12,
                                reports=["No findings."] * 12)
        return a_loop(tracker, runner=runner,
                      shell=overrides.pop("shell", self.shell()), **overrides)

    def a_ready_item(self):
        return Snapshot(items=[item(1, inbox.READY, change="add-thing")],
                        milestone="bolt/x")

    def stages_written(self, tracker):
        return [w[2] for w in tracker.writes
                if w[0] == "add_label" and w[2] in inbox.STAGE_LABELS]

    def test_a_full_cycle_writes_the_four_boundaries_in_the_order_it_runs_them(self):
        snapshot = self.a_ready_item()
        tracker = FakeTracker(snapshot, comments={1: [{"body": "built it"}]})
        self.worked(tracker).cycle(1)
        self.assertEqual(self.stages_written(tracker),
                         [inbox.STAGE_PLANNED, inbox.STAGE_BUILT,
                          inbox.STAGE_VERIFIED, inbox.STAGE_MERGED])

    def test_an_item_carries_exactly_one_stage_label_at_a_time(self):
        snapshot = self.a_ready_item()
        tracker = FakeTracker(snapshot, comments={1: [{"body": "built it"}]})
        self.worked(tracker).cycle(1)
        self.assertEqual(tracker.labels[1] & set(inbox.STAGE_LABELS),
                         {inbox.STAGE_MERGED},
                         "the label names the LEADING EDGE, not the history")

    def test_no_stage_write_ever_touches_a_closed_label(self):
        snapshot = self.a_ready_item()
        tracker = FakeTracker(snapshot, comments={1: [{"body": "built it"}]})
        self.worked(tracker).cycle(1)
        touched = [w for w in tracker.writes
                   if w[0] in ("add_label", "remove_label")
                   and str(w[2]).startswith("closed:")]
        self.assertEqual(touched, [],
                         "closed:done stays the landing's, with the SHA")

    def test_a_stage_that_did_not_happen_writes_no_label(self):
        # The spec stage fails, so the cycle never reaches build.
        snapshot = self.a_ready_item()
        tracker = FakeTracker(snapshot)
        shell = FakeShell({("openspec", "validate"): Result(1),
                           ("git", "rev-list"): Result(0, "3\n"),
                           ("git", "merge-base"): Result(1)})
        self.worked(tracker, shell=shell).cycle(1)
        self.assertEqual(self.stages_written(tracker), [])

    def test_a_session_saying_it_built_is_not_the_evidence(self):
        # The build session settles claiming success, but no commit exists
        # on the item's branch — so no stage:built, because the check is
        # `git rev-list` and not the report.
        snapshot = self.a_ready_item()
        tracker = FakeTracker(snapshot, comments={1: [{"body": "all green!"}]})
        self.worked(tracker, shell=self.shell(commits="0\n", ancestor=1)).cycle(1)
        self.assertNotIn(inbox.STAGE_BUILT, self.stages_written(tracker))

    # -- the re-derivation -------------------------------------------------

    def in_flight(self, *labels):
        return Snapshot(items=[item(1, inbox.IN_PROGRESS, *labels,
                                    change="add-thing")],
                        milestone="bolt/x")

    def reconcile(self, snapshot, shell, seed=()):
        tracker = FakeTracker(snapshot)
        tracker.labels[1] = set(seed)
        actions = []
        a_loop(tracker, shell=shell).guard_stages(snapshot, actions)
        return tracker, actions

    def test_a_commit_the_loop_never_saw_written_supplies_stage_built(self):
        # A process died after the build session committed and before the
        # label was written. The next cycle repairs it with no record of
        # the earlier run consulted.
        tracker, actions = self.reconcile(self.in_flight(),
                                          self.shell(ancestor=1))
        self.assertIn(("add_label", 1, inbox.STAGE_BUILT), tracker.writes)
        self.assertEqual(len(actions), 1)

    def test_ancestry_of_the_bolt_branch_supplies_stage_merged(self):
        tracker, actions = self.reconcile(self.in_flight(),
                                          self.shell(ancestor=0))
        self.assertIn(("add_label", 1, inbox.STAGE_MERGED), tracker.writes)

    def test_a_label_ahead_of_the_tree_is_walked_back(self):
        tracker, actions = self.reconcile(
            self.in_flight(inbox.STAGE_MERGED), self.shell(ancestor=1),
            seed=[inbox.IN_PROGRESS, inbox.STAGE_MERGED])
        self.assertIn(("remove_label", 1, inbox.STAGE_MERGED), tracker.writes)
        self.assertIn(("add_label", 1, inbox.STAGE_BUILT), tracker.writes)

    def test_verified_is_never_walked_back_because_git_cannot_witness_it(self):
        # A restart mid-verify must not invent a verdict, and must not undo
        # one either: verify being clean is a session's finding, and the
        # only way to re-derive it is to re-run verify.
        tracker, actions = self.reconcile(
            self.in_flight(inbox.STAGE_VERIFIED), self.shell(ancestor=1),
            seed=[inbox.IN_PROGRESS, inbox.STAGE_VERIFIED])
        self.assertEqual(tracker.writes, [])
        self.assertEqual(actions, [])

    def test_re_derivation_never_invents_planned_or_verified(self):
        tracker, _ = self.reconcile(self.in_flight(), self.shell(ancestor=1))
        written = [w[2] for w in tracker.writes if w[0] == "add_label"]
        self.assertNotIn(inbox.STAGE_PLANNED, written)
        self.assertNotIn(inbox.STAGE_VERIFIED, written)

    def test_a_tree_that_witnesses_nothing_writes_nothing(self):
        tracker, actions = self.reconcile(
            self.in_flight(), self.shell(commits="0\n", ancestor=1))
        self.assertEqual(tracker.writes, [])
        self.assertEqual(actions, [])

    def test_an_item_not_yet_in_progress_acquires_no_stage(self):
        # `stage:*` refines `state:in-progress` and never replaces a
        # `state:*` label, so a queued item has no stage to reconcile.
        snapshot = Snapshot(items=[item(1, inbox.QUEUED, change="add-thing")],
                            milestone="bolt/x")
        tracker, actions = self.reconcile(snapshot, self.shell(ancestor=0))
        self.assertEqual(tracker.writes, [])

    def test_the_dry_cycle_holds_with_the_new_guard(self):
        # Two consecutive cycles against an unchanged tracker and an
        # unchanged tree: the second writes nothing.
        snapshot = self.in_flight()
        tracker = FakeTracker(snapshot)
        program = a_loop(tracker, shell=self.shell(ancestor=0))
        first, _ = program.guards(snapshot)
        self.assertEqual(len(first), 1)
        before = len(tracker.writes)
        again, _ = program.guards(snapshot)
        self.assertEqual(again, [], "a check that changed nothing records nothing")
        self.assertEqual(len(tracker.writes), before, "and writes nothing")

    # -- the type that runs no verify --------------------------------------

    def direct(self, tracker):
        return self.worked(tracker, type_name="bolt-direct", config=loop.LoopConfig(
            name="bolt-direct", strategy="ff",
            stages=("spec", "build", "merge", "land")))

    def test_a_bolt_direct_cycle_launches_no_verify_session(self):
        snapshot = self.a_ready_item()
        tracker = FakeTracker(snapshot, comments={1: [{"body": "built it"}]})
        result = self.direct(tracker).cycle(1)
        self.assertEqual([o.stage for o in result.outcomes],
                         ["spec", "build", "merge"])

    def test_every_stage_the_cycle_runs_is_gated_on_the_declared_set(self):
        # `runs()` claims the next type that varies the sequence declares
        # its own set and adds no flag. That is only true if EVERY stage is
        # gated — gating the one stage bolt-direct omits would make the
        # claim true of it and false of the type after it.
        snapshot = self.a_ready_item()
        tracker = FakeTracker(snapshot, comments={1: [{"body": "built it"}]})
        program = self.worked(tracker, type_name="spec-only", config=loop.LoopConfig(
            name="spec-only", strategy="ff", stages=("spec",)))
        result = program.cycle(1)
        self.assertEqual([o.stage for o in result.outcomes], ["spec"],
                         "no build, no verify, no merge")
        self.assertFalse(program.landing_wanted(
            "force", inbox.BoltInbox(milestone="bolt/x"), [object()]),
            "and no landing, because the set does not name one")

    def test_a_type_that_declares_no_build_still_writes_no_built_label(self):
        snapshot = self.a_ready_item()
        tracker = FakeTracker(snapshot, comments={1: [{"body": "built it"}]})
        self.worked(tracker, type_name="spec-only", config=loop.LoopConfig(
            name="spec-only", strategy="ff", stages=("spec",))).cycle(1)
        self.assertEqual(self.stages_written(tracker), [inbox.STAGE_PLANNED])

    def test_a_bolt_direct_item_goes_built_to_merged_with_no_verified(self):
        snapshot = self.a_ready_item()
        tracker = FakeTracker(snapshot, comments={1: [{"body": "built it"}]})
        self.direct(tracker).cycle(1)
        self.assertEqual(self.stages_written(tracker),
                         [inbox.STAGE_PLANNED, inbox.STAGE_BUILT,
                          inbox.STAGE_MERGED])
        self.assertNotIn(inbox.STAGE_VERIFIED, tracker.labels[1])


class LandingTest(unittest.TestCase):

    def snapshot(self):
        return Snapshot(items=[item(1, inbox.TYPE_ASSERTION, inbox.IN_PROGRESS),
                               item(2, inbox.TYPE_ASSERTION, inbox.IN_PROGRESS)],
                        milestone="bolt/x")

    def program(self, criteria, ancestor=0, runner=None, tracker=None):
        tracker = tracker or FakeTracker(self.snapshot())
        shell = FakeShell({("git", "merge-base"): Result(ancestor),
                           ("git", "rev-parse"): Result(0, "abc1234\n")})
        program = a_loop(tracker, runner=runner or ScriptedRunner(), shell=shell)
        program.merge_criteria = lambda: criteria
        return program, tracker

    def test_every_item_ends_at_closed_done_with_the_landing_sha(self):
        program, tracker = self.program("Landing: merge", ancestor=0)
        outcome = program.land_stage(self.snapshot())
        self.assertEqual(outcome.status, "done")
        upgraded = [w for w in tracker.writes if w[0] == "reclose"]
        self.assertEqual([w[1] for w in upgraded], [1, 2])
        self.assertIn("abc1234", upgraded[0][2])
        self.assertEqual(tracker.reasons, [(1, inbox.CLOSED_DONE),
                                           (2, inbox.CLOSED_DONE)])

    def test_a_pull_request_landing_upgrades_nothing(self):
        program, tracker = self.program("Landing: pr", ancestor=1)
        outcome = program.land_stage(self.snapshot())
        self.assertEqual(outcome.status, "done")
        self.assertEqual([w for w in tracker.writes
                          if w[0] in ("close", "reclose")], [],
                         "the items stay at closed:merged until the PR merges")

    def test_the_default_landing_mode_is_merge(self):
        program, _ = self.program("Acceptance suites green on the bolt branch.")
        self.assertEqual(program.landing_mode(), "merge")

    def test_a_branch_that_did_not_land_upgrades_nothing_and_reports_the_failure(self):
        program, tracker = self.program("Landing: merge", ancestor=1)
        outcome = program.land_stage(self.snapshot())
        self.assertEqual(outcome.status, "failed")
        self.assertEqual([w for w in tracker.writes
                          if w[0] in ("close", "reclose")], [])

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

    def test_a_milestone_with_nothing_unlanded_has_nothing_to_land(self):
        program = a_loop(FakeTracker())
        self.assertFalse(program.landing_wanted(
            "force", inbox.BoltInbox(milestone="bolt/x"), []))

    def test_a_landing_that_fails_twice_in_one_run_pauses_rather_than_retrying(self):
        program, tracker = self.program("Landing: merge", ancestor=1)
        program.land_stage(self.snapshot())
        outcome = program.land_stage(self.snapshot())
        self.assertEqual(outcome.status, "paused")

    def merge_closed_only(self):
        """The NORMAL state at the landing once the merge boundary closes:
        every assertion closed at `closed:merged`, nothing open."""
        return Snapshot(items=[
            Item(number=1, milestone="bolt/x", title="one", state="closed",
                 labels=frozenset({inbox.TYPE_ASSERTION, inbox.CLOSED_MERGED})),
            Item(number=2, milestone="bolt/x", title="two", state="closed",
                 labels=frozenset({inbox.TYPE_ASSERTION, inbox.CLOSED_MERGED})),
        ], milestone="bolt/x")

    def test_a_failed_landing_on_an_all_merge_closed_milestone_still_pauses(self):
        # The landing is the last boundary, with no session downstream to
        # catch what it drops. An open-items-only set is empty here, and
        # the pause would write nothing at all.
        snapshot = self.merge_closed_only()
        program, tracker = self.program("Landing: merge", ancestor=1,
                                        tracker=FakeTracker(snapshot))
        program.land_stage(snapshot)
        outcome = program.land_stage(snapshot)
        self.assertEqual(outcome.status, "paused")
        self.assertIn(("add_label", 1, inbox.NEEDS_OPERATOR), tracker.writes)

    def test_an_andon_on_a_merge_closed_item_is_still_read(self):
        # The landing session's own work order tells it to raise the andon
        # on an item; by then every assertion is closed.
        snapshot = self.merge_closed_only()
        tracker = FakeTracker(snapshot, comments={
            1: [{"body": inbox.format_andon("criterion two failed again")}]})
        program, tracker = self.program("Landing: merge", ancestor=1,
                                        tracker=tracker)
        outcome = program.land_stage(snapshot)
        self.assertEqual(outcome.status, "paused")
        self.assertIn("andon on #1", outcome.detail)
        self.assertIn(("add_label", 1, inbox.NEEDS_OPERATOR), tracker.writes)

    def test_the_landing_records_its_launch_on_merge_closed_items(self):
        # `drive` skips mark_launch on an empty number set, and the stall
        # budget is recovered from that marker across a restart.
        snapshot = self.merge_closed_only()
        program, tracker = self.program("Landing: merge", ancestor=1,
                                        tracker=FakeTracker(snapshot))
        program.land_stage(snapshot)
        self.assertTrue(any(loop.SESSION_OPEN in w[2] for w in tracker.writes
                            if w[0] == "comment"))


class MergeCloseTest(unittest.TestCase):
    """#98 via the ruling on #118 — the sub-issue checks off at merge-back.

    The unit parent's bar is GitHub's own and counts CLOSED sub-issues, so
    the check-off is a close. `closed:merged` rather than a reasonless close
    is what keeps tracker.md invariant 5 verbatim.
    """

    def shell(self, ancestor=0, commits="3\n"):
        return FakeShell({("git", "rev-list"): Result(0, commits),
                          ("git", "merge-base"): Result(ancestor),
                          ("git", "rev-parse"): Result(0, "abc1234\n")})

    def a_batch(self, *items):
        return loop.WorkBatch(slug="add-thing", items=tuple(items))

    def test_the_merge_boundary_closes_assertions_with_closed_merged(self):
        tracker = FakeTracker()
        program = a_loop(tracker, shell=self.shell())
        program.close_merged(self.a_batch(
            item(1, inbox.TYPE_ASSERTION, inbox.IN_PROGRESS),
            item(2, inbox.TYPE_ASSERTION, inbox.IN_PROGRESS)))
        self.assertEqual(tracker.reasons, [(1, inbox.CLOSED_MERGED),
                                           (2, inbox.CLOSED_MERGED)])
        self.assertTrue(all("abc1234" in w[2] for w in tracker.writes
                            if w[0] == "close"))

    def test_a_discovery_item_on_the_bolt_is_untouched_by_the_merge(self):
        # A discovery closes on its own evidence, as it does today.
        tracker = FakeTracker()
        program = a_loop(tracker, shell=self.shell())
        program.close_merged(self.a_batch(
            item(1, inbox.TYPE_ASSERTION, inbox.IN_PROGRESS),
            item(5, inbox.IN_PROGRESS, title="a discovery")))
        self.assertEqual([n for n, _ in tracker.reasons], [1])

    def test_the_merge_session_is_told_the_loop_does_the_closing(self):
        runner = ScriptedRunner()
        shell = FakeShell({("git", "merge-base"): Result(1)})
        a_loop(FakeTracker(), runner=runner, shell=shell).merge_stage(
            loop.WorkBatch(slug="add-thing", items=(item(1, inbox.READY),)))
        order = runner.launched[0].order
        self.assertIn("The LOOP closes each assertion `closed:merged`", order)
        self.assertNotIn("do not close them", order)

    def test_a_full_cycle_merges_and_closes_in_one_go(self):
        snapshot = Snapshot(items=[item(1, inbox.TYPE_ASSERTION, inbox.READY,
                                        change="add-thing")],
                            milestone="bolt/x")
        tracker = FakeTracker(snapshot, comments={1: [{"body": "built it"}]})
        runner = ScriptedRunner(states=[WaitState.SETTLED_DONE] * 12,
                                reports=["No findings."] * 12)
        a_loop(tracker, runner=runner, shell=self.shell()).cycle(1)
        self.assertIn(inbox.STAGE_MERGED, tracker.labels[1])
        self.assertIn(inbox.CLOSED_MERGED, tracker.labels[1])

    # -- the landing's upgrade ---------------------------------------------

    def merged_snapshot(self):
        return Snapshot(items=[
            Item(number=1, milestone="bolt/x", title="one", state="closed",
                 labels=frozenset({inbox.TYPE_ASSERTION, inbox.CLOSED_MERGED})),
            Item(number=2, milestone="bolt/x", title="two", state="closed",
                 labels=frozenset({inbox.TYPE_ASSERTION, inbox.CLOSED_MERGED})),
        ], milestone="bolt/x")

    def landing(self, snapshot, ancestor=0):
        tracker = FakeTracker(snapshot)
        program = a_loop(tracker, shell=self.shell(ancestor=ancestor))
        program.merge_criteria = lambda: "Landing: merge"
        return program, tracker

    def test_the_landing_upgrades_merged_to_done_with_the_sha(self):
        snapshot = self.merged_snapshot()
        program, tracker = self.landing(snapshot)
        outcome = program.land_stage(snapshot)
        self.assertEqual(outcome.status, "done")
        for n in (1, 2):
            self.assertIn(inbox.CLOSED_DONE, tracker.labels[n])
            self.assertNotIn(inbox.CLOSED_MERGED, tracker.labels[n],
                             "never both reasons, never neither")
        self.assertTrue(all("abc1234" in w[2] for w in tracker.writes
                            if w[0] == "reclose"))

    def test_the_landing_is_not_blocked_by_an_already_closed_item(self):
        snapshot = self.merged_snapshot()
        program, tracker = self.landing(snapshot)
        self.assertEqual(program.land_stage(snapshot).status, "done")
        self.assertEqual(len([w for w in tracker.writes if w[0] == "reclose"]), 2)

    def test_an_item_that_never_merged_back_still_ends_at_closed_done(self):
        # The landing's job is the end state, not a transition it witnessed.
        snapshot = Snapshot(items=[item(1, inbox.TYPE_ASSERTION,
                                        inbox.IN_PROGRESS)],
                            milestone="bolt/x")
        program, tracker = self.landing(snapshot)
        program.land_stage(snapshot)
        self.assertIn(inbox.CLOSED_DONE, tracker.labels[1])

    def test_a_bolt_whose_every_item_is_merge_closed_still_lands(self):
        # Without this the last batch merges, the milestone looks empty,
        # and the bolt never lands at all.
        snapshot = self.merged_snapshot()
        program = a_loop(FakeTracker(snapshot), shell=self.shell())
        box = inbox.bolt_inbox(snapshot, "x")
        self.assertEqual(box.ready, (), "a closed item is never ready")
        unlanded = [i for i in snapshot.items if i.is_open or i.merge_closed]
        self.assertEqual(len(unlanded), 2)
        program._merged = 1
        self.assertTrue(program.landing_wanted("auto", box, unlanded))
        self.assertFalse(program.landing_wanted("auto", box, []))

    # -- re-derivation over the merged edge ---------------------------------

    def reconcile(self, snapshot, ancestor=0, seed=None):
        tracker = FakeTracker(snapshot)
        for number, labels in (seed or {}).items():
            tracker.labels[number] = set(labels)
        actions = []
        a_loop(tracker, shell=self.shell(ancestor=ancestor)).guard_stages(
            snapshot, actions)
        return tracker, actions

    def test_a_process_that_died_after_the_label_has_its_close_repaired(self):
        snapshot = Snapshot(items=[item(1, inbox.TYPE_ASSERTION,
                                        inbox.IN_PROGRESS, inbox.STAGE_MERGED,
                                        change="add-thing")],
                            milestone="bolt/x")
        tracker, actions = self.reconcile(
            snapshot, seed={1: {inbox.IN_PROGRESS, inbox.STAGE_MERGED}})
        self.assertEqual(tracker.reasons, [(1, inbox.CLOSED_MERGED)])
        self.assertTrue(any("closed:merged" in a for a in actions), actions)

    def test_a_process_that_died_after_the_close_has_its_label_repaired(self):
        snapshot = Snapshot(items=[
            Item(number=1, milestone="bolt/x", title="one", state="closed",
                 change="add-thing",
                 labels=frozenset({inbox.TYPE_ASSERTION, inbox.CLOSED_MERGED}))],
            milestone="bolt/x")
        tracker, actions = self.reconcile(
            snapshot, seed={1: {inbox.CLOSED_MERGED}})
        self.assertIn(("add_label", 1, inbox.STAGE_MERGED), tracker.writes)
        self.assertEqual(tracker.reasons, [], "already closed; not closed again")

    def test_a_landed_item_is_never_walked_back(self):
        snapshot = Snapshot(items=[
            Item(number=1, milestone="bolt/x", title="one", state="closed",
                 change="add-thing",
                 labels=frozenset({inbox.TYPE_ASSERTION, inbox.CLOSED_DONE,
                                   inbox.STAGE_MERGED}))],
            milestone="bolt/x")
        tracker, actions = self.reconcile(snapshot)
        self.assertEqual(tracker.writes, [], "the landing is downstream of merge")
        self.assertEqual(actions, [])

    def test_the_dry_cycle_holds_with_merged_closed_items_on_the_milestone(self):
        snapshot = Snapshot(items=[
            Item(number=1, milestone="bolt/x", title="one", state="closed",
                 change="add-thing",
                 labels=frozenset({inbox.TYPE_ASSERTION, inbox.CLOSED_MERGED,
                                   inbox.STAGE_MERGED}))],
            milestone="bolt/x")
        tracker = FakeTracker(snapshot)
        tracker.labels[1] = {inbox.CLOSED_MERGED, inbox.STAGE_MERGED}
        program = a_loop(tracker, shell=self.shell())
        first, _ = program.guards(snapshot)
        self.assertEqual(first, [])
        again, _ = program.guards(snapshot)
        self.assertEqual(again, [])
        self.assertEqual(tracker.writes, [])


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
