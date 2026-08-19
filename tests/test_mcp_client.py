"""The daemon's stdio MCP client — handshake, results, and the no-raise rule.

The daemon must never die on a broken proxy, so every failure shape a
spawned server can produce — refusing to spawn, dying mid-handshake,
speaking garbage, erroring a call — has to come back as a delivery
result. These tests script the server side through a fake Popen.
"""

import io
import json
import unittest

from context import BIN  # noqa: F401 — puts bin/ on sys.path

import _flywheel_mcp_client as mcp_client  # noqa: E402


def replies(*messages):
    return "".join(json.dumps(m, separators=(",", ":")) + "\n"
                   for m in messages)


INIT_OK = {"jsonrpc": "2.0", "id": 1,
           "result": {"protocolVersion": mcp_client.PROTOCOL_VERSION,
                      "capabilities": {"tools": {}},
                      "serverInfo": {"name": "flywheel-dispatch",
                                     "version": "0"}}}


class Recorder(io.StringIO):
    def close(self):  # keep the buffer readable after the client closes us
        pass


class FakeProc:
    def __init__(self, stdout_text):
        self.stdin = Recorder()
        self.stdout = io.StringIO(stdout_text)
        self.killed = False

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.killed = True


def fake_popen(stdout_text, spawns=None):
    def popen(argv, **kwargs):
        proc = FakeProc(stdout_text)
        if spawns is not None:
            spawns.append((argv, proc))
        return proc
    return popen


class HandshakeTest(unittest.TestCase):

    def test_initialize_then_initialized_then_the_call(self):
        spawns = []
        call_reply = {"jsonrpc": "2.0", "id": 2,
                      "result": {"structuredContent": {"delivered": True},
                                 "content": [], "isError": False}}
        with mcp_client.StdioMcp(["srv"],
                                 popen=fake_popen(replies(INIT_OK, call_reply),
                                                  spawns)) as mcp:
            result = mcp.call("relay", {"items": [{"number": 1}]})
        self.assertEqual(result, {"delivered": True})
        sent = [json.loads(line) for line in
                spawns[0][1].stdin.getvalue().splitlines()]
        self.assertEqual([m.get("method") for m in sent],
                         ["initialize", "notifications/initialized",
                          "tools/call"])
        self.assertEqual(sent[0]["params"]["protocolVersion"],
                         mcp_client.PROTOCOL_VERSION)
        self.assertEqual(sent[2]["params"],
                         {"name": "relay", "arguments": {"items": [{"number": 1}]}})

    def test_text_content_is_the_fallback_for_structured(self):
        payload = {"delivered": False, "reason": "dispatch is absent"}
        call_reply = {"jsonrpc": "2.0", "id": 2,
                      "result": {"content": [{"type": "text",
                                              "text": json.dumps(payload)}],
                                 "isError": False}}
        with mcp_client.StdioMcp(["srv"],
                                 popen=fake_popen(replies(INIT_OK, call_reply))
                                 ) as mcp:
            self.assertEqual(mcp.call("relay", {"items": []}), payload)


class NeverRaiseTest(unittest.TestCase):

    def test_a_server_that_cannot_spawn_is_a_delivery_result(self):
        def popen(argv, **kwargs):
            raise OSError("no such file")
        with mcp_client.StdioMcp(["srv"], popen=popen) as mcp:
            result = mcp.call("relay", {"items": []})
        self.assertFalse(result["delivered"])
        self.assertIn("no such file", result["reason"])

    def test_a_server_that_dies_mid_handshake_is_a_delivery_result(self):
        with mcp_client.StdioMcp(["srv"], popen=fake_popen("")) as mcp:
            result = mcp.call("relay", {"items": []})
        self.assertFalse(result["delivered"])
        self.assertTrue(result["reason"])

    def test_a_garbage_speaking_server_is_a_delivery_result(self):
        with mcp_client.StdioMcp(["srv"],
                                 popen=fake_popen("not json\n")) as mcp:
            result = mcp.call("relay", {"items": []})
        self.assertFalse(result["delivered"])
        self.assertIn("non-JSON", result["reason"])

    def test_a_jsonrpc_error_reply_is_a_delivery_result(self):
        err = {"jsonrpc": "2.0", "id": 2,
               "error": {"code": -32602, "message": "unknown tool: nope"}}
        with mcp_client.StdioMcp(["srv"],
                                 popen=fake_popen(replies(INIT_OK, err))) as mcp:
            result = mcp.call("nope", {})
        self.assertFalse(result["delivered"])
        self.assertIn("unknown tool: nope", result["reason"])


class DispatchOverMcpTest(unittest.TestCase):

    def test_the_adapter_maps_both_tools_onto_one_session(self):
        spawns = []
        r1 = {"jsonrpc": "2.0", "id": 2,
              "result": {"structuredContent": {"delivered": True}}}
        r2 = {"jsonrpc": "2.0", "id": 3,
              "result": {"structuredContent": {
                  "delivered": False, "reason": "dispatch is busy (working)"}}}
        dispatch = mcp_client.DispatchOverMcp(
            ["srv"], popen=fake_popen(replies(INIT_OK, r1, r2), spawns))
        with dispatch() as d:
            self.assertEqual(d.relay([{"number": 1}]), {"delivered": True})
            self.assertEqual(d.triage([{"number": 2}])["reason"],
                             "dispatch is busy (working)")
        self.assertEqual(len(spawns), 1)
        sent = [json.loads(line) for line in
                spawns[0][1].stdin.getvalue().splitlines()]
        names = [m["params"]["name"] for m in sent
                 if m.get("method") == "tools/call"]
        self.assertEqual(names, ["relay", "triage"])


if __name__ == "__main__":
    unittest.main()
