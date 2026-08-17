"""The run ledger: entries, rendering, the expectation gate, approval."""

import json
import tempfile
import unittest
from pathlib import Path

from context import ledger


def make(root, gate_mode="gate", clock=lambda: 1_755_000_000.0):
    return ledger.RunLedger(root, "bolt-demo", run_id="run1",
                            gate_mode=gate_mode, clock=clock)


PLAN = [
    {"step": "spec:demo-1", "trigger": "#1 ready, no spec",
     "expected": "change validates, commit on build/demo-1"},
    {"step": "build:demo-1", "trigger": "spec validated",
     "expected": "commit by pathspec on build/demo-1"},
]


class Entries(unittest.TestCase):
    def test_entries_land_in_the_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            led = make(tmp)
            led.precondition("#1 state:ready")
            led.expect("spec:demo-1", "#1 ready", "validates")
            led.actual("spec:demo-1", "commit ab12f3", ok=True)
            led.note("nothing else this pass")
            lines = [json.loads(l) for l in
                     led.path.read_text().strip().splitlines()]
            self.assertEqual(
                ["precondition", "expect", "actual", "note"],
                [e["kind"] for e in lines])
            self.assertTrue(all("ts" in e for e in lines))

    def test_write_failure_is_best_effort(self):
        with tempfile.TemporaryDirectory() as tmp:
            blocked = Path(tmp) / "flat"
            blocked.write_text("")          # scope dir cannot be created
            logged = []
            led = ledger.RunLedger(blocked / "x", "bolt-demo", run_id="run1",
                                   log=logged.append)
            led.precondition("still records in memory")
            self.assertEqual(1, led.write_failures)
            self.assertEqual(1, len(led.entries))
            self.assertTrue(logged)


class Gate(unittest.TestCase):
    def test_unapproved_plan_gates_and_writes_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            led = make(tmp)
            self.assertFalse(led.gate(PLAN))
            scope = Path(tmp) / "bolt-demo"
            pending = json.loads((scope / "pending.json").read_text())
            self.assertEqual(ledger.expectation_key(PLAN), pending["key"])
            self.assertTrue((scope / "run1.plan.md").exists())

    def test_approved_plan_drives_and_does_not_regate(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(make(tmp).gate(PLAN))
            record = ledger.approve(tmp, "bolt-demo")
            self.assertEqual(ledger.expectation_key(PLAN), record["key"])
            # a later run with the same plan proceeds
            led2 = ledger.RunLedger(tmp, "bolt-demo", run_id="run2")
            self.assertTrue(led2.gate(PLAN))

    def test_changed_plan_regates(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(make(tmp).gate(PLAN))
            ledger.approve(tmp, "bolt-demo")
            other = PLAN + [{"step": "landing", "trigger": "all merged",
                             "expected": "criteria green"}]
            self.assertFalse(make(tmp).gate(other))

    def test_key_ignores_entry_order(self):
        self.assertEqual(ledger.expectation_key(PLAN),
                         ledger.expectation_key(list(reversed(PLAN))))

    def test_empty_plan_never_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(make(tmp).gate([]))

    def test_courtesy_writes_the_plan_and_drives(self):
        with tempfile.TemporaryDirectory() as tmp:
            led = make(tmp, gate_mode="courtesy")
            self.assertTrue(led.gate(PLAN))
            scope = Path(tmp) / "bolt-demo"
            self.assertTrue((scope / "run1.plan.md").exists())
            self.assertFalse((scope / "pending.json").exists())

    def test_approve_with_nothing_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(ledger.approve(tmp, "bolt-demo"))


class Report(unittest.TestCase):
    def test_mismatches_render_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            led = make(tmp)
            led.precondition("#1 state:ready")
            led.expect("spec:demo-1", "#1 ready", "validates")
            led.actual("spec:demo-1", "commit ab12f3", ok=True)
            led.expect("verify:demo-1", "build landed", "NONE")
            led.actual("verify:demo-1", "2 findings", ok=False)
            path = led.write_report()
            text = path.read_text()
            self.assertIn("1 of 2 step(s) diverged", text)
            self.assertLess(text.index("verify:demo-1"),
                            text.index("spec:demo-1"))
            self.assertIn("✗ 2 findings", text)

    def test_expected_without_actual_is_a_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            led = make(tmp)
            led.expect("merge:demo-1", "verify clean", "ancestry confirmed")
            text = led.write_report().read_text()
            self.assertIn("✗ never happened", text)

    def test_clean_run_says_so(self):
        with tempfile.TemporaryDirectory() as tmp:
            led = make(tmp)
            led.expect("spec:demo-1", "#1 ready", "validates")
            led.actual("spec:demo-1", "commit ab12f3", ok=True)
            text = led.write_report().read_text()
            self.assertIn("The run matched expectations.", text)

    def test_no_actions_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            led = make(tmp)
            led.precondition("queue empty")
            led.note("nothing ready — no action")
            text = led.write_report().read_text()
            self.assertIn("No actions this run.", text)
            self.assertIn("nothing ready", text)

    def test_null_ledger_is_inert(self):
        led = ledger.NullLedger()
        led.precondition("x")
        led.expect("a", "b", "c")
        led.actual("a", "d")
        self.assertTrue(led.gate(PLAN))
        self.assertIsNone(led.write_report())


if __name__ == "__main__":
    unittest.main()
