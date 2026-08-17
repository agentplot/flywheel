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
         milestone="bolt/observer-rework"):
    return inbox.PlanCard(number=number, title=title, body=body,
                          status=status, team=team, stale=stale,
                          blocked_by=tuple(blocked_by), milestone=milestone)


class PlanCardTest(unittest.TestCase):
    def test_slug_system_and_provenance_parse(self):
        c = card()
        self.assertEqual(c.slug, "observer-rework")
        self.assertEqual(c.system, "flywheel")
        self.assertEqual(c.derived_from, ("abc1234", "def5678"))

    def test_task_table_parses_with_after(self):
        tasks = inbox.plan_tasks(PLAN_BODY)
        self.assertEqual([t["change"] for t in tasks],
                         ["first-change", "second-change"])
        self.assertEqual(tasks[0]["after"], "")
        self.assertEqual(tasks[1]["after"], "first-change")

    def test_ready_card_is_a_server_job(self):
        snap = inbox.TrackerSnapshot(plan_cards=[card()])
        jobs = inbox.server_inbox(snap)
        self.assertIn(("bolt/observer-rework", "run"),
                      [(j.milestone, j.kind) for j in jobs])

    def test_backlog_card_is_not_a_job(self):
        snap = inbox.TrackerSnapshot(plan_cards=[card(status="Backlog")])
        self.assertEqual(inbox.server_inbox(snap), [])


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


class ExpansionTest(unittest.TestCase):
    def loop(self, tracker):
        params = bolt.BoltParams(slug="observer-rework", repo_dir=".")
        return bolt.BoltLoop(params, tracker)

    def test_expansion_full_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = bolt.FixtureTracker(fixture(tmp, [card_item()]))
            loop = self.loop(tracker)
            actions = []
            failure = loop.guard_expand(tracker.snapshot(), actions)
            self.assertIsNone(failure)
            kinds = [w[0] for w in tracker.writes]
            self.assertIn("create_milestone", kinds)
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
            loop.guard_expand(tracker.snapshot(), [])
            before = list(tracker.writes)
            failure = loop.guard_expand(tracker.snapshot(), [])
            self.assertIsNone(failure)
            self.assertEqual(tracker.writes, before,
                             "the second pass writes nothing")

    def test_no_team_refuses_with_needs_operator(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = bolt.FixtureTracker(fixture(tmp, [card_item(team=None)]))
            loop = self.loop(tracker)
            failure = loop.guard_expand(tracker.snapshot(), [])
            self.assertIn("no Team", failure)
            self.assertIn("needs-operator", tracker._item(12)["labels"])
            self.assertNotIn("create_milestone",
                             [w[0] for w in tracker.writes])

    def test_blocked_by_unlanded_predecessor_defers(self):
        with tempfile.TemporaryDirectory() as tmp:
            items = [card_item(blocked_by=[11]),
                     {"number": 11, "title": "Bolt: predecessor",
                      "labels": ["plan"], "milestone": None,
                      "state": "open", "blocked_by": []}]
            tracker = bolt.FixtureTracker(fixture(tmp, items))
            loop = self.loop(tracker)
            failure = loop.guard_expand(tracker.snapshot(), [])
            self.assertIsNone(failure, "a defer is not a pause")
            self.assertEqual(tracker.writes, [], "a defer writes nothing")

    def test_blocked_by_landed_predecessor_expands(self):
        with tempfile.TemporaryDirectory() as tmp:
            items = [card_item(blocked_by=[11]),
                     {"number": 11, "title": "Bolt: predecessor",
                      "labels": ["unit", "closed:done"], "milestone": "bolt/predecessor",
                      "state": "closed", "blocked_by": []}]
            tracker = bolt.FixtureTracker(fixture(tmp, items))
            loop = self.loop(tracker)
            failure = loop.guard_expand(tracker.snapshot(), [])
            self.assertIsNone(failure)
            self.assertIn("create_milestone", [w[0] for w in tracker.writes])


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
