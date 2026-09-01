"""A stdio MCP client, sized for one consumer: the fleet daemon.

The daemon talks to dispatch ONLY through the plugin's dispatch MCP
server — the same three tools every plugin-bearing session holds — so the
interface stays load-bearing and the cloud move later is a transport swap
here, not a daemon rewrite. One `StdioMcp` session per reconcile pass:
the proxy distinguishes "busy on our own earlier prompt" from external
busy by session lifetime, so the pass's calls must share one.

Nothing here raises to the caller. A proxy that cannot be spawned, dies
mid-handshake, speaks garbage, or exceeds the deadline yields
`{"delivered": false, "reason": ...}` — the daemon records the divergence
and takes the next tick; it must never die on a broken proxy.
"""

import json
import select
import subprocess
import time

PROTOCOL_VERSION = "2025-06-18"

# The proxy's relay path legitimately polls for ~32s before conceding a
# prompt never went to work; the deadline sits well above it and well
# below a pass interval pile-up.
CALL_TIMEOUT_S = 120


class StdioMcp:
    """One MCP session over a spawned stdio server. Use as a context
    manager; `call()` never raises."""

    def __init__(self, argv, env=None, popen=subprocess.Popen,
                 timeout=CALL_TIMEOUT_S, clock=time.monotonic):
        self.argv = [str(a) for a in argv]
        self.env = env
        self.popen = popen
        self.timeout = timeout
        self.clock = clock
        self.proc = None
        self.fault = None
        self._id = 0

    # -- lifecycle ---------------------------------------------------------

    def __enter__(self):
        try:
            self.proc = self.popen(self.argv, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, text=True,
                                   env=self.env)
        except OSError as e:
            self.fault = f"could not start {self.argv[0]}: {e}"
            return self
        reply = self._request("initialize", {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "flywheel-server"},
        })
        if reply is None or "error" in reply:
            self.fault = self.fault or "the dispatch MCP server refused initialize"
        else:
            self._notify("notifications/initialized")
        return self

    def __exit__(self, *_exc):
        if self.proc is None:
            return False
        try:
            self.proc.stdin.close()
        except (OSError, ValueError):
            pass
        try:
            self.proc.wait(timeout=5)
        except Exception:  # noqa: BLE001 — a hung proxy is killed, not waited on
            try:
                self.proc.kill()
            except OSError:
                pass
        return False

    # -- the one public verb ----------------------------------------------

    def call(self, tool: str, arguments: dict) -> dict:
        """One tools/call, returned as the tool's payload dict. Every
        failure shape is a delivery result, never an exception."""
        if self.fault:
            return {"delivered": False, "reason": self.fault}
        reply = self._request("tools/call",
                              {"name": tool, "arguments": arguments})
        if reply is None:
            return {"delivered": False,
                    "reason": self.fault or "no reply from the dispatch MCP server"}
        if "error" in reply:
            return {"delivered": False,
                    "reason": ("dispatch MCP error: "
                               + str(reply["error"].get("message", reply["error"])))}
        result = reply.get("result") or {}
        structured = result.get("structuredContent")
        if isinstance(structured, dict):
            return structured
        for block in result.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "text":
                try:
                    payload = json.loads(block.get("text", ""))
                except ValueError:
                    break
                if isinstance(payload, dict):
                    return payload
        return {"delivered": False,
                "reason": "the dispatch MCP server returned an unreadable result"}

    # -- plumbing ----------------------------------------------------------

    def _notify(self, method: str) -> None:
        self._write({"jsonrpc": "2.0", "method": method})

    def _request(self, method: str, params: dict) -> dict | None:
        self._id += 1
        if not self._write({"jsonrpc": "2.0", "id": self._id,
                            "method": method, "params": params}):
            return None
        deadline = self.clock() + self.timeout
        while True:
            line = self._readline(deadline)
            if line is None:
                return None
            line = line.strip()
            if not line:
                continue
            try:
                reply = json.loads(line)
            except ValueError:
                self.fault = "the dispatch MCP server spoke a non-JSON line"
                return None
            # Server-initiated notifications are skipped; only the answer
            # to OUR id ends the wait.
            if isinstance(reply, dict) and reply.get("id") == self._id:
                return reply

    def _write(self, msg: dict) -> bool:
        try:
            self.proc.stdin.write(json.dumps(msg, separators=(",", ":")) + "\n")
            self.proc.stdin.flush()
            return True
        except (OSError, ValueError, BrokenPipeError) as e:
            self.fault = f"the dispatch MCP server is unwritable: {e}"
            return False

    def _readline(self, deadline: float) -> str | None:
        stream = self.proc.stdout
        try:
            fd = stream.fileno()
        except Exception:  # noqa: BLE001 — test doubles have no fd; block
            line = stream.readline()
            if not line:
                self.fault = "the dispatch MCP server closed its stream"
                return None
            return line
        while True:
            left = deadline - self.clock()
            if left <= 0:
                self.fault = (f"the dispatch MCP server answered nothing "
                              f"within {self.timeout}s")
                return None
            ready, _, _ = select.select([fd], [], [], min(left, 1.0))
            if not ready:
                continue
            line = stream.readline()
            if not line:
                self.fault = "the dispatch MCP server closed its stream"
                return None
            return line


class DispatchOverMcp:
    """The daemon's handle on dispatch — a factory the server opens once
    per pass (`with dispatch() as d:`), so the pass's relay and triage
    calls share one proxy session."""

    def __init__(self, argv, env=None, popen=subprocess.Popen,
                 timeout=CALL_TIMEOUT_S):
        self.argv = argv
        self.env = env
        self.popen = popen
        self.timeout = timeout
        self._mcp = None

    def __call__(self):
        return self

    def __enter__(self):
        self._mcp = StdioMcp(self.argv, env=self.env, popen=self.popen,
                             timeout=self.timeout).__enter__()
        return self

    def __exit__(self, *exc):
        mcp, self._mcp = self._mcp, None
        return mcp.__exit__(*exc)

    def relay(self, items: list) -> dict:
        return self._mcp.call("relay", {"items": items})

    def triage(self, items: list) -> dict:
        return self._mcp.call("triage", {"items": items})

    def round(self, items: list) -> dict:
        return self._mcp.call("round", {"items": items})
