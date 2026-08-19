"""The fleet manifest — `fleet.yaml` at the org folder root.

The manifest is a constrained YAML subset parsed here without a YAML
dependency: two-space indentation, top-level scalars, `actors:` a list
of flat maps, `hosts:` a map of flat maps, scalar values only. Only
FULL-LINE comments are recognized — a `#` inside a value is part of the
value.

`fleet.yaml` is machine-local and never in git: placement is per-machine,
and `cwd:` entries are relative to the manifest's directory. `validate`
therefore refuses with a message rather than migrating — a message is the
only migration a file outside version control can have.
"""

import sys
from pathlib import Path

STATES = {"running", "parked"}

# Two manifest keys retired with the agent fleet they configured: one named
# the directory those agents started in, the other the model they launched
# on. The server starts loop PROCESSES, which have a working directory and no
# model. A manifest still carrying either key is stale in a way that would
# otherwise be silent — the server would look for `loops_cwd:`, find nothing
# and start nothing — so these are named, matched, and refused with the fix.
# `fleet.yaml` is machine-local and no commit can migrate it; only a message
# can. The strings below are that matcher, not a live reference.
RETIRED_KEYS = {
    "conductors_cwd": "loops_cwd",
    "conductor_model": None,
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
    actors: list[dict] = []
    teams: dict[str, str] = {}
    books: dict[str, dict] = {}
    top: dict[str, str] = {}
    section = None
    current: dict | None = None
    current_host = None
    current_book = None
    for raw in path.read_text().splitlines():
        if raw.lstrip().startswith("#") or not raw.strip():
            continue
        line = raw.rstrip()
        if line == "hosts:":
            section, current = "hosts", None
        elif line == "actors:":
            section, current = "actors", None
        elif line == "teams:":
            section, current = "teams", None
        elif line == "books:":
            section, current, current_book = "books", None, None
        elif not line.startswith(" ") and ":" in line:
            # a top-level key anywhere ends the current section — never
            # silently absorbed into the last actor or host
            section, current, current_host = None, None, None
            k, _, v = line.partition(":")
            top[k.strip()] = v.strip().strip('"')
        elif section == "hosts" and line.startswith("  ") and not line.startswith("    "):
            current_host = line.strip().rstrip(":")
            hosts[current_host] = {}
        elif section == "hosts" and line.startswith("    ") and current_host:
            k, _, v = line.strip().partition(":")
            hosts[current_host][k] = v.strip().strip('"')
        elif section == "actors" and line.lstrip().startswith("- "):
            current = {}
            actors.append(current)
            k, _, v = line.lstrip()[2:].partition(":")
            current[k.strip()] = v.strip().strip('"')
        elif section == "actors" and current is not None:
            k, _, v = line.strip().partition(":")
            current[k.strip()] = v.strip().strip('"')
        elif section == "teams" and line.startswith("  "):
            k, _, v = line.strip().partition(":")
            teams[k.strip()] = v.strip().strip('"')
        elif section == "books" and line.startswith("  ") and not line.startswith("    "):
            current_book = line.strip().rstrip(":")
            books[current_book] = {}
        elif section == "books" and line.startswith("    ") and current_book:
            k, _, v = line.strip().partition(":")
            books[current_book][k.strip()] = v.strip().strip('"')
    manifest = {"top": top, "hosts": hosts, "actors": actors,
                "teams": teams, "books": books, "root": path.parent,
                "path": path}
    validate(manifest)
    return manifest


def validate(manifest: dict) -> None:
    problems = []
    for key, replacement in RETIRED_KEYS.items():
        if key in manifest["top"]:
            problems.append(
                f"`{key}:` retired with the agent fleet — "
                + (f"rename it to `{replacement}:`" if replacement
                   else "drop it; a loop process has no model"))
    for a in manifest["actors"]:
        name = a.get("name", "<unnamed>")
        for field in ("name", "profile", "host", "state", "cwd"):
            if not a.get(field):
                problems.append(f"{name}: missing {field}")
        if a.get("state") and a["state"] not in STATES:
            problems.append(f"{name}: state '{a['state']}' is not one of {sorted(STATES)}")
        if a.get("host") and a["host"] not in manifest["hosts"]:
            problems.append(f"{name}: host '{a['host']}' is not in hosts:")
        if a.get("cwd", "").startswith("/"):
            problems.append(f"{name}: cwd is absolute — cwd: entries are "
                            "relative to the manifest's directory")
    for team, host in manifest["teams"].items():
        if host not in manifest["hosts"]:
            problems.append(f"teams: {team} → '{host}' is not in hosts:")
    if problems:
        sys.exit("manifest invalid:\n  " + "\n  ".join(problems))
