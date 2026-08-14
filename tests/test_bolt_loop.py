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
        self.closed = set()
        self.reasons = []

    # reads
    def snapshot(self, milestone=None, with_edges=True):
        return self._snapshot

    def comments(self, number):
        return list(self._comments.get(number, ()))

    def has_label(self, number, label):
        return label in self.labels.get(number, set())

    def closed_with(self, number, label):
        # Both halves, as the real tracker reads them: a label present on a
        # still-open issue is a torn close, not a finished one.
        return number in self.closed and label in self.labels.get(number, set())

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
                  "bolt-adversarial": ("new+continue", ("/opsx:new", "/opsx:continue")),
                  "bolt-direct": ("ff", ("/opsx:ff",))}
        for name, (strategy, invocations) in wanted.items():
            config = loop.load_type(name, ROOT)
            self.assertEqual(config.strategy, strategy, name)
            self.assertEqual(config.invocations, invocations, name)

    def test_each_shipped_type_declares_the_stage_set_it_runs(self):
        # Strategy and invocations are not the whole declaration: the stage
        # set is what makes bolt-direct a fourth named config rather than a
        # branch in the loop's code. A schema edited to add `verify` back to
        # bolt-direct must fail something, and this is that something.
        wanted = {
            "bolt-quick": ("spec", "build", "verify", "merge", "land"),
            "bolt-default": ("spec", "build", "verify", "merge", "land"),
            "bolt-adversarial": ("spec", "build", "verify", "merge", "land"),
            "bolt-direct": ("spec", "build", "merge", "land"),
        }
        for name, stages in wanted.items():
            self.assertEqual(tuple(loop.load_type(name, ROOT).stages), stages, name)
        self.assertNotIn("verify", loop.load_type("bolt-direct", ROOT).stages)

    def test_bolt_direct_declares_no_hook_for_a_boundary_it_never_reaches(self):
        # A hook naming a boundary that never occurs is a review point
        # nothing can ever attach to.
        config = loop.load_type("bolt-direct", ROOT)
        self.assertNotIn("post-verify", config.hooks)
        for name in ("bolt-quick", "bolt-default", "bolt-adversarial"):
            self.assertIn("post-verify", loop.load_type(name, ROOT).hooks, name)

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

    def test_a_command_line_type_disagreeing_with_the_binding_is_refused(self):
        # The other route to "no program downgrades the scrutiny the release
        # approved". The declaration door is shut; this is the entry point's
        # own precedence, which resolved --type ahead of the binding and so
        # let a flag alone run a bolt-default bolt with no verify stage.
        with self.assertRaises(loop.LoopError) as caught:
            loop.refuse_type_disagreement({"schema": "bolt-default"}, "bolt-direct")
        message = str(caught.exception)
        self.assertIn("bolt-default", message, "the refusal names the binding's type")
        self.assertIn("bolt-direct", message, "and the type it was asked for")

    def test_a_command_line_type_agreeing_with_the_binding_runs(self):
        self.assertEqual(
            loop.refuse_type_disagreement({"schema": "bolt-direct"}, "bolt-direct"),
            "bolt-direct")

    def test_a_bolt_with_no_binding_still_honours_the_flag(self):
        # There is no recorded approval for it to contradict, and refusing
        # would leave an unbound bolt unable to run at all.
        self.assertEqual(loop.refuse_type_disagreement({}, "bolt-direct"),
                         "bolt-direct")
        self.assertEqual(loop.refuse_type_disagreement(None, "bolt-direct"),
                         "bolt-direct")

    def test_the_binding_is_used_when_no_type_is_named(self):
        self.assertEqual(
            loop.refuse_type_disagreement({"schema": "bolt-adversarial"}, None),
            "bolt-adversarial")
        self.assertEqual(loop.refuse_type_disagreement({}, None), "bolt-quick")

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

    def test_a_born_ready_unit_parent_is_not_a_discovery_and_is_never_composed(self):
        """A release's own container is not work the release discovered.

        The born-ready unit parent this change introduces is labelled
        `unit` + `state:queued`, sits on `bolt/<slug>`, and is nobody's
        sub-issue — which is the orphan filter's shape exactly. Left in,
        the guard composes a SECOND unit over the release's own container,
        and that unit is itself a fresh orphan next cycle: it does not
        converge, and `cycle`'s STOP can never fire because the guard
        writes an action every pass.

        The three sibling sweeps all carry this exclusion
        (`_flywheel_inbox.compose_plan`, `server_inbox`, `guard_stages`);
        this one is the outlier. It is the first sweep to meet a unit on a
        bolt milestone, because on the handoff path the unit sits on the
        intent milestone.
        """
        snapshot = Snapshot(
            items=[item(9, inbox.UNIT, inbox.QUEUED, title="the release")],
            milestone="bolt/x")
        shell = FakeShell()
        tracker = FakeTracker(snapshot)
        program = a_loop(tracker, runner=ScriptedRunner(reports=["ROUTE: keep"]),
                         shell=shell)
        actions, failure = program.guards(snapshot)
        self.assertIsNone(failure)
        self.assertEqual(actions, [], "a container is not a discovery")
        self.assertEqual([c for c, _ in shell.calls
                          if "flywheel-batch" in c[0]], [],
                         "and nothing composes a unit over a unit")

    def test_an_elaboration_parent_is_excluded_on_the_same_grounds(self):
        snapshot = Snapshot(
            items=[item(8, inbox.ELABORATION, inbox.QUEUED)],
            milestone="bolt/x")
        shell = FakeShell()
        program = a_loop(FakeTracker(snapshot),
                         runner=ScriptedRunner(reports=["ROUTE: keep"]),
                         shell=shell)
        actions, _ = program.guards(snapshot)
        self.assertEqual(actions, [])
        self.assertEqual([c for c, _ in shell.calls
                          if "flywheel-batch" in c[0]], [])

    def test_a_real_discovery_beside_a_unit_parent_is_still_routed(self):
        """The exclusion must not swallow the guard's actual job."""
        snapshot = Snapshot(
            items=[item(9, inbox.UNIT, inbox.QUEUED),
                   item(5, inbox.QUEUED, title="a discovery")],
            milestone="bolt/x")
        tracker = FakeTracker(snapshot, milestones=[{"title": "intent/y"}])
        program = a_loop(tracker, runner=ScriptedRunner(
            reports=["ROUTE: intent/y\nWHY: no criterion needs it"]))
        program.guards(snapshot)
        self.assertIn(("set_milestone", 5, "intent/y"), tracker.writes)
        self.assertNotIn(9, [w[1] for w in tracker.writes])

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


class StageLabelTest(unittest.TestCase):
    """#96 — a label at each boundary, one at a time, re-derived from git."""

    #: A tree that says: the item's branch holds commits, and (by default)
    #: is an ancestor of the bolt branch. No rev-parse answer: the branch's
    #: base ref stays unresolved, so the cycle tests' batches never read as
    #: already merged before the merge stage runs.
    def shell(self, commits="3\n", ancestor=0):
        return FakeShell({("git", "rev-list"): Result(0, commits),
                          ("git", "merge-base"): Result(ancestor)})

    #: The re-derivation tree: the branch exists, its base ref resolves,
    #: and `commits` counts past the cut point — what `batch_merged` asks.
    def reshell(self, commits="3\n", ancestor=0):
        return FakeShell({("git", "rev-list"): Result(0, commits),
                          ("git", "rev-parse"): Result(0, "abc1234\n"),
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
                                          self.reshell(ancestor=0))
        self.assertIn(("add_label", 1, inbox.STAGE_MERGED), tracker.writes)

    def test_an_untouched_branch_gets_no_stage_and_no_close(self):
        # #173 — #164 re-entered at this guard: an untouched branch's tip
        # is an ancestor of everything it was cut from, so bare ancestry
        # read it as merged and closed its items. Advancement is the fact
        # that makes ancestry mean something.
        snap = Snapshot(items=[item(1, inbox.TYPE_ASSERTION,
                                    inbox.IN_PROGRESS, change="add-thing")],
                        milestone="bolt/x")
        tracker = FakeTracker(snap)
        actions = []
        a_loop(tracker, shell=self.reshell(commits="0\n", ancestor=0)) \
            .guard_stages(snap, actions)
        self.assertEqual([w for w in tracker.writes if w[0] == "add_label"],
                         [], "an empty branch witnesses nothing")
        self.assertEqual([w for w in tracker.writes if w[0] == "close"], [])

    def test_an_absent_branch_gets_no_stage(self):
        snap = Snapshot(items=[item(1, inbox.TYPE_ASSERTION,
                                    inbox.IN_PROGRESS, change="add-thing")],
                        milestone="bolt/x")
        tracker = FakeTracker(snap)
        shell = FakeShell({("git", "rev-parse"): Result(1),
                           ("git", "rev-list"): Result(128),
                           ("git", "merge-base"): Result(0)})
        actions = []
        a_loop(tracker, shell=shell).guard_stages(snap, actions)
        self.assertEqual([w for w in tracker.writes if w[0] == "add_label"],
                         [], "work not yet started is not merged")

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

    # -- the merge-close, torn -----------------------------------------------

    def torn_close(self):
        """The state a process killed inside `close` leaves behind.

        `BoltTracker.close` writes the label and then PATCHes the state, so
        a death between them leaves the item OPEN and carrying
        `closed:merged` — the one combination `merge_closed` (which is
        `not is_open and CLOSED_MERGED in labels`) reads as False.
        """
        torn = item(1, inbox.TYPE_ASSERTION, inbox.IN_PROGRESS,
                    inbox.CLOSED_MERGED, change="add-thing")
        snapshot = Snapshot(items=[torn], milestone="bolt/x")
        tracker = FakeTracker(snapshot)
        tracker.labels[1] = {inbox.CLOSED_MERGED}
        return snapshot, tracker

    def test_a_process_killed_inside_the_close_has_the_close_finished(self):
        """R10: the guard ends the item at whichever half a dead process
        left undone. The label half survived; the state half did not."""
        snapshot, tracker = self.torn_close()
        program = a_loop(tracker, shell=self.reshell())
        actions = []
        program.guard_stages(snapshot, actions)
        self.assertIn(1, tracker.closed, "the close is finished, not re-skipped")
        self.assertIn(inbox.CLOSED_MERGED, tracker.labels[1])

    def test_the_torn_close_repair_records_only_the_write_it_made(self):
        """`guards`' contract: `actions` records writes made, not writes
        attempted. The repair used to append unconditionally while
        `close_merged` skipped on the label already being there — an action
        every cycle, forever, for a write that never happened."""
        snapshot, tracker = self.torn_close()
        program = a_loop(tracker, shell=self.reshell())
        first = []
        program.guard_stages(snapshot, first)
        self.assertTrue(any("closed" in a for a in first), first)

        # Second pass, against the tracker the first one left behind.
        repaired = Snapshot(items=[item(1, inbox.TYPE_ASSERTION,
                                        inbox.IN_PROGRESS, inbox.CLOSED_MERGED,
                                        change="add-thing", state="closed")],
                            milestone="bolt/x")
        before = len(tracker.writes)
        again = []
        program.guard_stages(repaired, again)
        self.assertEqual(again, [], "the repair converges")
        self.assertEqual(len(tracker.writes), before, "and writes nothing")

    def test_an_item_already_closed_at_merge_is_left_entirely_alone(self):
        # Idempotence in the normal direction, which the old skip did give.
        closed = item(1, inbox.TYPE_ASSERTION, inbox.IN_PROGRESS,
                      inbox.CLOSED_MERGED, change="add-thing", state="closed")
        snapshot = Snapshot(items=[closed], milestone="bolt/x")
        tracker = FakeTracker(snapshot)
        tracker.labels[1] = {inbox.CLOSED_MERGED}
        tracker.closed.add(1)
        program = a_loop(tracker, shell=self.shell())
        actions = []
        program.guard_stages(snapshot, actions)
        self.assertEqual([w for w in tracker.writes if w[0] == "close"], [])

    # -- the type that runs no verify --------------------------------------

    def direct(self, tracker):
        # The REAL schema, not a config built here. A config constructed in a
        # test asserts what its author believed; the point is to hold what the
        # plugin ships, so a schema edited to add `verify` back to bolt-direct
        # fails this cycle test too and not only the declaration tests above.
        return self.worked(tracker, type_name="bolt-direct",
                           config=loop.load_type("bolt-direct", ROOT))

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

    def test_every_boundary_writes_off_ran_rather_than_ok(self):
        """The four writes share one test, and it is not `ok`.

        `ok` means "the cycle may carry on" and admits `skipped`; `ran`
        means "this boundary occurred". Pinning the distinction on the
        outcome type itself, so the next stage that learns to skip cannot
        start labelling itself by inheriting the wrong predicate.
        """
        skipped = loop.StageOutcome("verify", "skipped", "did not run")
        self.assertTrue(skipped.ok, "a skipped stage does not stop the cycle")
        self.assertFalse(skipped.ran, "but it did not happen")
        done = loop.StageOutcome("verify", "done", "clean")
        self.assertTrue(done.ok)
        self.assertTrue(done.ran)
        for status in ("paused", "failed", "stalled", "blocked"):
            outcome = loop.StageOutcome("verify", status)
            self.assertFalse(outcome.ok, status)
            self.assertFalse(outcome.ran, status)

    def test_a_skipped_stage_writes_no_label_on_the_plan_mode_path(self):
        """A stage that did not happen writes no label — and on the plan-mode
        path TWO stages do not happen.

        `spec_stage` and `verify_stage` both return `skipped` under
        `plan_mode`, and `StageOutcome.ok` admits `skipped` so that the
        cycle carries on past them. That makes `.ok` the wrong test for
        "did this boundary occur": `bolt-quick` declares the default stage
        set, so `config.runs("verify")` is true on a plan-mode bolt and the
        verify boundary would write `stage:verified` for a session that was
        never launched — the same wrong audit answer the spec forbids on
        `bolt-direct`, arrived at by a different route.

        `stage:planned` is still written on this path, by `plan_mode_build`
        at the APPROVED verdict — the one boundary the plan-mode path has.
        """
        snapshot = self.a_ready_item()
        tracker = FakeTracker(snapshot, comments={1: [{"body": "built it"}]})
        runner = ScriptedRunner(states=[WaitState.SETTLED_DONE] * 12,
                                reports=["a plan"] * 12)
        program = a_loop(tracker, runner=runner, shell=self.shell(),
                         plan_mode=True)
        # Approve once, then let the session read as finished — `approved`
        # re-enters the dialog loop, so a judge that only ever approves
        # never returns.
        verdicts = iter([("approved", "matches the claim"),
                         ("unreadable", "finished")])
        program.judge_plan = lambda *a: next(verdicts)
        program.cycle(1)
        self.assertNotIn(inbox.STAGE_VERIFIED, self.stages_written(tracker),
                         "no verify session ran, so no verify label")
        self.assertNotIn(inbox.STAGE_VERIFIED, tracker.labels[1])
        self.assertEqual(self.stages_written(tracker),
                         [inbox.STAGE_PLANNED, inbox.STAGE_BUILT,
                          inbox.STAGE_MERGED])


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

    def test_every_item_ends_at_closed_done_with_the_landing_sha(self):
        program, tracker = self.program("Landing: merge", ancestor=0)
        outcome = program.land_stage(self.snapshot())
        self.assertEqual(outcome.status, "done")
        upgraded = [w for w in tracker.writes if w[0] == "reclose"]
        self.assertEqual([w[1] for w in upgraded], [1, 2])
        self.assertIn("abc1234", upgraded[0][2])
        self.assertEqual(tracker.reasons, [(1, inbox.CLOSED_DONE),
                                           (2, inbox.CLOSED_DONE)])

    def with_unit(self, parent=9, kind=inbox.UNIT, milestone="bolt/x"):
        return Snapshot(
            items=[item(1, inbox.TYPE_ASSERTION, inbox.IN_PROGRESS, parent_batch=parent),
                   item(2, inbox.TYPE_ASSERTION, inbox.IN_PROGRESS, parent_batch=parent)],
            batches=[Batch(number=parent, kind=kind, status=inbox.STATUS_READY,
                           sub_issues=(1, 2), milestone=milestone)],
            milestone="bolt/x")

    def test_the_landing_closes_the_releases_unit_parent(self):
        # Nothing closed one before, so a born-ready bolt's parent stayed
        # open at Status Ready and its milestone reported a job forever.
        snapshot = self.with_unit()
        program, tracker = self.program("Landing: merge", ancestor=0,
                                        tracker=FakeTracker(snapshot))
        self.assertEqual(program.land_stage(snapshot).status, "done")
        closes = [w for w in tracker.writes if w[0] == "close"]
        self.assertEqual([w[1] for w in closes], [9])
        self.assertIn((9, inbox.CLOSED_DONE), tracker.reasons,
                      "a container closes with one reason like anything else")

    def test_closing_the_parent_touches_no_sub_issue(self):
        # The assertions' closes belong to the merge boundary and to the
        # upgrade; a container's close is not a cascade.
        snapshot = self.with_unit()
        program, tracker = self.program("Landing: merge", ancestor=0,
                                        tracker=FakeTracker(snapshot))
        program.land_stage(snapshot)
        self.assertEqual([w[1] for w in tracker.writes if w[0] == "close"], [9])
        self.assertEqual([w[1] for w in tracker.writes if w[0] == "reclose"], [1, 2],
                         "the sub-issues are upgraded, never closed a second time")

    def test_an_elaboration_on_the_milestone_is_not_closed_by_a_landing(self):
        snapshot = self.with_unit(kind=inbox.ELABORATION)
        program, tracker = self.program("Landing: merge", ancestor=0,
                                        tracker=FakeTracker(snapshot))
        program.land_stage(snapshot)
        self.assertEqual([w for w in tracker.writes if w[0] == "close"], [])

    def test_a_handoff_parent_off_the_bolt_milestone_is_reached_by_parentage(self):
        # The handoff path puts the parent on `intent/<slug>` deliberately —
        # it is born before any assertion has moved to a bolt — so the only
        # handle is a landed item's own parent.
        snapshot = self.with_unit(milestone="intent/x")
        program, tracker = self.program("Landing: merge", ancestor=0,
                                        tracker=FakeTracker(snapshot))
        program.land_stage(snapshot)
        self.assertEqual([w[1] for w in tracker.writes if w[0] == "close"], [9])

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

    def test_a_restarted_process_lands_a_bolt_whose_work_is_all_merged(self):
        # `_merged` is per process, and the server starts a loop for an
        # all-merge-closed milestone precisely so it can land. Counting
        # only this process's merges declined the landing it was started
        # for. The previous test pinned it only after setting `_merged`.
        merged = [Item(number=n, milestone="bolt/x", title=str(n), state="closed",
                       labels=frozenset({inbox.TYPE_ASSERTION, inbox.CLOSED_MERGED}))
                  for n in (1, 2)]
        program = a_loop(FakeTracker())
        box = inbox.BoltInbox(milestone="bolt/x")
        self.assertEqual(program._merged, 0, "a fresh process merged nothing")
        self.assertTrue(program.landing_wanted("auto", box, merged))

    def test_a_bolt_with_an_assertion_still_building_is_not_landed(self):
        # The caution `_merged` encoded, kept: an empty ready set is also
        # what a process sees while a sibling's session is still building.
        merged = Item(number=1, milestone="bolt/x", title="1", state="closed",
                      labels=frozenset({inbox.TYPE_ASSERTION, inbox.CLOSED_MERGED}))
        building = item(2, inbox.TYPE_ASSERTION, inbox.IN_PROGRESS)
        program = a_loop(FakeTracker())
        box = inbox.BoltInbox(milestone="bolt/x")
        self.assertFalse(program.landing_wanted("auto", box, [merged, building]))

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
        program.close_merged([
            item(1, inbox.TYPE_ASSERTION, inbox.IN_PROGRESS),
            item(2, inbox.TYPE_ASSERTION, inbox.IN_PROGRESS)])
        self.assertEqual(tracker.reasons, [(1, inbox.CLOSED_MERGED),
                                           (2, inbox.CLOSED_MERGED)])
        self.assertTrue(all("abc1234" in w[2] for w in tracker.writes
                            if w[0] == "close"))

    def test_a_discovery_item_on_the_bolt_is_untouched_by_the_merge(self):
        # A discovery closes on its own evidence, as it does today.
        tracker = FakeTracker()
        program = a_loop(tracker, shell=self.shell())
        program.close_merged([
            item(1, inbox.TYPE_ASSERTION, inbox.IN_PROGRESS),
            item(5, inbox.IN_PROGRESS, title="a discovery")])
        self.assertEqual([n for n, _ in tracker.reasons], [1])

    def test_the_merge_session_is_told_the_loop_does_the_closing(self):
        runner = ScriptedRunner()
        shell = FakeShell({("git", "merge-base"): Result(1)})
        a_loop(FakeTracker(), runner=runner, shell=shell).merge_stage(
            loop.WorkBatch(slug="add-thing", items=(item(1, inbox.READY),)))
        order = runner.launched[0].order
        self.assertIn("the LOOP closes each assertion `closed:merged`", order)
        self.assertNotIn("do not close them", order)
        # …and the one write it must never be told to withhold.
        self.assertIn("ANDON CORD IS THE EXCEPTION", order)
        self.assertIn("andon marker", order)

    def test_a_full_cycle_merges_and_closes_in_one_go(self):
        snapshot = Snapshot(items=[item(1, inbox.TYPE_ASSERTION, inbox.READY,
                                        change="add-thing")],
                            milestone="bolt/x")
        tracker = FakeTracker(snapshot, comments={1: [{"body": "built it"}]})
        runner = ScriptedRunner(states=[WaitState.SETTLED_DONE] * 12,
                                reports=["No findings."] * 12)
        # Ancestry must FLIP when the merge session runs: a branch that
        # reads merged from the start is parked awaiting the landing by
        # the resume partition and never drives at all.
        class MergeAwareShell(FakeShell):
            def __call__(self, argv, cwd=None, env=None, timeout=None):
                if tuple(argv[:2]) == ("git", "merge-base"):
                    self.calls.append((tuple(argv), cwd))
                    merged = any(s.name.startswith("merge-")
                                 for s in runner.launched)
                    return Result(0 if merged else 1)
                return super().__call__(argv, cwd=cwd, env=env, timeout=timeout)
        shell = MergeAwareShell({("git", "rev-list"): Result(0, "3\n"),
                                 ("git", "rev-parse"): Result(0, "abc1234\n")})
        a_loop(tracker, runner=runner, shell=shell).cycle(1)
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

    def test_every_write_on_the_tracker_is_named_in_the_dry_runs_refusal_set(self):
        """`ReadOnlyTracker` refuses by NAME, so a new write method is a
        hole in `--dry-run` until it is listed. Deriving the expected set
        from the real tracker rather than restating it, so the next write
        added to `Tracker`/`BoltTracker` fails here instead of silently
        writing during a dry run."""
        surfaces = (inbox.Tracker, loop.BoltTracker)
        writes = {name for cls in surfaces for name in vars(cls)
                  if name in ("add_label", "remove_label", "swap_label",
                              "comment", "set_milestone", "clear_milestone",
                              "close", "reclose", "create_item")}
        missing = writes - set(loop.ReadOnlyTracker.WRITES)
        self.assertEqual(missing, set(),
                         f"unguarded write(s) in a dry run: {sorted(missing)}")

    def test_every_tracker_surface_answers_the_reads_the_loop_makes(self):
        """A run can be pointed at three trackers, and the loop calls the
        same reads on all of them. `closed_with` was added for the torn
        merge-close and would have been an AttributeError on the fixture
        path — green suite, broken `--fixture` run — so the surfaces are
        compared rather than trusted."""
        reads = ("has_label", "closed_with", "comments", "snapshot")
        for surface in (loop.BoltTracker, loop.FixtureTracker):
            for name in reads:
                self.assertTrue(hasattr(surface, name),
                                f"{surface.__name__} cannot answer {name}")
        # …and the read-only wrapper passes reads through rather than
        # refusing them, or a dry run could not even look.
        guarded = loop.ReadOnlyTracker(FakeTracker())
        self.assertFalse(guarded.closed_with(1, inbox.CLOSED_MERGED))

    def test_the_atomic_label_swap_is_refused_in_a_dry_run(self):
        guarded = loop.ReadOnlyTracker(FakeTracker())
        with self.assertRaises(loop.LoopError):
            guarded.swap_label(1, add=inbox.CLOSED_DONE,
                               remove=inbox.CLOSED_MERGED)
        self.assertEqual(guarded.refused[0][0], "swap_label")

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


class TrackerWriteTest(unittest.TestCase):
    """The real `BoltTracker`, against a recording `gh`.

    Everything else in this file drives `FakeTracker`, which implements
    `reclose` itself — so the real one's API shape was never exercised.
    That is exactly how a two-call label swap survived: the fake swapped
    atomically because Python sets do, and the code underneath did not.
    """

    def tracker(self):
        calls = []

        def recorder(token, *args, **kw):
            calls.append(list(args))
            return {}

        return loop.BoltTracker("tok", "o", "r", gh=recorder), calls

    def label_edits(self, calls):
        return [c for c in calls if c[:2] == ["issue", "edit"]]

    def test_the_landings_upgrade_swaps_both_reasons_in_one_call(self):
        """Invariant: exactly one `closed:*` reason AT EVERY MOMENT.

        Add-then-remove satisfies "never neither" and violates "never
        both" — there is a window, however short, in which the item is
        closed:merged AND closed:done. A concurrent reader of the Landed
        view (`is:closed label:closed:done`) sees it as landed early.

        The repo's own reference already documents the atomic form and
        gives this justification verbatim — `skills/_reference/herdr.md`,
        `--add-label closed:done --remove-label closed:merged`.
        """
        tracker, calls = self.tracker()
        tracker.reclose(1, was=inbox.CLOSED_MERGED, now=inbox.CLOSED_DONE)
        edits = self.label_edits(calls)
        self.assertEqual(len(edits), 1,
                         f"one call, not two — got {edits}")
        self.assertIn("--add-label", edits[0])
        self.assertIn(inbox.CLOSED_DONE, edits[0])
        self.assertIn("--remove-label", edits[0])
        self.assertIn(inbox.CLOSED_MERGED, edits[0])

    def test_an_item_that_never_merged_back_is_still_closed_done(self):
        # `was=None` — nothing to remove, and the item must still end
        # carrying closed:done. One call, no --remove-label.
        tracker, calls = self.tracker()
        tracker.reclose(1, was=None, now=inbox.CLOSED_DONE)
        edits = self.label_edits(calls)
        self.assertEqual(len(edits), 1)
        self.assertIn(inbox.CLOSED_DONE, edits[0])
        self.assertNotIn("--remove-label", edits[0])

    def test_a_reason_swapped_for_itself_removes_nothing(self):
        tracker, calls = self.tracker()
        tracker.reclose(1, was=inbox.CLOSED_DONE, now=inbox.CLOSED_DONE)
        edits = self.label_edits(calls)
        self.assertEqual(len(edits), 1)
        self.assertNotIn("--remove-label", edits[0])

    def test_the_state_patch_still_runs_so_an_unmerged_item_ends_closed(self):
        tracker, calls = self.tracker()
        tracker.reclose(1, was=inbox.CLOSED_MERGED)
        self.assertTrue(any(c[:1] == ["api"] and "--method" in c
                            and "PATCH" in c for c in calls), calls)


if __name__ == "__main__":
    unittest.main()
