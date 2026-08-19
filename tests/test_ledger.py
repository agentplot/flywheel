"""The run ledger: entries and rendering."""

import json
import tempfile
import unittest
from pathlib import Path

from context import ledger


def make(root, clock=lambda: 1_755_000_000.0):
    return ledger.RunLedger(root, "bolt-demo", run_id="run1", clock=clock)


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


class Plan(unittest.TestCase):
    def test_plan_renders_and_never_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            led = make(tmp)
            path = led.write_plan(PLAN)
            scope = Path(tmp) / "bolt-demo"
            self.assertEqual(scope / "run1.plan.md", path)
            text = path.read_text()
            self.assertIn("spec:demo-1", text)
            self.assertNotIn("approve", text)
            self.assertFalse((scope / "pending.json").exists())

    def test_empty_plan_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            led = make(tmp)
            self.assertIsNone(led.write_plan([]))
            self.assertFalse((Path(tmp) / "bolt-demo" / "run1.plan.md").exists())


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
        self.assertIsNone(led.write_plan(PLAN))
        self.assertIsNone(led.write_report())


if __name__ == "__main__":
    unittest.main()
