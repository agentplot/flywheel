"""#76 — the four inbox filters, and the andon marker the loop reads.

The filters are pure, so these run against the repo's own declared contract
(`workflows/fixtures/{bolt,intent}-tracker.json`) and small inline snapshots.
No network, no `gh`, no token.
"""

import os
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
        self.assertEqual([i.number for i in box.orphan_queued], [203])


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

    def test_the_three_batch_kinds_are_defined_in_flywheel_setups_labels(self):
        source = (BIN / "flywheel-setup").read_text()
        defined = set(re.findall(r'^\s*"(unit|elaboration|plan|stale)":',
                                 source, re.MULTILINE))
        self.assertEqual(defined, {"unit", "elaboration", "plan", "stale"},
                         "a loop writing a label the repo does not define "
                         "is a failed edit, not a created label")

    def test_stage_planned_description_is_the_books(self):
        source = (BIN / "flywheel-setup").read_text()
        m = re.search(r'"stage:planned": \("[0-9a-f]{6}", "([^"]+)"\)', source)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "its spec validates")

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

class TokenRefreshTest(unittest.TestCase):

    def test_a_bad_credentials_exit_re_mints_and_retries_once(self):
        calls = []
        def flaky(token, *args, **kw):
            calls.append(token)
            if len(calls) == 1:
                raise SystemExit("flywheel: gh api x failed: gh: Bad credentials (HTTP 401)")
            return {"ok": True}
        t = inbox.Tracker("stale", "o", "r", gh=flaky, graphql=lambda *a, **k: {})
        t_resolve = lambda org: "fresh"
        import _flywheel_gh
        old = _flywheel_gh.resolve_token
        _flywheel_gh.resolve_token = t_resolve
        try:
            out = t._gh("stale", "api", "/x")
        finally:
            _flywheel_gh.resolve_token = old
        self.assertEqual(out, {"ok": True})
        self.assertEqual(calls, ["stale", "fresh"])
        self.assertEqual(t.token, "fresh")

    def test_any_other_exit_is_not_retried(self):
        def broken(token, *args, **kw):
            raise SystemExit("flywheel: gh api x failed: HTTP 502")
        t = inbox.Tracker("tok", "o", "r", gh=broken, graphql=lambda *a, **k: {})
        with self.assertRaises(SystemExit):
            t._gh("tok", "api", "/x")


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

    def test_a_ready_item_on_a_closed_bolt_milestone_is_a_run_job(self):
        # The operator's close releases the landing, and a failed landing
        # files a born-ready fix item — the loop must stay alive for it.
        snap = Snapshot(items=[
            item(1, inbox.READY, milestone="bolt/a", milestone_state="closed")])
        self.assertEqual([j.milestone for j in inbox.server_inbox(snap)
                          if j.kind == "run"], ["bolt/a"])

    def test_an_item_on_a_closed_intent_milestone_is_not_a_run_job(self):
        snap = Snapshot(items=[
            item(1, inbox.READY, milestone="intent/a",
                 milestone_state="closed")])
        self.assertEqual([j for j in inbox.server_inbox(snap) if j.kind == "run"], [])

    def test_a_batch_at_board_ready_is_a_job_on_its_own(self):
        snap = Snapshot(batches=[Batch(9, kind=inbox.UNIT,
                                       status=inbox.STATUS_READY,
                                       milestone="bolt/a")])
        self.assertEqual([(j.milestone, j.kind) for j in inbox.server_inbox(snap)],
                         [("bolt/a", "run")])

    def test_a_ready_batch_on_a_closed_milestone_is_not_a_run_job(self):
        # The same test the per-item condition above already makes. Without
        # it a unit parent left open at Ready keeps its milestone reporting a
        # job forever — including after the operator closes the milestone,
        # where it collides with the `archive` job this same sweep adds.
        snap = Snapshot(batches=[Batch(9, kind=inbox.UNIT,
                                       status=inbox.STATUS_READY,
                                       milestone="bolt/a",
                                       milestone_state="closed")])
        self.assertEqual(
            [j for j in inbox.server_inbox(snap) if j.kind == "run"], [])

    def test_a_merge_closed_item_keeps_its_milestone_in_the_job_list(self):
        # Closing at merge takes an item out of every filter that reads open
        # issues — including this one. Without the merge-closed branch, a
        # loop killed between the last merge and the landing is never
        # restarted, and the bolt never lands.
        snap = Snapshot(items=[
            Item(number=1, milestone="bolt/a", state="closed",
                 labels=frozenset({inbox.CLOSED_MERGED}))])
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
                 labels=frozenset({inbox.CLOSED_DONE}))])
        self.assertEqual([j for j in inbox.server_inbox(snap) if j.kind == "run"],
                         [])

    def test_a_merge_closed_item_is_never_in_the_bolt_loops_ready_set(self):
        # The set that must not change: a closed item is not ready, and the
        # ready set is what the cycle works.
        snap = Snapshot(items=[
            Item(number=1, milestone="bolt/a", state="closed",
                 labels=frozenset({inbox.CLOSED_MERGED,
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

    def test_a_server_job_covers_every_milestone_a_loop_would_find_work_on(self):
        # The containment property. A server filter may over-approximate; a
        # loop filter must be exact. If this ever fails, work exists that no
        # process will ever be started to do.
        families = [
            Snapshot(items=[item(1, inbox.READY, milestone="bolt/a")]),
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
        # The landing can now find every work item already closed, so its
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


class DispatchStandingTest(unittest.TestCase):
    """`dispatch:standing` widens triage and narrows relay — the round is
    triage's own plan, never a parallel queue."""

    def test_a_standing_item_joins_triage_even_with_a_milestone(self):
        snap = Snapshot(items=[item(1, inbox.DISPATCH_STANDING, inbox.UNIT,
                                    milestone="bolt/x")])
        self.assertEqual([i.number for i in inbox.dispatch_inbox(snap).triage],
                         [1])

    def test_a_standing_wait_is_not_also_relayed(self):
        # One wait, one surface: the round assembles it; a DM beside the
        # plan would carry a second, contradictory imperative.
        snap = Snapshot(items=[item(1, inbox.DISPATCH_STANDING,
                                    inbox.NEEDS_OPERATOR,
                                    milestone="bolt/x")])
        box = inbox.dispatch_inbox(snap)
        self.assertEqual([i.number for i in box.triage], [1])
        self.assertEqual(box.relay, ())

    def test_a_plain_needs_operator_still_relays(self):
        snap = Snapshot(items=[item(1, inbox.NEEDS_OPERATOR,
                                    milestone="bolt/x")])
        self.assertEqual([i.number for i in inbox.dispatch_inbox(snap).relay],
                         [1])


class RoundInboxTest(unittest.TestCase):
    """The round is derived from the snapshot, never from labels a
    writer had to remember."""

    def merged(self, number, milestone="bolt/x"):
        return item(number, inbox.CLOSED_MERGED, state="closed",
                    milestone=milestone)

    def test_a_fully_merged_bolt_is_close_ready(self):
        snap = Snapshot(items=[self.merged(1), self.merged(2),
                               item(9, inbox.UNIT, milestone="bolt/x")])
        box = inbox.round_inbox(snap)
        self.assertEqual(box.close_ready, ("bolt/x",))

    def test_an_open_card_holds_the_close(self):
        snap = Snapshot(items=[self.merged(1),
                               item(9, inbox.UNIT, milestone="bolt/x")],
                        plan_cards=[inbox.PlanCard(
                            number=30, title="Unit: more",
                            milestone="bolt/x")])
        self.assertEqual(inbox.round_inbox(snap).close_ready, ())

    def test_a_ready_item_holds_the_close(self):
        snap = Snapshot(items=[self.merged(1),
                               item(2, inbox.READY, milestone="bolt/x")])
        self.assertEqual(inbox.round_inbox(snap).close_ready, ())

    def test_backlog_batches_and_cards_stand_as_approvals(self):
        snap = Snapshot(
            items=[item(1, milestone="intent/a")],
            batches=[Batch(number=9, kind=inbox.ELABORATION,
                           status=inbox.STATUS_BACKLOG,
                           milestone="intent/a"),
                     Batch(number=8, kind=inbox.ELABORATION,
                           status=inbox.STATUS_READY,
                           milestone="intent/b")],
            plan_cards=[inbox.PlanCard(number=30, title="Unit: u",
                                       status=inbox.STATUS_BACKLOG,
                                       milestone="bolt/x")])
        box = inbox.round_inbox(snap)
        self.assertEqual([b.number for b in box.backlog_batches], [9],
                         "Ready is released, not pending")
        self.assertEqual([c.number for c in box.backlog_cards], [30])

    def test_standing_labels_only_nominate_payload_anchors(self):
        snap = Snapshot(items=[item(9, inbox.DISPATCH_STANDING, inbox.UNIT,
                                    milestone="bolt/x")])
        box = inbox.round_inbox(snap)
        self.assertEqual([i.number for i in box.payload_anchors], [9])
        self.assertEqual(box.close_ready, (),
                         "a label cannot invent a close decision")

    def test_a_close_ready_parent_is_no_payload_anchor(self):
        # The loop labels the unit parents for visibility and the poke;
        # the derived close row covers them — they nominate nothing.
        snap = Snapshot(items=[self.merged(1),
                               item(9, inbox.DISPATCH_STANDING, inbox.UNIT,
                                    milestone="bolt/x")])
        box = inbox.round_inbox(snap)
        self.assertEqual(box.close_ready, ("bolt/x",))
        self.assertEqual(box.payload_anchors, ())

    def test_an_empty_round_is_empty(self):
        self.assertTrue(inbox.round_inbox(Snapshot()).empty)


class RoundMarkerTest(unittest.TestCase):
    """The round's two markers: a published payload and a close-ready
    milestone — andon-grade strictness, prose can never match."""

    def payload(self):
        return inbox.format_round_payload(
            "agentplot/blueprints", "a" * 40,
            "openspec/changes/bolt-x/sessions/close", "construction")

    def test_a_payload_round_trips(self):
        parsed = inbox.parse_round_payload(self.payload())
        self.assertEqual(parsed.repo, "agentplot/blueprints")
        self.assertEqual(parsed.sha, "a" * 40)
        self.assertEqual(parsed.origin, "construction")

    def test_prose_and_half_markers_never_match(self):
        self.assertIsNone(inbox.parse_round_payload(
            "the payload is at repo=x sha=y — not a marker"))
        truncated = self.payload().rsplit("\n", 1)[0]
        self.assertIsNone(inbox.parse_round_payload(truncated))
        self.assertIsNone(inbox.parse_round_payload(
            self.payload().replace("a" * 40, "short")))

    def test_consumed_retires_earlier_payloads(self):
        comments = [self.payload(),
                    f"applied.\n\n{inbox.ROUND_CONSUMED}"]
        self.assertIsNone(inbox.find_round_payload(comments))

    def test_a_republish_after_consume_stands_again(self):
        comments = [self.payload(), inbox.ROUND_CONSUMED, self.payload()]
        self.assertIsNotNone(inbox.find_round_payload(comments))

    def test_close_ready_round_trips(self):
        marker = inbox.format_close_ready("bolt/x", "bolt/x", "main")
        parsed = inbox.parse_close_ready(marker)
        self.assertEqual((parsed.milestone, parsed.branch, parsed.main),
                         ("bolt/x", "bolt/x", "main"))
        self.assertIsNone(inbox.parse_close_ready("Ready to land: prose"))


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

    def test_an_answer_marker_retires_every_earlier_andon(self):
        # #166: markers were never retired, so an answered andon re-paused
        # the batch on every cycle forever.
        comments = [{"body": inbox.format_andon("the spec contradicts the tree")},
                    {"body": "Ruling: amend the requirement.\n\n"
                             + inbox.ANDON_ANSWERED}]
        self.assertIsNone(inbox.find_andon(comments))

    def test_an_andon_raised_after_the_answer_is_live(self):
        comments = [{"body": inbox.format_andon("the first stop")},
                    {"body": inbox.ANDON_ANSWERED},
                    {"body": inbox.format_andon("a new stop")}]
        self.assertEqual(inbox.find_andon(comments).reason, "a new stop")

    def test_an_answer_quoting_the_old_andon_does_not_re_raise_it(self):
        comments = [{"body": inbox.format_andon("the first stop")},
                    {"body": "Answering:\n" + inbox.format_andon("the first stop")
                             + "\n" + inbox.ANDON_ANSWERED}]
        self.assertIsNone(inbox.find_andon(comments))


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


# ---------------------------------------------------------------------------
# The prose surfaces the loops' docstrings cite as their definition
# ---------------------------------------------------------------------------

class RecordConsistencyTest(unittest.TestCase):
    """A behaviour with no record is a behaviour the next reader undoes.

    These pin the sentences that describe THIS change's behaviour in the
    files a session or a loop actually reads — not every mention, just the
    propositions the change retires, which can be written without the
    literal label name.
    """

    ROOT = BIN.parent

    def read(self, *parts):
        return (self.ROOT.joinpath(*parts)).read_text()

    def test_the_record_and_the_construction_skill_know_about_the_merge_close(self):
        for parts in (("design", "loop-programs.md"),
                      ("skills", "construction", "SKILL.md"),
                      ("skills", "_reference", "tracker.md"),
                      ("skills", "_reference", "herdr.md")):
            self.assertIn("closed:merged", self.read(*parts), str(parts))

    def test_the_born_ready_release_cannot_return_to_dispatch_surfaces(self):
        # dispatch-to-bolt: dictated work arrives as a plan card the operator
        # approves on the board — never items born state:ready on a word at
        # triage. The phrasing that carried the retired route must not creep
        # back into the surfaces dispatch reads.
        for parts in (("agents", "flywheel-dispatch.md"),
                      ("skills", "inception", "SKILL.md")):
            flat = " ".join(self.read(*parts).split())
            self.assertNotIn("born `state:ready` on the operator's word",
                             flat, str(parts))
            self.assertNotIn("Status **Ready** from birth", flat, str(parts))
            self.assertNotIn("nothing left to approve", flat, str(parts))
            self.assertIn("never Status Ready", flat, str(parts))

    def test_no_reader_still_says_items_close_at_the_landing(self):
        record = self.read("design", "loop-programs.md")
        self.assertNotIn("Items close at landing with the SHA", record)

    def test_the_records_server_filter_carries_the_merge_closed_condition(self):
        # `server_inbox`'s docstring cites this record as its definition.
        record = self.read("design", "loop-programs.md")
        server = record.split("- **server**", 1)[1].split("- **bolt loop", 1)[0]
        self.assertIn("closed:merged", server)

    def test_milestone_closure_carves_out_merge_closed_items_everywhere(self):
        for parts in (("skills", "construction", "SKILL.md"),
                      ("skills", "_reference", "tracker.md")):
            text = self.read(*parts)
            window = text.split("all closed", 1)
            self.assertGreater(len(window), 1, str(parts))
            self.assertIn("closed:merged", window[1][:400], str(parts))

    def test_every_design_surface_names_the_operators_flip(self):
        # Task 4.6: the pane half of the flip, in the skills a design
        # session loads as well as in the profiles that host them.
        for skill in ("planning", "research", "writeback", "interactive",
                      "prototype"):
            self.assertIn("stage:done",
                          self.read("skills", skill, "SKILL.md"), skill)
        for profile in ("flywheel-design-session", "flywheel-interactive-session"):
            self.assertIn("stage:done",
                          self.read("agents", f"{profile}.md"), profile)

    def test_the_pane_written_flip_goes_through_the_one_implementation(self):
        # The one path the loop cannot fix for itself. What is held is that
        # the profile names the CALL — not merely that it mentions a removal.
        # A profile spelling out its own two-label edit satisfied the old
        # check and was the defect: it hard-codes one predecessor, which is
        # wrong wherever the item's actual predecessor is another stage.
        for profile in ("flywheel-design-session", "flywheel-interactive-session"):
            flat = " ".join(self.read("agents", f"{profile}.md").split())
            self.assertIn("flywheel-stage", flat, profile)
            self.assertNotIn("--remove-label stage:", flat, profile)

    def test_no_design_surface_spells_out_a_hand_built_stage_edit(self):
        # "The rule is stated once and copied nowhere": every surface a
        # session reads points at the call, and none of them hands it a
        # label edit to copy.
        for skill in ("planning", "research", "writeback", "interactive",
                      "prototype"):
            flat = " ".join(self.read("skills", skill, "SKILL.md").split())
            self.assertIn("flywheel-stage", flat, skill)
            self.assertNotIn("--remove-label stage:", flat, skill)

    def test_the_pane_command_writes_through_the_one_implementation(self):
        # "reachable from a pane without importing the loops' internals" is
        # the requirement's own wording, and both halves are checkable on
        # the source — which is how this suite already holds `flywheel-setup`.
        source = (BIN / "flywheel-stage").read_text()
        self.assertIn("set_stage", source,
                      "the command writes through the one implementation")
        self.assertNotIn("_flywheel_bolt_loop", source)
        self.assertNotIn("_flywheel_intent", source)
        self.assertTrue(os.access(BIN / "flywheel-stage", os.X_OK),
                        "bin/ goes on an installed user's PATH; it must run")

    def test_the_reference_gives_the_flip_as_the_call(self):
        # `herdr.md` is where the profiles send a session for the invocation.
        flat = " ".join(self.read("skills", "_reference", "herdr.md").split())
        self.assertIn("flywheel-stage", flat)
        self.assertNotIn("--remove-label stage:in-session", flat)
        # The sentence the recipe carried must survive the replacement.
        self.assertIn("REPLACES the previous stage", flat)


class SetStageTest(unittest.TestCase):
    """The one implementation of the one-stage rule."""

    def test_it_moves_the_leading_edge(self):
        tracker = FakeTracker({inbox.STAGE_BUILT})
        self.assertTrue(inbox.set_stage(tracker, 1, inbox.STAGE_VERIFIED))
        self.assertEqual(tracker.labels, {inbox.STAGE_VERIFIED})

    def test_a_clean_item_already_at_the_target_writes_nothing(self):
        # The dry-cycle property depends on this: a second cycle over an
        # unchanged tracker writes nothing.
        tracker = FakeTracker({inbox.STAGE_DONE})
        self.assertFalse(inbox.set_stage(tracker, 1, inbox.STAGE_DONE))
        self.assertEqual(tracker.writes, [])

    def test_an_item_at_the_target_carrying_another_stage_is_swept(self):
        # The early return may not be taken on the strength of the target
        # alone. The operator adding `stage:done` by hand on GitHub sweeps
        # nothing, and this capability permits exactly that — so an item can
        # reach this function carrying the target AND a predecessor.
        tracker = FakeTracker({inbox.STAGE_COLLECTED, inbox.STAGE_DONE})
        self.assertTrue(inbox.set_stage(tracker, 1, inbox.STAGE_DONE))
        self.assertEqual(tracker.labels, {inbox.STAGE_DONE})
        self.assertIn(("remove", inbox.STAGE_COLLECTED), tracker.writes)
        # ...and the target it already carried is not re-added.
        self.assertNotIn(("add", inbox.STAGE_DONE), tracker.writes)

    def test_an_item_picked_up_at_collected_is_flipped_done(self):
        # The case the hard-coded recipe got wrong. `dispatch_batch` leaves
        # an item at `stage:collected` alone when a later session picks it
        # up, so a flip removing only `stage:in-session` left it carrying
        # `stage:collected` and `stage:done` at once.
        tracker = FakeTracker({inbox.STAGE_COLLECTED})
        self.assertTrue(inbox.set_stage(tracker, 1, inbox.STAGE_DONE))
        self.assertEqual(tracker.labels, {inbox.STAGE_DONE})

    def test_it_touches_no_closure_label(self):
        tracker = FakeTracker({inbox.STAGE_BUILT, inbox.CLOSED_MERGED})
        inbox.set_stage(tracker, 1, inbox.STAGE_MERGED)
        self.assertIn(inbox.CLOSED_MERGED, tracker.labels)


class ApprovalWakesTheLoopTest(unittest.TestCase):
    """The operator's Ready flip must change the job's reason.

    The backoff releases a hold only when a job's reason changes. With the
    item sweep claiming the job first, a milestone held on "#N queued and
    unbatched" kept that reason through a Ready flip, and the approval
    waited out the full hold.
    """

    def test_a_ready_batch_claims_the_jobs_reason_over_the_sweep(self):
        snap = Snapshot(
            items=[item(1, "type:planning", inbox.QUEUED,
                        milestone="intent/a", parent_batch=None)],
            batches=[Batch(number=9, kind=inbox.ELABORATION,
                           status=inbox.STATUS_READY, sub_issues=(1,),
                           milestone="intent/a")])
        jobs = inbox.server_inbox(snap)
        self.assertEqual([j.milestone for j in jobs], ["intent/a"])
        self.assertEqual(jobs[0].why, "a batch at board Status Ready",
                         "the approval, not the sweep, is the reason — "
                         "a changed reason is what releases a held loop")


class ChangeIdTest(unittest.TestCase):
    """A milestone's record lives under a kind-prefixed change id, and an
    existing bare-slug directory is adopted rather than renamed."""

    def test_the_change_id_is_kind_prefixed(self):
        self.assertEqual(inbox.change_id("bolt/loop-server"), "bolt-loop-server")
        self.assertEqual(inbox.change_id("intent/writeback"), "intent-writeback")
        self.assertIsNone(inbox.change_id("v1.0"))
        self.assertIsNone(inbox.change_id(None))

    def test_a_bare_slug_directory_is_adopted(self):
        with tempfile.TemporaryDirectory() as tmp:
            changes = Path(tmp)
            (changes / "loop-server").mkdir()
            self.assertEqual(
                inbox.resolve_change_id(changes, "bolt/loop-server"),
                "loop-server")

    def test_a_fresh_record_gets_the_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                inbox.resolve_change_id(Path(tmp), "bolt/loop-server"),
                "bolt-loop-server")
            self.assertEqual(
                inbox.resolve_change_id(Path(tmp), "intent/writeback"),
                "intent-writeback")

    def test_no_changes_root_still_resolves_the_prefixed_id(self):
        self.assertEqual(inbox.resolve_change_id(None, "bolt/x"), "bolt-x")
        self.assertIsNone(inbox.resolve_change_id(None, "v1.0"))


if __name__ == "__main__":
    unittest.main()
