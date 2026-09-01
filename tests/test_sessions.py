"""#75 — one session abstraction over herdr and headless runners.

Every test here proves a clause of the claim rather than exercising trivia.
Nothing starts herdr, spawns `claude`, or sleeps: the runners take an injected
`run=` and `sleep=`, and `supervise` takes an injected `clock=`.
"""

import unittest

from context import sessions

SessionSpec = sessions.SessionSpec
WaitState = sessions.WaitState


class Result:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class FakeHerdr:
    """A herdr that lives in a dict. Records every argv it is handed."""

    def __init__(self, roster=None):
        self.roster = dict(roster or {})
        self.calls = []

    def __call__(self, argv, cwd=None, env=None, timeout=None):
        self.calls.append(argv)
        verb = argv[1:4]
        if verb[:2] == ["agent", "list"]:
            return Result(stdout=_json_agents(self.roster))
        if verb[:2] == ["tab", "create"]:
            return Result(stdout='{"result": {"tab": {"tab_id": "w1:t9"}, '
                                 '"root_pane": {"pane_id": "w1:p9"}}}')
        if verb[:2] == ["agent", "start"]:
            name = argv[3]
            self.roster[name] = {
                "name": name, "agent_status": "idle",
                "terminal_title_stripped": name, "interactive_ready": True,
                "pane_id": "w1:p9", "tab_id": "w1:t9",
            }
            return Result()
        if verb[:2] == ["agent", "prompt"]:
            self.roster.setdefault(argv[3], {})["agent_status"] = "working"
            return Result()
        if verb[:2] == ["agent", "read"]:
            return Result(stdout='{"result": {"text": "the report"}}')
        return Result()

    def verbs(self):
        return [" ".join(a[1:3]) for a in self.calls]


def _json_agents(roster):
    import json
    return json.dumps({"result": {"agents": list(roster.values())}})


class ScriptedRunner:
    """A runner whose `wait` returns a scripted sequence, for `supervise`."""

    def __init__(self, states):
        self.states = list(states)
        self.waits = 0

    def wait(self, handle, timeout=None):
        self.waits += 1
        if self.states:
            return self.states.pop(0)
        return WaitState.WORKING


class FakeClock:
    """Time that only moves when a wait consumes it."""

    def __init__(self, step=600):
        self.now = 0.0
        self.step = step

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def spec(**kw):
    base = dict(name="build-substrate", cwd="/tmp/wt", order="/flywheel:build\n\ngo",
                profile="flywheel-construction-session", model="opus[1m]")
    base.update(kw)
    return SessionSpec(**base)


def herdr_runner(**kw):
    """A HerdrRunner that never sleeps and never touches ~/.claude.json."""
    kw.setdefault("sleep", lambda _s: None)
    kw.setdefault("seed_trust", lambda _cwd: None)
    kw.setdefault("seed_plugin", lambda _cwd: None)
    return sessions.HerdrRunner(**kw)


# ---------------------------------------------------------------------------
# The work order
# ---------------------------------------------------------------------------

class WorkOrderTest(unittest.TestCase):

    def test_invocation_is_the_first_line(self):
        order = sessions.work_order("/flywheel:build", "Items: #75, #76.\nGoal: x")
        self.assertEqual(order.splitlines()[0], "/flywheel:build")

    def test_it_is_one_prompt_not_two(self):
        order = sessions.work_order("/opsx:ff slug", "the brief")
        self.assertIsInstance(order, str)
        self.assertIn("the brief", order)

    def test_a_slash_command_in_the_brief_is_not_promoted(self):
        order = sessions.work_order("/flywheel:build", "later run /opsx:apply")
        self.assertEqual(order.splitlines()[0], "/flywheel:build")

    def test_an_invocation_must_be_one_line(self):
        with self.assertRaises(ValueError):
            sessions.work_order("/a\n/b", "brief")

    def test_an_order_needs_an_invocation(self):
        with self.assertRaises(ValueError):
            sessions.work_order("", "brief")


# ---------------------------------------------------------------------------
# The spec
# ---------------------------------------------------------------------------

class SpecTest(unittest.TestCase):

    def test_the_name_cap_is_herdrs_and_is_refused_before_any_subprocess(self):
        herdr = FakeHerdr()
        runner = herdr_runner(run=herdr, sleep=lambda _s: None)
        with self.assertRaises(ValueError):
            runner.launch(spec(name="human-code-review-substrate-runners"))
        self.assertEqual(herdr.calls, [], "a bad name must cost no subprocess")

    def test_plan_mode_and_skip_permissions_are_exclusive_shapes(self):
        self.assertEqual(spec(plan_mode=True).permission_flag,
                         ["--permission-mode", "plan"])
        self.assertEqual(spec().permission_flag, ["--dangerously-skip-permissions"])
        self.assertEqual(spec(skip_permissions=False).permission_flag, [])


# ---------------------------------------------------------------------------
# Idempotent launch — the property the claim names
# ---------------------------------------------------------------------------

class IdempotentLaunchTest(unittest.TestCase):

    def test_an_agent_already_under_the_name_is_reused_and_not_re_prompted(self):
        herdr = FakeHerdr({"build-substrate": {
            "name": "build-substrate", "agent_status": "working",
            "terminal_title_stripped": "◑ build-substrate",
            "pane_id": "w1:p3", "tab_id": "w1:t3",
        }})
        runner = herdr_runner(run=herdr, sleep=lambda _s: None)
        handle = runner.launch(spec())

        self.assertTrue(handle.reused)
        self.assertEqual(handle.ref["tab_id"], "w1:t3")
        self.assertNotIn("tab create", herdr.verbs())
        self.assertNotIn("agent start", herdr.verbs())
        self.assertNotIn("agent prompt", herdr.verbs(),
                         "reuse must never re-send the work order")

    def test_a_fresh_launch_pins_the_deterministic_session_id(self):
        herdr = FakeHerdr()
        runner = herdr_runner(run=herdr, sleep=lambda _s: None,
                                      transcript_exists=lambda c, s: False)
        runner.launch(spec(session_id="abc-123"))
        start = next(a for a in herdr.calls if a[1:3] == ["agent", "start"])
        self.assertIn("--session-id", start)
        self.assertEqual(start[start.index("--session-id") + 1], "abc-123")

    def test_a_launch_with_a_transcript_resumes_the_warm_session(self):
        # #178: the pane is disposable, the session is durable — a
        # transcript under the derived id means resume, never start cold.
        herdr = FakeHerdr()
        runner = herdr_runner(run=herdr, sleep=lambda _s: None,
                                      transcript_exists=lambda c, s: True)
        runner.launch(spec(session_id="abc-123"))
        start = next(a for a in herdr.calls if a[1:3] == ["agent", "start"])
        self.assertIn("--resume", start)
        self.assertEqual(start[start.index("--resume") + 1], "abc-123")
        self.assertNotIn("--session-id", start)

    def test_a_fresh_launch_creates_the_tab_then_starts_then_prompts(self):
        herdr = FakeHerdr()
        runner = herdr_runner(run=herdr, sleep=lambda _s: None)
        runner.launch(spec())
        verbs = [v for v in herdr.verbs() if v != "agent list"]
        self.assertEqual(verbs[:4], ["tab create", "agent start",
                                     "agent send-keys", "agent prompt"])

    def test_delivery_clears_the_composer_before_typing_the_order(self):
        # A stranded prompt concatenates with the next one — the garbage
        # line `/rename scaffold-x/opsx:new x` observed on first boot. One
        # esc before the order guarantees a clean composer.
        herdr = FakeHerdr()
        runner = herdr_runner(run=herdr, sleep=lambda _s: None)
        runner.launch(spec())
        keys = [a for a in herdr.calls if a[1:3] == ["agent", "send-keys"]]
        prompt_at = next(i for i, a in enumerate(herdr.calls)
                         if a[1:3] == ["agent", "prompt"])
        esc_at = next(i for i, a in enumerate(herdr.calls)
                      if a[1:3] == ["agent", "send-keys"] and a[4] == "esc")
        self.assertLess(esc_at, prompt_at)

    def test_a_stubborn_title_never_provokes_a_typed_rename(self):
        # The glued line `/rename scaffold-…/opsx:new …` observed live on
        # bolt/matches-the-book: anything typed for a title can strand in
        # the composer and swallow the order. A title that never converges
        # costs nothing — the order still delivers, and no /rename is typed.
        class StubbornTitle(FakeHerdr):
            def __call__(self, argv, cwd=None, env=None, timeout=None):
                out = super().__call__(argv, cwd=cwd, env=env, timeout=timeout)
                if argv[1:3] == ["agent", "start"]:
                    self.roster[argv[3]]["terminal_title_stripped"] = "1"
                return out
        herdr = StubbornTitle()
        runner = herdr_runner(run=herdr, sleep=lambda _s: None,
                                      submit_attempts=2)
        runner.launch(spec())
        prompts = [a[4] for a in herdr.calls if a[1:3] == ["agent", "prompt"]]
        self.assertFalse([p for p in prompts if p.startswith("/rename")],
                         "a title is never worth typing into the composer")
        self.assertTrue([p for p in prompts if p.startswith("/flywheel:build")],
                        "the order must still deliver")

    def test_a_pane_that_never_reaches_its_composer_fails_the_launch(self):
        # Typing into a not-ready pane buffers keystrokes that land glued
        # once claude comes up — refuse instead, pane kept for inspection.
        class NeverReady(FakeHerdr):
            def __call__(self, argv, cwd=None, env=None, timeout=None):
                out = super().__call__(argv, cwd=cwd, env=env, timeout=timeout)
                if argv[1:3] == ["agent", "start"]:
                    self.roster[argv[3]]["interactive_ready"] = False
                return out
        herdr = NeverReady()
        runner = herdr_runner(run=herdr, sleep=lambda _s: None,
                                      ready_attempts=2)
        with self.assertRaises(sessions.SessionError):
            runner.launch(spec())
        self.assertNotIn("agent prompt", herdr.verbs(),
                         "nothing is typed into a pane that never got ready")
        renames = [a for a in herdr.calls if a[1:3] == ["agent", "rename"]]
        self.assertTrue(renames and renames[-1][4].endswith("-notready"),
                        "the failed launch must release the name")

    def test_an_order_that_never_submits_fails_the_launch(self):
        class DeafComposer(FakeHerdr):
            def __call__(self, argv, cwd=None, env=None, timeout=None):
                out = super().__call__(argv, cwd=cwd, env=env, timeout=timeout)
                if argv[1:3] == ["agent", "prompt"]:
                    self.roster[argv[3]]["agent_status"] = "idle"
                return out
        herdr = DeafComposer()
        runner = herdr_runner(run=herdr, sleep=lambda _s: None,
                                      submit_attempts=2)
        with self.assertRaises(sessions.SessionError):
            runner.launch(spec())
        # #169: the corpse must not keep the name — launch is idempotent by
        # name and never re-sends an order, so an unreleased name wedges
        # every later pass.
        renames = [a for a in herdr.calls if a[1:3] == ["agent", "rename"]]
        self.assertTrue(renames, "the failed launch must release the name")
        self.assertTrue(renames[-1][4].endswith("-undelivered"))

    def test_the_name_is_set_at_launch_so_there_is_no_rename_to_race(self):
        herdr = FakeHerdr()
        runner = herdr_runner(run=herdr, sleep=lambda _s: None)
        runner.launch(spec())
        start = next(a for a in herdr.calls if a[1:3] == ["agent", "start"])
        self.assertIn("-n", start)
        self.assertEqual(start[start.index("-n") + 1], "build-substrate")
        prompts = [a[4] for a in herdr.calls if a[1:3] == ["agent", "prompt"]]
        self.assertFalse([p for p in prompts if p.startswith("/rename")],
                         "-n took, so the rename dance must not run")

    def test_a_working_agents_title_keeps_its_glyph_and_still_counts_as_named(self):
        # Measured on the live roster: an idle agent reads `dispatch`, a
        # working one reads `◑ build-substrate`. Comparing raw would send a
        # pointless /rename to every busy session.
        self.assertEqual(sessions.strip_glyph("◑ build-substrate"), "build-substrate")
        self.assertEqual(sessions.strip_glyph("✳ dispatch"), "dispatch")


# ---------------------------------------------------------------------------
# The four verbs, plus send
# ---------------------------------------------------------------------------

class VerbTest(unittest.TestCase):

    def setUp(self):
        self.herdr = FakeHerdr({"n": {
            "name": "n", "agent_status": "idle", "terminal_title_stripped": "n",
            "pane_id": "p", "tab_id": "t", "interactive_ready": True}})
        self.runner = herdr_runner(run=self.herdr, sleep=lambda _s: None)
        self.handle = sessions.SessionHandle(name="n", runner="herdr",
                                             ref={"tab_id": "t"})

    def test_wait_is_a_single_bounded_call_never_a_loop(self):
        self.runner.wait(self.handle, timeout=600)
        waits = [a for a in self.herdr.calls if a[1:3] == ["agent", "wait"]]
        self.assertEqual(len(waits), 1)
        self.assertIn("--timeout", waits[0])
        self.assertEqual(waits[0][waits[0].index("--timeout") + 1], "600000")

    def test_wait_does_not_pin_until_because_done_would_never_fire(self):
        self.runner.wait(self.handle)
        waits = [a for a in self.herdr.calls if a[1:3] == ["agent", "wait"]]
        self.assertNotIn("--until", waits[0])

    def test_states_map_from_the_roster(self):
        for status, expected in [("idle", WaitState.SETTLED_DONE),
                                 ("done", WaitState.SETTLED_DONE),
                                 ("blocked", WaitState.SETTLED_BLOCKED),
                                 ("working", WaitState.WORKING)]:
            self.herdr.roster["n"]["agent_status"] = status
            self.assertEqual(self.runner.state("n"), expected)

    def test_a_missing_agent_is_gone(self):
        self.herdr.roster.clear()
        self.assertEqual(self.runner.state("n"), WaitState.GONE)

    def test_collect_reads_the_pane_unwrapped(self):
        got = self.runner.collect(self.handle)
        self.assertEqual(got.report, "the report")
        read = next(a for a in self.herdr.calls if a[1:3] == ["agent", "read"])
        self.assertIn("recent-unwrapped", read)

    def test_close_closes_the_tab(self):
        self.runner.close(self.handle)
        self.assertIn(["herdr", "tab", "close", "t"], self.herdr.calls)

    def test_send_re_prompts_a_live_session(self):
        self.runner.send(self.handle, "go fix these")
        prompts = [a for a in self.herdr.calls if a[1:3] == ["agent", "prompt"]]
        self.assertEqual(prompts[0][4], "go fix these")


# ---------------------------------------------------------------------------
# The clocks — the program owns all waiting
# ---------------------------------------------------------------------------

class ClockTest(unittest.TestCase):

    def supervise(self, states, clock, **kw):
        runner = ScriptedRunner(states)
        original = runner.wait

        def wait(handle, timeout=None):
            clock.advance(timeout or 600)
            return original(handle, timeout)

        runner.wait = wait
        notices = []
        result = sessions.supervise(
            runner, sessions.SessionHandle("n", "herdr"), clock=clock,
            on_notify=lambda h, e: notices.append(e), **kw)
        return result, notices

    def test_nothing_fires_before_ninety_minutes(self):
        clock = FakeClock()
        states = [WaitState.WORKING] * 8 + [WaitState.SETTLED_DONE]
        result, notices = self.supervise(states, clock)
        self.assertEqual(notices, [])
        self.assertEqual(result.state, WaitState.SETTLED_DONE)

    def test_ninety_minutes_notifies_once_and_keeps_waiting(self):
        clock = FakeClock()
        states = [WaitState.WORKING] * 12 + [WaitState.SETTLED_DONE]
        result, notices = self.supervise(states, clock)
        self.assertEqual(len(notices), 1)
        self.assertGreaterEqual(notices[0], sessions.NOTIFY_AFTER_S)
        self.assertEqual(result.state, WaitState.SETTLED_DONE,
                         "a notice is a live wait, not a stop")

    def test_it_never_notifies_twice(self):
        # invariant 7: needs-operator marks a LIVE wait. A second comment on
        # every pass is exactly the pollution that invariant forbids.
        clock = FakeClock()
        states = [WaitState.WORKING] * 20 + [WaitState.SETTLED_DONE]
        _result, notices = self.supervise(states, clock)
        self.assertEqual(len(notices), 1)

    def test_four_hours_stalls(self):
        clock = FakeClock()
        result, _ = self.supervise([WaitState.WORKING] * 100, clock)
        self.assertEqual(result.state, WaitState.STALLED)
        self.assertGreaterEqual(result.elapsed, sessions.STALL_AFTER_S)

    def test_an_operator_round_never_auto_stalls_but_still_notifies(self):
        clock = FakeClock()
        states = [WaitState.WORKING] * 40 + [WaitState.SETTLED_DONE]
        result, notices = self.supervise(states, clock, operator_round=True)
        self.assertEqual(result.state, WaitState.SETTLED_DONE)
        self.assertGreater(result.elapsed, sessions.STALL_AFTER_S)
        self.assertEqual(len(notices), 1, "the record excepts the stall, not the notice")

    def test_a_restarted_loop_does_not_hand_a_hung_session_a_fresh_budget(self):
        # The stateless-process test. A loop that dies at 80 minutes and is
        # restarted by the 60s reconcile must not reset the clock — on a
        # flapping server the session would never stall at all.
        clock = FakeClock()
        clock.now = 5 * 3600
        result, _ = self.supervise([WaitState.WORKING] * 100, clock,
                                   origin=0.0)
        self.assertEqual(result.state, WaitState.STALLED)
        self.assertLessEqual(result.waits, 1,
                             "one look at the pane, then the verdict — a "
                             "settled session must never stall unseen")

    def test_a_restart_does_not_re_notify(self):
        clock = FakeClock()
        clock.now = 2 * 3600
        _result, notices = self.supervise(
            [WaitState.WORKING, WaitState.SETTLED_DONE], clock,
            origin=0.0, notified=True, stall_after=10 * 3600)
        self.assertEqual(notices, [])

    def test_the_clock_restarts_on_re_entry_which_is_how_approval_resets_it(self):
        clock = FakeClock()
        first, notices = self.supervise([WaitState.WORKING] * 12 + [WaitState.SETTLED_BLOCKED], clock)
        self.assertEqual(len(notices), 1)
        # the plan is approved; the session works again; a new supervise call
        second, notices2 = self.supervise([WaitState.SETTLED_DONE], clock)
        self.assertEqual(notices2, [], "the new round starts with a fresh clock")
        self.assertLess(second.elapsed, first.elapsed)


# ---------------------------------------------------------------------------
# headless
# ---------------------------------------------------------------------------

class FakeProc:
    def __init__(self, pid=4242):
        self.pid = pid

    def poll(self):
        return None

    def terminate(self):
        pass


class HeadlessTest(unittest.TestCase):

    def runner(self, tmp, alive=lambda _p: False):
        self.spawned = []

        def popen(argv, cwd=None, env=None, stdout=None, stderr=None):
            self.spawned.append({"argv": argv, "cwd": cwd, "env": env})
            return FakeProc()

        return sessions.HeadlessRunner(popen=popen, state_dir=tmp, alive=alive,
                                       seed_trust=lambda _cwd: None,
                                       seed_plugin=lambda _cwd: None)

    def test_it_refuses_plan_mode_at_launch_not_at_four_hours(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            runner = self.runner(tmp)
            with self.assertRaises(sessions.RunnerUnavailable):
                runner.launch(spec(plan_mode=True, runner="headless"))

    def test_the_argv_reuses_the_cli_login_and_injects_no_credential(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            runner = self.runner(tmp)
            runner.launch(spec(runner="headless"))
            call = self.spawned[0]
            self.assertEqual(call["argv"][:2], ["claude", "-p"])
            self.assertIsNone(call["env"], "the environment is inherited, not built")
            joined = " ".join(call["argv"])
            for secret in ("ANTHROPIC_API_KEY", "GH_TOKEN", "--api-key"):
                self.assertNotIn(secret, joined)

    def test_the_session_id_is_derived_so_a_restart_recomputes_it(self):
        first = sessions.derived_session_id("build-substrate")
        self.assertEqual(first, sessions.derived_session_id("build-substrate"))
        self.assertNotEqual(first, sessions.derived_session_id("build-other"))

    def test_a_live_recorded_process_is_reused_rather_than_twinned(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            runner = self.runner(tmp)
            runner.launch(spec(runner="headless"))
            again = self.runner(tmp, alive=lambda _p: True)
            handle = again.launch(spec(runner="headless"))
            self.assertTrue(handle.reused)
            self.assertEqual(self.spawned, [], "a live session must not be respawned")


# ---------------------------------------------------------------------------
# cloud, and runner choice
# ---------------------------------------------------------------------------

class CloudTest(unittest.TestCase):

    def test_every_verb_raises_with_the_reason_not_an_attribute_error(self):
        runner = sessions.CloudRunner()
        handle = sessions.SessionHandle("n", "cloud")
        for call in (lambda: runner.launch(spec()),
                     lambda: runner.wait(handle),
                     lambda: runner.send(handle, "x"),
                     lambda: runner.collect(handle),
                     lambda: runner.close(handle)):
            with self.assertRaises(sessions.RunnerUnavailable) as caught:
                call()
            self.assertIn("stub", str(caught.exception))


class RunnerChoiceTest(unittest.TestCase):

    def test_supervised_stages_default_to_a_pane_and_mechanical_ones_do_not(self):
        self.assertEqual(sessions.choose_runner("build"), "herdr")
        self.assertEqual(sessions.choose_runner("merge"), "herdr")
        self.assertEqual(sessions.choose_runner("query"), "headless")

    def test_an_unknown_stage_defaults_supervised(self):
        # A stage wrongly run headless has no pane for the question it turns
        # out to have, so the unsafe direction is the one we do not default to.
        self.assertEqual(sessions.choose_runner("something-new"), "herdr")

    def test_config_wins(self):
        self.assertEqual(sessions.choose_runner("build", {"build": "headless"}),
                         "headless")

    def test_runner_for_names_the_alternatives_when_it_fails(self):
        with self.assertRaises(sessions.SessionError) as caught:
            sessions.runner_for("telepathy")
        self.assertIn("herdr", str(caught.exception))


class SettledBeforeStallTest(unittest.TestCase):
    """The stall budget measures a session SEEN working — a settled pane
    resumed with an hours-old origin settles, never stalls."""

    def test_a_settled_session_with_an_ancient_origin_settles(self):
        class Runner:
            def wait(self, handle, timeout=None):
                return sessions.WaitState.SETTLED_DONE
        watch = sessions.supervise(Runner(), object(), origin=0.0,
                                   clock=lambda: 100_000.0)
        self.assertEqual(watch.state, sessions.WaitState.SETTLED_DONE)

    def test_a_working_session_past_the_budget_still_stalls(self):
        class Runner:
            def wait(self, handle, timeout=None):
                return sessions.WaitState.WORKING
        watch = sessions.supervise(Runner(), object(), origin=0.0,
                                   clock=lambda: 100_000.0)
        self.assertEqual(watch.state, sessions.WaitState.STALLED)


# ---------------------------------------------------------------------------
# Launch robustness — transient startup failures retry, corpses are reaped
# ---------------------------------------------------------------------------

class LaunchRobustnessTest(unittest.TestCase):

    def test_not_ready_and_startup_timeout_retry_like_pane_busy(self):
        # Problem 3 (willdan fleet): each of these transients failed the
        # stage outright and the batch waited a whole cycle.
        class Flaky(FakeHerdr):
            def __init__(self):
                super().__init__()
                self.failures = [
                    "timeout — timed out waiting for agent startup",
                    "agent_not_ready — blocked during startup",
                ]

            def __call__(self, argv, cwd=None, env=None, timeout=None):
                if argv[1:3] == ["agent", "start"] and self.failures:
                    self.calls.append(argv)
                    return Result(1, stderr=self.failures.pop(0))
                return super().__call__(argv, cwd=cwd, env=env, timeout=timeout)

        herdr = Flaky()
        sleeps = []
        runner = herdr_runner(run=herdr, sleep=sleeps.append)
        handle = runner.launch(spec())
        self.assertFalse(handle.reused)
        starts = [a for a in herdr.calls if a[1:3] == ["agent", "start"]]
        self.assertEqual(len(starts), 3, "two transients, then success")
        self.assertTrue(sleeps, "retries back off rather than hammering")

    def test_a_non_transient_start_error_fails_on_the_first_try(self):
        class Broken(FakeHerdr):
            def __call__(self, argv, cwd=None, env=None, timeout=None):
                if argv[1:3] == ["agent", "start"]:
                    self.calls.append(argv)
                    return Result(1, stderr="agent_kind_unsupported")
                return super().__call__(argv, cwd=cwd, env=env, timeout=timeout)

        herdr = Broken()
        runner = herdr_runner(run=herdr)
        with self.assertRaises(sessions.SessionError):
            runner.launch(spec())
        starts = [a for a in herdr.calls if a[1:3] == ["agent", "start"]]
        self.assertEqual(len(starts), 1)
        self.assertIn(["herdr", "tab", "close", "w1:t9"], herdr.calls)

    def test_an_agent_that_came_up_behind_a_timeout_is_adopted(self):
        # A startup timeout can return while claude is still booting; the
        # roster then carries the very agent the start asked for, and every
        # re-start would read pane_busy forever. The roster is the truth.
        class LateBoot(FakeHerdr):
            def __call__(self, argv, cwd=None, env=None, timeout=None):
                if argv[1:3] == ["agent", "start"]:
                    self.calls.append(argv)
                    name = argv[3]
                    self.roster[name] = {
                        "name": name, "agent_status": "idle",
                        "terminal_title_stripped": name,
                        "interactive_ready": True,
                        "pane_id": "w1:p9", "tab_id": "w1:t9",
                    }
                    return Result(
                        1, stderr="timeout — timed out waiting for agent startup")
                return super().__call__(argv, cwd=cwd, env=env, timeout=timeout)

        herdr = LateBoot()
        runner = herdr_runner(run=herdr)
        handle = runner.launch(spec())
        starts = [a for a in herdr.calls if a[1:3] == ["agent", "start"]]
        self.assertEqual(len(starts), 1, "the roster hit ends the retries")
        self.assertEqual(handle.ref["pane_id"], "w1:p9")
        prompts = [a for a in herdr.calls if a[1:3] == ["agent", "prompt"]]
        self.assertTrue(prompts, "the adopted boot still gets its order")

    def test_the_start_timeout_matches_the_fleet_drivers(self):
        # 839387a2 granted a cold claude start 300s in bin/flywheel; the
        # runner granting 120s was the source of every startup timeout.
        herdr = FakeHerdr()
        runner = herdr_runner(run=herdr)
        runner.launch(spec())
        start = next(a for a in herdr.calls if a[1:3] == ["agent", "start"])
        self.assertEqual(start[start.index("--timeout") + 1], "300000")

    def test_a_wedged_herdr_call_is_a_failure_not_a_crash(self):
        import subprocess as sp

        class Wedged(FakeHerdr):
            def __call__(self, argv, cwd=None, env=None, timeout=None):
                if argv[1:3] == ["agent", "wait"]:
                    self.calls.append(argv)
                    raise sp.TimeoutExpired(argv, timeout)
                return super().__call__(argv, cwd=cwd, env=env, timeout=timeout)

        herdr = Wedged({"n": {
            "name": "n", "agent_status": "working",
            "terminal_title_stripped": "n", "pane_id": "p", "tab_id": "t"}})
        runner = herdr_runner(run=herdr)
        state = runner.wait(sessions.SessionHandle(name="n", runner="herdr"),
                            timeout=600)
        self.assertEqual(state, WaitState.WORKING,
                         "the roster answers when the wait cannot")


# ---------------------------------------------------------------------------
# Reuse is health-checked — a corpse under the name is reaped, not adopted
# ---------------------------------------------------------------------------

class ReuseHealthTest(unittest.TestCase):

    def row(self, **kw):
        base = {"name": "build-substrate", "agent_status": "idle",
                "terminal_title_stripped": "build-substrate",
                "interactive_ready": True,
                "pane_id": "w1:p3", "tab_id": "w1:t3"}
        base.update(kw)
        return {"build-substrate": base}

    def test_a_blocked_pane_that_never_reached_its_composer_is_reaped(self):
        # The problem-3 shape: a leftover from an earlier failed launch
        # holds the name; adopting it never re-sends the order and every
        # prompt to it returns agent_blocked.
        herdr = FakeHerdr(self.row(agent_status="blocked",
                                   interactive_ready=False))
        runner = herdr_runner(run=herdr)
        handle = runner.launch(spec())
        self.assertFalse(handle.reused)
        self.assertIn(["herdr", "tab", "close", "w1:t3"], herdr.calls,
                      "the corpse's tab is closed before the fresh launch")
        self.assertIn("agent start", herdr.verbs())

    def test_a_blocked_pane_with_a_live_composer_is_reused(self):
        # A real question mid-conversation also reads blocked — a respawned
        # loop must reattach and relay it, never kill the session that asked.
        herdr = FakeHerdr(self.row(agent_status="blocked"))
        runner = herdr_runner(run=herdr)
        handle = runner.launch(spec())
        self.assertTrue(handle.reused)
        self.assertNotIn("tab close", herdr.verbs())
        self.assertNotIn("agent start", herdr.verbs())

    def test_an_unclassified_row_is_reaped_and_relaunched(self):
        herdr = FakeHerdr(self.row(agent_status="unknown"))
        runner = herdr_runner(run=herdr)
        handle = runner.launch(spec())
        self.assertFalse(handle.reused)
        self.assertIn("agent start", herdr.verbs())


# ---------------------------------------------------------------------------
# Settle needs more than one read — a between-turns blip is not a finish
# ---------------------------------------------------------------------------

class SettleDebounceTest(unittest.TestCase):

    def make(self, statuses, **kw):
        class Blip(FakeHerdr):
            def __init__(self, seq):
                super().__init__({"n": {
                    "name": "n", "agent_status": "working",
                    "terminal_title_stripped": "n",
                    "pane_id": "p", "tab_id": "t"}})
                self.seq = list(seq)

            def __call__(self, argv, cwd=None, env=None, timeout=None):
                if argv[1:3] == ["agent", "list"] and self.seq:
                    self.roster["n"]["agent_status"] = self.seq.pop(0)
                return super().__call__(argv, cwd=cwd, env=env, timeout=timeout)

        herdr = Blip(statuses)
        return herdr, herdr_runner(run=herdr, **kw)

    def test_a_momentary_idle_between_turns_does_not_settle(self):
        # Problem 5 (willdan fleet): build-codebuild-fleet was collected
        # and merged 25 minutes before its session finished. One idle read
        # between turns must stay WORKING.
        herdr, runner = self.make(["idle", "working"])
        state = runner.wait(sessions.SessionHandle(name="n", runner="herdr"))
        self.assertEqual(state, WaitState.WORKING)

    def test_a_settle_that_holds_across_spaced_reads_is_believed(self):
        sleeps = []
        herdr, runner = self.make(["idle", "idle", "idle"],
                                  sleep=sleeps.append)
        state = runner.wait(sessions.SessionHandle(name="n", runner="herdr"))
        self.assertEqual(state, WaitState.SETTLED_DONE)
        self.assertEqual(len(sleeps), runner.settle_reads - 1,
                         "the confirming reads are spaced, not back-to-back")

    def test_blocked_returns_on_the_first_read(self):
        # A question deserves the operator now, not after a debounce.
        herdr, runner = self.make(["blocked"])
        state = runner.wait(sessions.SessionHandle(name="n", runner="herdr"))
        self.assertEqual(state, WaitState.SETTLED_BLOCKED)


# ---------------------------------------------------------------------------
# Close is guarded — never a working pane, and the roster's tab wins
# ---------------------------------------------------------------------------

class GuardedCloseTest(unittest.TestCase):

    def test_close_refuses_a_working_pane(self):
        herdr = FakeHerdr({"n": {
            "name": "n", "agent_status": "working",
            "terminal_title_stripped": "n", "pane_id": "p", "tab_id": "t"}})
        runner = herdr_runner(run=herdr)
        runner.close(sessions.SessionHandle(name="n", runner="herdr",
                                            ref={"tab_id": "t"}))
        self.assertNotIn("tab close", runner._run.verbs()
                         if hasattr(runner._run, "verbs") else [])
        self.assertNotIn(["herdr", "tab", "close", "t"], herdr.calls)

    def test_close_reaps_by_roster_tab_when_the_handle_carries_none(self):
        # The intent loop closes sessions its process never launched — a
        # synthesized handle has no tab_id, and closing nothing left panes
        # open forever.
        herdr = FakeHerdr({"n": {
            "name": "n", "agent_status": "idle",
            "terminal_title_stripped": "n", "pane_id": "p", "tab_id": "t"}})
        runner = herdr_runner(run=herdr)
        runner.close(sessions.SessionHandle(name="n", runner="herdr"))
        self.assertIn(["herdr", "tab", "close", "t"], herdr.calls)


# ---------------------------------------------------------------------------
# Trust seeding — the dialog is answered before claude can ask it
# ---------------------------------------------------------------------------

class TrustSeedTest(unittest.TestCase):

    def test_seeding_writes_the_dialog_answer_for_the_path(self):
        import json as j
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "claude.json"
            self.assertTrue(sessions.seed_workspace_trust("/w/build-x", config))
            data = j.loads(config.read_text())
            self.assertTrue(
                data["projects"]["/w/build-x"]["hasTrustDialogAccepted"])

    def test_seeding_is_idempotent_and_preserves_the_rest_of_the_config(self):
        import json as j
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "claude.json"
            config.write_text(j.dumps({
                "theme": "dark",
                "projects": {"/w/build-x": {"hasTrustDialogAccepted": True,
                                            "history": [1, 2]}}}))
            before = j.loads(config.read_text())
            self.assertFalse(sessions.seed_workspace_trust("/w/build-x", config))
            self.assertEqual(j.loads(config.read_text()), before)

    def test_launch_seeds_trust_for_the_spec_cwd(self):
        seeded = []
        runner = herdr_runner(run=FakeHerdr(), seed_trust=seeded.append)
        runner.launch(spec())
        self.assertEqual(seeded, ["/tmp/wt"])

    def test_reuse_seeds_nothing(self):
        seeded = []
        herdr = FakeHerdr({"build-substrate": {
            "name": "build-substrate", "agent_status": "working",
            "terminal_title_stripped": "build-substrate",
            "pane_id": "p", "tab_id": "t"}})
        runner = herdr_runner(run=herdr, seed_trust=seeded.append)
        runner.launch(spec())
        self.assertEqual(seeded, [])


class PluginSeedTest(unittest.TestCase):
    """A repo can enable the flywheel plugin, but claude only loads it where
    an install record exists for that exact project path — a fresh worktree
    boots agentless and the launch times out on an agent that never was."""

    def _records(self, tmp, paths):
        import json as j
        from pathlib import Path
        plugins = Path(tmp) / "installed_plugins.json"
        plugins.write_text(j.dumps({"plugins": {
            sessions.FLYWHEEL_PLUGIN: [{"projectPath": p} for p in paths]}}))
        return plugins

    def test_a_missing_record_installs_the_plugin_in_that_cwd(self):
        import tempfile
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            plugins = self._records(tmp, ["/w/other"])
            ran = sessions.seed_plugin_install(
                "/w/build-x",
                run=lambda argv, cwd=None, env=None, timeout=None:
                    (calls.append((argv, cwd)), Result())[1],
                plugins_path=plugins)
        self.assertTrue(ran)
        self.assertEqual(calls, [(
            ["claude", "plugin", "install", sessions.FLYWHEEL_PLUGIN,
             "--scope", "local"], "/w/build-x")])

    def test_an_existing_record_installs_nothing(self):
        import tempfile
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            plugins = self._records(tmp, ["/w/build-x"])
            ran = sessions.seed_plugin_install(
                "/w/build-x",
                run=lambda *a, **kw: calls.append(a) or Result(),
                plugins_path=plugins)
        self.assertFalse(ran)
        self.assertEqual(calls, [])

    def test_an_unreadable_registry_still_attempts_the_install(self):
        calls = []
        ran = sessions.seed_plugin_install(
            "/w/build-x",
            run=lambda argv, cwd=None, env=None, timeout=None:
                (calls.append(argv), Result())[1],
            plugins_path="/nonexistent/installed_plugins.json")
        self.assertTrue(ran)
        self.assertEqual(len(calls), 1)

    def test_a_failed_install_is_not_a_launch_failure(self):
        def boom(argv, cwd=None, env=None, timeout=None):
            raise OSError("no claude on PATH")
        self.assertFalse(sessions.seed_plugin_install(
            "/w/build-x", run=boom,
            plugins_path="/nonexistent/installed_plugins.json"))

    def test_launch_seeds_the_plugin_for_the_spec_cwd(self):
        seeded = []
        runner = herdr_runner(run=FakeHerdr(), seed_plugin=seeded.append)
        runner.launch(spec())
        self.assertEqual(seeded, ["/tmp/wt"])


if __name__ == "__main__":
    unittest.main()
