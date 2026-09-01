"""The fleet manifest — `fleet.yaml` at the org folder root.

The manifest is a constrained YAML subset parsed here without a YAML
dependency: two-space indentation, top-level scalars, `hosts:` a map of
flat maps, `dispatch:` one flat map whose `env:` value is itself a flat
map, scalar values only. Only FULL-LINE comments are recognized — a `#`
inside a value is part of the value.

`fleet.yaml` is machine-local and never in git: placement is per-machine,
and `cwd:` entries are relative to the manifest's directory. `validate`
therefore refuses with a message rather than migrating — a message is the
only migration a file outside version control can have.
"""

import sys
from pathlib import Path

# The dispatch block's whole vocabulary. A hand-rolled parser's failure
# mode is silence, so a key outside this set is refused by name rather
# than dropped — a typo must not vanish.
DISPATCH_KEYS = {"host", "model", "channels", "env", "prompt"}

# The fleet-level credentials block: environment every actor the
# manifest launches inherits — the daemon, the loops it starts, and the
# panes. Squatting the org's GitHub App id in `dispatch.env` left every
# non-dispatch actor re-reading dispatch's block by hand (problem 10,
# willdan fleet). `FLYWHEEL_GH_APP_KEY` accepts `flywheel-token`'s
# `op:<vault>/<item>` form as well as a pem path.
CREDENTIAL_KEYS = {"FLYWHEEL_GH_APP_ID", "FLYWHEEL_GH_APP_KEY",
                   "FLYWHEEL_GH_ORG"}

# Manifest keys retired as the fleet's shape settled, each matched and
# refused with its fix. The server starts loop PROCESSES, which have a
# working directory and no model, and dispatch — the one standing agent —
# has its own `dispatch:` block and its own start command. A manifest
# still carrying one of these keys is stale in a way that would otherwise
# be silent. `fleet.yaml` is machine-local and no commit can migrate it;
# only a message can. The strings below are that matcher, not a live
# reference.
RETIRED_KEYS = {
    "conductors_cwd": "rename it to `loops_cwd:`",
    "conductor_model": "drop it; a loop process has no model",
    "actors": "replace it with a top-level `dispatch:` block — dispatch is "
              "the only standing agent, started by `flywheel dispatch`; "
              "the loops are processes the server starts",
}


def find_manifest(override: str | None) -> Path:
    if override:
        p = Path(override).expanduser().resolve()
        if not p.is_file():
            sys.exit(f"--fleet {override}: no such file")
        return p
    cur = Path.cwd().resolve()
    for d in [cur, *cur.parents]:
        candidate = d / "fleet.yaml"
        if candidate.is_file():
            return candidate
    sys.exit("no fleet.yaml found walking up from here — the manifest lives "
             "at the org folder root; pass --fleet to name one explicitly")


def parse_manifest(path: Path) -> dict:
    hosts: dict[str, dict] = {}
    dispatch: dict = {}
    teams: dict[str, str] = {}
    books: dict[str, dict] = {}
    credentials: dict[str, str] = {}
    top: dict[str, str] = {}
    section = None
    current_host = None
    current_book = None
    in_env = False
    for raw in path.read_text().splitlines():
        if raw.lstrip().startswith("#") or not raw.strip():
            continue
        line = raw.rstrip()
        if line == "hosts:":
            section = "hosts"
        elif line == "dispatch:":
            section, in_env = "dispatch", False
        elif line == "teams:":
            section = "teams"
        elif line == "credentials:":
            section = "credentials"
        elif line == "books:":
            section, current_book = "books", None
        elif not line.startswith(" ") and ":" in line:
            # a top-level key anywhere ends the current section — never
            # silently absorbed into the last open map
            section, current_host = None, None
            k, _, v = line.partition(":")
            top[k.strip()] = v.strip().strip('"')
        elif section == "hosts" and line.startswith("  ") and not line.startswith("    "):
            current_host = line.strip().rstrip(":")
            hosts[current_host] = {}
        elif section == "hosts" and line.startswith("    ") and current_host:
            k, _, v = line.strip().partition(":")
            hosts[current_host][k] = v.strip().strip('"')
        elif section == "dispatch" and line == "  env:":
            in_env = True
            dispatch.setdefault("env", {})
        elif section == "dispatch" and in_env and line.startswith("    "):
            k, _, v = line.strip().partition(":")
            dispatch["env"][k.strip()] = v.strip().strip('"')
        elif section == "dispatch" and line.startswith("  ") and not line.startswith("    "):
            in_env = False
            k, _, v = line.strip().partition(":")
            dispatch[k.strip()] = v.strip().strip('"')
        elif section == "teams" and line.startswith("  "):
            k, _, v = line.strip().partition(":")
            teams[k.strip()] = v.strip().strip('"')
        elif section == "credentials" and line.startswith("  "):
            k, _, v = line.strip().partition(":")
            credentials[k.strip()] = v.strip().strip('"')
        elif section == "books" and line.startswith("  ") and not line.startswith("    "):
            current_book = line.strip().rstrip(":")
            books[current_book] = {}
        elif section == "books" and line.startswith("    ") and current_book:
            k, _, v = line.strip().partition(":")
            books[current_book][k.strip()] = v.strip().strip('"')
    manifest = {"top": top, "hosts": hosts, "dispatch": dispatch,
                "teams": teams, "books": books, "credentials": credentials,
                "root": path.parent, "path": path}
    validate(manifest)
    return manifest


def validate(manifest: dict) -> None:
    problems = []
    for key, fix in RETIRED_KEYS.items():
        if key in manifest["top"]:
            problems.append(f"`{key}:` retired — {fix}")
    dispatch = manifest.get("dispatch") or {}
    for key in dispatch:
        if key not in DISPATCH_KEYS:
            problems.append(f"dispatch: unknown key `{key}:` — the block "
                            f"takes {', '.join(sorted(DISPATCH_KEYS))}")
    if dispatch and not dispatch.get("prompt"):
        problems.append("dispatch: missing prompt")
    if dispatch.get("host") and dispatch["host"] not in manifest["hosts"]:
        problems.append(f"dispatch: host '{dispatch['host']}' is not in hosts:")
    for team, host in manifest["teams"].items():
        if host not in manifest["hosts"]:
            problems.append(f"teams: {team} → '{host}' is not in hosts:")
    for key in manifest.get("credentials") or {}:
        if key not in CREDENTIAL_KEYS:
            problems.append(
                f"credentials: unknown key `{key}:` — the block takes "
                f"{', '.join(sorted(CREDENTIAL_KEYS))}")
    if problems:
        sys.exit("manifest invalid:\n  " + "\n  ".join(problems))
