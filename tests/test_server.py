"""#74 — the server: one loop process per milestone with a job.

The pass splits into a pure planner and an impure executor, so most of what
this server claims is checkable as arithmetic: `plan()` is a function of
(jobs, teams, host, running, backoff) and nothing else. What is left — the
processes, the archive, the teardown — is exercised through injected `run=`,
`popen=` and `clock=` seams. No network, no `gh`, no token, no sleeping.
"""

import unittest
from pathlib import Path

from context import BIN, inbox, ledger as obs  # noqa: F401 — BIN puts bin/ on sys.path

import _flywheel_server as server  # noqa: E402

Item = inbox.Item
Batch = inbox.Batch
Snapshot = inbox.TrackerSnapshot
Job = inbox.Job


def item(number, *labels, **kw):
    kw.setdefault("milestone", "bolt/a")
    return Item(number=number, labels=frozenset(labels), **kw)


class Result:
    """A `subprocess.CompletedProcess` stand-in."""

    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


class FakeRun:
    """Answers argv prefixes from a table; records every call."""

    def __init__(self, table=None):
        self.table = table or {}
        self.calls = []

    def __call__(self, argv, cwd=None, env=None, timeout=None):
        self.calls.append((tuple(argv), cwd))
        for prefix, result in self.table.items():
            if tuple(argv[:len(prefix)]) == tuple(prefix):
                return result
        return Result()

    def ran(self, *prefix):
        return any(argv[:len(prefix)] == tuple(prefix) for argv, _ in self.calls)


class FakeProc:
    def __init__(self, pid=1234, codes=None):
        self.pid = pid
        self.codes = list(codes or [None])
        self.signals = []

    def poll(self):
        return self.codes[0] if len(self.codes) == 1 else self.codes.pop(0)

    def terminate(self):
        self.signals.append("TERM")

    def kill(self):
        self.signals.append("KILL")


class FakePopen:
    def __init__(self, procs=None):
        self.procs = list(procs or [])
        self.calls = []

    def __call__(self, argv, **kw):
        self.calls.append((tuple(argv), kw))
        return self.procs.pop(0) if self.procs else FakeProc()


class FakeClock:
    def __init__(self, now=1000.0, step=0.0):
        self.now, self.step = now, step

    def __call__(self):
        value = self.now
        self.now += self.step
        return value

    def advance(self, seconds):
        self.now += seconds


class FakeTracker:
    def __init__(self, snapshot=None, board=(), labels=()):
        self._snapshot = snapshot or Snapshot()
        self.board = list(board)
        self.labels = set(labels)      # (number, label)
        self.writes = []

    def snapshot(self, milestone=None, with_edges=True):
        return self._snapshot

    def board_items(self):
        return self.board

    def has_label(self, number, label):
        return (number, label) in self.labels

    def add_label(self, number, label):
        self.labels.add((number, label))
        self.writes.append(("add_label", number, label))

    def comment(self, number, body):
        self.writes.append(("comment", number, body))


class FakeDispatch:
    """The dispatch MCP surface, as the daemon sees it: a factory yielding
    one per-pass session with relay/triage. Records calls and sessions."""

    def __init__(self, result=None):
        self.result = result or {"delivered": True}
        self.calls = []
        self.sessions = 0

    def __call__(self):
        self.sessions += 1
        return self

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def relay(self, items):
        self.calls.append(("relay", items))
        return self.result

    def triage(self, items):
        self.calls.append(("triage", items))
        return self.result


def a_server(tracker=None, run=None, popen=None, clock=None, **kw):
    config = server.ServerConfig(
        org="agentplot", repo="flywheel", host="workstation",
        loops_cwd=Path("/tmp/does-not-need-to-exist"),
        teams=kw.pop("teams", {}), bin_dir=Path("/bin-dir"))
    box = server.Server(
        config, tracker=tracker or FakeTracker(), run=run or FakeRun(),
        popen=popen or FakePopen(), clock=clock or FakeClock(),
        sleep=lambda _s: None, log=kw.pop("log", None) or (lambda _m: None),
        opener=lambda path: None, **kw)
    return box


# ---- 1 · the plan -------------------------------------------------------

class PlanTest(unittest.TestCase):

    def test_a_job_with_no_process_is_started(self):
        got = server.plan([Job("bolt/a", "run", "#1 open")], host="w")
        self.assertEqual([(w.milestone, w.kind, w.slug) for w in got.start],
                         [("bolt/a", "run", "a")])

    def test_a_process_whose_milestone_lost_its_job_is_stopped(self):
        got = server.plan([], host="w", running={("bolt/a", "run")})
        self.assertEqual(got.stop, (("bolt/a", "run"),),
                         "the symmetric rule: no job, no process")

    def test_a_job_whose_process_is_alive_is_left_alone(self):
        got = server.plan([Job("bolt/a", "run")], host="w",
                          running={("bolt/a", "run")})
        self.assertEqual((got.start, got.stop), ((), ()))
        self.assertEqual(got.keep, (("bolt/a", "run"),))

    def test_a_milestone_a_no_loop_owns_is_ignored(self):
        got = server.plan([Job("chore/tidy", "run")], host="w")
        self.assertEqual(got.start, (),
                         "only intent/* and bolt/* have loop programs")

    def test_work_teamed_to_another_host_is_never_started_here(self):
        got = server.plan([Job("bolt/a", "run")], host="workstation",
                          teams={"Platform": "laptop"},
                          board_teams={"bolt/a": "Platform"})
        self.assertEqual(got.start, ())
        self.assertEqual(got.elsewhere, (("bolt/a", "laptop"),))

    def test_re_teaming_work_stops_the_process_already_running_here(self):
        got = server.plan([Job("bolt/a", "run")], host="workstation",
                          teams={"Platform": "laptop"},
                          board_teams={"bolt/a": "Platform"},
                          running={("bolt/a", "run")})
        self.assertEqual(got.stop, (("bolt/a", "run"),),
                         "the operator moved it; this host must let go")

    def test_work_with_no_team_or_an_unmapped_one_runs_here(self):
        for board in ({}, {"bolt/a": "Unmapped"}):
            got = server.plan([Job("bolt/a", "run")], host="workstation",
                              teams={"Platform": "laptop"}, board_teams=board)
            self.assertEqual([w.milestone for w in got.start], ["bolt/a"],
                             f"board_teams={board}")

    def test_an_archive_job_is_a_want_of_its_own_kind(self):
        got = server.plan([Job("bolt/a", "archive", "closed")], host="w")
        self.assertEqual([(w.kind, w.slug) for w in got.start],
                         [("archive", "a")])


# ---- 2 · the backoff ----------------------------------------------------

class BackoffTest(unittest.TestCase):
    """A loop that exits against an unchanged tracker must not be restarted
    every 60 seconds forever — `server_inbox` hands out a `run` job for an
    item at `state:in-progress`, and the loop STOPs when nothing is *ready*."""

    def test_an_exit_against_an_unchanged_job_holds_the_restart(self):
        held = server.Backoff()
        held.record_exit("#1 in-progress", now=1000)
        got = server.plan([Job("bolt/a", "run", "#1 in-progress")], host="w",
                          now=1001, backoff={("bolt/a", "run"): held})
        self.assertEqual(got.start, ())
        self.assertEqual(got.waiting, (("bolt/a", 59),))

    def test_the_hold_expires(self):
        held = server.Backoff()
        held.record_exit("#1 in-progress", now=1000)
        got = server.plan([Job("bolt/a", "run", "#1 in-progress")], host="w",
                          now=1000 + server.BACKOFF_BASE_S,
                          backoff={("bolt/a", "run"): held})
        self.assertEqual([w.milestone for w in got.start], ["bolt/a"])

    def test_a_changed_job_releases_the_hold_at_once(self):
        held = server.Backoff()
        held.record_exit("#1 in-progress", now=1000)
        got = server.plan([Job("bolt/a", "run", "#2 ready")], host="w",
                          now=1001, backoff={("bolt/a", "run"): held})
        self.assertEqual([w.milestone for w in got.start], ["bolt/a"],
                         "the tracker moved, so there is new work to do")

    def test_repeated_exits_double_the_hold_up_to_the_ceiling(self):
        held = server.Backoff()
        for _ in range(20):
            held.record_exit("same", now=1000)
        self.assertEqual(held.wait_left(1000, "same"), server.BACKOFF_MAX_S)


# ---- 3 · the command lines ----------------------------------------------

class ArgvTest(unittest.TestCase):

    def test_a_bolt_milestone_starts_the_bolt_loop_on_its_slug(self):
        box = a_server(run=FakeRun({("git", "worktree"): Result(1)}))
        argv = box.argv_for(Job("bolt/loop-server", "run"))
        self.assertEqual(argv[0], "/bin-dir/flywheel-bolt-loop")
        self.assertIn("--slug", argv)
        self.assertEqual(argv[argv.index("--slug") + 1], "loop-server")
        self.assertEqual(argv[argv.index("--repo-dir") + 1],
                         "/tmp/does-not-need-to-exist")

    def test_an_intent_milestone_starts_the_intent_loop(self):
        argv = a_server().argv_for(Job("intent/kit-lift", "run"))
        self.assertEqual(argv[0], "/bin-dir/flywheel-intent-loop")
        self.assertEqual(argv[argv.index("--slug") + 1], "kit-lift")

    def test_the_bolt_branchs_worktree_is_read_from_git_when_it_exists(self):
        porcelain = ("worktree /w/main\nHEAD abc\nbranch refs/heads/main\n\n"
                     "worktree /w/bolt-x\nHEAD def\n"
                     "branch refs/heads/bolt/x\n")
        box = a_server(run=FakeRun({("git", "worktree"): Result(0, porcelain)}))
        argv = box.argv_for(Job("bolt/x", "run"))
        self.assertEqual(argv[argv.index("--bolt-worktree") + 1], "/w/bolt-x")

    def test_no_completion_signal_is_ever_invented(self):
        # R1 is open. The intent loop is built to run every stage up to
        # supervision and stop before collecting, saying so; a default here
        # would answer the operator's question for them, inside a daemon.
        argv = a_server().argv_for(Job("intent/x", "run"))
        self.assertNotIn("--completion-signal", argv)


# ---- 4 · the pass -------------------------------------------------------

class PassTest(unittest.TestCase):

    def test_a_ready_item_starts_one_loop_process(self):
        tracker = FakeTracker(Snapshot(items=[item(1, inbox.READY)]))
        popen = FakePopen()
        box = a_server(tracker=tracker, popen=popen)
        box.pass_once()
        self.assertEqual(len(popen.calls), 1)
        self.assertIn("flywheel-bolt-loop", popen.calls[0][0][0])
        self.assertIn(("bolt/a", "run"), box.processes)

    def test_a_second_pass_starts_nothing_more(self):
        tracker = FakeTracker(Snapshot(items=[item(1, inbox.READY)]))
        popen = FakePopen([FakeProc(codes=[None])])
        box = a_server(tracker=tracker, popen=popen)
        box.pass_once()
        box.pass_once()
        self.assertEqual(len(popen.calls), 1,
                         "the live process is the job being done")

    def test_a_dry_pass_starts_nothing_and_writes_nothing(self):
        tracker = FakeTracker(Snapshot(items=[item(1, inbox.READY)]))
        popen, run = FakePopen(), FakeRun()
        box = a_server(tracker=tracker, popen=popen, run=run, dry_run=True)
        box.pass_once()
        self.assertEqual(popen.calls, [])
        self.assertEqual(tracker.writes, [])

    def test_an_exited_loop_is_reaped_and_leaves_the_registry(self):
        tracker = FakeTracker(Snapshot(items=[item(1, inbox.READY)]))
        popen = FakePopen([FakeProc(codes=[0])])
        box = a_server(tracker=tracker, popen=popen)
        box.pass_once()      # starts it; the pass reaps before it starts
        box.reap()           # the loop has since stopped, as loops do
        self.assertEqual(box.processes, {})
        self.assertEqual(box.backoff[("bolt/a", "run")].exits, 1)

    def test_a_tracker_that_raises_leaves_the_daemon_and_registry_intact(self):
        class Exploding(FakeTracker):
            def snapshot(self, milestone=None, with_edges=True):
                raise SystemExit("flywheel: gh api failed: 502")

        box = a_server(tracker=Exploding())
        box.processes[("bolt/a", "run")] = "sentinel"
        self.assertEqual(box.pass_once(), 1)
        self.assertIn(("bolt/a", "run"), box.processes,
                      "one bad read must not tear the fleet down")

    def test_relay_and_triage_are_each_called_once_in_one_pass(self):
        snap = Snapshot(items=[
            item(1, inbox.NEEDS_OPERATOR),
            item(2, milestone=None),
        ])
        dispatch = FakeDispatch()
        box = a_server(tracker=FakeTracker(snap), dispatch=dispatch)
        box.pass_once()
        kinds = [kind for kind, _items in dispatch.calls]
        self.assertEqual(kinds, ["relay", "triage"],
                         "both queues in one pass, escalations first")
        relay_items = dispatch.calls[0][1]
        self.assertEqual(relay_items[0]["number"], 1)
        self.assertEqual(relay_items[0]["url"],
                         "https://github.com/agentplot/flywheel/issues/1")
        self.assertIn("title", relay_items[0])
        self.assertEqual(dispatch.calls[1][1][0]["number"], 2)

    def test_one_pass_opens_one_dispatch_session_for_both_calls(self):
        snap = Snapshot(items=[
            item(1, inbox.NEEDS_OPERATOR),
            item(2, milestone=None),
        ])
        dispatch = FakeDispatch()
        box = a_server(tracker=FakeTracker(snap), dispatch=dispatch)
        box.pass_once()
        self.assertEqual(dispatch.sessions, 1,
                         "the proxy's own-busy rule needs one shared session")

    def test_a_dry_pass_logs_the_queues_and_opens_no_session(self):
        snap = Snapshot(items=[item(1, inbox.NEEDS_OPERATOR)])
        dispatch = FakeDispatch()
        lines = []
        box = a_server(tracker=FakeTracker(snap), dispatch=dispatch,
                       dry_run=True, log=lines.append)
        box.pass_once()
        self.assertEqual(dispatch.sessions, 0)
        self.assertTrue(any("would relay: #1" in line for line in lines))


# ---- 5 · stopping -------------------------------------------------------

class StopTest(unittest.TestCase):

    def test_a_stop_is_a_sigterm_then_a_sigkill_on_the_next_pass(self):
        box = a_server()
        proc = FakeProc(codes=[None])
        box.processes[("bolt/a", "run")] = server.LoopProcess(
            key=("bolt/a", "run"), want=server.Want("bolt/a", "run", "a"),
            proc=proc)
        box.stop(("bolt/a", "run"), "no job")
        self.assertEqual(proc.signals, ["TERM"])
        box.stop(("bolt/a", "run"), "no job")
        self.assertEqual(proc.signals, ["TERM", "KILL"])

    def test_shutdown_takes_every_child_down(self):
        box = a_server()
        procs = [FakeProc(pid=1, codes=[None]), FakeProc(pid=2, codes=[None])]
        for n, proc in enumerate(procs):
            key = (f"bolt/{n}", "run")
            box.processes[key] = server.LoopProcess(
                key=key, want=server.Want(f"bolt/{n}", "run", str(n)),
                proc=proc)
        box.stop_all()
        self.assertEqual(box.processes, {})
        for proc in procs:
            self.assertEqual(proc.signals, ["TERM", "KILL"])


# ---- 6 · the archive one-shot -------------------------------------------

class ArchiveTest(unittest.TestCase):
    """`openspec archive <slug> --yes --json` is deterministic and cannot
    prompt — openspec 1.8.0's archive.js says JSON mode "never prompts at
    all" and turns each decision point into a machine-readable diagnostic on
    a non-zero exit. So the mechanism is code, and only the decision the code
    cannot take reaches the operator."""

    def want(self):
        return server.Want("bolt/a", "archive", "a", why="closed milestone")

    def test_a_clean_archive_is_committed_by_pathspec(self):
        run = FakeRun({
            ("openspec", "archive"): Result(0),
            ("git", "rev-parse"): Result(1),          # not mid-merge
            ("git", "status"): Result(0, " M openspec/specs/x/spec.md\n"),
        })
        self.assertTrue(a_server(run=run).archive(self.want(), Snapshot()))
        self.assertTrue(run.ran("openspec", "archive", "a", "--yes", "--json"))
        self.assertTrue(run.ran("git", "commit"))
        commits = [argv for argv, _ in run.calls if argv[:2] == ("git", "commit")]
        self.assertEqual(commits[0][-2:], ("--", "openspec/"),
                         "by pathspec, never -a and never a tree-wide add")

    def test_a_blocked_archive_commits_nothing_and_reaches_the_operator(self):
        blocked = ('{"diagnostics":[{"severity":"error",'
                   '"code":"archive_confirmation_required",'
                   '"message":"Updating 3 spec(s) requires confirmation"}]}')
        run = FakeRun({("openspec", "archive"): Result(1, blocked)})
        tracker = FakeTracker(Snapshot(items=[item(7, milestone="bolt/a")]))
        box = a_server(tracker=tracker, run=run)
        snap = tracker.snapshot()
        self.assertFalse(box.archive(self.want(), snap))
        self.assertFalse(run.ran("git", "commit"))
        self.assertIn(("add_label", 7, inbox.NEEDS_OPERATOR), tracker.writes)
        self.assertTrue(any("Updating 3 spec(s)" in w[2]
                            for w in tracker.writes if w[0] == "comment"))

    def test_a_second_blocked_pass_writes_nothing(self):
        # The dry-cycle property, on this path too: `set_needs_operator`
        # writes only when the label is absent.
        run = FakeRun({("openspec", "archive"): Result(1, "", "nope")})
        tracker = FakeTracker(Snapshot(items=[item(7, milestone="bolt/a")]))
        box = a_server(tracker=tracker, run=run)
        snap = tracker.snapshot()
        box.archive(self.want(), snap)
        tracker.writes.clear()
        box.archive(self.want(), snap)
        self.assertEqual(tracker.writes, [])

    def test_a_mid_merge_checkout_is_never_committed_into(self):
        run = FakeRun({
            ("openspec", "archive"): Result(0),
            ("git", "rev-parse"): Result(0, "abc123"),   # MERGE_HEAD exists
        })
        tracker = FakeTracker(Snapshot(items=[item(7, milestone="bolt/a")]))
        box = a_server(tracker=tracker, run=run)
        self.assertFalse(box.archive(self.want(), tracker.snapshot()))
        self.assertFalse(run.ran("git", "commit"))

    def test_an_archive_with_nothing_to_commit_is_a_success(self):
        run = FakeRun({
            ("openspec", "archive"): Result(0),
            ("git", "rev-parse"): Result(1),
            ("git", "status"): Result(0, "\n"),
        })
        self.assertTrue(a_server(run=run).archive(self.want(), Snapshot()))


# ---- 7 · state on disk --------------------------------------------------

class StateTest(unittest.TestCase):

    def test_the_state_directory_follows_xdg_and_never_a_literal_home(self):
        got = server.state_dir("agentplot", environ={"XDG_STATE_HOME": "/x"})
        self.assertEqual(got, Path("/x/flywheel/agentplot"))
        fallback = server.state_dir("agentplot", environ={}, home="/h")
        self.assertEqual(fallback, Path("/h/.local/state/flywheel/agentplot"))

    def test_a_pidfile_whose_process_is_gone_is_not_a_running_server(self):
        # Two servers on one host would start every loop twice, so the pid is
        # probed rather than trusted.
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = server.pid_path("o", environ={"XDG_STATE_HOME": tmp})
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("4242\n")
            env = {"XDG_STATE_HOME": tmp}
            self.assertIsNone(server.running_pid("o", alive=lambda _p: False,
                                                 environ=env))
            self.assertEqual(server.running_pid("o", alive=lambda _p: True,
                                                environ=env), 4242)


class DispatchLedgerTest(unittest.TestCase):
    """#4.1 — dispatch activity is observable through the same surface,
    one ledger step per tool call, with the non-delivery's reason."""

    def snap(self):
        return Snapshot(items=[item(1, inbox.NEEDS_OPERATOR)])

    def test_a_delivered_relay_writes_expect_and_actual(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            led = obs.RunLedger(tmp, "dispatch")
            box = a_server(tracker=FakeTracker(self.snap()), ledger=led,
                           dispatch=FakeDispatch())
            box.pass_once()
            kinds = [e["kind"] for e in led.entries]
            self.assertIn("expect", kinds)
            self.assertIn("actual", kinds)
            actual = next(e for e in led.entries if e["kind"] == "actual")
            self.assertTrue(actual["ok"])
            self.assertEqual(actual["step"], "relay:1")

    def test_a_failed_delivery_is_a_recorded_divergence_with_its_reason(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            led = obs.RunLedger(tmp, "dispatch")
            refusing = FakeDispatch(
                {"delivered": False, "reason": "dispatch is busy (working)"})
            box = a_server(tracker=FakeTracker(self.snap()), ledger=led,
                           dispatch=refusing)
            self.assertEqual(box.pass_once(), 1)
            actual = next(e for e in led.entries if e["kind"] == "actual")
            self.assertFalse(actual["ok"])
            self.assertIn("dispatch is busy (working)", actual["outcome"])
            text = led.write_report().read_text()
            self.assertIn("diverged", text)


if __name__ == "__main__":
    unittest.main()
