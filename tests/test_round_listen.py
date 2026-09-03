"""The round's ear — the poll lives outside the pane, feedback is
handed in as a prompt, and the loop stops when the operator ends it."""

import tempfile
import unittest
from pathlib import Path

from context import BIN  # noqa: F401 — puts bin/ on sys.path
import _flywheel_round_listen as ear  # noqa: E402


class ListenTest(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.plan = Path(self._tmp.name) / "2026-09-03-round-29" / "plan.html"
        self.plan.parent.mkdir(parents=True)
        self.plan.write_text("<html></html>")
        self.delivered = []

    def tearDown(self):
        self._tmp.cleanup()

    def scripted(self, *answers):
        queue = list(answers)
        return lambda: queue.pop(0) if queue else (1, "")

    def deliver(self, text):
        self.delivered.append(text)
        return True

    def test_feedback_is_written_beside_the_plan_and_handed_to_the_pane(self):
        made = ear.listen(self.plan, self.scripted((0, '{"prompt": "yes to all"}')),
                          self.deliver, log=lambda m: None)
        self.assertEqual(made, 1)
        path = ear.feedback_path(self.plan, 1)
        self.assertEqual(path.read_text(), '{"prompt": "yes to all"}')
        self.assertEqual(len(self.delivered), 1)
        self.assertIn(str(path), self.delivered[0])
        self.assertIn("round-29", self.delivered[0])
        self.assertIn("operator", self.delivered[0])

    def test_every_answer_is_a_numbered_delivery_until_the_session_ends(self):
        made = ear.listen(self.plan, self.scripted(
            (0, "first"), (0, "second"),
            (0, '{"prompt": "done", "session_ended": true}')),
            self.deliver, log=lambda m: None)
        self.assertEqual(made, 3)
        self.assertEqual([p.name for p in sorted(
            (self.plan.parent / "feedback").iterdir())],
            ["001.md", "002.md", "003.md"])

    def test_a_refusing_poll_stops_the_listener(self):
        # lavish gone, or the page closed from the browser: no spin.
        logs = []
        made = ear.listen(self.plan, self.scripted((1, "")), self.deliver,
                          log=logs.append)
        self.assertEqual(made, 0)
        self.assertEqual(self.delivered, [])
        self.assertTrue(any("stopping" in m for m in logs))

    def test_a_failed_handoff_keeps_the_file_and_says_so(self):
        logs = []
        made = ear.listen(self.plan, self.scripted((0, "answer"), (1, "")),
                          lambda text: False, log=logs.append)
        self.assertEqual(made, 1)
        self.assertTrue(ear.feedback_path(self.plan, 1).is_file())
        self.assertTrue(any("could not be handed" in m for m in logs))


class DeliverSettledTest(unittest.TestCase):
    """A prompt into a working pane interrupts its tool — the very kill
    this listener exists to avoid — so delivery waits for settle."""

    def test_delivery_waits_for_the_pane_to_settle(self):
        statuses = iter(["working", "working", "idle"])
        sent = []

        def agents(env):
            return {"dispatch": {"agent_status": next(statuses)}}

        def send(name, text, env):
            sent.append((name, text))
            return True, ""
        old = ear.herdr.herdr_agents, ear.herdr.send_prompt
        ear.herdr.herdr_agents, ear.herdr.send_prompt = agents, send
        try:
            ok = ear.deliver_settled("dispatch", "go", {}, sleep=lambda s: None,
                                     log=lambda m: None)
        finally:
            ear.herdr.herdr_agents, ear.herdr.send_prompt = old
        self.assertTrue(ok)
        self.assertEqual(sent, [("dispatch", "go")])


if __name__ == "__main__":
    unittest.main()
