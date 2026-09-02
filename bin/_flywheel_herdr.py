"""Herdr plumbing shared by the fleet CLI and the dispatch MCP proxy.

Everything here RETURNS its outcome — nothing prints and nothing exits.
The callers split two ways: `bin/flywheel` wraps these with the printing
and the `sys.exit`s its commands owe the operator, and the dispatch MCP
proxy shares its stdout with the protocol stream, where a stray print is
a corrupted message. That constraint is why this module exists.
"""

import json
import os
import re
import shutil
import subprocess
import time


def session_name(manifest: dict) -> str:
    name = manifest["top"].get("session") or manifest["root"].name
    # normalize an org folder like github_willdan to its plain org name
    return re.sub(r"^github_", "", name)


def session_socket(name: str, run=subprocess.run) -> str | None:
    """The socket path of the running herdr session `name`, or None when
    that session is not running. Raises RuntimeError when herdr itself
    cannot be asked — a missing binary and a failing `session list` are
    faults, not absences."""
    if shutil.which("herdr") is None:
        raise RuntimeError(
            "herdr not on PATH — the fleet is not addressable from here")
    out = run(["herdr", "session", "list"], capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"herdr session list failed: {out.stderr.strip()}")
    sock = None
    for line in out.stdout.splitlines()[1:]:
        cols = line.split()
        if len(cols) >= 4 and cols[0] == name and cols[1] == "running":
            sock = cols[-1]
    return sock


def session_environ(sock: str, environ=None) -> dict:
    env = dict(os.environ if environ is None else environ)
    env["HERDR_SOCKET_PATH"] = sock
    return env


def herdr_json(argv: list[str], env: dict, run=subprocess.run) -> dict:
    out = run(argv, capture_output=True, text=True, env=env)
    if out.returncode != 0:
        raise RuntimeError(f"{' '.join(argv)} failed: {out.stderr.strip()}")
    try:
        return json.loads(out.stdout or "{}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"{' '.join(argv)} returned unparseable output: {e}")


def herdr_agents(env: dict, run=subprocess.run) -> dict[str, dict]:
    data = herdr_json(["herdr", "agent", "list"], env, run=run)
    rows = data.get("result", {}).get("agents", [])
    return {
        (a.get("name") or a.get("terminal_title_stripped", "")): a
        for a in rows
        if isinstance(a, dict)
    }


def send_prompt(name: str, text: str, env: dict,
                run=subprocess.run, sleep=time.sleep) -> tuple[bool, str]:
    """Deliver one prompt to the named agent — `(delivered, reason)`.

    The roster row is the address: a pane listed under its title alone
    (herdr reports some agents with no `name` — observed live on
    plan-willdan-blueprints) is not reachable by that title, and the
    prompt fails `agent_not_found`. So the target is the row's name when
    it has one and its pane id otherwise."""
    try:
        row = herdr_agents(env, run=run).get(name, {})
    except RuntimeError:
        row = {}
    target = row.get("name") or row.get("pane_id") or name
    sent = run(["herdr", "agent", "prompt", target, text],
               capture_output=True, text=True, env=env)
    if sent.returncode != 0:
        return False, f"prompt to {name} failed: {sent.stderr.strip()}"
    # A multi-line or slow-composer prompt can land unsubmitted — the
    # agent stays idle with the text sitting at its prompt. Verify it
    # went to work; one Enter submits a stuck composer. A fresh session
    # initializes for tens of seconds (plugin load), so the window is
    # generous — a first prompt regularly submits near the 30s mark.
    for _attempt in range(8):
        sleep(4)
        try:
            agent = herdr_agents(env, run=run).get(name, {})
        except RuntimeError as e:
            return False, str(e)
        if agent.get("agent_status") == "working":
            return True, ""
        run(["herdr", "agent", "send-keys", target, "enter"],
            capture_output=True, text=True, env=env)
    return False, (f"{name} never went to work on the prompt — read its pane "
                   "and prompt it by hand")
