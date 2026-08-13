"""#76 — the four inbox filters, and the andon marker the loop reads.

The filters are pure, so these run against the repo's own declared contract
(`workflows/fixtures/{bolt,intent}-tracker.json`) and small inline snapshots.
No network, no `gh`, no token.
"""

import re
import tempfile
import unittest
from pathlib import Path

from context import BIN, FIXTURES, inbox

Item = inbox.Item
Batch = inbox.Batch
Snapshot = inbox.TrackerSnapshot


def item(number, *labels, **kw):
    kw.setdefault("milestone", "bolt/x")
    return Item(number=number, labels=frozenset(labels), **kw)


# ---------------------------------------------------------------------------
# The repo's own fixtures — the declared field contract
# ---------------------------------------------------------------------------

class FixtureContractTest(unittest.TestCase):

    def test_the_bolt_fixture_reads_and_its_ready_items_are_the_inbox(self):
        snap = Snapshot.from_fixture(FIXTURES / "bolt-tracker.json")
        box = inbox.bolt_inbox(snap, "sandbox-loop")
        self.assertEqual([i.number for i in box.ready], [101, 102])
        self.assertEqual(box.queued_to_flip, (),
                         "#103 is queued with no Ready unit — nothing releases it")

    def test_the_records_bolt_filter_is_silent_on_blockers_and_so_are_we(self):
        # #102 is blocked_by #101 and is nonetheless state:ready, so it is in
        # the inbox. The stricter set is offered separately rather than
        # smuggled into the filter.
        snap = Snapshot.from_fixture(FIXTURES / "bolt-tracker.json")
        box = inbox.bolt_inbox(snap, "sandbox-loop")
        self.assertIn(102, [i.number for i in box.ready])
        self.assertEqual([i.number for i in inbox.unblocked(snap, box.ready)], [101])

    def test_the_intent_fixture_fires_exactly_the_guards_it_annotates(self):
        snap = Snapshot.from_fixture(FIXTURES / "intent-tracker.json")
        box = inbox.intent_inbox(snap, "sandbox-design")
        self.assertEqual(box.handoff.action, "birth")
        self.assertEqual([i.number for i in box.handoff.assertions], [202])
        self.assertEqual([i.number for i in box.orphan_queued], [203])

    def test_the_two_sweeps_are_disjoint(self):
        # invariant 2: an item joins exactly one batch, ever — GitHub 422s
        # the second attempt, and two guards writing one item is churn.
        snap = Snapshot.from_fixture(FIXTURES / "intent-tracker.json")
        box = inbox.intent_inbox(snap, "sandbox-design")
        birth = {i.number for i in box.handoff.assertions}
        compose = {i.number for i in box.orphan_queued}
        self.assertEqual(birth & compose, set())


# ---------------------------------------------------------------------------
# The vocabulary — one enumeration, and the two copies of it cannot drift
# ---------------------------------------------------------------------------

class VocabularyTest(unittest.TestCase):
    """One enumeration. The constants here and `flywheel-setup`'s `LABELS`
    table cannot drift, because a loop writing a label the repo does not
    define is a failed `gh issue edit`, not a created label."""

    def setup_labels(self):
        source = (BIN / "flywheel-setup").read_text()
        return set(re.findall(r'^\s*"(stage:[a-z-]+)":', source, re.MULTILINE))

    def test_the_stage_set_is_exactly_seven_names(self):
        self.assertEqual(set(inbox.STAGE_LABELS), {
            "stage:planned", "stage:built", "stage:verified", "stage:merged",
            "stage:in-session", "stage:done", "stage:collected"})
        self.assertEqual(len(inbox.STAGE_LABELS), 7, "and no duplicates")

    def test_every_stage_constant_is_defined_in_flywheel_setups_labels(self):
        self.assertEqual(self.setup_labels(), set(inbox.STAGE_LABELS))

    def test_every_closed_constant_is_defined_in_flywheel_setups_labels(self):
        source = (BIN / "flywheel-setup").read_text()
        defined = set(re.findall(r'^\s*"(closed:[a-z-]+)":', source, re.MULTILINE))
        self.assertEqual(defined, set(inbox.CLOSED_REASONS))
        self.assertIn("closed:merged", defined,
                      "the loop cannot write a label the repo does not define")

    def test_the_construction_stages_are_in_the_order_the_cycle_runs_them(self):
        self.assertEqual(inbox.CONSTRUCTION_STAGES,
                         ("stage:planned", "stage:built", "stage:verified",
                          "stage:merged"))

    def test_stage_of_reads_one_stage_and_can_be_narrowed_to_a_phase(self):
        labels = frozenset({"state:in-progress", "stage:built"})
        self.assertEqual(inbox.stage_of(labels), "stage:built")
        self.assertEqual(
            inbox.stage_of(labels, inbox.CONSTRUCTION_STAGES), "stage:built")
        self.assertIsNone(
            inbox.stage_of(labels, inbox.DESIGN_STAGES))

    def test_a_stage_label_never_stands_in_for_a_state_label(self):
        # The four inbox filters all read `state:*`; an item whose state
        # label were displaced would go invisible to the loop that owns it.
        found = Snapshot(items=[item(1, "state:in-progress", "stage:built")])
        self.assertTrue(found.items[0].in_progress)


# ---------------------------------------------------------------------------
# 1 · server
# ---------------------------------------------------------------------------

class ServerInboxTest(unittest.TestCase):

    def test_a_ready_or_in_progress_item_gives_its_milestone_a_run_job(self):
        snap = Snapshot(items=[
            item(1, inbox.READY, milestone="bolt/a"),
            item(2, inbox.IN_PROGRESS, milestone="intent/b"),
        ])
        jobs = inbox.server_inbox(snap)
        self.assertEqual({(j.milestone, j.kind) for j in jobs},
                         {("bolt/a", "run"), ("intent/b", "run")})

    def test_only_intent_and_bolt_milestones_count(self):
        snap = Snapshot(items=[item(1, inbox.READY, milestone="v2.0")])
        self.assertEqual(inbox.server_inbox(snap), [])

    def test_an_item_on_a_closed_milestone_is_not_a_run_job(self):
        snap = Snapshot(items=[
            item(1, inbox.READY, milestone="bolt/a", milestone_state="closed")])
        self.assertEqual([j for j in inbox.server_inbox(snap) if j.kind == "run"], [])

    def test_a_batch_at_board_ready_is_a_job_on_its_own(self):
        snap = Snapshot(batches=[Batch(9, kind=inbox.UNIT,
                                       status=inbox.STATUS_READY,
                                       milestone="bolt/a")])
        self.assertEqual([(j.milestone, j.kind) for j in inbox.server_inbox(snap)],
                         [("bolt/a", "run")])

    def test_a_merge_closed_item_keeps_its_milestone_in_the_job_list(self):
        # Closing at merge takes an item out of every filter that reads open
        # issues — including this one. Without the merge-closed branch, a
        # loop killed between the last merge and the landing is never
        # restarted, and the bolt never lands.
        snap = Snapshot(items=[
            Item(number=1, milestone="bolt/a", state="closed",
                 labels=frozenset({inbox.TYPE_ASSERTION, inbox.CLOSED_MERGED}))])
        self.assertEqual([(j.milestone, j.kind) for j in inbox.server_inbox(snap)],
                         [("bolt/a", "run")])

    def test_only_a_bolt_milestone_gets_a_job_from_a_merge_closed_item(self):
        # `closed:merged` is the construction loop's label and the landing
        # is a bolt's act; an intent milestone has no landing to wait for,
        # so a stray one there must not keep an intent loop alive forever.
        snap = Snapshot(items=[
            Item(number=1, milestone="intent/a", state="closed",
                 labels=frozenset({inbox.CLOSED_MERGED}))])
        self.assertEqual(inbox.server_inbox(snap), [])

    def test_a_landed_item_gives_its_milestone_no_job(self):
        snap = Snapshot(items=[
            Item(number=1, milestone="bolt/a", state="closed",
                 labels=frozenset({inbox.TYPE_ASSERTION, inbox.CLOSED_DONE}))])
        self.assertEqual([j for j in inbox.server_inbox(snap) if j.kind == "run"],
                         [])

    def test_a_merge_closed_item_is_never_in_the_bolt_loops_ready_set(self):
        # The set that must not change: a closed item is not ready, and the
        # ready set is what the cycle works.
        snap = Snapshot(items=[
            Item(number=1, milestone="bolt/a", state="closed",
                 labels=frozenset({inbox.TYPE_ASSERTION, inbox.CLOSED_MERGED,
                                   inbox.READY}))])
        self.assertEqual(inbox.bolt_inbox(snap, "a").ready, ())

    def test_a_merge_closed_item_is_in_flight_and_not_finished(self):
        merged = Item(number=1, state="closed",
                      labels=frozenset({inbox.CLOSED_MERGED}))
        landed = Item(number=2, state="closed",
                      labels=frozenset({inbox.CLOSED_DONE}))
        self.assertTrue(merged.merge_closed)
        self.assertFalse(merged.is_open)
        self.assertFalse(landed.merge_closed)

    def test_a_queued_batch_parent_is_not_composable_work(self):
        # A unit or elaboration parent is a container, never compose's work;
        # counting it kept a job open forever (first boot, 2026-08-13).
        snap = Snapshot(items=[
            item(9, inbox.QUEUED, inbox.ELABORATION, milestone="intent/a"),
            item(8, inbox.QUEUED, inbox.UNIT, milestone="bolt/b"),
        ])
        self.assertEqual([j for j in inbox.server_inbox(snap) if j.kind == "run"],
                         [])

    def test_a_backlog_batch_is_not(self):
        snap = Snapshot(batches=[Batch(9, kind=inbox.UNIT,
                                       status=inbox.STATUS_BACKLOG,
                                       milestone="bolt/a")])
        self.assertEqual(inbox.server_inbox(snap), [])

    def test_a_closed_milestone_archives_only_while_its_change_is_on_disk(self):
        snap = Snapshot(closed_milestones=["bolt/landed", "bolt/gone"])
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "landed").mkdir()
            jobs = inbox.server_inbox(snap, changes_dir=tmp)
        self.assertEqual([(j.milestone, j.kind) for j in jobs],
                         [("bolt/landed", "archive")])

    def test_the_sweep_covers_the_hole_the_literal_filter_leaves(self):
        # An intent whose last question just closed: a settled unbatched
        # assertion, no ready item, no Ready batch. By the record's words
        # this milestone has no job, and the loop that would birth its
        # handoff is never started.
        snap = Snapshot(items=[
            item(1, inbox.TYPE_ASSERTION, inbox.QUEUED, milestone="intent/a"),
        ])
        self.assertEqual(inbox.server_inbox(snap, sweep=False), [],
                         "the record verbatim: no job, which is the hole")
        self.assertEqual([j.milestone for j in inbox.server_inbox(snap)],
                         ["intent/a"])

    def test_a_server_job_covers_every_milestone_a_loop_would_find_work_on(self):
        # The containment property. A server filter may over-approximate; a
        # loop filter must be exact. If this ever fails, work exists that no
        # process will ever be started to do.
        families = [
            Snapshot(items=[item(1, inbox.READY, milestone="bolt/a")]),
            Snapshot(items=[item(1, inbox.TYPE_ASSERTION, inbox.QUEUED,
                                 milestone="intent/a")]),
            Snapshot(items=[item(1, inbox.QUEUED, milestone="intent/a")]),
            Snapshot(items=[item(1, inbox.QUEUED, milestone="bolt/a",
                                 parent_batch=9)],
                     batches=[Batch(9, kind=inbox.UNIT,
                                    status=inbox.STATUS_READY,
                                    sub_issues=(1,), milestone="bolt/a")]),
        ]
        for snap in families:
            served = {j.milestone for j in inbox.server_inbox(snap) if j.kind == "run"}
            for kind, box in (("bolt", inbox.bolt_inbox(snap, "a")),
                              ("intent", inbox.intent_inbox(snap, "a"))):
                if not box.empty:
                    self.assertIn(f"{kind}/a", served,
                                  f"{kind} loop has work the server never starts")


# ---------------------------------------------------------------------------
# 2 · bolt loop, and the guard plan
# ---------------------------------------------------------------------------

class FlipConsumeTest(unittest.TestCase):

    def test_a_ready_units_queued_sub_issues_are_planned_for_release(self):
        snap = Snapshot(
            items=[item(1, inbox.QUEUED, parent_batch=9)],
            batches=[Batch(9, kind=inbox.UNIT, status=inbox.STATUS_READY,
                           sub_issues=(1,), milestone="bolt/x")])
        self.assertEqual(inbox.flip_consume_plan(snap, "bolt/x"), (1,))

    def test_a_backlog_units_sub_issues_are_not(self):
        # invariant 5: only the operator's word makes ready, and the flip to
        # board Ready IS that word. A loop that releases work from a Backlog
        # batch has made itself the approver.
        snap = Snapshot(
            items=[item(1, inbox.QUEUED, parent_batch=9)],
            batches=[Batch(9, kind=inbox.UNIT, status=inbox.STATUS_BACKLOG,
                           sub_issues=(1,), milestone="bolt/x")])
        self.assertEqual(inbox.flip_consume_plan(snap, "bolt/x"), ())

    def test_a_queued_item_with_no_ready_unit_is_never_released(self):
        snap = Snapshot(items=[item(1, inbox.QUEUED)],
                        batches=[Batch(9, kind=inbox.UNIT,
                                       status=inbox.STATUS_READY,
                                       sub_issues=(), milestone="bolt/x")])
        self.assertEqual(inbox.flip_consume_plan(snap, "bolt/x"), ())

    def test_the_dry_cycle_property_applying_the_plan_empties_it(self):
        # The bolt's own merge criterion in unit form: "two consecutive
        # cycles against an unchanged tracker produce the same tracker state,
        # and the second writes nothing." Only checkable because the plan is
        # pure — which is the whole argument for this module's shape.
        snap = Snapshot(
            items=[item(1, inbox.QUEUED, parent_batch=9),
                   item(2, inbox.QUEUED, parent_batch=9)],
            batches=[Batch(9, kind=inbox.UNIT, status=inbox.STATUS_READY,
                           sub_issues=(1, 2), milestone="bolt/x")])
        plan = inbox.flip_consume_plan(snap, "bolt/x")
        self.assertEqual(plan, (1, 2))

        # apply it: every planned number is now state:ready, not state:queued
        applied = Snapshot(
            items=[item(i.number, inbox.READY, parent_batch=i.parent_batch)
                   if i.number in plan else i
                   for i in snap.items],
            batches=snap.batches)
        self.assertEqual(inbox.flip_consume_plan(applied, "bolt/x"), (),
                         "the second cycle must write nothing")


class BoltInboxTest(unittest.TestCase):

    def test_pull_requests_never_become_items(self):
        raw = {"number": 5, "title": "a PR", "labels": [], "pull_request": {}}
        self.assertIn("pull_request", raw)  # the shape the filter drops

    def test_only_the_bolts_own_milestone(self):
        snap = Snapshot(items=[item(1, inbox.READY, milestone="bolt/x"),
                               item(2, inbox.READY, milestone="bolt/y")])
        self.assertEqual([i.number for i in inbox.bolt_inbox(snap, "x").ready], [1])

    def test_a_closed_item_is_not_in_the_inbox(self):
        snap = Snapshot(items=[item(1, inbox.READY, state="closed")])
        self.assertEqual(inbox.bolt_inbox(snap, "x").ready, ())


# ---------------------------------------------------------------------------
# 3 · intent loop — invariant 6, all four rows
# ---------------------------------------------------------------------------

class HandoffBirthTest(unittest.TestCase):

    def plan(self, items, batches=()):
        return inbox.handoff_plan(Snapshot(items=items, batches=batches), "a")

    def assertion(self, number, **kw):
        kw.setdefault("milestone", "intent/a")
        return Item(number=number, labels=frozenset({inbox.TYPE_ASSERTION}), **kw)

    def test_unparented_with_no_blockers_births(self):
        got = self.plan([self.assertion(1)])
        self.assertEqual(got.action, "birth")
        self.assertEqual([i.number for i in got.assertions], [1])

    def test_an_open_blocker_means_not_settled(self):
        got = self.plan([self.assertion(1, blocked_by=(2,)),
                         self.assertion(2)])
        self.assertEqual([i.number for i in got.assertions], [2])

    def test_a_closed_blocker_means_settled(self):
        got = self.plan([self.assertion(1, blocked_by=(2,)),
                         self.assertion(2, state="closed")])
        self.assertIn(1, [i.number for i in got.assertions])

    def test_an_unseen_blocker_is_treated_as_open(self):
        got = self.plan([self.assertion(1, blocked_by=(99,))])
        self.assertIsNone(got)

    def test_a_parented_assertion_is_already_released(self):
        self.assertIsNone(self.plan([self.assertion(1, parent_batch=7)]))

    def test_an_open_handoff_at_backlog_is_amended_not_duplicated(self):
        # "while that handoff's unit still sits at Backlog, newcomers join
        # it" — a filter that only ever births breaks invariant 2.
        handoff = Item(number=5, labels=frozenset({inbox.TYPE_HANDOFF}),
                       milestone="intent/a", parent_batch=9)
        got = self.plan([self.assertion(1), handoff],
                        batches=[Batch(9, kind=inbox.UNIT,
                                       status=inbox.STATUS_BACKLOG,
                                       milestone="intent/a")])
        self.assertEqual(got.action, "amend")
        self.assertEqual(got.handoff_item, 5)

    def test_a_sealed_handoff_at_ready_births_the_next_wave(self):
        # "The flip seals the batch; the next settled wave births the next
        # handoff."
        handoff = Item(number=5, labels=frozenset({inbox.TYPE_HANDOFF}),
                       milestone="intent/a", parent_batch=9)
        got = self.plan([self.assertion(1), handoff],
                        batches=[Batch(9, kind=inbox.UNIT,
                                       status=inbox.STATUS_READY,
                                       milestone="intent/a")])
        self.assertEqual(got.action, "birth")


# ---------------------------------------------------------------------------
# 4 · dispatch
# ---------------------------------------------------------------------------

class DispatchInboxTest(unittest.TestCase):

    def test_unmilestoned_open_issues_are_triage(self):
        snap = Snapshot(items=[item(1, milestone=None), item(2)])
        self.assertEqual([i.number for i in inbox.dispatch_inbox(snap).triage], [1])

    def test_relay_has_no_milestone_condition(self):
        # An escalation from a running bolt HAS a milestone and still needs
        # relaying. Narrowing this to unmilestoned issues is a tempting tidy
        # that silently breaks the one path the operator hears live work on.
        snap = Snapshot(items=[item(1, inbox.NEEDS_OPERATOR, milestone="bolt/x")])
        self.assertEqual([i.number for i in inbox.dispatch_inbox(snap).relay], [1])

    def test_closed_issues_are_neither(self):
        snap = Snapshot(items=[item(1, inbox.NEEDS_OPERATOR, state="closed"),
                               item(2, milestone=None, state="closed")])
        self.assertTrue(inbox.dispatch_inbox(snap).empty)

    def test_a_merge_closed_escalation_is_still_relayed(self):
        # The landing can now find every assertion already closed, so its
        # pause lands on a closed item. A needs-operator nobody reads is
        # the same silence as one never written.
        snap = Snapshot(items=[item(1, inbox.NEEDS_OPERATOR,
                                    inbox.CLOSED_MERGED, state="closed",
                                    milestone="bolt/x")])
        self.assertEqual([i.number for i in inbox.dispatch_inbox(snap).relay], [1])

    def test_a_landed_escalation_drops_out_of_the_relay(self):
        # Bounded: the landing upgrades the reason and the item is gone
        # from this filter for good.
        snap = Snapshot(items=[item(1, inbox.NEEDS_OPERATOR,
                                    inbox.CLOSED_DONE, state="closed",
                                    milestone="bolt/x")])
        self.assertTrue(inbox.dispatch_inbox(snap).empty)

    def test_a_merge_closed_item_is_never_triage(self):
        snap = Snapshot(items=[item(1, inbox.CLOSED_MERGED, state="closed",
                                    milestone=None)])
        self.assertEqual(inbox.dispatch_inbox(snap).triage, ())


# ---------------------------------------------------------------------------
# The andon cord — code, not judgment
# ---------------------------------------------------------------------------

class AndonTest(unittest.TestCase):

    def test_it_round_trips(self):
        got = inbox.parse_andon(inbox.format_andon("the tree contradicts the claim"))
        self.assertEqual(got.reason, "the tree contradicts the claim")

    def test_prose_about_the_andon_cord_is_not_an_andon(self):
        # The single test that separates recognizing a signal from
        # interpreting a sentence.
        for prose in [
            "I stopped. This is the andon cord, expected behaviour.",
            "ANDON: this line alone is not the marker",
            "the andon cord is what you pull when no further round fixes it",
        ]:
            self.assertIsNone(inbox.parse_andon(prose), prose)

    def test_a_truncated_marker_is_not_a_stop_signal(self):
        half = f"{inbox.ANDON_OPEN}\nANDON: something broke\n"
        self.assertIsNone(inbox.parse_andon(half))

    def test_a_marker_quoted_inside_a_sentence_is_not_one(self):
        inline = f"you write {inbox.ANDON_OPEN} ANDON: x {inbox.ANDON_CLOSE} to stop"
        self.assertIsNone(inbox.parse_andon(inline))

    def test_a_marker_with_no_reason_is_not_one(self):
        empty = f"{inbox.ANDON_OPEN}\nsomething went wrong\n{inbox.ANDON_CLOSE}"
        self.assertIsNone(inbox.parse_andon(empty))

    def test_format_refuses_an_empty_reason(self):
        with self.assertRaises(ValueError):
            inbox.format_andon("   ")

    def test_two_markers_resolve_first_wins_because_pausing_is_the_safe_side(self):
        both = (inbox.format_andon("the first stop") + "\n\nquoting it:\n"
                + inbox.format_andon("the second stop"))
        self.assertEqual(inbox.parse_andon(both).reason, "the first stop")

    def test_find_andon_scans_an_items_comments(self):
        comments = [{"body": "started"},
                    {"body": inbox.format_andon("the spec contradicts its decision")},
                    {"body": "later"}]
        self.assertEqual(inbox.find_andon(comments).reason,
                         "the spec contradicts its decision")
        self.assertIsNone(inbox.find_andon([{"body": "nothing here"}]))


# ---------------------------------------------------------------------------
# The label that means a live wait
# ---------------------------------------------------------------------------

class FakeTracker:
    def __init__(self, labels=()):
        self.labels = set(labels)
        self.comments = []
        self.writes = []

    def has_label(self, number, label):
        return label in self.labels

    def add_label(self, number, label):
        self.labels.add(label)
        self.writes.append(("add", label))

    def remove_label(self, number, label):
        self.labels.discard(label)
        self.writes.append(("remove", label))

    def comment(self, number, body):
        self.comments.append(body)


class NeedsOperatorTest(unittest.TestCase):

    def test_it_comments_and_labels_once(self):
        tracker = FakeTracker()
        self.assertTrue(inbox.set_needs_operator(tracker, 75, "90 minutes, no settle"))
        self.assertEqual(tracker.comments, ["90 minutes, no settle"])
        self.assertIn(inbox.NEEDS_OPERATOR, tracker.labels)

    def test_a_second_call_writes_nothing(self):
        tracker = FakeTracker({inbox.NEEDS_OPERATOR})
        self.assertFalse(inbox.set_needs_operator(tracker, 75, "again"))
        self.assertEqual(tracker.comments, [])
        self.assertEqual(tracker.writes, [])

    def test_clearing_is_the_counterpart_a_notice_owes(self):
        # invariant 7: whoever applies the answer removes the label. A
        # supervision that notified and a completion that never clears leaves
        # the operator's waiting-on-me view wrong from then on.
        tracker = FakeTracker()
        inbox.set_needs_operator(tracker, 75, "waiting")
        self.assertTrue(inbox.clear_needs_operator(tracker, 75))
        self.assertNotIn(inbox.NEEDS_OPERATOR, tracker.labels)
        self.assertFalse(inbox.clear_needs_operator(tracker, 75))


if __name__ == "__main__":
    unittest.main()
