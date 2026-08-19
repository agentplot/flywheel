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

import importlib.machinery
import importlib.util
import json
import tempfile
import types
import unittest
from pathlib import Path

from context import BIN, ROOT, inbox, ledger as obs, sessions  # noqa: F401
import _flywheel_bolt_loop as loop  # noqa: E402

Item = inbox.Item
Batch = inbox.Batch
Snapshot = inbox.TrackerSnapshot
WaitState = sessions.WaitState


def item(number, *labels, **kw):
    kw.setdefault("milestone", "bolt/x")
    # A `unit` item is a card the loop expanded, and its title is what
    # names its plan document. `guard_charter` pauses the cycle on a unit
    # title that parses no slug, so a placeholder title on a unit here
    # would halt every cycle test in the file on a fixture artefact rather
    # than on anything the test is about.
    kw.setdefault("title", f"Unit: unit-{number}" if inbox.UNIT in labels
                  else f"item {number}")
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
    """A runner whose settles, pane reads and file channels are scripted.

    The loop reads verify's findings and the review's ruling from files
    the sessions write (#200), so this double writes them at collect time
    — the moment the real session would have. `verify_files` scripts the
    findings per verify run and falls back to NONE (clean); `rulings`
    scripts the review's JSON and writes nothing when exhausted.
    """

    def __init__(self, states=(), reports=(), verify_files=(), rulings=()):
        self.states = list(states) or [WaitState.SETTLED_DONE]
        self.reports = list(reports)
        self.verify_files = list(verify_files)
        self.rulings = list(rulings)
        self.launched, self.sent, self.keys, self.closed = [], [], [], []

    def _write(self, rel, content):
        path = TREE / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

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
        if handle.name.startswith("verify"):
            self._write(loop.VERIFY_REPORT,
                        self.verify_files.pop(0) if self.verify_files
                        else loop.NO_FINDINGS)
        elif handle.name.startswith("review") and self.rulings:
            self._write(loop.REVIEW_RULING, self.rulings.pop(0))
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


#: A worktree whose change record is CHARTERED, so guard 0
#: (charter-if-missing) is a no-op everywhere except where a test wants it
#: to fire. A directory alone no longer buys that: the guard's test is
#: `bolt.md`, so a bare directory here would drive a scaffold session into
#: every cycle test in the file. The charter is the minimum the guard's own
#: reader — `merge_criteria()`, which the landing reads through — accepts.
_TREE = tempfile.TemporaryDirectory()
TREE = Path(_TREE.name)
(TREE / "openspec" / "changes" / "x").mkdir(parents=True, exist_ok=True)
(TREE / "openspec" / "changes" / "x" / "bolt.md").write_text(
    "# Bolt: x\n\n## Scope\nWhat this bolt builds.\n\n## Sources\n- a source\n"
    "\n## Repos\n- flywheel \u00b7 bolt branch `bolt/x`\n\n## Merge criteria\n"
    "Acceptance suites green on the bolt branch.\nLanding: merge\n")


def a_loop(tracker, runner=None, shell=None, clock=None, plan=False,
           strategy="ff", ledger=None, **overrides):
    fields = dict(slug="x", org="o", repo="r", repo_dir=str(TREE),
                  bolt_worktree=str(TREE), type_name="bolt-quick",
                  config=loop.LoopConfig(name="bolt-quick", strategy=strategy,
                                         mode="plan" if plan else "spec"))
    fields.update(overrides)
    runner = runner or ScriptedRunner()
    return loop.BoltLoop(loop.BoltParams(**fields), tracker,
                         runner_factory=lambda stage: runner,
                         run=shell or FakeShell(), clock=clock or FakeClock(),
                         ledger=ledger)


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


class StatelessResumeTest(unittest.TestCase):
    """A restarted loop re-adopts its own in-progress items (observed live:
    a restart saw only state:ready, found nothing, and stranded the bolt)."""

    def _snap(self):
        return Snapshot(items=[
            item(96, inbox.IN_PROGRESS,
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
        self.assertFalse(
            l.landing_wanted("auto", box, list(self._snap().items)),
            "merged work awaits the operator's close — never an auto landing")
        released = [Item(number=i.number, milestone=i.milestone,
                         milestone_state="closed", title=i.title,
                         state=i.state, labels=i.labels)
                    for i in self._snap().items]
        self.assertTrue(l.landing_wanted("auto", box, released))

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

    def test_the_plan_path_belongs_to_bolt_plan_alone(self):
        # There is no mode beside the type: bolt-plan declares mode: plan
        # in its loop block and every other type is the spec path.
        self.assertTrue(loop.load_type("bolt-plan", ROOT).plan)
        for name in ("bolt-default", "bolt-adversarial", "bolt-quick",
                     "bolt-direct"):
            self.assertFalse(loop.load_type(name, ROOT).plan, name)

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
                                     "bolt-direct", "bolt-plan",
                                     "bolt-quick", "flywheel-intent"])


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


class InertQueueTest(unittest.TestCase):
    """A queued item on a bolt milestone is inert to machinery: no routing
    session, no composed unit, no move — it waits until an author folds it
    into a plan card. Expansion of an approved card is the only birth."""

    def test_a_queued_orphan_charges_no_session_and_moves_nowhere(self):
        snapshot = Snapshot(items=[item(5, inbox.QUEUED, title="a note")],
                            milestone="bolt/x")
        shell = FakeShell()
        tracker = FakeTracker(snapshot)
        runner = ScriptedRunner(reports=["should never be read"])
        program = a_loop(tracker, runner=runner, shell=shell)
        actions, failure = program.guards(snapshot)
        self.assertIsNone(failure)
        self.assertEqual(actions, [])
        self.assertNotIn("set_milestone", tracker.kinds())
        self.assertNotIn("clear_milestone", tracker.kinds())
        self.assertEqual([c for c, _ in shell.calls
                          if "flywheel-batch" in str(c[0])], [],
                         "nothing composes a unit from queued items")

    def test_containers_and_orphans_alike_are_left_alone(self):
        snapshot = Snapshot(
            items=[item(9, inbox.UNIT, inbox.QUEUED),
                   item(8, inbox.ELABORATION, inbox.QUEUED),
                   item(5, inbox.QUEUED, title="a note")],
            milestone="bolt/x")
        tracker = FakeTracker(snapshot)
        actions, _ = a_loop(tracker).guards(snapshot)
        self.assertEqual(actions, [])
        self.assertEqual(tracker.writes, [])


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

    def build_handle(self):
        return loop.StageOutcome("build", "done", handle=sessions.SessionHandle(
            name="build-add-thing", runner="fake"))

    def test_refix_rounds_exhaust_into_a_pause(self):
        finding = "FINDING: the spec asks for a flag that is not there"
        refix = '{"action": "refix", "prompt": "add the flag"}'
        tracker = FakeTracker()
        runner = ScriptedRunner(verify_files=[finding] * 3, rulings=[refix] * 3)
        shell = FakeShell({("git", "rev-list"): Result(0, "3\n")})
        outcome = a_loop(tracker, runner=runner, shell=shell).verify_stage(
            self.batch(1), self.build_handle())
        self.assertEqual(outcome.status, "paused")
        self.assertIn(("add_label", 1, inbox.NEEDS_OPERATOR), tracker.writes)

    def test_verify_clean_is_the_file_saying_none_and_validate_green(self):
        outcome = a_loop(FakeTracker(), runner=ScriptedRunner()).verify_stage(
            self.batch(1), loop.StageOutcome("build", "done"))
        self.assertEqual(outcome.status, "done")

    def test_verify_clean_closes_the_build_pane(self):
        # The pane's purpose — the build/verify conversation — ends at
        # clean; the session stays resumable by its id (#178).
        runner = ScriptedRunner()
        outcome = a_loop(FakeTracker(), runner=runner).verify_stage(
            self.batch(1), self.build_handle())
        self.assertEqual(outcome.status, "done")
        self.assertIn("build-add-thing", runner.closed)

    def test_verify_settling_without_its_report_file_pauses(self):
        # The channel is a file the loop owns, deleted before the launch —
        # a session that settles without writing it produced nothing the
        # review can rule on, and the loop never guesses from the pane.
        class Silent(ScriptedRunner):
            def collect(self, handle, lines=200):
                return sessions.Collected(state=WaitState.SETTLED_DONE, report="")
        tracker = FakeTracker()
        outcome = a_loop(tracker, runner=Silent()).verify_stage(
            self.batch(1), loop.StageOutcome("build", "done"))
        self.assertEqual(outcome.status, "paused")
        self.assertIn(("add_label", 1, inbox.NEEDS_OPERATOR), tracker.writes)

    def test_a_proceed_ruling_overrides_the_findings(self):
        runner = ScriptedRunner(
            verify_files=["FINDING: a naming nit"],
            rulings=['{"action": "proceed", "reason": "cosmetic; merge"}'])
        outcome = a_loop(FakeTracker(), runner=runner).verify_stage(
            self.batch(1), self.build_handle())
        self.assertEqual(outcome.status, "done")
        self.assertIn("proceed", outcome.detail)

    def test_an_escalate_ruling_pauses_with_the_reason(self):
        tracker = FakeTracker()
        runner = ScriptedRunner(
            verify_files=["FINDING: the migration drops a column"],
            rulings=['{"action": "escalate", "reason": "data loss risk"}'])
        outcome = a_loop(tracker, runner=runner).verify_stage(
            self.batch(1), self.build_handle())
        self.assertEqual(outcome.status, "paused")
        self.assertEqual(outcome.detail, "review escalated")
        self.assertIn(("add_label", 1, inbox.NEEDS_OPERATOR), tracker.writes)

    def test_the_refix_prompt_reaches_the_build_session_verbatim(self):
        runner = ScriptedRunner(
            verify_files=["FINDING: the flag is missing"],
            rulings=['{"action": "refix", "prompt": "Add only the --flag option."}'])
        outcome = a_loop(FakeTracker(), runner=runner).verify_stage(
            self.batch(1), self.build_handle())
        self.assertEqual(outcome.status, "done", "second verify run is clean")
        self.assertIn(("build-add-thing", "Add only the --flag option."),
                      runner.sent)

    def test_an_unreadable_ruling_escalates_never_guesses(self):
        tracker = FakeTracker()
        runner = ScriptedRunner(
            verify_files=["FINDING: something"],
            rulings=["shrug, looks fine to me"])
        outcome = a_loop(tracker, runner=runner).verify_stage(
            self.batch(1), self.build_handle())
        self.assertEqual(outcome.status, "paused")
        self.assertEqual(outcome.detail, "review escalated")

    def test_a_built_tree_skips_the_build_session(self):
        # Symmetric with spec's already-validates: a restarted loop re-buys
        # no build for a boundary the tree already proves.
        runner = ScriptedRunner()
        shell = FakeShell({("git", "rev-list"): Result(0, "3\n")})
        outcome = a_loop(FakeTracker(), runner=runner,
                         shell=shell).build_stage(self.batch(1))
        self.assertEqual(outcome.status, "done")
        self.assertEqual(runner.launched, [], "no session for proven work")

    def test_a_recorded_clean_verdict_skips_verify_while_the_branch_holds(self):
        sha = "abc123def456"
        mark = f'Verify is clean at `{sha}`.\n\n<!-- flywheel:verified sha="{sha}" -->'
        tracker = FakeTracker(comments={1: [{"body": mark}]})
        runner = ScriptedRunner()
        shell = FakeShell({("git", "rev-parse"): Result(0, sha + "\n")})
        build = loop.StageOutcome("build", "done")
        outcome = a_loop(tracker, runner=runner, shell=shell).verify_stage(
            self.batch(1), build)
        self.assertEqual(outcome.status, "done")
        self.assertIn("has not moved", outcome.detail)
        self.assertEqual(runner.launched, [], "no session re-buys the verdict")

    def test_a_moved_branch_spends_the_recorded_verdict(self):
        mark = 'Verify is clean at `oldsha`.\n\n<!-- flywheel:verified sha="0ld5ha" -->'
        tracker = FakeTracker(comments={1: [{"body": mark}]})
        runner = ScriptedRunner(reports=["whatever"],
                                states=[WaitState.SETTLED_DONE] * 4)
        shell = FakeShell({("git", "rev-parse"): Result(0, "newsha\n")})
        build = loop.StageOutcome("build", "done")
        a_loop(tracker, runner=runner, shell=shell).verify_stage(
            self.batch(1), build)
        self.assertTrue(runner.launched, "one commit later, verify runs again")

    def test_a_clean_verify_records_its_verdict_on_the_items(self):
        sha = "abc123def456"
        tracker = FakeTracker()
        runner = ScriptedRunner(states=[WaitState.SETTLED_DONE] * 4)
        shell = FakeShell({("git", "rev-parse"): Result(0, sha + "\n")})
        program = a_loop(tracker, runner=runner, shell=shell)
        program.read_channel = lambda cwd, rel: "NONE"
        build = loop.StageOutcome("build", "done")
        outcome = program.verify_stage(self.batch(1), build)
        self.assertEqual(outcome.status, "done")
        marked = [w[2] for w in tracker.writes
                  if w[0] == "comment" and "flywheel:verified" in w[2]]
        self.assertTrue(marked, "the verdict is durable on the item")
        self.assertIn(sha, marked[0])

    def test_the_build_order_is_the_command_and_the_commit_rule(self):
        # The slug alone points opsx at its context; items, worktree prose,
        # escalation hints and settling instructions are loop plumbing that
        # primes the roaming (#167, extended to build by the operator).
        runner = ScriptedRunner()
        shell = FakeShell({("git", "rev-list"): Result(0, "3\n"),
                           ("openspec", "validate"): Result(1, "", "not green")})
        a_loop(FakeTracker(), runner=runner, shell=shell).build_stage(self.batch(1))
        order = runner.launched[0].order
        self.assertTrue(order.startswith("/opsx:apply add-thing"))
        self.assertIn("pathspec", order)
        for noise in ("#1", "ANDON", "milestone", "settling", "worktree"):
            self.assertNotIn(noise, order)

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
        program = a_loop(FakeTracker(), plan=True)
        self.assertEqual(program.spec_stage(self.batch(1)).status, "skipped")
        self.assertEqual(
            program.verify_stage(self.batch(1), loop.StageOutcome("build", "done")).status,
            "skipped")

    def test_a_plan_returned_twice_pauses_the_batch_rather_than_bouncing_again(self):
        tracker = FakeTracker()
        runner = ScriptedRunner(
            states=[WaitState.SETTLED_BLOCKED] * 12,
            reports=["a plan"] * 12)
        program = a_loop(tracker, runner=runner, plan=True)
        program.judge_plan = lambda batch, handle, pane: ("returned", "claim #1 dropped")
        outcome = program.plan_mode_build(self.batch(1, change=None), "build-x")
        self.assertEqual(outcome.status, "paused")
        self.assertIn(("add_label", 1, inbox.NEEDS_OPERATOR), tracker.writes)

    def test_an_approved_plan_is_driven_through_the_dialog_and_the_clock_restarts(self):
        tracker = FakeTracker()
        runner = ScriptedRunner(states=[WaitState.SETTLED_BLOCKED,
                                        WaitState.SETTLED_DONE],
                                reports=["a plan", "built it"])
        program = a_loop(tracker, runner=runner, plan=True)
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

    def test_the_merge_is_a_static_step_never_a_session(self):
        # Merging is bookkeeping: fixed command, same gate either way,
        # success answered by git. No agent has anything to decide here.
        runner = ScriptedRunner()
        shell = FakeShell({("git", "merge-base"): Result(0)})
        outcome = a_loop(FakeTracker(), runner=runner, shell=shell).merge_stage(
            self.batch(1))
        self.assertEqual(outcome.status, "done")
        self.assertEqual(runner.launched, [], "no merge session exists")
        self.assertTrue(any(a[:4] == ("wt", "merge", "build/add-thing",
                                      "--no-remove")
                            for a, _ in shell.calls))

    def test_a_red_gate_goes_back_to_the_build_session_with_the_output(self):
        results = iter([Result(1, "gate: the books check failed"), Result(0)])
        shell = FakeShell({("wt", "merge"): lambda: next(results),
                           ("git", "merge-base"): Result(0)})
        runner = ScriptedRunner()
        build = loop.StageOutcome("build", "done", handle=sessions.SessionHandle(
            name="build-add-thing", runner="fake"))
        outcome = a_loop(FakeTracker(), runner=runner, shell=shell).merge_stage(
            self.batch(1), build)
        self.assertEqual(outcome.status, "done", "green on the retry")
        self.assertTrue(any("the books check failed" in prompt
                            for _, prompt in runner.sent))

    def test_a_gate_red_past_the_budget_pauses_the_batch(self):
        shell = FakeShell({("wt", "merge"): Result(1, "gate: still red"),
                           ("git", "merge-base"): Result(0)})
        tracker = FakeTracker()
        build = loop.StageOutcome("build", "done", handle=sessions.SessionHandle(
            name="build-add-thing", runner="fake"))
        outcome = a_loop(tracker, shell=shell).merge_stage(self.batch(1), build)
        self.assertEqual(outcome.status, "paused")
        self.assertIn(("add_label", 1, inbox.NEEDS_OPERATOR), tracker.writes)

    def test_a_merge_conflict_pauses_for_the_operator(self):
        # The agent seat for conflicts is reserved, stubbed to a pause:
        # a conflict means a sibling moved under this branch, and nobody
        # auto-resolves that today.
        shell = FakeShell({("wt", "merge"): Result(1, "CONFLICT (content): x"),
                           ("git", "merge-base"): Result(1)})
        tracker = FakeTracker()
        runner = ScriptedRunner()
        outcome = a_loop(tracker, runner=runner, shell=shell).merge_stage(
            self.batch(1))
        self.assertEqual(outcome.status, "paused")
        self.assertEqual(outcome.detail, "merge conflict")
        self.assertEqual(runner.sent, [], "no refix round on a conflict")
        self.assertIn(("add_label", 1, inbox.NEEDS_OPERATOR), tracker.writes)
        self.assertTrue(any(a[:3] == ("git", "merge", "--abort")
                            for a, _ in shell.calls))


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

    def test_the_loop_writes_the_built_comment_not_the_session(self):
        # Bookkeeping is the loop's: the work order no longer points the
        # build session at the tracker, so the built boundary writes the
        # branch-and-SHA comment itself.
        snapshot = self.a_ready_item()
        tracker = FakeTracker(snapshot, comments={1: [{"body": "built it"}]})
        self.worked(tracker).cycle(1)
        bodies = [str(w[2]) for w in tracker.writes if w[0] == "comment"]
        self.assertTrue(any("Built on build/" in b for b in bodies))

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
        snap = Snapshot(items=[item(1, 
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
        snap = Snapshot(items=[item(1, 
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
        torn = item(1, inbox.IN_PROGRESS,
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
        repaired = Snapshot(items=[item(1, 
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
        closed = item(1, inbox.IN_PROGRESS,
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
                         plan=True)
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
        return Snapshot(items=[item(1, inbox.IN_PROGRESS),
                               item(2, inbox.IN_PROGRESS)],
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
        snap = Snapshot(items=[item(1, inbox.IN_PROGRESS,
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

    def with_unit(self, parent=9, kind=inbox.UNIT, milestone="bolt/x",
                  second=None, elaboration=None):
        """One unit, its two items, and their parentage.

        `second=(number, (a, b))` adds a second unit of its own on this
        bolt's milestone — the shape of any bolt whose operator approved
        more than one card — and `elaboration=number` adds an elaboration
        beside them, which no landing closes.
        """
        items = [item(1, inbox.IN_PROGRESS, parent_batch=parent),
                 item(2, inbox.IN_PROGRESS, parent_batch=parent)]
        batches = [Batch(number=parent, kind=kind, status=inbox.STATUS_READY,
                         sub_issues=(1, 2), milestone=milestone)]
        if second:
            number, subs = second
            items += [item(n, inbox.IN_PROGRESS,
                           parent_batch=number) for n in subs]
            batches.append(Batch(number=number, kind=inbox.UNIT,
                                 status=inbox.STATUS_READY,
                                 sub_issues=tuple(subs), milestone="bolt/x"))
        if elaboration:
            batches.append(Batch(number=elaboration, kind=inbox.ELABORATION,
                                 status=inbox.STATUS_READY, milestone="bolt/x"))
        return Snapshot(items=items, batches=batches, milestone="bolt/x")

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

    def test_a_unit_open_on_the_milestone_is_closed_by_the_landing(self):
        # The live shape: the unit parent is itself an OPEN ITEM on the
        # milestone, so it rides the stage's item set (the pause and andon
        # surface). Subtracting that whole set as "landed" excluded every
        # open unit from its own close — #255 landed and stayed open.
        snapshot = self.with_unit()
        snapshot = Snapshot(
            items=list(snapshot.items) + [item(9, inbox.UNIT)],
            batches=snapshot.batches, milestone="bolt/x")
        program, tracker = self.program("Landing: merge", ancestor=0,
                                        tracker=FakeTracker(snapshot))
        self.assertEqual(program.land_stage(snapshot).status, "done")
        self.assertIn(9, [w[1] for w in tracker.writes if w[0] == "close"],
                      "the open unit closes even though it rode the item set")

    def test_closing_the_parent_touches_no_sub_issue(self):
        # The work items' closes belong to the merge boundary and to the
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

    def test_both_units_on_one_milestone_close_at_the_one_landing(self):
        # A bolt milestone holds as many units as the operator approved
        # cards on it, and one landing serves them all. Closing "the
        # release's unit parent" would leave the second open at Status
        # Ready, naming a job on the board forever.
        snapshot = self.with_unit(second=(10, (3, 4)), elaboration=11)
        program, tracker = self.program("Landing: merge", ancestor=0,
                                        tracker=FakeTracker(snapshot))
        self.assertEqual(program.land_stage(snapshot).status, "done")
        closes = [w for w in tracker.writes if w[0] == "close"]
        self.assertEqual([w[1] for w in closes], [9, 10],
                         "every unit on the milestone, and only the units")
        for number, comment in [(w[1], w[2]) for w in closes]:
            self.assertIn("abc1234", comment, f"#{number} carries the SHA")
        self.assertEqual(sorted(tracker.reasons),
                         [(1, inbox.CLOSED_DONE), (2, inbox.CLOSED_DONE),
                          (3, inbox.CLOSED_DONE), (4, inbox.CLOSED_DONE),
                          (9, inbox.CLOSED_DONE), (10, inbox.CLOSED_DONE)])
        self.assertEqual([w[1] for w in tracker.writes if w[0] == "reclose"],
                         [1, 2, 3, 4],
                         "each sub-issue is upgraded once and closed no second time")

    def test_an_elaboration_beside_two_units_is_left_alone(self):
        snapshot = self.with_unit(second=(10, (3, 4)), elaboration=11)
        program, tracker = self.program("Landing: merge", ancestor=0,
                                        tracker=FakeTracker(snapshot))
        program.land_stage(snapshot)
        self.assertNotIn(11, [w[1] for w in tracker.writes],
                         "an elaboration authorizes design work, not this release")

    def test_a_handoff_parent_off_the_bolt_milestone_is_reached_by_parentage(self):
        # The handoff path puts the parent on `intent/<slug>` deliberately —
        # it is born before any work item has moved to a bolt — so the only
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
        self.assertFalse(
            program.landing_wanted("auto", box, open_items),
            "an open milestone never lands — the operator's close releases it")
        released = [Item(number=i.number, milestone=i.milestone,
                         milestone_state="closed", title=i.title,
                         state=i.state, labels=i.labels)
                    for i in open_items]
        self.assertTrue(program.landing_wanted("auto", box, released))

    def test_a_restarted_process_lands_a_bolt_whose_work_is_all_merged(self):
        # `_merged` is per process, and the server starts a loop for an
        # all-merge-closed milestone precisely so it can land. Counting
        # only this process's merges declined the landing it was started
        # for. The previous test pinned it only after setting `_merged`.
        merged = [Item(number=n, milestone="bolt/x", milestone_state="closed",
                       title=str(n), state="closed",
                       labels=frozenset({inbox.CLOSED_MERGED}))
                  for n in (1, 2)]
        program = a_loop(FakeTracker())
        box = inbox.BoltInbox(milestone="bolt/x")
        self.assertEqual(program._merged, 0, "a fresh process merged nothing")
        self.assertTrue(program.landing_wanted("auto", box, merged))

    def test_a_bolt_with_an_item_still_building_is_not_landed(self):
        # The caution `_merged` encoded, kept: an empty ready set is also
        # what a process sees while a sibling's session is still building.
        merged = Item(number=1, milestone="bolt/x", title="1", state="closed",
                      labels=frozenset({inbox.CLOSED_MERGED}))
        building = item(2, inbox.IN_PROGRESS)
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
        every work item closed at `closed:merged`, nothing open."""
        return Snapshot(items=[
            Item(number=1, milestone="bolt/x", title="one", state="closed",
                 labels=frozenset({inbox.CLOSED_MERGED})),
            Item(number=2, milestone="bolt/x", title="two", state="closed",
                 labels=frozenset({inbox.CLOSED_MERGED})),
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
        # on an item; by then every work item is closed.
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


class LandingHoldTest(unittest.TestCase):
    """The landing is the bolt's boundary, and an open unit card holds it.

    A bolt lands once, for its milestone, however many units it carries —
    so the operator's unruled card is not a question about one unit, it is
    the bolt still being planned. Nothing here may reach main while one is
    open, and the run has to SAY so: the report line is what distinguishes
    a held bolt from a quiet one, and both used to read `not attempted`.
    """

    def card(self, number=12, status=inbox.STATUS_BACKLOG, milestone="bolt/x",
             stale=False):
        return inbox.PlanCard(number=number, title=f"Unit: u{number}",
                              status=status, milestone=milestone, stale=stale,
                              team="build")

    def merged(self, number, parent=None, milestone_state="closed"):
        """A work item that has reached the bolt branch — the state at the
        landing, once the merge boundary has closed every item.

        `milestone_state="closed"`, matching the fixtures elsewhere in this
        file: the operator's close is the landing's other release condition,
        and leaving it at the `"open"` default would make every test here
        decline the landing for the milestone rather than for the card.
        """
        return Item(number=number, milestone="bolt/x", title=f"item {number}",
                    state="closed", parent_batch=parent,
                    milestone_state=milestone_state,
                    labels=frozenset({inbox.CLOSED_MERGED}))

    def at_the_landing(self, cards=(), batches=()):
        """Every work item `closed:merged` and the operator's close made: the
        landing is otherwise wanted, so anything that declines it here is the
        card hold and nothing else."""
        return Snapshot(items=[self.merged(1), self.merged(2)],
                        batches=list(batches), plan_cards=list(cards),
                        milestone="bolt/x")

    def milestone_still_open(self, cards=(), batches=()):
        """The same tree, with the operator's close NOT yet made: every
        item merged, and the milestone the items carry still open."""
        return Snapshot(items=[self.merged(1, milestone_state="open"),
                               self.merged(2, milestone_state="open")],
                        batches=list(batches), plan_cards=list(cards),
                        milestone="bolt/x")

    def program(self, snapshot, ledger=None):
        shell = FakeShell({("git", "merge-base"): Result(0),
                           ("git", "rev-parse"): Result(0, "abc1234\n"),
                           ("git", "rev-list"): Result(0, "1\n")})
        tracker = FakeTracker(snapshot)
        runner = ScriptedRunner()
        program = a_loop(tracker, runner=runner, shell=shell, ledger=ledger)
        program.merge_criteria = lambda: "Landing: merge"
        return program, tracker, runner

    # -- the card set ------------------------------------------------------

    def test_an_open_card_at_backlog_is_in_the_holding_set(self):
        snapshot = self.at_the_landing(cards=[self.card()])
        program, _, _ = self.program(snapshot)
        self.assertEqual([c.number for c in program.holding_cards(snapshot)], [12],
                         "board Status is not read: an unruled card holds")

    def test_a_ready_card_not_yet_expanded_holds_it_too(self):
        # Deferred behind its predecessor, or approved after the last merge:
        # either way the operator has ruled and the unit is not built yet.
        snapshot = self.at_the_landing(
            cards=[self.card(status=inbox.STATUS_READY)])
        program, _, _ = self.program(snapshot)
        self.assertEqual([c.number for c in program.holding_cards(snapshot)], [12])

    def test_a_stale_card_holds_it_as_any_other_does(self):
        snapshot = self.at_the_landing(cards=[self.card(stale=True)])
        program, _, _ = self.program(snapshot)
        self.assertEqual([c.number for c in program.holding_cards(snapshot)], [12])

    def test_a_card_on_another_bolts_milestone_holds_nothing_here(self):
        snapshot = self.at_the_landing(cards=[self.card(milestone="bolt/other")])
        program, _, _ = self.program(snapshot)
        self.assertEqual(program.holding_cards(snapshot), [])

    def test_a_card_naming_no_bolt_milestone_holds_nothing(self):
        # `PlanCard.bolt` answers None, and a card no bolt owns is no bolt's
        # card to hold — it is the planner's to file.
        snapshot = self.at_the_landing(cards=[self.card(milestone=None)])
        program, _, _ = self.program(snapshot)
        self.assertEqual(program.holding_cards(snapshot), [])

    def test_an_expanded_unit_holds_nothing(self):
        # Expansion swaps `plan` for `unit`, so the card leaves `plan_cards`.
        # Reading an open unit as a card still open would make the hold
        # unsatisfiable: a unit stays open across the landing precisely so
        # the landing can close it.
        snapshot = self.at_the_landing(
            batches=[Batch(number=9, kind=inbox.UNIT, status=inbox.STATUS_READY,
                           sub_issues=(1, 2), milestone="bolt/x")])
        program, _, _ = self.program(snapshot)
        self.assertEqual(program.holding_cards(snapshot), [])

    # -- what the run does, and what it says -------------------------------

    def test_a_held_run_lands_nothing_and_says_so_by_card_number(self):
        snapshot = self.at_the_landing(cards=[self.card()])
        program, tracker, runner = self.program(snapshot)
        box = inbox.bolt_inbox(snapshot, "x")
        self.assertTrue(program.landing_wanted("auto", box, list(snapshot.items)),
                        "the landing is otherwise wanted; the card is the hold")
        report = program.run(max_cycles=1, land="auto")
        self.assertEqual(runner.launched, [], "no landing session runs")
        self.assertEqual([w for w in tracker.writes
                          if w[0] in ("close", "reclose")], [],
                         "nothing reaches main and nothing is upgraded")
        self.assertTrue(report.landing.startswith("held"), report.landing)
        self.assertIn("#12", report.landing)

    def test_a_forced_landing_is_held_by_the_same_card(self):
        # `force` is a claim about what this process knows, not a ruling on
        # the card. The way past an open card is to rule it.
        snapshot = self.at_the_landing(cards=[self.card()])
        program, tracker, runner = self.program(snapshot)
        report = program.run(max_cycles=1, land="force")
        self.assertEqual(runner.launched, [])
        self.assertTrue(report.landing.startswith("held"), report.landing)
        self.assertIn("#12", report.landing)

    def test_two_open_cards_are_both_named(self):
        snapshot = self.at_the_landing(cards=[self.card(12), self.card(13)])
        program, _, _ = self.program(snapshot)
        report = program.run(max_cycles=1, land="auto")
        self.assertIn("#12", report.landing)
        self.assertIn("#13", report.landing)

    def test_a_run_told_not_to_land_still_reports_the_hold(self):
        # The hold is not a branch of the landing question, it is asked
        # first: `land` says what this process meant to do, and the card
        # says what the bolt is waiting for.
        snapshot = self.at_the_landing(cards=[self.card()])
        program, tracker, runner = self.program(snapshot)
        report = program.run(max_cycles=1, land=False)
        self.assertTrue(report.landing.startswith("held"), report.landing)
        self.assertEqual(runner.launched, [])

    def test_a_hold_is_reported_while_released_work_is_still_in_flight(self):
        # Released work declines the landing on its own, so the two answers
        # coincide here — and the run that reports `not attempted` sends the
        # operator to watch the work when the standing question is the card.
        snapshot = Snapshot(items=[self.merged(1),
                                   item(2, inbox.READY)],
                            plan_cards=[self.card()], milestone="bolt/x")
        program, tracker, runner = self.program(snapshot)
        box = inbox.bolt_inbox(snapshot, "x")
        self.assertFalse(
            program.landing_wanted("force", box, list(snapshot.items)),
            "the landing is not otherwise wanted: the work is still running")
        report = program.run(max_cycles=1, land="force")
        self.assertTrue(report.landing.startswith("held"), report.landing)
        self.assertIn("#12", report.landing)

    def test_a_held_run_keeps_its_note_and_still_renders_its_report(self):
        # The run record is not skipped because the run held: the note names
        # the cards, and the observation report is written as on any pass.
        with tempfile.TemporaryDirectory() as tmp:
            led = obs.RunLedger(tmp, "bolt-x", gate_mode="courtesy")
            snapshot = self.at_the_landing(cards=[self.card()])
            program, _, _ = self.program(snapshot, ledger=led)
            program.run(max_cycles=1, land="auto")
            written = next((Path(tmp) / "bolt-x").glob("*.report.md")).read_text()
            self.assertIn("landing held", written)
            self.assertIn("#12", written)

    def test_both_readers_of_a_run_carry_the_held_line(self):
        """The printed report and the `--json` both read `report.landing`,
        and a held run is legible in each. Loaded by path: the commands are
        extensionless on purpose, `bin/` being on an installed user's PATH.
        """
        snapshot = self.at_the_landing(cards=[self.card()])
        program, _, _ = self.program(snapshot)
        report = program.run(max_cycles=1, land="auto")
        loader = importlib.machinery.SourceFileLoader(
            "flywheel_bolt_loop_cli", str(BIN / "flywheel-bolt-loop"))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        cli = importlib.util.module_from_spec(spec)
        loader.exec_module(cli)
        printed = cli.render(report, program.params)
        self.assertIn(f"landing: {report.landing}", printed)
        self.assertIn("#12", printed)
        self.assertEqual(cli.as_dict(report)["landing"], report.landing)
        self.assertNotIn("not attempted", printed)

    def test_a_run_with_nothing_to_land_still_reads_not_attempted(self):
        # The other half of the distinction: `not attempted` is reserved for
        # a run that never had a landing to reach for, and stays reserved.
        program, _, runner = self.program(Snapshot(milestone="bolt/x"))
        report = program.run(max_cycles=1, land="auto")
        self.assertEqual(report.landing, "not attempted")
        self.assertEqual(runner.launched, [])

    def test_the_last_card_ruled_lets_the_landing_run(self):
        # The operator closed the card they declined, or approved it and the
        # loop expanded it: either way no open `plan` card remains, and the
        # landing proceeds under its existing preconditions.
        snapshot = self.at_the_landing(
            batches=[Batch(number=9, kind=inbox.UNIT, status=inbox.STATUS_READY,
                           sub_issues=(1, 2), milestone="bolt/x")])
        program, tracker, _ = self.program(snapshot)
        report = program.run(max_cycles=1, land="auto")
        self.assertTrue(report.landing.startswith("done"), report.landing)
        self.assertEqual([w[1] for w in tracker.writes if w[0] == "close"], [9])

    # -- the operator's close ----------------------------------------------
    #
    # The landing's OTHER release condition, specified alongside the card
    # hold by `flywheel-construction-stages`, "The operator's milestone
    # close releases the landing, and the card hold is asked first".
    # Neither condition subsumes the other, and every other fixture in this
    # class carries the close made — so without these three the branch that
    # reads the milestone state has no positive coverage at all.

    def test_an_open_milestone_declines_an_automatic_landing(self):
        # Every work item merged and every card ruled: necessary, never
        # sufficient. Merged work does not reach main on the machinery's own
        # initiative — the operator's close is the release gesture.
        snapshot = self.milestone_still_open()
        program, tracker, runner = self.program(snapshot)
        box = inbox.bolt_inbox(snapshot, "x")
        unlanded = [i for i in snapshot.items if i.is_open or i.merge_closed]
        self.assertEqual(program.holding_cards(snapshot), [],
                         "no card holds: the milestone is the only condition left")
        self.assertFalse(program.landing_wanted("auto", box, unlanded),
                         "the milestone is open; the landing is not released")
        report = program.run(max_cycles=1, land="auto")
        self.assertEqual(runner.launched, [], "no landing session runs")
        self.assertEqual([w for w in tracker.writes
                          if w[0] in ("close", "reclose")], [],
                         "nothing reaches main and nothing is upgraded")
        self.assertFalse(report.landing.startswith("done"), report.landing)

    def test_a_forced_landing_passes_the_open_milestone(self):
        # The asymmetry between the two conditions: a force is a claim about
        # what this process knows — the operator landing deliberately, or the
        # server resuming a run that died before its landing — so the close it
        # stands in for is being made by that same hand. Its other half, that
        # a force does NOT pass the card hold, is
        # `test_a_forced_landing_is_held_by_the_same_card` above.
        snapshot = self.milestone_still_open(
            batches=[Batch(number=9, kind=inbox.UNIT, status=inbox.STATUS_READY,
                           sub_issues=(1, 2), milestone="bolt/x")])
        program, tracker, _ = self.program(snapshot)
        report = program.run(max_cycles=1, land="force")
        self.assertTrue(report.landing.startswith("done"), report.landing)
        self.assertEqual([w[1] for w in tracker.writes if w[0] == "close"], [9])

    def test_both_conditions_outstanding_reports_the_card_not_the_milestone(self):
        # The card hold is asked first and its answer is final: the card is
        # the gesture the operator can act on next, and the more specific
        # fact. So the line names the card — never the milestone, and never
        # `not attempted`, which would send them to watch work that is done.
        snapshot = self.milestone_still_open(cards=[self.card()])
        program, tracker, runner = self.program(snapshot)
        report = program.run(max_cycles=1, land="auto")
        self.assertTrue(report.landing.startswith("held"), report.landing)
        self.assertIn("#12", report.landing)
        self.assertNotIn("milestone", report.landing)
        self.assertEqual(runner.launched, [])

    # -- the boundary ------------------------------------------------------

    def test_a_second_unit_expanded_later_does_not_buy_a_second_landing(self):
        """The bolt lands once, after the second unit's work merges too.

        Expansion takes the card out of the holding set, so the hold is not
        what declines the landing here — the released work is, exactly as it
        would for the first unit. Then one landing serves both.
        """
        running = Snapshot(
            items=[self.merged(1, parent=9), self.merged(2, parent=9),
                   item(3, inbox.READY, parent_batch=10,
                        milestone_state="closed"),
                   item(4, inbox.READY, parent_batch=10,
                        milestone_state="closed")],
            batches=[Batch(number=9, kind=inbox.UNIT, status=inbox.STATUS_READY,
                           sub_issues=(1, 2), milestone="bolt/x"),
                     Batch(number=10, kind=inbox.UNIT, status=inbox.STATUS_READY,
                           sub_issues=(3, 4), milestone="bolt/x")],
            milestone="bolt/x")
        program, _, _ = self.program(running)
        self.assertEqual(program.holding_cards(running), [],
                         "the second card became a unit; it holds nothing")
        box = inbox.bolt_inbox(running, "x")
        unlanded = [i for i in running.items if i.is_open or i.merge_closed]
        self.assertFalse(program.landing_wanted("force", box, unlanded),
                         "the second unit's items are released work")

        landed = Snapshot(
            items=[self.merged(n, parent=9 if n in (1, 2) else 10)
                   for n in (1, 2, 3, 4)],
            batches=list(running.batches), milestone="bolt/x")
        program, tracker, _ = self.program(landed)
        report = program.run(max_cycles=1, land="auto")
        self.assertTrue(report.landing.startswith("done"), report.landing)
        self.assertEqual([w[1] for w in tracker.writes if w[0] == "close"], [9, 10],
                         "one landing, both units closed")


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

    def test_the_merge_boundary_closes_work_items_with_closed_merged(self):
        tracker = FakeTracker()
        program = a_loop(tracker, shell=self.shell())
        program.close_merged([
            item(1, inbox.IN_PROGRESS),
            item(2, inbox.IN_PROGRESS)])
        self.assertEqual(tracker.reasons, [(1, inbox.CLOSED_MERGED),
                                           (2, inbox.CLOSED_MERGED)])
        self.assertTrue(all("abc1234" in w[2] for w in tracker.writes
                            if w[0] == "close"))

    def test_every_work_item_closes_whatever_labels_it_carries(self):
        # Expansion-born items carry no type label; no carve-out exempts an
        # item from its merge close.
        tracker = FakeTracker()
        program = a_loop(tracker, shell=self.shell())
        program.close_merged([
            item(1, inbox.IN_PROGRESS),
            item(5, inbox.IN_PROGRESS, title="an expansion-born item")])
        self.assertEqual(sorted(n for n, _ in tracker.reasons), [1, 5])

    def test_a_full_cycle_merges_and_closes_in_one_go(self):
        snapshot = Snapshot(items=[item(1, inbox.READY,
                                        change="add-thing")],
                            milestone="bolt/x")
        tracker = FakeTracker(snapshot, comments={1: [{"body": "built it"}]})
        runner = ScriptedRunner(states=[WaitState.SETTLED_DONE] * 12,
                                reports=["No findings."] * 12)
        # Ancestry must FLIP when the wt merge subprocess runs: a branch
        # that reads merged from the start is parked awaiting the landing
        # by the resume partition and never drives at all.
        class MergeAwareShell(FakeShell):
            def __call__(self, argv, cwd=None, env=None, timeout=None):
                if tuple(argv[:2]) == ("git", "merge-base"):
                    self.calls.append((tuple(argv), cwd))
                    merged = any(a[:2] == ("wt", "merge")
                                 for a, _ in self.calls)
                    return Result(0 if merged else 1)
                return super().__call__(argv, cwd=cwd, env=env, timeout=timeout)
        shell = MergeAwareShell({("git", "rev-list"): Result(0, "3\n"),
                                 ("git", "rev-parse"): Result(0, "abc1234\n")})
        a_loop(tracker, runner=runner, shell=shell).cycle(1)
        self.assertIn(inbox.STAGE_MERGED, tracker.labels[1])
        self.assertIn(inbox.CLOSED_MERGED, tracker.labels[1])

    # -- the landing's upgrade ---------------------------------------------

    def merged_snapshot(self):
        # milestone_state closed: the operator's close released the landing.
        return Snapshot(items=[
            Item(number=1, milestone="bolt/x", milestone_state="closed",
                 title="one", state="closed",
                 labels=frozenset({inbox.CLOSED_MERGED})),
            Item(number=2, milestone="bolt/x", milestone_state="closed",
                 title="two", state="closed",
                 labels=frozenset({inbox.CLOSED_MERGED})),
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
        snapshot = Snapshot(items=[item(1, 
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
        snapshot = Snapshot(items=[item(1, 
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
                 labels=frozenset({inbox.CLOSED_MERGED}))],
            milestone="bolt/x")
        tracker, actions = self.reconcile(
            snapshot, seed={1: {inbox.CLOSED_MERGED}})
        self.assertIn(("add_label", 1, inbox.STAGE_MERGED), tracker.writes)
        self.assertEqual(tracker.reasons, [], "already closed; not closed again")

    def test_a_landed_item_is_never_walked_back(self):
        snapshot = Snapshot(items=[
            Item(number=1, milestone="bolt/x", title="one", state="closed",
                 change="add-thing",
                 labels=frozenset({inbox.CLOSED_DONE,
                                   inbox.STAGE_MERGED}))],
            milestone="bolt/x")
        tracker, actions = self.reconcile(snapshot)
        self.assertEqual(tracker.writes, [], "the landing is downstream of merge")
        self.assertEqual(actions, [])

    def test_the_dry_cycle_holds_with_merged_closed_items_on_the_milestone(self):
        snapshot = Snapshot(items=[
            Item(number=1, milestone="bolt/x", title="one", state="closed",
                 change="add-thing",
                 labels=frozenset({inbox.CLOSED_MERGED,
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
        reads = ("has_label", "closed_with", "closed", "comments", "snapshot")
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
# The charter the scaffold writes, and the landing that reads it
# ---------------------------------------------------------------------------

#: A charter of the shape the schema template names: the bolt's four
#: sections, the `Landing:` line stated, and nothing else yet.
CHARTER = """# Bolt: x

## Scope
What this bolt builds, one paragraph.

## Sources
- loop-boundaries — handoff task: carve the loop's boundaries

## Repos
- flywheel · bolt branch `bolt/x`

## Merge criteria
Acceptance suites green on the bolt branch; merge gate always.
Landing: merge
"""

#: The same charter a planner-born bolt used to get: one unit's plan
#: document under its heading, and not one bolt-level section.
UNIT_ONLY = """# Unit: u1

The unit's plan document, which is not the bolt's charter.

## Left out

Something this unit does not do.
"""


class SettlingScaffold(ScriptedRunner):
    """A scaffold session that leaves behind the charter it was handed.

    The loop reads the tree, never the report, so what this writes at
    launch time IS this session's whole deliverable. `charter=None` is the
    session that made the directory and wrote no charter at all.
    """

    def __init__(self, change_dir, charter=CHARTER, **kw):
        super().__init__(**kw)
        self.change_dir = Path(change_dir)
        self.charter = charter

    def launch(self, spec):
        self.change_dir.mkdir(parents=True, exist_ok=True)
        if self.charter is not None:
            (self.change_dir / "bolt.md").write_text(self.charter)
        return super().launch(spec)


class ScaffoldCharterTest(unittest.TestCase):
    """Guard 0 asks for a charter, and checks that one came back.

    The order used to name one thing to write — the lowest-numbered unit's
    plan document — so a planner-born bolt got a charter with no bolt-level
    sections at all, and both readers of `## Merge criteria` then read
    nothing.
    """

    def loop_over(self, tmp, runner=None, description="", dry_run=False):
        program = a_loop(FakeTracker(), runner=runner or ScriptedRunner(),
                         repo_dir=str(tmp), bolt_worktree=str(tmp),
                         description=description)
        program.dry_run = dry_run
        return program

    def change_dir(self, tmp):
        return Path(tmp) / "openspec" / "changes" / "x"

    # -- what the order says (5.1) ----------------------------------------

    def test_the_order_names_the_four_sections_and_carries_the_description(self):
        with tempfile.TemporaryDirectory() as tmp:
            runner = ScriptedRunner()
            program = self.loop_over(
                tmp, runner=runner,
                description="Carve the loop's boundaries. Three units, ~9 items.")
            program.guard_scaffold([])
            order = runner.launched[0].order
            for heading in loop.BoltLoop.CHARTER_SECTIONS:
                self.assertIn(heading, order, heading)
            self.assertIn("Landing: merge", order)
            self.assertIn("Landing: pr", order)
            self.assertIn("openspec instructions bolt --change x", order,
                          "the template stays the authority for the content")
            self.assertIn("Carve the loop's boundaries. Three units, ~9 items.",
                          order, "the description is the charter's stated source")
            self.assertIn("units/<slug>.md", order,
                          "and the unit files are named as the loop's own")

    def test_a_milestone_with_no_description_still_gets_all_four_sections(self):
        # An absent description is a thinner charter, never a missing one.
        with tempfile.TemporaryDirectory() as tmp:
            runner = ScriptedRunner()
            program = self.loop_over(tmp, runner=runner, description="")
            program.guard_scaffold([])
            order = runner.launched[0].order
            for heading in loop.BoltLoop.CHARTER_SECTIONS:
                self.assertIn(heading, order, heading)
            self.assertIn("carries no description", order)
            self.assertIn("what the milestone and its items say", order)

    def test_no_order_asks_for_a_unit_document_in_the_charter(self):
        # 4.1: the record splits, so the four sections are the whole
        # charter whether or not the milestone carries unit cards. An
        # order that still asked for the copy would put a unit's `##`
        # subsections back in the file the criteria reader reads.
        with tempfile.TemporaryDirectory() as tmp:
            for description in ("Three units, ~9 items.", ""):
                runner = ScriptedRunner()
                self.loop_over(tmp, runner=runner,
                               description=description).guard_scaffold([])
                order = runner.launched[0].order
                self.assertNotIn("# Unit:", order, description or "(none)")
                self.assertNotIn("LOWEST-NUMBERED", order)
                self.assertNotIn("verbatim", order)
                self.assertIn("No unit's plan document goes into bolt.md",
                              order)

    def test_the_order_never_inlines_the_schema_template(self):
        # `design.md`: a second copy of the template in the loop program
        # would drift the first time a schema version moved.
        with tempfile.TemporaryDirectory() as tmp:
            runner = ScriptedRunner()
            self.loop_over(tmp, runner=runner).guard_scaffold([])
            order = runner.launched[0].order
            template = (ROOT / "schemas" / "bolt-default" / "templates" / "bolt.md")
            if template.exists():
                body = [l for l in template.read_text().splitlines()
                        if l.startswith("[")]
                for line in body:
                    self.assertNotIn(line, order)

    # -- what the guard does with what came back (5.2) --------------------

    def test_a_unit_only_charter_fails_the_guard_by_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            runner = SettlingScaffold(self.change_dir(tmp), charter=UNIT_ONLY)
            program = self.loop_over(tmp, runner=runner)
            actions = []
            failure = program.guard_scaffold(actions)
            self.assertIsNotNone(failure, "a settle is no longer the whole test")
            self.assertIn("openspec/changes/x/bolt.md", failure)
            self.assertIn("## Merge criteria", failure)
            self.assertIn("## Scope", failure)
            self.assertEqual(actions, [],
                             "a charter that fails records no scaffold action")

    def test_an_empty_merge_criteria_section_fails_it_too(self):
        # Four headings and no body under the one with readers is the
        # failure mode the risk section named.
        charter = "# Bolt: x\n\n## Scope\ns\n\n## Merge criteria\n\n# Unit: u1\n\np\n"
        with tempfile.TemporaryDirectory() as tmp:
            runner = SettlingScaffold(self.change_dir(tmp), charter=charter)
            program = self.loop_over(tmp, runner=runner)
            self.assertIsNotNone(program.guard_scaffold([]))

    def test_a_session_that_wrote_no_charter_at_all_fails_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            runner = SettlingScaffold(self.change_dir(tmp), charter=None)
            program = self.loop_over(tmp, runner=runner)
            failure = program.guard_scaffold([])
            self.assertIsNotNone(failure)
            self.assertIn("openspec/changes/x/bolt.md", failure)

    def test_a_charter_with_merge_criteria_passes_and_records_its_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            runner = SettlingScaffold(self.change_dir(tmp))
            program = self.loop_over(tmp, runner=runner)
            actions = []
            self.assertIsNone(program.guard_scaffold(actions))
            self.assertEqual(actions, ["scaffolded openspec/changes/x"])

    def test_the_check_is_the_landings_own_reader(self):
        # Not a second regex: "the guard passed" and "the landing can read
        # it" must be the same question, asked once.
        with tempfile.TemporaryDirectory() as tmp:
            runner = SettlingScaffold(self.change_dir(tmp))
            program = self.loop_over(tmp, runner=runner)
            seen = []
            real = program.merge_criteria
            program.merge_criteria = lambda: seen.append(1) or real()
            program.guard_scaffold([])
            self.assertEqual(len(seen), 1, "merge_criteria() is what was asked")

    # -- the charter is the test, not the directory (5.3) -----------------

    def test_the_charter_is_the_test_not_the_directory(self):
        # The distinction that used to collapse, asserted as the pair it
        # is: a change directory carrying no `bolt.md` is a charterless
        # record and gets a session; the same directory carrying one is
        # done and gets none.
        with tempfile.TemporaryDirectory() as tmp:
            self.change_dir(tmp).mkdir(parents=True)
            runner = SettlingScaffold(self.change_dir(tmp))
            program = self.loop_over(tmp, runner=runner)
            self.assertIsNone(program.guard_scaffold([]))
            self.assertEqual(len(runner.launched), 1,
                             "a directory without a charter is owed one")
        with tempfile.TemporaryDirectory() as tmp:
            self.change_dir(tmp).mkdir(parents=True)
            (self.change_dir(tmp) / "bolt.md").write_text(CHARTER)
            runner = ScriptedRunner()
            program = self.loop_over(tmp, runner=runner)
            actions = []
            self.assertIsNone(program.guard_scaffold(actions))
            self.assertEqual(runner.launched, [])
            self.assertEqual(actions, [])

    def test_a_charterless_change_directory_is_continued_not_created(self):
        # `/opsx:new` cannot be obeyed on a change that exists — its own
        # guardrail says to continue instead — and a session that cannot
        # obey its order writes nothing while reading as settled.
        with tempfile.TemporaryDirectory() as tmp:
            self.change_dir(tmp).mkdir(parents=True)
            runner = SettlingScaffold(self.change_dir(tmp))
            program = self.loop_over(
                tmp, runner=runner,
                description="Carve the loop's boundaries. Three units, ~9 items.")
            actions = []
            self.assertIsNone(program.guard_scaffold(actions))
            order = runner.launched[0].order
            self.assertTrue(order.startswith("/opsx:continue x"),
                            "the invocation adds the missing artifact")
            self.assertNotIn("/opsx:new x", order)
            self.assertNotIn("/opsx:ff", order)
            for heading in loop.BoltLoop.CHARTER_SECTIONS:
                self.assertIn(heading, order, heading)
            self.assertIn("Landing: merge", order)
            self.assertIn("openspec instructions bolt --change x", order)
            self.assertIn("Carve the loop's boundaries. Three units, ~9 items.",
                          order, "the description is the charter's stated source")
            self.assertIn("No unit's plan document goes into bolt.md", order)
            self.assertIn("Commit by pathspec", order)
            self.assertIn("Deliver by settling", order)
            self.assertIn(program.params.type_name, order,
                          "the order names the schema the change is bound to")
            self.assertIn("confirm the binding", order)
            self.assertEqual(actions,
                             ["wrote the charter into openspec/changes/x"])

    def test_both_paths_drive_the_same_session_name(self):
        # The session id derives from the name and cwd, so a charterless
        # record found on a later pass resumes the warm scaffold
        # conversation rather than opening a cold second one.
        names = []
        for pre_made in (False, True):
            with tempfile.TemporaryDirectory() as tmp:
                if pre_made:
                    self.change_dir(tmp).mkdir(parents=True)
                runner = SettlingScaffold(self.change_dir(tmp))
                self.loop_over(tmp, runner=runner).guard_scaffold([])
                names.append(runner.launched[0].name)
        self.assertEqual(names[0], names[1])

    def test_the_two_orders_carry_the_same_charter_text(self):
        # One expression in the program, so the charter a record gets does
        # not depend on which path wrote it. Only the framing and the
        # invocation above it differ.
        marker = "bolt.md is the BOLT'S CHARTER"
        charters, orders = [], []
        for pre_made in (False, True):
            with tempfile.TemporaryDirectory() as tmp:
                if pre_made:
                    self.change_dir(tmp).mkdir(parents=True)
                runner = SettlingScaffold(self.change_dir(tmp))
                self.loop_over(tmp, runner=runner,
                               description="Three units, ~9 items.").guard_scaffold([])
                order = runner.launched[0].order
                self.assertIn(marker, order)
                orders.append(order)
                charters.append(order[order.index(marker):])
        self.assertEqual(charters[0], charters[1],
                         "one charter text, two invocations")
        self.assertNotEqual(orders[0], orders[1], "the framing does differ")
        for order in orders:
            for heading in loop.BoltLoop.CHARTER_SECTIONS:
                self.assertIn(heading, order, heading)
            self.assertIn("Three units, ~9 items.", order)

    def test_the_post_settle_reason_is_one_string_whichever_path_drove_it(self):
        # A charter written into an existing change is held to exactly
        # what a charter written with its directory is held to.
        def failure_from(pre_made, charter):
            with tempfile.TemporaryDirectory() as tmp:
                if pre_made:
                    self.change_dir(tmp).mkdir(parents=True)
                runner = SettlingScaffold(self.change_dir(tmp), charter=charter)
                program = self.loop_over(tmp, runner=runner)
                actions = []
                failure = program.guard_scaffold(actions)
                self.assertEqual(actions, [],
                                 "a charter that fails records no action")
                return failure

        creating = failure_from(False, None)
        continuing = failure_from(True, None)
        self.assertIsNotNone(continuing, "the check runs on both paths")
        self.assertEqual(creating, continuing)
        self.assertIn("openspec/changes/x/bolt.md", continuing)
        self.assertIn("## Merge criteria", continuing)
        self.assertIn("## Scope", continuing)
        bodyless = failure_from(
            True, "# Bolt: x\n\n## Scope\ns\n\n## Merge criteria\n\n")
        self.assertEqual(bodyless, continuing)

    # -- the dry-cycle property (3.3) -------------------------------------

    def test_a_present_charter_with_no_readable_criteria_is_left_alone(self):
        # A charter that has lost its sections, or never carried them, is
        # the landing's refusal to make. A guard that repaired it would be
        # a second writer over committed prose.
        with tempfile.TemporaryDirectory() as tmp:
            self.change_dir(tmp).mkdir(parents=True)
            (self.change_dir(tmp) / "bolt.md").write_text(UNIT_ONLY)
            runner = ScriptedRunner()
            program = self.loop_over(tmp, runner=runner)
            actions = []
            self.assertIsNone(program.guard_scaffold(actions))
            self.assertEqual(runner.launched, [])
            self.assertEqual(actions, [])
            self.assertEqual(program.merge_criteria(), "",
                             "and it still reads back nothing")
            self.assertEqual((self.change_dir(tmp) / "bolt.md").read_text(),
                             UNIT_ONLY, "left exactly as it stands")

    def test_dry_run_over_a_charterless_change_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.change_dir(tmp).mkdir(parents=True)
            runner = ScriptedRunner()
            program = self.loop_over(tmp, runner=runner, dry_run=True)
            actions = []
            self.assertIsNone(program.guard_scaffold(actions))
            self.assertEqual(runner.launched, [])
            self.assertEqual(len(actions), 1)
            self.assertIn("charter", actions[0])
            self.assertIn("openspec/changes/x", actions[0])
            self.assertFalse((self.change_dir(tmp) / "bolt.md").exists(),
                             "and the tree is untouched")

    def test_dry_run_still_only_reports_what_it_would_scaffold(self):
        with tempfile.TemporaryDirectory() as tmp:
            runner = ScriptedRunner()
            program = self.loop_over(tmp, runner=runner, dry_run=True)
            actions = []
            self.assertIsNone(program.guard_scaffold(actions))
            self.assertEqual(runner.launched, [])
            self.assertEqual(len(actions), 1)
            self.assertIn("would scaffold openspec/changes/x", actions[0])


class BoltParamsDescriptionTest(unittest.TestCase):
    """The planner's summary reaches the session that writes the charter.

    `build_loop` already read the milestone's description — for the
    plan-mode flag, and for nothing else. It stopped there, so no guard
    could see the value the book names as the charter's source.
    """

    def cli(self):
        """`bin/flywheel-bolt-loop`, loaded by path: the commands are
        extensionless on purpose, `bin/` being on an installed user's PATH.

        Its `loop` attribute IS the module this file imported, so anything
        replaced on it is replaced everywhere — hence the cleanups.
        """
        loader = importlib.machinery.SourceFileLoader(
            "flywheel_bolt_loop_cli", str(BIN / "flywheel-bolt-loop"))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        module.resolve_token = lambda org: "token"
        return module

    def patch(self, obj, name, value):
        had = hasattr(obj, name)
        old = getattr(obj, name, None)
        setattr(obj, name, value)
        self.addCleanup(lambda: setattr(obj, name, old) if had
                        else delattr(obj, name))

    def tracker_answering(self, cli, milestone):
        answered = []

        class Tracker:
            def __init__(self, *args, **kwargs):
                pass

            def milestone(self, name):
                answered.append(name)
                return milestone

        self.patch(cli.loop, "BoltTracker", Tracker)
        return answered

    def built(self, cli, argv=()):
        return cli.build_loop(cli.parse_args(
            ["--slug", "x", "--type", "bolt-quick", "--repo-dir", str(ROOT),
             *argv]))[1]

    def test_a_loop_built_from_a_milestone_holds_its_description(self):
        cli = self.cli()
        described = "Carve the loop's boundaries. Three units, ~9 items."
        asked = self.tracker_answering(
            cli, {"title": "bolt/x", "description": described})
        params = self.built(cli)
        self.assertEqual(asked, ["bolt/x"], "read once, at the entry point")
        self.assertEqual(params.description, described)

    def test_a_milestone_with_no_description_holds_the_empty_string(self):
        cli = self.cli()
        self.tracker_answering(cli, {"title": "bolt/x"})
        self.assertEqual(self.built(cli).description, "")

    def test_a_fixture_run_holds_the_empty_string(self):
        # `FixtureTracker.milestone()` answers a stub with no description,
        # so a fixture takes the "milestone carries no description" path
        # the spec already covers rather than failing differently.
        cli = self.cli()
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "bolt-tracker.json"
            fixture.write_text(json.dumps({"items": []}))
            params = self.built(cli, ["--fixture", str(fixture), "--dry-run"])
        self.assertEqual(params.description, "")

    def test_the_milestone_description_carries_no_mode(self):
        # Mode moved to the unit card; the description is human prose the
        # charter is written from, and nothing machine-read lives on it.
        cli = self.cli()
        self.tracker_answering(cli, {"description": "Mode: plan"})
        params = self.built(cli)
        self.assertEqual(params.description, "Mode: plan",
                         "carried as prose only — the launch reads no mode "
                         "from the milestone; the unit's type decides")


class LandingCharterTest(unittest.TestCase):
    """The landing's charter refusal, reached through the REAL reader.

    Every other landing test in this file stubs `merge_criteria`; these
    write a charter into a temporary worktree and let `land_stage` read it,
    because what that reader answers is precisely the thing under test.
    """

    def merged(self, number):
        return Item(number=number, milestone="bolt/x", title=f"item {number}",
                    state="closed", milestone_state="closed",
                    labels=frozenset({inbox.CLOSED_MERGED}))

    def snapshot(self):
        return Snapshot(items=[item(1, inbox.IN_PROGRESS),
                               item(2, inbox.IN_PROGRESS)],
                        milestone="bolt/x")

    def at_the_landing(self):
        """Every work item merge-closed and the operator's close made, so
        the landing is otherwise wanted and only the charter can refuse."""
        return Snapshot(items=[self.merged(1), self.merged(2)],
                        milestone="bolt/x")

    def program(self, tmp, charter, snapshot=None):
        change = Path(tmp) / "openspec" / "changes" / "x"
        change.mkdir(parents=True, exist_ok=True)
        if charter is not None:
            (change / "bolt.md").write_text(charter)
        shell = FakeShell({("git", "merge-base"): Result(0),
                           ("git", "rev-parse"): Result(0, "abc1234\n"),
                           ("git", "rev-list"): Result(0, "1\n"),
                           ("wt", "list"): Result(0, json.dumps(
                               [{"branch": "bolt/x", "path": str(tmp)}]))})
        tracker = FakeTracker(snapshot or self.snapshot())
        runner = ScriptedRunner()
        program = a_loop(tracker, runner=runner, shell=shell,
                         repo_dir=str(tmp), bolt_worktree=str(tmp))
        return program, tracker, runner

    def refused(self, tmp, charter):
        program, tracker, runner = self.program(tmp, charter)
        outcome = program.land_stage(self.snapshot())
        self.assertEqual(outcome.status, "failed", outcome.detail)
        self.assertIn("openspec/changes/x/bolt.md", outcome.detail)
        self.assertIn("merge criteria could not be read", outcome.detail)
        self.assertEqual(runner.launched, [], "no landing session is driven")
        self.assertEqual([w for w in tracker.writes
                          if w[0] in ("close", "reclose")], [],
                         "nothing closed and nothing upgraded")
        self.assertEqual([n for n, l in tracker.labels.items()
                          if inbox.NEEDS_OPERATOR in l], [],
                         "a refusal is not a pause: no item waits on anyone")
        return outcome

    # -- the three empty cases (5.3) --------------------------------------

    def test_a_charter_with_no_merge_criteria_section_refuses_the_landing(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.refused(tmp, UNIT_ONLY)

    def test_an_empty_merge_criteria_section_refuses_it_the_same_way(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.refused(tmp, "# Bolt: x\n\n## Merge criteria\n\n# Unit: u1\n\np\n")

    def test_a_change_directory_with_no_bolt_md_refuses_it_too(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.refused(tmp, None)

    def test_a_charter_that_states_its_criteria_lands_as_before(self):
        with tempfile.TemporaryDirectory() as tmp:
            program, tracker, runner = self.program(tmp, CHARTER)
            outcome = program.land_stage(self.snapshot())
            self.assertEqual(outcome.status, "done", outcome.detail)
            self.assertEqual([w[1] for w in tracker.writes if w[0] == "reclose"],
                             [1, 2])

    def test_the_refusal_comes_before_the_work_less_branch_refusal(self):
        # Order matters only in what it says: a bolt that is both
        # charterless and empty is told about its charter, which is the
        # one an operator can act on.
        with tempfile.TemporaryDirectory() as tmp:
            program, _, _ = self.program(tmp, UNIT_ONLY)
            program.branch_advanced = lambda branch: False
            self.assertIn("merge criteria could not be read",
                          program.land_stage(self.snapshot()).detail)

    def test_a_live_wait_still_pauses_ahead_of_the_charter_refusal(self):
        # The charter refusal joins the existing two; it does not displace
        # the live wait, which is a standing question about an item.
        snap = Snapshot(items=[item(1, inbox.IN_PROGRESS,
                                    inbox.NEEDS_OPERATOR)],
                        milestone="bolt/x")
        with tempfile.TemporaryDirectory() as tmp:
            program, _, _ = self.program(tmp, UNIT_ONLY, snapshot=snap)
            outcome = program.land_stage(snap)
            self.assertEqual(outcome.status, "paused")
            self.assertIn("#1", outcome.detail)

    # -- a forced landing does not pass it (4.2) --------------------------

    def test_a_forced_landing_over_an_unreadable_charter_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            program, tracker, runner = self.program(
                tmp, UNIT_ONLY, snapshot=self.at_the_landing())
            report = program.run(max_cycles=1, land="force")
            self.assertTrue(report.landing.startswith("failed"), report.landing)
            self.assertIn("openspec/changes/x/bolt.md", report.landing)
            self.assertEqual(runner.launched, [])
            self.assertEqual([w for w in tracker.writes
                              if w[0] in ("close", "reclose")], [])

    def test_a_forced_landing_over_a_charter_with_criteria_still_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            program, tracker, runner = self.program(
                tmp, CHARTER, snapshot=self.at_the_landing())
            report = program.run(max_cycles=1, land="force")
            self.assertTrue(report.landing.startswith("done"), report.landing)
            self.assertEqual([w[1] for w in tracker.writes if w[0] == "reclose"],
                             [1, 2])

    # -- and the run says so (4.3) ----------------------------------------

    def test_both_readers_of_a_run_carry_the_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            program, _, _ = self.program(tmp, UNIT_ONLY,
                                         snapshot=self.at_the_landing())
            report = program.run(max_cycles=1, land="force")
            loader = importlib.machinery.SourceFileLoader(
                "flywheel_bolt_loop_cli", str(BIN / "flywheel-bolt-loop"))
            spec = importlib.util.spec_from_loader(loader.name, loader)
            cli = importlib.util.module_from_spec(spec)
            loader.exec_module(cli)
            printed = cli.render(report, program.params)
            self.assertIn(f"landing: {report.landing}", printed)
            self.assertIn("bolt.md", printed)
            self.assertEqual(cli.as_dict(report)["landing"], report.landing)
            self.assertNotIn("not attempted", printed)


class BoltSchemaArtifactTest(unittest.TestCase):
    """The four `bolt-*` schemas declare the record's two artifacts.

    The record's shape is not a function of the type, so all four members
    say the same thing about it: `bolt` → the charter, `unit` →
    `units/<slug>.md`. And the `bolt` instruction stops at the charter's
    four sections — it used to say "EXACTLY these four sections, and
    nothing else" and then name a fifth thing to append, which teaches the
    opposite of what it states.

    Read as text: the repo ships no YAML parser and the loop's own reader
    takes the `loop:` block alone, so these assert the file rather than a
    parse of it.
    """

    MEMBERS = ("bolt-default", "bolt-quick", "bolt-adversarial", "bolt-direct")

    def schema(self, member):
        return (ROOT / "schemas" / member / "schema.yaml").read_text()

    def instruction(self, member, artifact):
        """One artifact's block, from its `- id:` to the next one."""
        text = self.schema(member)
        start = text.index(f"  - id: {artifact}\n")
        rest = text[start + 1:]
        after = rest.find("\n  - id: ")
        tail = rest.find("\napply:\n")
        end = min(x for x in (after, tail, len(rest)) if x >= 0)
        return rest[:end]

    def test_every_member_declares_both_artifacts(self):
        for member in self.MEMBERS:
            text = self.schema(member)
            self.assertIn("  - id: bolt\n", text, member)
            self.assertIn("    generates: bolt.md\n", text, member)
            self.assertIn("  - id: unit\n", text, member)
            self.assertIn("    generates: units/<slug>.md\n", text, member)

    def test_every_member_ships_the_unit_template(self):
        # openspec requires a `template:` per artifact and refuses the
        # schema without one, so the declaration is not complete until the
        # file it names is on disk in that member.
        for member in self.MEMBERS:
            self.assertIn("    template: units/unit.md\n",
                          self.instruction(member, "unit"), member)
            self.assertTrue(
                (ROOT / "schemas" / member / "templates" / "units"
                 / "unit.md").is_file(), member)

    def test_the_unit_instruction_says_copied_not_composed(self):
        for member in self.MEMBERS:
            unit = self.instruction(member, "unit")
            self.assertIn("verbatim", unit, member)
            self.assertIn("expansion", unit, member)
            self.assertIn("not yours to compose", unit, member)
            self.assertIn("not yours to edit", unit, member)

    def test_no_bolt_instruction_directs_a_unit_document_into_the_charter(self):
        # The scenario is literally "no member contradicts itself".
        for member in self.MEMBERS:
            bolt_block = self.instruction(member, "bolt")
            self.assertIn("EXACTLY these four sections", bolt_block, member)
            for forbidden in ("What follows those four sections",
                              "# Unit:", "lowest-numbered unit"):
                self.assertNotIn(forbidden, bolt_block, f"{member}: {forbidden}")

    def test_every_bolt_instruction_names_the_description_and_the_landing_line(self):
        for member in self.MEMBERS:
            bolt_block = self.instruction(member, "bolt")
            self.assertIn("**Input:** the bolt milestone's description",
                          bolt_block, member)
            self.assertIn('A "Landing:" line', bolt_block, member)

    def test_the_bolt_templates_are_not_edited_by_this_change(self):
        # Task 1.2's non-goal: the template already carries the four
        # sections and nothing else.
        for member in self.MEMBERS:
            template = (ROOT / "schemas" / member / "templates"
                        / "bolt.md").read_text()
            self.assertNotIn("Unit:", template, member)
            for heading in loop.BoltLoop.CHARTER_SECTIONS:
                self.assertIn(heading, template, f"{member}: {heading}")


class CharterRegionTest(unittest.TestCase):
    """`merge_criteria()` reads the charter's region, not the whole file.

    A record written under the older shape carries the unit's plan
    document in `bolt.md` under a `# Unit: <slug>` heading, and that
    document can have a `## Merge criteria` of its own. Searching the
    whole file returns the first such section anywhere in it, so a charter
    with none of its own hands back a UNIT'S criteria as the bolt's, and
    `landing_mode()` takes a `Landing:` line from prose that never spoke
    for this bolt.
    """

    #: A charter that states its own criteria, with a stale unit section
    #: still below it stating different ones.
    LAYERED = """# Bolt: x

## Merge criteria
Acceptance suites green on the bolt branch.
Landing: merge

# Unit: u1

The unit's plan document.

## Merge criteria
The unit's own bar, which is not the bolt's.
Landing: pr

## Left out
Something this unit does not do.
"""

    #: The older shape with NO charter above the unit section — the state
    #: both records on disk are in, minus the coincidence that neither of
    #: their unit bodies happens to carry a criteria subsection.
    OLDER = """# Unit: the-bolt-charter

Some unit plan prose.

## Merge criteria
THE UNIT'S OWN CRITERIA — not the bolt's.
Landing: pr
"""

    def charter(self, tmp, text):
        change = Path(tmp) / "openspec" / "changes" / "x"
        change.mkdir(parents=True, exist_ok=True)
        (change / "bolt.md").write_text(text)
        return a_loop(FakeTracker(), bolt_worktree=str(tmp))

    def test_a_charter_that_states_its_own_criteria_is_read_from_disk(self):
        # 7.5: its own charter, written here, rather than a repo path that
        # has since been archived and takes a skip branch.
        with tempfile.TemporaryDirectory() as tmp:
            program = self.charter(tmp, CHARTER)
            self.assertIn("Acceptance suites green", program.merge_criteria())
            self.assertIn("Landing: merge", program.merge_criteria())
            self.assertEqual(program.landing_mode(), "merge")

    def test_a_stale_unit_section_below_the_charter_is_not_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            program = self.charter(tmp, self.LAYERED)
            criteria = program.merge_criteria()
            self.assertIn("Acceptance suites green", criteria)
            self.assertNotIn("The unit's own bar", criteria)
            self.assertNotIn("Left out", criteria)
            self.assertEqual(program.landing_mode(), "merge",
                             "the charter's declaration, not the unit's")

    def test_a_stale_unit_section_cannot_supply_the_criteria(self):
        # The live defect: with no charter above it, the whole-file search
        # returned the UNIT'S text and `landing_mode()` read `pr` out of it.
        with tempfile.TemporaryDirectory() as tmp:
            program = self.charter(tmp, self.OLDER)
            self.assertEqual(program.merge_criteria(), "",
                             "this bolt's criteria read as absent")
            self.assertNotEqual(program.landing_mode(), "pr",
                                "and no mode is taken from the unit's prose")

    def test_the_older_shape_reaches_the_guards_check_and_the_refusal(self):
        # 7.3: the absent case has to be genuinely absent, or neither the
        # scaffold's post-settle check nor the landing's refusal fires.
        with tempfile.TemporaryDirectory() as tmp:
            change = Path(tmp) / "openspec" / "changes" / "x"
            change.mkdir(parents=True)
            (change / "bolt.md").write_text(self.OLDER)
            shell = FakeShell({("git", "merge-base"): Result(0),
                               ("git", "rev-parse"): Result(0, "abc1234\n"),
                               ("git", "rev-list"): Result(0, "1\n")})
            snapshot = Snapshot(
                items=[item(1, inbox.IN_PROGRESS)],
                milestone="bolt/x")
            program = a_loop(FakeTracker(snapshot), shell=shell,
                             repo_dir=str(tmp), bolt_worktree=str(tmp))
            outcome = program.land_stage(snapshot)
            self.assertEqual(outcome.status, "failed", outcome.detail)
            self.assertIn("merge criteria could not be read", outcome.detail)

    def test_a_charter_with_no_unit_heading_is_its_own_region_entire(self):
        with tempfile.TemporaryDirectory() as tmp:
            program = self.charter(tmp, CHARTER)
            self.assertEqual(program.charter_region(CHARTER), CHARTER)


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


class ObservedRunTest(unittest.TestCase):
    """The run ledger and the expectation gate on the bolt loop."""

    def shell(self):
        return FakeShell({("git", "rev-list"): Result(0, "3\n"),
                          ("git", "merge-base"): Result(0)})

    def a_ready_item(self):
        return Snapshot(items=[item(1, inbox.READY, change="add-thing")],
                        milestone="bolt/x")

    def observed(self, tracker, root, gate_mode="gate", runner=None):
        led = obs.RunLedger(root, "bolt-x", gate_mode=gate_mode)
        runner = runner or ScriptedRunner(states=[WaitState.SETTLED_DONE] * 12,
                                          reports=["No findings."] * 12)
        return a_loop(tracker, runner=runner, shell=self.shell(),
                      ledger=led), led, runner

    def test_an_unapproved_pass_gates_before_any_drive(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = FakeTracker(self.a_ready_item())
            l, led, runner = self.observed(tracker, tmp)
            result = l.cycle(1)
            self.assertIn("gated", result.stopped)
            self.assertEqual(runner.launched, [], "nothing may be driven")
            scope = Path(tmp) / "bolt-x"
            self.assertTrue((scope / "pending.json").exists())
            self.assertTrue(list(scope.glob("*.plan.md")))

    def test_an_approved_plan_drives_and_does_not_regate(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = FakeTracker(self.a_ready_item(),
                                  comments={1: [{"body": "built it"}]})
            l, led, runner = self.observed(tracker, tmp)
            l.cycle(1)
            obs.approve(tmp, "bolt-x")
            l2, led2, runner2 = self.observed(
                FakeTracker(self.a_ready_item(),
                            comments={1: [{"body": "built it"}]}), tmp)
            result = l2.cycle(1)
            self.assertNotIn("gated", result.stopped or "")
            self.assertTrue(runner2.launched)

    def test_a_changed_plan_regates(self):
        with tempfile.TemporaryDirectory() as tmp:
            l, led, _ = self.observed(FakeTracker(self.a_ready_item()), tmp)
            l.cycle(1)
            obs.approve(tmp, "bolt-x")
            other = Snapshot(items=[item(2, inbox.READY, change="other")],
                             milestone="bolt/x")
            l2, led2, runner2 = self.observed(FakeTracker(other), tmp)
            result = l2.cycle(1)
            self.assertIn("gated", result.stopped)
            self.assertEqual(runner2.launched, [])

    def test_courtesy_mode_writes_the_plan_and_drives(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = FakeTracker(self.a_ready_item(),
                                  comments={1: [{"body": "built it"}]})
            l, led, runner = self.observed(tracker, tmp, gate_mode="courtesy")
            result = l.cycle(1)
            self.assertNotIn("gated", result.stopped or "")
            self.assertTrue(runner.launched)
            self.assertTrue(list((Path(tmp) / "bolt-x").glob("*.plan.md")))

    def test_an_acting_run_renders_the_report_with_actuals(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = FakeTracker(self.a_ready_item(),
                                  comments={1: [{"body": "built it"}]})
            l, led, _ = self.observed(tracker, tmp, gate_mode="courtesy")
            l.run(max_cycles=1, land=False)
            report = next((Path(tmp) / "bolt-x").glob("*.report.md"))
            text = report.read_text()
            self.assertIn("spec:add-thing", text)
            self.assertIn("✓", text)

    def test_a_no_action_run_still_records_its_preconditions(self):
        with tempfile.TemporaryDirectory() as tmp:
            l, led, _ = self.observed(FakeTracker(Snapshot()), tmp)
            l.run(max_cycles=1, land=False)
            report = next((Path(tmp) / "bolt-x").glob("*.report.md"))
            self.assertIn("nothing ready", report.read_text())


class UnitTypeTest(unittest.TestCase):
    """The unit card's Type line picks the type its batches run under."""

    def loop_with(self, body):
        snapshot = Snapshot(
            items=[item(1, inbox.READY, parent_batch=9),
                   item(9, inbox.UNIT, body=body)],
            batches=[Batch(number=9, kind=inbox.UNIT, sub_issues=(1,),
                           milestone="bolt/x")])
        program = a_loop(FakeTracker(snapshot), repo_dir=str(ROOT))
        batch = types.SimpleNamespace(numbers=(1,))
        return program, batch, snapshot

    def test_the_unit_card_names_the_type_the_batch_runs(self):
        program, batch, snapshot = self.loop_with(
            "Sequence: 1 of 1 · builds on: none\n"
            "Type: `bolt-direct` · Price: 2 changes · ~1 day\n")
        config = program.unit_config(batch, snapshot)
        self.assertEqual(config.name, "bolt-direct")
        self.assertFalse(config.runs("verify"))
        self.assertFalse(config.plan, "bolt-direct is spec-path")

    def test_a_unit_naming_no_type_runs_the_bolts_bound_type(self):
        program, batch, snapshot = self.loop_with("no structured line here")
        self.assertIs(program.unit_config(batch, snapshot),
                      program.params.config)

    def test_the_plan_path_is_a_type(self):
        # There is no mode beside the type: bolt-plan IS the plan path.
        program, batch, snapshot = self.loop_with(
            "Type: `bolt-plan` · Price: 2 changes · ~1 day")
        config = program.unit_config(batch, snapshot)
        self.assertEqual(config.name, "bolt-plan")
        self.assertTrue(config.plan)
        self.assertFalse(config.runs("verify"))

    def test_an_unknown_type_is_refused_not_downgraded(self):
        program, batch, snapshot = self.loop_with("Type: `bolt-bogus`")
        with self.assertRaises(loop.LoopError):
            program.unit_config(batch, snapshot)


if __name__ == "__main__":
    unittest.main()


class BuildWitnessTest(unittest.TestCase):
    """A commit on the branch is not the build's witness — the change's own
    task list is: every box checked, or the build still owes work (observed
    live: a spec session's planning commit satisfied the old skip and build
    skipped over zero implementation)."""

    def loop_with_tasks(self, tmp, body):
        change_dir = Path(tmp) / "openspec" / "changes" / "add-thing"
        change_dir.mkdir(parents=True)
        (change_dir / "tasks.md").write_text(body)
        runner = ScriptedRunner(states=[WaitState.SETTLED_DONE] * 4)
        shell = FakeShell({("git", "rev-list"): Result(0, "3\n")})
        program = a_loop(FakeTracker(), runner=runner, shell=shell)
        program.batch_worktree = lambda b: tmp
        return program, runner

    def test_unchecked_tasks_mean_the_build_still_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            program, runner = self.loop_with_tasks(
                tmp, "# Tasks\n\n- [x] 1.1 done\n- [ ] 1.2 not yet\n")
            batch = loop.WorkBatch(slug="add-thing", items=(
                item(1, inbox.READY, change="add-thing"),))
            program.build_stage(batch)
            self.assertTrue(runner.launched,
                            "an unchecked task list is not a built change")

    def test_a_checked_task_list_completes_the_witness(self):
        with tempfile.TemporaryDirectory() as tmp:
            program, runner = self.loop_with_tasks(
                tmp, "# Tasks\n\n- [x] 1.1 done\n- [x] 1.2 also done\n")
            batch = loop.WorkBatch(slug="add-thing", items=(
                item(1, inbox.READY, change="add-thing"),))
            outcome = program.build_stage(batch)
            self.assertEqual(outcome.status, "done")
            self.assertEqual(runner.launched, [])


class CloseReadyTest(unittest.TestCase):
    """When everything is merged and every card ruled, the wait moves to
    the operator — needs-operator on the unit parent, visible in Waiting
    On Me — and the close that starts the landing answers it."""

    def merged_open_milestone(self):
        return Snapshot(items=[
            item(9, inbox.UNIT, title="Unit: x"),
            Item(number=1, milestone="bolt/x", title="one", state="closed",
                 labels=frozenset({inbox.CLOSED_MERGED})),
        ], milestone="bolt/x")

    def test_all_merged_on_an_open_milestone_marks_the_parent(self):
        snap = self.merged_open_milestone()
        tracker = FakeTracker(snap)
        program = a_loop(tracker)
        program.run(max_cycles=1)
        self.assertIn(("add_label", 9, inbox.NEEDS_OPERATOR), tracker.writes)
        comments = [w for w in tracker.writes
                    if w[0] == "comment" and w[1] == 9]
        self.assertTrue(any("Closing the bolt/x milestone" in w[2]
                            for w in comments))

    def test_the_mark_is_written_once(self):
        snap = Snapshot(items=[
            item(9, inbox.UNIT, inbox.NEEDS_OPERATOR, title="Unit: x"),
            Item(number=1, milestone="bolt/x", title="one", state="closed",
                 labels=frozenset({inbox.CLOSED_MERGED})),
        ], milestone="bolt/x")
        tracker = FakeTracker(snap)
        a_loop(tracker).run(max_cycles=1)
        self.assertNotIn(("add_label", 9, inbox.NEEDS_OPERATOR),
                         tracker.writes, "an existing mark is not re-written")

    def test_the_close_answers_the_parents_wait(self):
        # A container's needs-operator never refuses the landing; the close
        # that started it is the answer, and the label comes off.
        snap = Snapshot(items=[
            item(9, inbox.UNIT, inbox.NEEDS_OPERATOR, title="Unit: x",
                 milestone_state="closed"),
            Item(number=1, milestone="bolt/x", milestone_state="closed",
                 title="one", state="closed",
                 labels=frozenset({inbox.CLOSED_MERGED})),
        ], milestone="bolt/x")
        tracker = FakeTracker(snap)
        shell = FakeShell({("git", "rev-list"): Result(0, "3\n"),
                           ("git", "merge-base"): Result(0),
                           ("git", "rev-parse"): Result(0, "abc\n")})
        program = a_loop(tracker, shell=shell,
                         runner=ScriptedRunner(
                             states=[WaitState.SETTLED_DONE] * 4))
        outcome = program.land_stage(snap)
        self.assertIn(("remove_label", 9, inbox.NEEDS_OPERATOR),
                      tracker.writes)
        self.assertNotEqual(outcome.status, "paused",
                            "a container's wait never pauses the landing")

    def test_new_cards_withdraw_the_close_ready_mark(self):
        # More units arrive after the mark: "ready to land" is no longer
        # true, so the label comes off until the new units finish too.
        snap = Snapshot(
            items=[item(9, inbox.UNIT, inbox.NEEDS_OPERATOR, title="Unit: x"),
                   Item(number=1, milestone="bolt/x", title="one",
                        state="closed",
                        labels=frozenset({inbox.CLOSED_MERGED}))],
            milestone="bolt/x")
        snap.plan_cards = (inbox.PlanCard(
            number=30, title="Unit: more", body="", status="Backlog",
            milestone="bolt/x"),)
        tracker = FakeTracker(snap)
        a_loop(tracker).run(max_cycles=1)
        self.assertIn(("remove_label", 9, inbox.NEEDS_OPERATOR),
                      tracker.writes)
        self.assertNotIn(("add_label", 9, inbox.NEEDS_OPERATOR),
                         tracker.writes)


class FindingsRoutingChargeTest(unittest.TestCase):
    """A run that stops at a non-empty queue charges the findings-routing
    session — the construction origin of the dispatch plan. The queued
    items are the bolt's findings inbox: durable, inert, and routed only
    through the operator's round; the charge is launch-and-leave, so the
    run never waits on the pane."""

    def test_a_stop_at_a_queue_charges_the_routing_session(self):
        snapshot = Snapshot(items=[item(5, inbox.QUEUED, title="a flake"),
                                   item(7, inbox.QUEUED, title="a gap")],
                            milestone="bolt/x")
        runner = ScriptedRunner()
        program = a_loop(FakeTracker(snapshot), runner=runner)
        report = program.run(land=False)
        self.assertEqual(len(runner.launched), 1)
        spec = runner.launched[0]
        self.assertEqual(spec.profile, loop.FINDINGS_PROFILE)
        self.assertEqual(spec.name, "findings-routing-x-5",
                         "deterministic, keyed to the lowest queued number")
        self.assertTrue(spec.operator_round,
                        "the round is the operator's to take as long as "
                        "they like")
        self.assertEqual(spec.model, loop.STAGE_MODELS["findings"])
        self.assertIn("#5", spec.order)
        self.assertIn("#7", spec.order)
        self.assertIn("findings-routing-x-5", report.routing)

    def test_an_empty_queue_charges_nothing(self):
        runner = ScriptedRunner()
        program = a_loop(FakeTracker(Snapshot(milestone="bolt/x")),
                         runner=runner)
        report = program.run(land=False)
        self.assertEqual(runner.launched, [])
        self.assertEqual(report.routing, "")

    def test_a_queued_container_is_not_a_finding(self):
        # A batch parent at state:queued is a container, never inbox work.
        snapshot = Snapshot(items=[item(9, inbox.UNIT, inbox.QUEUED)],
                            milestone="bolt/x")
        runner = ScriptedRunner()
        program = a_loop(FakeTracker(snapshot), runner=runner)
        report = program.run(land=False)
        self.assertEqual(runner.launched, [])
        self.assertEqual(report.routing, "")

    def test_a_dry_run_reports_the_charge_it_would_make(self):
        snapshot = Snapshot(items=[item(5, inbox.QUEUED, title="a flake")],
                            milestone="bolt/x")
        runner = ScriptedRunner()
        program = a_loop(FakeTracker(snapshot), runner=runner)
        program.dry_run = True
        report = program.run(land=False)
        self.assertEqual(runner.launched, [])
        self.assertIn("would charge", report.routing)

    def test_a_charge_that_cannot_launch_is_reported_never_a_halt(self):
        snapshot = Snapshot(items=[item(5, inbox.QUEUED, title="a flake")],
                            milestone="bolt/x")

        class NoLaunch(ScriptedRunner):
            def launch(self, spec):
                raise sessions.SessionError("no herdr here")

        program = a_loop(FakeTracker(snapshot), runner=NoLaunch())
        report = program.run(land=False)
        self.assertFalse(report.halted)
        self.assertIn("not charged", report.routing)
