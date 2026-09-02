"""The dispatch MCP server — renders, session semantics, protocol framing.

The proxy is the seam that moves when dispatch becomes a hosted service,
so what these tests pin is the CONTRACT: undeliverability is a tool
result and never an error, external busy is never interrupted, our own
busy queues, and every emitted line is one JSON document.
"""

import io
import json
import unittest

from context import dispatch_mcp, herdr


def roster_run(agents, calls=None):
    """A fake subprocess.run serving `herdr agent list` from a dict and
    recording every argv."""
    def run(argv, **kwargs):
        if calls is not None:
            calls.append(list(argv))
        out = type("Out", (), {})()
        out.returncode = 0
        out.stderr = ""
        if argv[:3] == ["herdr", "agent", "list"]:
            rows = [dict(a, name=name) for name, a in agents.items()]
            out.stdout = json.dumps({"result": {"agents": rows}})
        else:
            out.stdout = "{}"
        return out
    return run


def proxy_with(agents, calls=None):
    p = dispatch_mcp.DispatchProxy(
        environ={"HERDR_SOCKET_PATH": "/tmp/sock"},
        run=roster_run(agents, calls), sleep=lambda s: None)
    return p


class SendPromptTargetTest(unittest.TestCase):
    """A pane herdr lists under its title alone is not addressable by
    that title — the prompt goes to its pane id instead."""

    def run_for(self, rows, calls):
        def run(argv, **kwargs):
            calls.append(list(argv))
            out = type("Out", (), {})()
            out.returncode, out.stderr = 0, ""
            out.stdout = (json.dumps({"result": {"agents": rows}})
                          if argv[:3] == ["herdr", "agent", "list"] else "{}")
            return out
        return run

    def test_a_nameless_row_is_prompted_by_pane_id(self):
        calls = []
        rows = [{"terminal_title_stripped": "plan-x", "pane_id": "w1:p9",
                 "agent_status": "working"}]
        delivered, _ = herdr.send_prompt(
            "plan-x", "go", {}, run=self.run_for(rows, calls),
            sleep=lambda s: None)
        self.assertTrue(delivered)
        self.assertIn(["herdr", "agent", "prompt", "w1:p9", "go"], calls)

    def test_a_named_row_is_prompted_by_name(self):
        calls = []
        rows = [{"name": "plan-x", "pane_id": "w1:p9",
                 "agent_status": "working"}]
        herdr.send_prompt("plan-x", "go", {}, run=self.run_for(rows, calls),
                          sleep=lambda s: None)
        self.assertIn(["herdr", "agent", "prompt", "plan-x", "go"], calls)


class RenderTest(unittest.TestCase):

    ITEMS = [{"number": 12, "title": "a question", "url": "https://x/12"},
             {"number": 34}]

    def test_relay_names_numbers_urls_and_the_dm_imperative(self):
        text = dispatch_mcp.render_relay(self.ITEMS)
        self.assertIn("#12", text)
        self.assertIn('"a question"', text)
        self.assertIn("https://x/12", text)
        self.assertIn("#34", text)
        self.assertIn("DM each item's assignee", text)
        self.assertNotIn("\n", text)

    def test_triage_is_the_round_trigger_the_charter_names(self):
        # The sentence must match the dispatch charter's trigger phrase —
        # a narrow per-item routing order here made dispatch decline the
        # poke forever while a published payload stood unshown.
        text = dispatch_mcp.render_triage(self.ITEMS)
        self.assertIn("#12", text)
        self.assertIn("standing material awaits a dispatch plan", text)
        self.assertIn("run the round", text)
        self.assertNotIn("\n", text)

    def test_round_names_the_backlog_work_and_the_round_imperative(self):
        # Problem 12: Backlog board work never poked dispatch at all.
        text = dispatch_mcp.render_round(self.ITEMS)
        self.assertIn("#12", text)
        self.assertIn("Backlog", text)
        self.assertIn("run the round", text)
        self.assertNotIn("\n", text)


class SessionSemanticsTest(unittest.TestCase):

    def test_absent_dispatch_is_an_undelivered_result(self):
        result = proxy_with({}).relay([{"number": 1}])
        self.assertEqual(result["delivered"], False)
        self.assertIn("absent", result["reason"])

    def test_externally_busy_dispatch_is_never_interrupted(self):
        calls = []
        proxy = proxy_with({"dispatch": {"agent_status": "working"}}, calls)
        result = proxy.relay([{"number": 1}])
        self.assertEqual(result["delivered"], False)
        self.assertIn("busy (working)", result["reason"])
        prompts = [c for c in calls if c[:3] == ["herdr", "agent", "prompt"]]
        self.assertEqual(prompts, [])

    def test_settled_dispatch_gets_the_prompt_and_the_work_poll(self):
        # idle at delivery, working on the first poll
        state = {"dispatch": {"agent_status": "idle"}}
        calls = []
        proxy = proxy_with(state, calls)
        real_run = proxy.run

        def run(argv, **kwargs):
            if argv[:3] == ["herdr", "agent", "prompt"]:
                state["dispatch"]["agent_status"] = "working"
            return real_run(argv, **kwargs)
        proxy.run = run
        result = proxy.relay([{"number": 1}])
        self.assertEqual(result, {"delivered": True})
        self.assertTrue(proxy.delivered_this_session)

    def test_a_second_call_queues_behind_our_own_prompt(self):
        calls = []
        proxy = proxy_with({"dispatch": {"agent_status": "working"}}, calls)
        proxy.delivered_this_session = True
        result = proxy.triage([{"number": 2}])
        self.assertEqual(result["delivered"], True)
        self.assertIn("queued", result["reason"])
        prompts = [c for c in calls if c[:3] == ["herdr", "agent", "prompt"]]
        self.assertEqual(len(prompts), 1)

    def test_no_fleet_resolvable_is_a_result_not_a_raise(self):
        proxy = dispatch_mcp.DispatchProxy(
            fleet="/nowhere/fleet.yaml", environ={},
            run=roster_run({}), sleep=lambda s: None)
        result = proxy.relay([{"number": 1}])
        self.assertEqual(result["delivered"], False)
        self.assertTrue(result["reason"])

    def test_status_reports_presence_and_agent_status(self):
        present = proxy_with({"dispatch": {"agent_status": "idle"}}).status()
        self.assertEqual(present, {"present": True, "agent_status": "idle"})
        absent = proxy_with({}).status()
        self.assertEqual(absent, {"present": False})


class ProtocolTest(unittest.TestCase):

    def rpc(self, lines, proxy=None):
        stdin = io.StringIO("".join(json.dumps(m) + "\n" if isinstance(m, dict)
                                    else m + "\n" for m in lines))
        stdout = io.StringIO()
        dispatch_mcp.serve(stdin, stdout, proxy or proxy_with({}),
                           version="9.9.9")
        return stdout.getvalue()

    def test_initialize_answers_version_and_tools_capability(self):
        out = self.rpc([{"jsonrpc": "2.0", "id": 1, "method": "initialize",
                         "params": {"protocolVersion": "2025-06-18",
                                    "capabilities": {},
                                    "clientInfo": {"name": "t"}}}])
        reply = json.loads(out)
        self.assertEqual(reply["result"]["protocolVersion"],
                         dispatch_mcp.PROTOCOL_VERSION)
        self.assertIn("tools", reply["result"]["capabilities"])
        self.assertEqual(reply["result"]["serverInfo"]["version"], "9.9.9")

    def test_tools_list_carries_every_tool_with_both_schemas(self):
        out = self.rpc([{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}])
        tools = json.loads(out)["result"]["tools"]
        self.assertEqual([t["name"] for t in tools],
                         ["relay", "triage", "round", "status"])
        for tool in tools:
            self.assertIn("inputSchema", tool)
            self.assertIn("outputSchema", tool)

    def test_a_tool_call_returns_structured_content_and_never_iserror(self):
        out = self.rpc([{"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                         "params": {"name": "relay",
                                    "arguments": {"items": [{"number": 7}]}}}])
        result = json.loads(out)["result"]
        self.assertEqual(result["isError"], False)
        self.assertEqual(result["structuredContent"]["delivered"], False)
        text_payload = json.loads(result["content"][0]["text"])
        self.assertEqual(text_payload, result["structuredContent"])

    def test_the_initialized_notification_yields_no_reply(self):
        out = self.rpc([{"jsonrpc": "2.0",
                         "method": "notifications/initialized"}])
        self.assertEqual(out, "")

    def test_an_unknown_method_is_32601(self):
        out = self.rpc([{"jsonrpc": "2.0", "id": 4, "method": "resources/list"}])
        self.assertEqual(json.loads(out)["error"]["code"], -32601)

    def test_a_garbage_line_is_32700(self):
        out = self.rpc(["this is not json"])
        self.assertEqual(json.loads(out)["error"]["code"], -32700)

    def test_every_reply_is_one_newline_terminated_json_line(self):
        out = self.rpc([
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "ping"},
        ])
        lines = out.splitlines()
        self.assertEqual(len(lines), 3)
        self.assertTrue(out.endswith("\n"))
        for line in lines:
            json.loads(line)


if __name__ == "__main__":
    unittest.main()
