"""The dispatch MCP server — the one standardized way to talk to dispatch.

Dispatch is the org's standing agent; everything that wants a word with it
calls these tools. Today the server is a PROXY: it renders each tool
call's items into prompt text and delivers it to the `dispatch` claude
session in its herdr pane. When dispatch becomes a hosted service, this
proxy's internals are what change — consumers keep the same three tools:

  relay(items)  -> {delivered, reason?}   needs-operator escalations
  triage(items) -> {delivered, reason?}   unmilestoned open items
  status()      -> {present, agent_status?, reason?}

Undeliverability is always a tool RESULT, never a JSON-RPC error: a
dispatch that is absent or busy is a fact for the caller to record, not a
protocol failure. Where the fact becomes tracker-visible is deliberately
unbuilt (the relay-delivery questions stay open); the caller gets the
truth and does with it what its own contract says.

Transport: newline-delimited JSON-RPC 2.0 over stdio, per the MCP spec —
one message per line, stdout carries protocol messages ONLY (diagnostics
go to stderr), which is why everything herdr-shaped here returns instead
of printing.

This process runs in every plugin-bearing session, fleetless hosts
included, so startup can never fail: the herdr session is resolved lazily
per call, and every resolution failure is a `delivered: false` reason.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _flywheel_herdr as herdr        # noqa: E402
import _flywheel_manifest as manifest_mod  # noqa: E402

PROTOCOL_VERSION = "2025-06-18"
SETTLED = {"idle", "done"}

_ITEM = {
    "type": "object",
    "properties": {
        "number": {"type": "integer"},
        "url": {"type": "string"},
        "title": {"type": "string"},
        # Unsent by today's caller; here so a richer caller — or the
        # hosted dispatch — can pass them without a schema change.
        "assignee": {"type": "string"},
        "question": {"type": "string"},
    },
    "required": ["number"],
}
_ITEMS = {
    "type": "object",
    "properties": {"items": {"type": "array", "items": _ITEM}},
    "required": ["items"],
}
_DELIVERY = {
    "type": "object",
    "properties": {"delivered": {"type": "boolean"},
                   "reason": {"type": "string"}},
    "required": ["delivered"],
}
_STATUS = {
    "type": "object",
    "properties": {"present": {"type": "boolean"},
                   "agent_status": {"type": "string"},
                   "reason": {"type": "string"}},
    "required": ["present"],
}

TOOLS = [
    {
        "name": "relay",
        "description": "Hand dispatch the needs-operator items awaiting "
                       "relay to the operator. Returns whether the batch "
                       "was delivered to dispatch, with the reason when "
                       "it was not.",
        "inputSchema": _ITEMS,
        "outputSchema": _DELIVERY,
    },
    {
        "name": "triage",
        "description": "Hand dispatch the material standing for a round — "
                       "unmilestoned intake and dispatch:standing items. "
                       "Returns whether the batch was delivered to "
                       "dispatch, with the reason when it was not.",
        "inputSchema": _ITEMS,
        "outputSchema": _DELIVERY,
    },
    {
        "name": "round",
        "description": "Hand dispatch the board work parked at Backlog — "
                       "batch parents and plan cards awaiting the "
                       "operator's approval. Returns whether the batch "
                       "was delivered to dispatch, with the reason when "
                       "it was not.",
        "inputSchema": _ITEMS,
        "outputSchema": _DELIVERY,
    },
    {
        "name": "status",
        "description": "Whether dispatch is reachable right now, and what "
                       "it is doing.",
        "inputSchema": {"type": "object", "properties": {}},
        "outputSchema": _STATUS,
    },
]


def _ref(item: dict) -> str:
    parts = [f"#{item.get('number')}"]
    if item.get("title"):
        parts.append(f'"{item["title"]}"')
    if item.get("url"):
        parts.append(item["url"])
    if item.get("question"):
        parts.append(f"({item['question']})")
    return " ".join(parts)


def render_relay(items: list) -> str:
    refs = "; ".join(_ref(i) for i in items)
    return (f"needs-operator items await relay: {refs} — DM each item's "
            "assignee with the question and the link")


def render_round(items: list) -> str:
    # Backlog board objects — elaboration parents and bolt plan cards —
    # awaiting the operator's approval. Nothing but a round can release
    # them, so the imperative is the same as triage's: run the round.
    refs = "; ".join(_ref(i) for i in items)
    return (f"board work awaits approval at Backlog: {refs} — run the "
            "round: derive it with flywheel-round and render the plan on "
            "both surfaces so the operator can flip, hold, or drop them")


def render_triage(items: list) -> str:
    # The round trigger the dispatch charter names as the server's poke:
    # standing payloads and close-ready parents ride this queue beside raw
    # intake, so the imperative is "run the round", never a per-item routing
    # order — the round derivation, not this sentence, says what each is.
    refs = "; ".join(_ref(i) for i in items)
    return (f"standing material awaits a dispatch plan: {refs} — run the "
            "round: derive it with flywheel-round, render the plan on both "
            "surfaces, and route any raw intake it carries")


class DispatchProxy:
    """Delivers to the dispatch claude session in its herdr pane.

    Resolution is lazy and per-call — the fleet, the session, and the
    roster are all read when a tool is called, never at startup.

    One session-scoped fact matters: whether WE have already delivered a
    prompt in this proxy's lifetime. A dispatch found busy before our
    first delivery is doing external work and is never interrupted; a
    dispatch busy after it is working on our own earlier prompt, and a
    follow-up is submitted into its composer queue. The caller spawning
    one proxy per pass is what makes that distinction sound.
    """

    def __init__(self, fleet: str | None = None, environ: dict | None = None,
                 run=subprocess.run, sleep=time.sleep):
        self.fleet = fleet
        self.environ = dict(os.environ if environ is None else environ)
        self.run = run
        self.sleep = sleep
        self.delivered_this_session = False

    # -- resolution --------------------------------------------------------

    def _env(self) -> tuple[dict | None, str | None]:
        """The herdr-addressed environment, or `(None, why_not)`."""
        if self.environ.get("HERDR_SOCKET_PATH"):
            return self.environ, None
        try:
            path = self._manifest_path()
            if path is None:
                return None, ("no fleet.yaml found walking up from here — "
                              "run inside the org folder or pass --fleet")
            try:
                manifest = manifest_mod.parse_manifest(path)
            except SystemExit as e:
                return None, str(e)
            name = herdr.session_name(manifest)
            try:
                sock = herdr.session_socket(name, run=self.run)
            except RuntimeError as e:
                return None, str(e)
            if not sock:
                return None, f"the '{name}' herdr session is not running"
            env = dict(self.environ)
            env["HERDR_SOCKET_PATH"] = sock
            return env, None
        except Exception as e:  # noqa: BLE001 — a tool result, never a crash
            return None, f"{type(e).__name__}: {e}"

    def _manifest_path(self) -> Path | None:
        if self.fleet:
            p = Path(self.fleet).expanduser().resolve()
            return p if p.is_file() else None
        cur = Path.cwd().resolve()
        for d in [cur, *cur.parents]:
            if (d / "fleet.yaml").is_file():
                return d / "fleet.yaml"
        return None

    def _agent(self, env: dict) -> tuple[dict | None, str | None]:
        try:
            return herdr.herdr_agents(env, run=self.run).get("dispatch"), None
        except RuntimeError as e:
            return None, str(e)

    # -- the tools ---------------------------------------------------------

    def status(self) -> dict:
        env, why = self._env()
        if env is None:
            return {"present": False, "reason": why}
        agent, fault = self._agent(env)
        if fault:
            return {"present": False, "reason": fault}
        if not agent:
            return {"present": False}
        return {"present": True,
                "agent_status": agent.get("agent_status", "alive")}

    def deliver(self, text: str) -> dict:
        env, why = self._env()
        if env is None:
            return {"delivered": False, "reason": why}
        agent, fault = self._agent(env)
        if fault:
            return {"delivered": False, "reason": fault}
        if not agent:
            return {"delivered": False,
                    "reason": "dispatch is absent from the herdr session"}
        agent_status = agent.get("agent_status")
        if agent_status not in SETTLED:
            if not self.delivered_this_session:
                return {"delivered": False,
                        "reason": f"dispatch is busy ({agent_status})"}
            # Busy on our own earlier prompt: submit into the composer
            # queue rather than waiting a pass. The went-to-work poll
            # would trivially succeed against an already-working agent,
            # so it is not run — submission is the fact reported.
            sent = self.run(["herdr", "agent", "prompt", "dispatch", text],
                            capture_output=True, text=True, env=env)
            if sent.returncode != 0:
                return {"delivered": False,
                        "reason": ("prompt to dispatch failed: "
                                   + sent.stderr.strip())}
            self.run(["herdr", "agent", "send-keys", "dispatch", "enter"],
                     capture_output=True, text=True, env=env)
            return {"delivered": True,
                    "reason": "queued behind the prior prompt"}
        delivered, reason = herdr.send_prompt("dispatch", text, env,
                                              run=self.run, sleep=self.sleep)
        if not delivered:
            return {"delivered": False, "reason": reason}
        self.delivered_this_session = True
        return {"delivered": True}

    def relay(self, items: list) -> dict:
        return self.deliver(render_relay(items))

    def triage(self, items: list) -> dict:
        return self.deliver(render_triage(items))

    def round(self, items: list) -> dict:
        return self.deliver(render_round(items))


# -- the protocol loop -------------------------------------------------------

def _result(msg_id, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _error(msg_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id,
            "error": {"code": code, "message": message}}


def handle(msg: dict, proxy: DispatchProxy, version: str = "0") -> dict | None:
    method = msg.get("method")
    msg_id = msg.get("id")
    if not isinstance(method, str):
        return (_error(msg_id, -32600, "no method") if msg_id is not None
                else None)
    if method.startswith("notifications/"):
        return None
    if method == "initialize":
        return _result(msg_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "flywheel-dispatch", "version": version},
        })
    if method == "ping":
        return _result(msg_id, {})
    if method == "tools/list":
        return _result(msg_id, {"tools": TOOLS})
    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if name == "relay":
            payload = proxy.relay(arguments.get("items") or [])
        elif name == "triage":
            payload = proxy.triage(arguments.get("items") or [])
        elif name == "round":
            payload = proxy.round(arguments.get("items") or [])
        elif name == "status":
            payload = proxy.status()
        else:
            return _error(msg_id, -32602, f"unknown tool: {name}")
        return _result(msg_id, {
            "content": [{"type": "text", "text": json.dumps(payload)}],
            "structuredContent": payload,
            "isError": False,
        })
    if msg_id is not None:
        return _error(msg_id, -32601, f"method not found: {method}")
    return None


def serve(stdin, stdout, proxy: DispatchProxy, version: str = "0") -> int:
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            _write(stdout, _error(None, -32700, "parse error"))
            continue
        reply = handle(msg, proxy, version)
        if reply is not None:
            _write(stdout, reply)
    return 0


def _write(stdout, reply: dict) -> None:
    # One newline-terminated JSON document per message; compact separators
    # and default ensure_ascii keep embedded newlines impossible.
    stdout.write(json.dumps(reply, separators=(",", ":")) + "\n")
    stdout.flush()


def plugin_version() -> str:
    plugin = Path(__file__).resolve().parent.parent / ".claude-plugin" / "plugin.json"
    try:
        return json.loads(plugin.read_text()).get("version", "0")
    except (OSError, ValueError):
        return "0"


def main(argv: list[str]) -> int:
    fleet = None
    if "--fleet" in argv:
        i = argv.index("--fleet")
        try:
            fleet = argv[i + 1]
        except IndexError:
            print("--fleet needs a value", file=sys.stderr)
            return 2
    proxy = DispatchProxy(fleet=fleet)
    return serve(sys.stdin, sys.stdout, proxy, version=plugin_version())
