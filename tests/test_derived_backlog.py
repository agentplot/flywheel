"""The derived backlog: plan cards, planner triggers, and expansion.

The spec is `flywheel-derived-backlog`. The fake stage here exercises the
whole path — a card parsed, a run charged, an approval expanded — with no
network, no model, and a fake clock.
"""

import json
import tempfile
import unittest
from pathlib import Path

from context import BIN  # noqa: F401 — sys.path side effect

import _flywheel_inbox as inbox
import _flywheel_server as server
import _flywheel_bolt_loop as bolt


PLAN_BODY = """System: flywheel

Two sentences of goal.

Sequence: 1 of 2 · builds on: none

| # | change | delivers | chapters | after | why this bolt |
|---|--------|----------|----------|-------|---------------|
| 1 | first-change | the base | books/flywheel/src/a.md | — | base |
| 2 | second-change | the rest | books/flywheel/src/b.md | first-change | rest |

Derived from: book abc1234 · specs def5678
"""


def card(number=12, status="Ready", team="workstation", body=PLAN_BODY,
         stale=False, blocked_by=(), title="Unit: observer-rework",
         milestone="bolt/observer-rework", milestone_state="open"):
    return inbox.PlanCard(number=number, title=title, body=body,
                          status=status, team=team, stale=stale,
                          blocked_by=tuple(blocked_by), milestone=milestone,
                          milestone_state=milestone_state)


class PlanCardTest(unittest.TestCase):
    def test_slug_system_and_provenance_parse(self):
        c = card()
        self.assertEqual(c.slug, "observer-rework")
        self.assertEqual(c.system, "flywheel")
        self.assertEqual(c.derived_from, ("abc1234", "def5678"))
        self.assertEqual(c.bolt, "bolt/observer-rework")

    def test_task_table_parses_with_after(self):
        tasks = inbox.plan_tasks(PLAN_BODY)
        self.assertEqual([t["change"] for t in tasks],
                         ["first-change", "second-change"])
        self.assertEqual(tasks[0]["after"], "")
        self.assertEqual(tasks[1]["after"], "first-change")

    def test_a_card_with_no_bolt_milestone_names_no_bolt(self):
        # No fallback to the title slug: a name synthesized from a title is
        # not a milestone the tracker holds. `slug` still parses.
        c = card(milestone=None)
        self.assertIsNone(c.bolt)
        self.assertEqual(c.slug, "observer-rework")
        self.assertIsNone(card(milestone="intent/design").bolt)


class ReadyCardIsABoltJobTest(unittest.TestCase):
    """The server inbox's card block: which milestone the job carries, and
    which reason that milestone reports."""

    def test_ready_card_is_a_server_job(self):
        snap = inbox.TrackerSnapshot(plan_cards=[card()])
        jobs = inbox.server_inbox(snap)
        self.assertIn(("bolt/observer-rework", "run"),
                      [(j.milestone, j.kind) for j in jobs])
        # The reason is what the run record prints and what the restart
        # backoff fingerprints, so the card must be legible in it.
        why = [j.why for j in jobs if j.milestone == "bolt/observer-rework"]
        self.assertEqual(why, ["plan card #12 at Ready, awaiting expansion"])

    def test_backlog_card_is_not_a_job(self):
        snap = inbox.TrackerSnapshot(plan_cards=[card(status="Backlog")])
        self.assertEqual(inbox.server_inbox(snap), [])

    def test_a_ready_card_with_no_bolt_milestone_is_not_a_job(self):
        # The title still says `Unit: observer-rework`; the server no longer
        # reads it as one. Nothing may name `bolt/observer-rework` here.
        snap = inbox.TrackerSnapshot(plan_cards=[card(milestone=None)])
        self.assertEqual(inbox.server_inbox(snap), [])

    def test_a_ready_card_on_a_closed_milestone_is_not_a_run_job(self):
        # The same test the Ready-batch set and the per-item loop make: a run
        # job on a closed milestone collides with that milestone's archive job.
        snap = inbox.TrackerSnapshot(
            plan_cards=[card(milestone_state="closed")])
        self.assertEqual(
            [j for j in inbox.server_inbox(snap) if j.kind == "run"], [])

    def test_the_cards_reason_wins_over_every_other_reason(self):
        # A Ready card also reaches the pass as a synthetic Ready batch, and
        # its milestone may hold a state:ready item too. One run job, and the
        # card is what it says the loop was started for.
        snap = inbox.TrackerSnapshot(
            items=[inbox.Item(number=7, milestone="bolt/observer-rework",
                              labels=frozenset({inbox.READY}))],
            batches=[inbox.Batch(number=9, kind=inbox.UNIT,
                                 status=inbox.STATUS_READY,
                                 milestone="bolt/observer-rework")],
            plan_cards=[card()])
        jobs = inbox.server_inbox(snap)
        self.assertEqual([(j.milestone, j.kind) for j in jobs],
                         [("bolt/observer-rework", "run")])
        self.assertEqual(jobs[0].why,
                         "plan card #12 at Ready, awaiting expansion")


class OperatorWaitsTest(unittest.TestCase):
    """`flywheel status`'s "waiting on the operator" block, at the pure seam
    `server_rows` builds it from."""

    def test_a_backlog_card_waits_on_the_operator(self):
        snap = inbox.TrackerSnapshot(plan_cards=[card(status="Backlog")])
        lines = inbox.operator_waits(snap, inbox.server_inbox(snap))
        self.assertEqual(len(lines), 1)
        self.assertIn("plan card #12", lines[0])
        self.assertIn("bolt/observer-rework", lines[0])
        self.assertIn("flip to Ready", lines[0])

    def test_a_ready_card_is_counted_by_its_job_row_not_here(self):
        snap = inbox.TrackerSnapshot(plan_cards=[card()])
        jobs = inbox.server_inbox(snap)
        self.assertEqual(inbox.operator_waits(snap, jobs), ())

    def test_a_ready_card_naming_no_bolt_milestone_is_reported(self):
        # It yields no job, so this line is the only place it can surface.
        snap = inbox.TrackerSnapshot(plan_cards=[card(milestone=None)])
        lines = inbox.operator_waits(snap, inbox.server_inbox(snap))
        self.assertEqual(len(lines), 1)
        self.assertIn("plan card #12", lines[0])
        self.assertIn("no bolt milestone", lines[0])

    def test_a_card_with_no_board_status_is_reported(self):
        # "every open, unexpanded `plan` card" — a card with no board row at
        # all yields no job, so the report is the only surface it has.
        snap = inbox.TrackerSnapshot(plan_cards=[card(status=None)])
        lines = inbox.operator_waits(snap, inbox.server_inbox(snap))
        self.assertEqual(len(lines), 1)
        self.assertIn("plan card #12", lines[0])
        self.assertIn("not on the board", lines[0])

    def test_batches_and_needs_operator_items_still_read_as_one_list(self):
        snap = inbox.TrackerSnapshot(
            items=[inbox.Item(number=5, title="a defect",
                              labels=frozenset({inbox.NEEDS_OPERATOR}),
                              milestone="bolt/observer-rework")],
            batches=[inbox.Batch(number=9, kind=inbox.UNIT, status="Backlog",
                                 milestone="bolt/observer-rework")],
            plan_cards=[card(number=12, status="Backlog")])
        lines = inbox.operator_waits(snap, ())
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[0].startswith("batch #9 at Backlog"))
        self.assertTrue(lines[1].startswith("plan card #12 at Backlog"))
        self.assertTrue(lines[2].startswith("#5 needs-operator"))


class CardThroughTheRealSnapshotTest(unittest.TestCase):
    """One Ready card reaches `server_inbox` as **two** objects: the card,
    and the synthetic Ready `Batch` that `Tracker.snapshot`'s board backfill
    builds for the same row. A hand-built `TrackerSnapshot` carries only the
    first, so the card block's closed-milestone guard can look right there
    while the backfill re-adds the job it declined. These drive the real
    `Tracker.snapshot` so both objects are in play."""

    class FakeTracker(inbox.Tracker):
        def __init__(self, milestone_state="open"):
            super().__init__("token", "org", "repo", project_title="Flywheel")
            self.milestone_state = milestone_state

        def open_issues(self):
            return [{"number": 12, "title": "Unit: observer-rework",
                     "body": PLAN_BODY, "state": "open",
                     "labels": [{"name": "plan"}],
                     "milestone": {"title": "bolt/observer-rework",
                                   "state": self.milestone_state}}]

        def merge_closed_issues(self):
            return []

        def board_items(self):
            return [{"number": 12, "status": "Ready", "team": "workstation",
                     "state": "OPEN", "milestone": "bolt/observer-rework"}]

        def closed_milestones(self):
            return (["bolt/observer-rework"]
                    if self.milestone_state == "closed" else [])

        def sub_issues(self, number):
            return []

        def blocked_by(self, number):
            # `with_edges=False` is the server's and `status`'s whole reason
            # for existing: no per-issue calls. A card must not make one.
            raise AssertionError(
                f"per-issue edge call for #{number} under with_edges=False")

    def snapshot(self, milestone_state="open"):
        return self.FakeTracker(milestone_state).snapshot(with_edges=False)

    def test_the_backfilled_batch_carries_the_real_milestone_state(self):
        snap = self.snapshot("closed")
        self.assertEqual([b.milestone_state for b in snap.batches], ["closed"])

    def test_a_ready_card_on_a_closed_milestone_yields_no_run_job(self):
        # The card block declines; the backfilled batch must not re-add it,
        # or the run job collides with this milestone's archive job.
        snap = self.snapshot("closed")
        jobs = inbox.server_inbox(snap)
        self.assertEqual([(j.milestone, j.kind) for j in jobs],
                         [("bolt/observer-rework", "archive")])

    def test_that_card_is_reported_as_waiting_instead(self):
        snap = self.snapshot("closed")
        lines = inbox.operator_waits(snap, inbox.server_inbox(snap))
        self.assertEqual(len(lines), 1)
        self.assertIn("plan card #12", lines[0])
        self.assertIn("its milestone is closed", lines[0])

    def test_an_open_milestone_still_yields_the_cards_run_job(self):
        snap = self.snapshot("open")
        jobs = inbox.server_inbox(snap)
        self.assertEqual([(j.milestone, j.kind) for j in jobs],
                         [("bolt/observer-rework", "run")])
        self.assertEqual(jobs[0].why,
                         "plan card #12 at Ready, awaiting expansion")
        self.assertEqual(inbox.operator_waits(snap, jobs), ())


class FixtureCardTest(unittest.TestCase):
    """`from_fixture` must reach a card's milestone fields the way it already
    reaches its sibling `Batch`'s — until it does, no fixture can express the
    closed-milestone scenario at all, and both loops build snapshots from
    fixtures."""

    def test_a_fixture_card_inherits_the_milestone_and_carries_its_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = fixture(tmp, [{"number": 12,
                                  "title": "Unit: observer-rework",
                                  "body": PLAN_BODY, "labels": ["plan"],
                                  "milestone_state": "closed"}])
            snap = inbox.TrackerSnapshot.from_fixture(path)
        card_ = snap.plan_cards[0]
        self.assertEqual(card_.bolt, "bolt/observer-rework")
        self.assertEqual(card_.milestone_state, "closed")


class DispatchFilterTest(unittest.TestCase):
    def test_a_plan_card_is_never_triage(self):
        item = inbox.Item(number=12, title="Unit: x",
                          labels=frozenset({"plan"}), milestone=None)
        box = inbox.dispatch_inbox(inbox.TrackerSnapshot(items=[item]))
        self.assertEqual(box.triage, ())


class AddressRoutingTest(unittest.TestCase):
    def plan_for(self, host):
        job = inbox.Job("bolt/x", "run", "why")
        return server.plan([job], host=host,
                           board_teams={"bolt/x": "afterthought@mac-studio"},
                           argv_for=lambda j: ["argv"])

    def test_address_routes_to_its_host(self):
        current = self.plan_for("mac-studio")
        self.assertEqual([w.milestone for w in current.start], ["bolt/x"])

    def test_address_routes_away_from_other_hosts(self):
        current = self.plan_for("macbook-pro")
        self.assertEqual(current.start, ())
        self.assertEqual(current.elsewhere, (("bolt/x", "mac-studio"),))

    def test_bare_value_still_uses_the_legacy_map(self):
        job = inbox.Job("bolt/x", "run", "why")
        current = server.plan([job], host="mac-studio",
                              teams={"flywheel": "mac-studio"},
                              board_teams={"bolt/x": "flywheel"},
                              argv_for=lambda j: ["argv"])
        self.assertEqual([w.milestone for w in current.start], ["bolt/x"])


class RecordingTracker:
    def __init__(self):
        self.labels_added = []

    def add_label(self, number, label):
        self.labels_added.append((number, label))


def make_server(books=None, tracker=None, planner=None, heads=None,
                now=1_000_000.0):
    config = server.ServerConfig(books=books or {})
    logs = []
    daemon = server.Server(
        config, tracker=tracker or RecordingTracker(),
        planner=planner, heads=heads,
        clock=lambda: now, log=logs.append)
    return daemon, logs


BINDING = {"book": "/b", "repo": "/r", "team": "ws", "settle_minutes": 90}


class PlannerTriggerTest(unittest.TestCase):
    def heads(self, epoch):
        return lambda binding, run=None: ("abc1234", epoch, "def5678")

    def test_missing_cards_on_settled_book_charges_a_run(self):
        charges = []
        daemon, _ = make_server(
            books={"flywheel": BINDING},
            planner=lambda name, b, order: charges.append(order) or True,
            heads=self.heads(1_000_000.0 - 90 * 60))
        daemon.plan_runs(inbox.TrackerSnapshot())
        self.assertEqual(len(charges), 1)
        self.assertIn("bolt planning for flywheel", charges[0])
        self.assertIn("mode: board", charges[0])

    def test_moving_book_charges_nothing(self):
        charges = []
        daemon, _ = make_server(
            books={"flywheel": BINDING},
            planner=lambda name, b, order: charges.append(order) or True,
            heads=self.heads(1_000_000.0 - 60))
        daemon.plan_runs(inbox.TrackerSnapshot())
        self.assertEqual(charges, [])

    def test_fresh_cards_charge_nothing(self):
        charges = []
        daemon, _ = make_server(
            books={"flywheel": BINDING},
            planner=lambda name, b, order: charges.append(order) or True,
            heads=self.heads(1_000_000.0 - 90 * 60))
        daemon.plan_runs(inbox.TrackerSnapshot(
            plan_cards=[card(status="Backlog")]))
        self.assertEqual(charges, [])

    def test_stale_card_is_marked_once_and_charges_when_settled(self):
        charges = []
        tracker = RecordingTracker()
        daemon, _ = make_server(
            books={"flywheel": BINDING}, tracker=tracker,
            planner=lambda name, b, order: charges.append(order) or True,
            heads=lambda binding, run=None: ("fff9999", 1_000_000.0 - 90 * 60,
                                             "def5678"))
        snap = inbox.TrackerSnapshot(plan_cards=[card(status="Backlog")])
        daemon.plan_runs(snap)
        self.assertEqual(tracker.labels_added, [(12, inbox.STALE)])
        self.assertEqual(len(charges), 1)
        # second pass: card now carries the marker — no second label write
        marked = inbox.TrackerSnapshot(
            plan_cards=[card(status="Backlog", stale=True)])
        daemon.backoff.clear()
        daemon.plan_runs(marked)
        self.assertEqual(tracker.labels_added, [(12, inbox.STALE)])

    def test_ready_card_is_never_marked(self):
        tracker = RecordingTracker()
        daemon, _ = make_server(
            books={"flywheel": BINDING}, tracker=tracker,
            heads=lambda binding, run=None: ("fff9999", 0, "def5678"))
        daemon.plan_runs(inbox.TrackerSnapshot(plan_cards=[card()]))
        self.assertEqual(tracker.labels_added, [])

    def test_charge_backs_off(self):
        charges = []
        daemon, _ = make_server(
            books={"flywheel": BINDING},
            planner=lambda name, b, order: charges.append(order) or True,
            heads=self.heads(1_000_000.0 - 90 * 60))
        daemon.plan_runs(inbox.TrackerSnapshot())
        daemon.plan_runs(inbox.TrackerSnapshot())
        self.assertEqual(len(charges), 1, "the second pass is held on backoff")


SECOND_BODY = """System: flywheel

The second unit, approved later.

Sequence: 2 of 2 · builds on: observer-rework

| # | change | delivers | chapters | after | why this bolt |
|---|--------|----------|----------|-------|---------------|
| 1 | third-change | the follow-on | books/flywheel/src/c.md | — | later |

Derived from: book abc1234 · specs def5678
"""


def fixture(tmp, items):
    path = Path(tmp) / "tracker.json"
    path.write_text(json.dumps({"milestone": "bolt/observer-rework",
                                "items": items}) + "\n")
    return path


def card_item(**kw):
    base = {"number": 12, "title": "Unit: observer-rework", "body": PLAN_BODY,
            "labels": ["plan"], "milestone": "bolt/observer-rework",
            "status": "Ready", "team": "workstation", "blocked_by": []}
    base.update(kw)
    return base


def unit_item(number=11, slug="predecessor", **kw):
    """An already-expanded unit card: `unit`, open, on this milestone."""
    base = {"number": number, "title": f"Unit: {slug}", "body": PLAN_BODY,
            "labels": ["unit"], "milestone": "bolt/observer-rework",
            "state": "open", "blocked_by": []}
    base.update(kw)
    return base


def work_item(number, parent=11, state="open", labels=("state:ready",), **kw):
    base = {"number": number, "title": f"change-{number}", "body": "",
            "labels": list(labels), "milestone": "bolt/observer-rework",
            "state": state, "blocked_by": [], "parent_batch": parent}
    base.update(kw)
    return base


class ExpansionTest(unittest.TestCase):
    MILESTONE = "bolt/observer-rework"

    def loop(self, tracker):
        params = bolt.BoltParams(slug="observer-rework", repo_dir=".")
        return bolt.BoltLoop(params, tracker)

    def snap(self, tracker):
        """The snapshot `cycle()` hands the guards: scoped to the
        milestone, so an issue off it is invisible and the guard's one
        fallback read is what answers for it."""
        return tracker.snapshot(self.MILESTONE)

    def test_expansion_full_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = bolt.FixtureTracker(fixture(tmp, [card_item()]))
            loop = self.loop(tracker)
            actions = []
            failure = loop.guard_expand(self.snap(tracker), actions)
            self.assertIsNone(failure)
            kinds = [w[0] for w in tracker.writes]
            self.assertNotIn("create_milestone", kinds,
                             "the milestone is the planner's write")
            self.assertNotIn("set_milestone", kinds,
                             "the planner already milestoned the card")
            self.assertIn("clear_board_status", kinds)
            self.assertEqual(kinds.count("create_item"), 2)
            self.assertEqual(kinds.count("attach_sub_issue"), 2)
            unit = tracker._item(12)
            self.assertIn("unit", unit["labels"])
            self.assertNotIn("plan", unit["labels"])
            self.assertEqual(unit["milestone"], "bolt/observer-rework")
            self.assertIsNone(unit["status"])
            items = [tracker._item(n) for n in (13, 14)]
            self.assertEqual([i["title"] for i in items],
                             ["first-change", "second-change"])
            for i in items:
                self.assertIn("state:ready", i["labels"])
                self.assertEqual(i["milestone"], "bolt/observer-rework")
                self.assertEqual(i["parent_batch"], 12)
            self.assertIn("After: first-change", items[1]["body"])

    def test_expanded_card_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = bolt.FixtureTracker(fixture(tmp, [card_item()]))
            loop = self.loop(tracker)
            loop.guard_expand(self.snap(tracker), [])
            before = list(tracker.writes)
            failure = loop.guard_expand(self.snap(tracker), [])
            self.assertIsNone(failure)
            self.assertEqual(tracker.writes, before,
                             "the second pass writes nothing")

    def test_a_second_approval_expands_beside_the_first_unit(self):
        # A bolt sees expansion once per approval, not once in its life,
        # and expanding one unit leaves every other one alone.
        with tempfile.TemporaryDirectory() as tmp:
            items = [unit_item(11, "observer-rework"), work_item(9, parent=11),
                     card_item(number=12, title="Unit: second-unit",
                               body=SECOND_BODY)]
            tracker = bolt.FixtureTracker(fixture(tmp, items))
            loop = self.loop(tracker)
            failure = loop.guard_expand(self.snap(tracker), [])
            self.assertIsNone(failure)
            self.assertIn("unit", tracker._item(12)["labels"])
            first, its_item = tracker._item(11), tracker._item(9)
            self.assertEqual(first["labels"], ["unit"])
            self.assertEqual(its_item["labels"], ["state:ready"])
            self.assertEqual(its_item["parent_batch"], 11)
            self.assertNotIn(11, [w[1] for w in tracker.writes])
            self.assertNotIn(9, [w[1] for w in tracker.writes])

    def test_a_card_on_another_bolts_milestone_is_not_ours_to_expand(self):
        for milestone in ("bolt/somewhere-else", None):
            with self.subTest(milestone=milestone):
                with tempfile.TemporaryDirectory() as tmp:
                    tracker = bolt.FixtureTracker(fixture(
                        tmp, [card_item(milestone=milestone)]))
                    loop = self.loop(tracker)
                    actions = []
                    failure = loop.guard_expand(self.snap(tracker), actions)
                    self.assertIsNone(failure)
                    self.assertEqual(tracker.writes, [])
                    self.assertEqual(actions, [])

    def test_no_team_refuses_with_needs_operator(self):
        with tempfile.TemporaryDirectory() as tmp:
            items = [unit_item(11, "sibling"), card_item(team=None)]
            tracker = bolt.FixtureTracker(fixture(tmp, items))
            loop = self.loop(tracker)
            failure = loop.guard_expand(self.snap(tracker), [])
            self.assertIn("no Team", failure)
            card = tracker._item(12)
            self.assertIn("needs-operator", card["labels"])
            self.assertIn("plan", card["labels"], "nothing was expanded")
            self.assertIn("so the unit is unroutable",
                          " ".join(card["comments"][0]["body"].split()))
            # the bolt's other units are untouched by the refusal
            self.assertEqual(tracker._item(11)["labels"], ["unit"])
            self.assertEqual([w[0] for w in tracker.writes],
                             ["add_label", "comment"])

    def test_an_unexpanded_predecessor_defers(self):
        # Its work has not been born yet, so there is nothing that could
        # be in. The wait is a deferral, never a refusal.
        with tempfile.TemporaryDirectory() as tmp:
            items = [card_item(blocked_by=[11]),
                     {"number": 11, "title": "Unit: predecessor",
                      "labels": ["plan"], "milestone": "bolt/observer-rework",
                      "status": "Backlog", "state": "open", "blocked_by": []}]
            tracker = bolt.FixtureTracker(fixture(tmp, items))
            loop = self.loop(tracker)
            failure = loop.guard_expand(self.snap(tracker), [])
            self.assertIsNone(failure, "a defer is not a pause")
            self.assertEqual(tracker.writes, [], "a defer writes nothing")

    def test_a_half_built_predecessor_defers(self):
        with tempfile.TemporaryDirectory() as tmp:
            items = [card_item(blocked_by=[11]), unit_item(11),
                     work_item(9, state="closed", labels=("closed:merged",)),
                     work_item(10, state="open")]
            tracker = bolt.FixtureTracker(fixture(tmp, items))
            loop = self.loop(tracker)
            failure = loop.guard_expand(self.snap(tracker), [])
            self.assertIsNone(failure, "a defer is not a pause")
            self.assertEqual(tracker.writes, [], "a defer writes nothing")

    def test_a_predecessor_whose_work_all_merged_expands(self):
        # The blocker itself is STILL OPEN — it closes only at the landing,
        # and the landing waits on the cards. Closure as the predicate is
        # what deadlocked; the merge is the fact this reads.
        with tempfile.TemporaryDirectory() as tmp:
            items = [card_item(blocked_by=[11]), unit_item(11),
                     work_item(9, state="closed", labels=("closed:merged",)),
                     work_item(10, state="closed", labels=("closed:merged",))]
            tracker = bolt.FixtureTracker(fixture(tmp, items))
            loop = self.loop(tracker)
            failure = loop.guard_expand(self.snap(tracker), [])
            self.assertIsNone(failure)
            self.assertEqual(tracker._item(11)["state"], "open")
            self.assertIn("unit", tracker._item(12)["labels"])

    def test_a_blocker_off_the_milestone_falls_back_to_one_tracker_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            items = [card_item(blocked_by=[11]),
                     {"number": 11, "title": "Something else",
                      "labels": ["closed:superseded"], "milestone": None,
                      "state": "closed", "blocked_by": []}]
            tracker = bolt.FixtureTracker(fixture(tmp, items))
            loop = self.loop(tracker)
            failure = loop.guard_expand(self.snap(tracker), [])
            self.assertIsNone(failure)
            self.assertIn("unit", tracker._item(12)["labels"],
                          "a closed blocker is closed, whatever the reason")


def result(returncode=0, stdout="", stderr=""):
    return type("R", (), {"returncode": returncode, "stdout": stdout,
                          "stderr": stderr})()


class FakeGit:
    """A git small enough to answer "is this committed?" honestly.

    `show HEAD:<path>` reads a committed snapshot, `add` stages, and a
    SUCCESSFUL `commit` is the only thing that moves a staged file into
    that snapshot. So a commit that fails leaves HEAD behind exactly as a
    real one would — which is the whole of what `guard_charter`'s
    committed-content test has to survive. A shell that answered every
    call green is why the torn-commit hole went unseen.
    """

    def __init__(self, root, head=None, fail_commit=False):
        self.root = Path(root)
        self.head = dict(head or {})
        self.fail_commit = fail_commit
        self.staged = []
        self.calls = []

    def __call__(self, argv, cwd=None, env=None, timeout=None):
        argv = tuple(argv)
        self.calls.append((argv, cwd))
        if argv[:2] == ("git", "show"):
            rel = argv[2].split(":", 1)[1]
            if rel not in self.head:
                return result(128, stderr=f"path '{rel}' does not exist in HEAD")
            return result(0, stdout=self.head[rel])
        if argv[:2] == ("git", "add"):
            self.staged += [a for a in argv[2:] if a != "--"]
            return result(0)
        if argv[:2] == ("git", "commit"):
            if self.fail_commit:
                return result(1, stderr="the pre-commit hook refused")
            for rel in self.staged:
                self.head[rel] = (self.root / rel).read_text()
            self.staged = []
            return result(0)
        return result(0)

    def of(self, verb):
        return [(a, cwd) for a, cwd in self.calls if a[:2] == ("git", verb)]


class NotTheFixtureTracker:
    """Stands in for the live tracker.

    `guard_charter` reads nothing off the tracker object — the snapshot
    carries the units — but it refuses to touch git when the tracker IS a
    `FixtureTracker`, because `guard_topology` skips itself there and
    `bolt_worktree` would still be the operator's own checkout. So these
    tests must not hand it one.
    """


class CharterTest(unittest.TestCase):
    """`guard_charter` — every expanded unit's plan document, in git.

    The scaffold session copies the first unit's document; a bolt of units
    sees expansion once per approval, and this guard is what carries the
    rest. Its test is what the charter carries AT HEAD, so it is
    idempotent without storing anything and a torn commit is retried.
    """

    MILESTONE = "bolt/observer-rework"
    REL = "openspec/changes/observer-rework/bolt.md"
    CHARTER = "# Unit: observer-rework\n\nthe first unit's document\n"

    def setup(self, tmp, items, charter=CHARTER, committed=True,
              tracker=None, fail_commit=False):
        # The bolt's worktree is NOT the main one — `repo_dir` is where a
        # fresh process starts and `guard_topology` is what moves it. Two
        # distinct paths, or "the commit ran in the bolt's worktree" is a
        # claim no assertion here could fail.
        main = Path(tmp) / "main"
        main.mkdir()
        tree = Path(tmp) / "tree"
        (tree / "openspec" / "changes" / "observer-rework").mkdir(parents=True)
        record = tree / self.REL
        if charter is not None:
            record.write_text(charter)
        # HEAD carries the charter the scaffold session committed, unless a
        # test wants the un-committed case.
        head = {self.REL: charter} if (charter and committed) else {}
        git = FakeGit(tree, head=head, fail_commit=fail_commit)
        snapshot = bolt.FixtureTracker(fixture(tmp, items)).snapshot(
            self.MILESTONE)
        params = bolt.BoltParams(slug="observer-rework", repo_dir=str(main),
                                 bolt_worktree=str(tree))
        loop = bolt.BoltLoop(params, tracker or NotTheFixtureTracker(),
                             run=git)
        return loop, git, record, snapshot

    def two_units(self):
        return [unit_item(11, "observer-rework"),
                unit_item(12, "second-unit", body=SECOND_BODY)]

    def test_a_missing_unit_section_is_appended_and_committed(self):
        with tempfile.TemporaryDirectory() as tmp:
            loop, git, record, snap = self.setup(tmp, self.two_units())
            actions = []
            self.assertIsNone(loop.guard_charter(snap, actions))
            text = record.read_text()
            self.assertIn("# Unit: second-unit", text)
            self.assertIn("The second unit, approved later.", text)
            self.assertLess(text.index("# Unit: observer-rework"),
                            text.index("# Unit: second-unit"),
                            "appended after what the charter already held")
            self.assertIn("the first unit's document", text)
            self.assertEqual([a for a, _ in git.of("add")],
                             [("git", "add", "--", self.REL)])
            commits = git.of("commit")
            self.assertEqual(len(commits), 1, "one commit, one path")
            self.assertEqual(commits[0][0][-2:], ("--", self.REL),
                             "by pathspec — never -a, never add -A")
            self.assertEqual(git.head[self.REL], text, "and it reached HEAD")
            self.assertEqual(len(actions), 1)

    def test_every_git_call_runs_in_the_bolts_worktree(self):
        # "committed to the branch that carries the bolt's record" is a
        # statement about WHERE, and nothing else here observes it.
        with tempfile.TemporaryDirectory() as tmp:
            loop, git, record, snap = self.setup(tmp, self.two_units())
            loop.guard_charter(snap, [])
            self.assertTrue(git.calls)
            self.assertNotEqual(loop.params.bolt_worktree,
                                loop.params.repo_dir,
                                "or this assertion proves nothing")
            for argv, cwd in git.calls:
                self.assertEqual(cwd, loop.params.bolt_worktree, str(argv))

    def test_a_second_pass_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            loop, git, record, snap = self.setup(tmp, self.two_units())
            loop.guard_charter(snap, [])
            before = record.read_text()
            actions = []
            self.assertIsNone(loop.guard_charter(snap, actions))
            self.assertEqual(record.read_text(), before)
            self.assertEqual(len(git.of("commit")), 1, "no second commit")
            self.assertEqual(len(git.of("add")), 1)
            self.assertEqual(actions, [], "a dry cycle records nothing")

    def test_a_hand_edited_section_is_never_overwritten(self):
        # Durable prose in git outranks mutable tracker state: the heading
        # is the test, so an edited section is left exactly as it stands.
        with tempfile.TemporaryDirectory() as tmp:
            edited = "# Unit: observer-rework\n\nrewritten by hand\n"
            loop, git, record, snap = self.setup(
                tmp, [unit_item(11, "observer-rework")], charter=edited)
            self.assertIsNone(loop.guard_charter(snap, []))
            self.assertEqual(record.read_text(), edited)
            self.assertEqual(git.of("commit"), [])

    def test_a_heading_in_another_case_is_still_the_same_unit(self):
        # The heading is the ONLY idempotency test the guard has, so a
        # section a session wrote `# unit:` must not be appended again —
        # once per pass, forever.
        with tempfile.TemporaryDirectory() as tmp:
            loop, git, record, snap = self.setup(
                tmp, [unit_item(11, "observer-rework")],
                charter="# unit: Observer-Rework\n\nlower-case heading\n")
            self.assertIsNone(loop.guard_charter(snap, []))
            self.assertEqual(record.read_text().count("nit:"), 1)
            self.assertEqual(git.of("commit"), [])

    def test_a_bolt_with_no_unit_cards_leaves_the_charter_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            plain = "## Scope\n\na quick bolt born at triage\n"
            loop, git, record, snap = self.setup(
                tmp, [work_item(9, parent=None)], charter=plain)
            self.assertIsNone(loop.guard_charter(snap, []))
            self.assertEqual(record.read_text(), plain)
            self.assertEqual(git.of("commit"), [])

    def test_no_charter_yet_is_the_scaffolds_to_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            loop, git, record, snap = self.setup(
                tmp, [unit_item(11, "observer-rework")], charter=None)
            self.assertIsNone(loop.guard_charter(snap, []))
            self.assertFalse(record.exists())
            self.assertEqual(git.calls, [])

    def test_a_charter_not_yet_in_head_falls_back_to_the_working_tree(self):
        # The scaffold session wrote bolt.md but its commit has not landed
        # in HEAD yet: there is nothing else to compare against, and the
        # first unit's section must not be duplicated on top of itself.
        with tempfile.TemporaryDirectory() as tmp:
            loop, git, record, snap = self.setup(
                tmp, [unit_item(11, "observer-rework")], committed=False)
            self.assertIsNone(loop.guard_charter(snap, []))
            self.assertEqual(record.read_text(), self.CHARTER)
            self.assertEqual(git.of("commit"), [])

    def test_the_bolts_merge_criteria_survive_an_appended_unit(self):
        # `merge_criteria()` reads the FIRST `## Merge criteria`, and a unit
        # document's own subsections are `##`. Appending keeps the bolt's.
        with tempfile.TemporaryDirectory() as tmp:
            charter = ("## Scope\n\nthe bolt\n\n"
                       "## Merge criteria\n\nthe bolt's own criteria\n")
            loop, git, record, snap = self.setup(
                tmp, [unit_item(11, "later", body="## Merge criteria\n\nthe "
                                                  "unit's\n")], charter=charter)
            self.assertIsNone(loop.guard_charter(snap, []))
            self.assertIn("# Unit: later", record.read_text())
            self.assertEqual(loop.merge_criteria(), "the bolt's own criteria")

    def test_a_torn_commit_is_named_and_retried_on_the_next_pass(self):
        # THE failure mode the committed-content test exists for. The
        # section is on disk the moment write_text returns; if the guard
        # asked the working tree "is it there?" it would answer yes
        # forever and the commit would never be retried.
        with tempfile.TemporaryDirectory() as tmp:
            loop, git, record, snap = self.setup(tmp, self.two_units(),
                                                 fail_commit=True)
            failure = loop.guard_charter(snap, [])
            self.assertIn("commit failed", failure)
            self.assertIn("# Unit: second-unit", record.read_text(),
                          "the working tree has it")
            self.assertNotIn("second-unit", git.head[self.REL],
                             "and HEAD does not")

            # ...the operator clears whatever refused the commit.
            git.fail_commit = False
            torn = record.read_text()
            actions = []
            self.assertIsNone(loop.guard_charter(snap, actions))
            self.assertEqual(record.read_text(), torn,
                             "appended once, not twice")
            self.assertIn("# Unit: second-unit", git.head[self.REL],
                          "the retry is what committed it")
            self.assertEqual(len(actions), 1)

    def test_a_fixture_run_never_writes_the_operators_checkout(self):
        # `guard_topology` skips itself under a fixture tracker, so
        # `bolt_worktree` is still `repo_dir` — the operator's own tree, on
        # whatever branch is out. Latent today only because no fixture
        # carries a unit card.
        with tempfile.TemporaryDirectory() as tmp:
            tracker = bolt.FixtureTracker(fixture(tmp, self.two_units()))
            loop, git, record, snap = self.setup(tmp, self.two_units(),
                                                 tracker=tracker)
            actions = []
            self.assertIsNone(loop.guard_charter(snap, actions))
            self.assertEqual(record.read_text(), self.CHARTER)
            self.assertEqual(git.of("commit"), [])
            self.assertEqual(git.of("add"), [])
            self.assertEqual(actions, [])

    def test_a_dry_run_says_what_it_would_append_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            loop, git, record, snap = self.setup(tmp, self.two_units())
            loop.dry_run = True
            actions = []
            self.assertIsNone(loop.guard_charter(snap, actions))
            self.assertEqual(record.read_text(), self.CHARTER)
            self.assertEqual(git.of("commit"), [])
            self.assertEqual(len(actions), 1)
            self.assertIn("would append", actions[0])
            self.assertIn("second-unit", actions[0])

    def test_the_charter_guard_runs_after_topology_names_the_worktree(self):
        # design.md makes this a Decision, and every other test here calls
        # guard_charter directly with `bolt_worktree` already set — so a
        # reorder would commit into the MAIN worktree with the suite green.
        with tempfile.TemporaryDirectory() as tmp:
            tracker = bolt.FixtureTracker(fixture(tmp, [unit_item(11)]))
            loop, git, record, snap = self.setup(tmp, [unit_item(11)],
                                                 tracker=tracker)
            seen = []

            def watch(name):
                original = getattr(loop, name)

                def call(*a, **kw):
                    seen.append(name)
                    return original(*a, **kw)
                setattr(loop, name, call)

            for name in ("guard_expand", "guard_scaffold", "guard_topology",
                         "guard_charter", "guard_flip_consume", "guard_route",
                         "guard_stages"):
                watch(name)
            loop.guards(snap)
            self.assertEqual(seen[:4], ["guard_expand", "guard_scaffold",
                                        "guard_topology", "guard_charter"])


class PlannerRecordConsistencyTest(unittest.TestCase):
    """The planner is prose-driven: its record IS the two files a run reads.

    Nothing executes a planning run, so the only thing that can hold the
    requirement "The planner session is hosted by its own profile" is a
    read of the surfaces the run loads — the bolt-planning skill's
    Delivery section and the planner profile's card conventions.

    These pin the propositions, not the phrasing. A wording change should
    keep them green; retiring the bolt-of-units shape should not.
    """

    ROOT = BIN.parent
    SURFACES = (("skills", "bolt-planning", "SKILL.md"),
                ("agents", "flywheel-bolt-planner.md"))

    def flat(self, *parts):
        """The file as one line — a proposition split across a line break
        is the same proposition."""
        return " ".join(self.ROOT.joinpath(*parts).read_text().split())

    def test_every_surface_names_the_unit_card_title(self):
        for parts in self.SURFACES:
            self.assertIn("Unit: <slug>", self.flat(*parts), str(parts))

    def test_every_surface_makes_the_milestone_a_planner_write(self):
        for parts in self.SURFACES:
            flat = self.flat(*parts)
            self.assertIn("bolt/<slug>` milestone", flat, str(parts))
            self.assertIn("bolt summary as its description", flat, str(parts))

    def test_every_surface_creates_the_milestone_only_when_it_is_missing(self):
        # Scenario "the milestone already exists": a second run files onto
        # the existing milestone rather than creating a second one. Without
        # this, a rewrite that drops the conditional — leaving a flat
        # "create the milestone" — stays green and the scenario is lost.
        for parts in self.SURFACES:
            self.assertRegex(
                self.flat(*parts),
                r"if it does not (already )?exist"
                r"|created if missing"
                r"|if it is missing",
                str(parts))

    def test_every_surface_files_the_cards_on_that_milestone(self):
        for parts in self.SURFACES:
            flat = self.flat(*parts)
            self.assertRegex(flat,
                             r"card per (proposed )?unit ON th(at|e) milestone",
                             str(parts))

    def test_every_surface_sets_the_team_at_filing(self):
        for parts in self.SURFACES:
            flat = self.flat(*parts)
            self.assertIn("Status Backlog", flat, str(parts))
            self.assertIn("work order's Team", flat, str(parts))

    def test_every_surface_mirrors_builds_on_as_blocked_by(self):
        for parts in self.SURFACES:
            flat = self.flat(*parts)
            self.assertIn("blocked-by", flat, str(parts))
            self.assertIn("unit cards", flat, str(parts))

    def test_every_surface_supersedes_the_unapproved_cards(self):
        for parts in self.SURFACES:
            self.assertIn("supersed", self.flat(*parts).lower(), str(parts))
        # The skill states the contract in full, so it carries the label.
        self.assertIn("closed:superseded",
                      self.flat("skills", "bolt-planning", "SKILL.md"))

    def test_the_skill_still_bounds_the_run_to_those_writes(self):
        flat = self.flat("skills", "bolt-planning", "SKILL.md")
        self.assertIn("no `state:*` label", flat)
        self.assertIn("no work items", flat)

    def test_no_surface_still_titles_a_filed_card_bolt(self):
        # The retired proposition, pinned by the title form itself: a
        # `Bolt:` heading in design/plans/ is a record of a run already
        # made, but neither surface a run READS may still ask for one.
        for parts in self.SURFACES:
            self.assertNotIn("Bolt: ", self.flat(*parts), str(parts))

    def test_no_surface_still_says_the_filed_card_is_milestone_less(self):
        # Bans the retired proposition — the filed card has no milestone —
        # in the three ways it was and would be written: "no milestone",
        # "unmilestoned"/"un-milestoned", "without a milestone".
        #
        # Deliberately NOT a ban on the bare substring "milestoned": an
        # affirmative statement of the NEW shape ("the card is milestoned
        # on `bolt/<slug>`") must stay green, and a guard on the old shape
        # that trips on the new one pins phrasing rather than proposition.
        for parts in self.SURFACES:
            self.assertNotRegex(
                self.flat(*parts),
                r"no milestone|un-?milestoned|without a milestone",
                str(parts))


if __name__ == "__main__":
    unittest.main()


class PerChangeDriveTest(unittest.TestCase):
    """Each expanded plan task is its own change, its own session, its own
    `build/<change>` branch; the plan's After chain defers an item until
    its predecessor merges (construction-loop.md)."""

    def sibling(self, number, change, state="open", labels=(), after=()):
        return inbox.Item(
            number=number, title=change,
            body=f"Change: {change}\n\ndelivers",
            labels=frozenset(labels), state=state,
            milestone="bolt/observer-rework", parent_batch=12,
            change=change, after=tuple(after))

    def snapshot(self, items):
        return inbox.TrackerSnapshot(
            items=items,
            batches=[inbox.Batch(number=12, kind="unit",
                                 sub_issues=tuple(i.number for i in items),
                                 milestone="bolt/observer-rework")])

    def test_distinct_changes_ride_alone(self):
        a = self.sibling(13, "first-change")
        b = self.sibling(14, "second-change")
        batches = bolt.analyse((a, b), self.snapshot([a, b]),
                               "observer-rework")
        self.assertEqual([(x.slug, x.numbers) for x in batches],
                         [("first-change", (13,)), ("second-change", (14,))])
        self.assertEqual([x.change for x in batches],
                         ["first-change", "second-change"])

    def test_changeless_siblings_still_ride_together(self):
        a = inbox.Item(number=13, title="a finding", parent_batch=12)
        b = inbox.Item(number=14, title="another", parent_batch=12)
        batches = bolt.analyse((a, b), self.snapshot([a, b]),
                               "observer-rework")
        self.assertEqual([(x.slug, x.numbers) for x in batches],
                         [("observer-rework-13", (13, 14))])

    def test_after_defers_until_the_predecessor_merges(self):
        done = self.sibling(13, "first-change")
        second = self.sibling(14, "second-change", after=("first-change",))
        snap = self.snapshot([done, second])
        runnable, held = bolt.after_split(snap, (done, second))
        self.assertEqual([i.number for i in runnable], [13])
        self.assertEqual([(i.number, why) for i, why in held],
                         [(14, "waits for #13 to merge")])
        merged = self.sibling(13, "first-change", state="closed",
                              labels=("closed:merged",))
        snap = self.snapshot([merged, second])
        runnable, held = bolt.after_split(snap, (second,))
        self.assertEqual([i.number for i in runnable], [14])
        self.assertEqual(held, ())

    def test_an_ordinal_after_resolves_to_the_nth_sibling(self):
        first = self.sibling(13, "first-change")
        second = self.sibling(14, "second-change", after=("1",))
        snap = self.snapshot([first, second])
        _runnable, held = bolt.after_split(snap, (second,))
        self.assertEqual([(i.number, why) for i, why in held],
                         [(14, "waits for #13 to merge")])

    def test_an_unresolvable_after_never_deadlocks(self):
        only = self.sibling(13, "first-change", after=("no-such-change",))
        runnable, held = bolt.after_split(self.snapshot([only]), (only,))
        self.assertEqual([i.number for i in runnable], [13])
        self.assertEqual(held, ())

    def test_live_items_carry_change_and_after_from_the_body(self):
        raw = {"number": 14, "title": "second-change",
               "body": "Change: second-change\n\nthe rest\n\n"
                       "Chapters: books/flywheel/src/b.md\n\n"
                       "After: first-change",
               "labels": [{"name": "state:ready"}],
               "milestone": {"title": "bolt/observer-rework"}}
        item = inbox.Item.from_api(raw)
        self.assertEqual(item.change, "second-change")
        self.assertEqual(item.after, ("first-change",))

    def test_expansion_stamps_the_change_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = bolt.FixtureTracker(fixture(tmp, [card_item()]))
            params = bolt.BoltParams(slug="observer-rework", repo_dir=".")
            bolt.BoltLoop(params, tracker).guard_expand(tracker.snapshot(), [])
            self.assertTrue(tracker._item(13)["body"].startswith(
                "Change: first-change"))

    def test_an_open_predecessor_at_stage_merged_satisfies_the_chain(self):
        # The merge step may leave the item open at stage:merged awaiting
        # the landing — merged is merged, whichever closure model wrote it.
        merged = self.sibling(13, "first-change",
                              labels=("state:in-progress", "stage:merged"))
        second = self.sibling(14, "second-change", after=("first-change",))
        runnable, held = bolt.after_split(
            self.snapshot([merged, second]), (second,))
        self.assertEqual([i.number for i in runnable], [14])
        self.assertEqual(held, ())


class ClosedMilestoneJobTest(unittest.TestCase):
    """The operator's close releases the landing — and the loop must stay
    alive for both halves of what follows: merged items awaiting their
    upgrade, and the born-ready fix item a failed landing files."""

    def job_for(self, item):
        return [(j.milestone, j.kind) for j in inbox.server_inbox(
            inbox.TrackerSnapshot(items=[item]))]

    def test_a_merged_item_on_a_closed_bolt_milestone_is_a_job(self):
        merged = inbox.Item(number=5, milestone="bolt/x",
                            milestone_state="closed", state="closed",
                            labels=frozenset({"closed:merged"}))
        self.assertIn(("bolt/x", "run"), self.job_for(merged))

    def test_a_ready_fix_item_on_a_closed_bolt_milestone_is_a_job(self):
        fix = inbox.Item(number=9, milestone="bolt/x",
                         milestone_state="closed",
                         labels=frozenset({"state:ready"}))
        self.assertIn(("bolt/x", "run"), self.job_for(fix))

    def test_a_closed_intent_milestone_item_is_never_a_job(self):
        stray = inbox.Item(number=9, milestone="intent/x",
                           milestone_state="closed",
                           labels=frozenset({"state:ready"}))
        self.assertEqual(self.job_for(stray), [])
