---
name: fleet
description: Drive an org's flywheel fleet from its manifest — flywheel up starts the server that runs the loops, flywheel dispatch starts the org's standing dispatch agent with its Discord channel, flywheel server is that daemon, flywheel status reports dispatch and every milestone with a job. Use when the operator asks to bring the fleet up, check on the fleet, start or place dispatch, join a host to the fleet, or set up a new org's fleet.yaml.
---

# Fleet — the org's server, its loops, and dispatch

One fleet per GitHub org, in its own named herdr session. The manifest is
`fleet.yaml` at the **org folder root** — the directory above the org's
repos — and it is not checked into git: placement is machine-local, and
`cwd:` entries are relative to that folder.

The manifest is **server config plus dispatch**. The work itself is not
in it and never was: the tracker says which milestones have jobs, and the
server starts one loop process per milestone that does.

## The command

The plugin's `bin/` is not reliably on `PATH` (measured: a
directory-marketplace install leaves it off), so invoke by the plugin
root — `${CLAUDE_PLUGIN_ROOT}` is substituted into this skill at load:

```bash
"${CLAUDE_PLUGIN_ROOT}"/bin/flywheel status    # dispatch vs the roster, and the tracker's jobs
"${CLAUDE_PLUGIN_ROOT}"/bin/flywheel up        # the server, detached
"${CLAUDE_PLUGIN_ROOT}"/bin/flywheel dispatch  # the standing dispatch agent
"${CLAUDE_PLUGIN_ROOT}"/bin/flywheel server    # the daemon itself, in the foreground
```

`server` takes `--interval SECONDS` (default 60), `--once` for a single
pass, and `--dry-run` to read and plan without starting, stopping or
writing anything. All three take `--fleet <path>` when invoked outside the org tree, and
`--host <name>` to override host detection. The command walks up from the
working directory to find `fleet.yaml`, so from any repo in the org the
bare command does the right thing.

## The session

The fleet runs in the herdr session named by the manifest's `session:`
field (default: the org folder's name, `github_` stripped). The command
targets that session's socket and never starts agents anywhere else.
When the session is not running the command stops and says:

```
herdr --session <org>
```

Starting the session is the operator's — attach it once and it persists.

## Setting up a new org

Copy `template-fleet.yaml` (beside this skill) to the org folder root as
`fleet.yaml`, then fill in `tracker:`, `loops_cwd:`, the hosts'
hostnames, and the `dispatch:` block.

`loops_cwd:` is the checkout the loop processes run in, relative to the
org folder — the repo holding `openspec/changes/`. Without it the server
has nowhere to start a loop and says so rather than starting nothing
quietly.

The dispatch block's `prompt:` is delivered as its own message rather
than folded into a longer one, which is what makes a slash command in it
load. Its `host:` is optional — set, it pins dispatch to one host and
the command run anywhere else refuses, naming the owner (reachable via
herdr remote); absent, dispatch runs wherever `flywheel dispatch` is
invoked. `channels:` and `env:` are what connect the Discord bridge: the
channel plugin lands on claude as `--channels`, and `DISCORD_STATE_DIR`
resolves to `<org folder>/.flywheel/discord` — the org's own bot token
and allowlist, seeded by the operator, never shared with a personal
machine-level bot.

### Grant each built repo's hook approvals

Once per built repo, before bringing the fleet up, the operator runs — in
a terminal, with the working directory inside that repo:

```
wt config approvals add
```

`wt` runs a project hook only against a standing grant, so a repo whose
`.config/wt.toml` hooks are ungranted is a repo whose merge gate its
agents cannot run. The server checks it before starting a loop process
and **refuses to start work into a repo that fails it**, naming the
ungranted templates and this command; `flywheel status` reports it as a
row for the loops' checkout. Ungranted, the stoppage would otherwise
land mid-merge, on an agent with no way to fix it. Dispatch is exempt by
shape — it holds no checkout and never merges — so `flywheel dispatch`
runs on a host with no grants at all.

It is deliberately the operator's step and deliberately interactive.
Read the templates it lists before approving them — approving is saying
these commands may run on your machine, and the fleet cannot say that on
your behalf. The grant is keyed on the template text, so one approval
covers every branch's expansion of a template, and moving a check
between hook events without changing its text keeps the grant (measured).
Adding or editing a template needs a fresh grant.

The fleet never writes the approvals store and never approves on your
behalf. If a repo's hooks change and no one has re-granted them, the
right outcome is the refusal you get — not a way around it.

## What these commands never do

They never decide ownership (the tracker items' assignee does) and never
stop an agent — teardown is the operator's, deliberate, never a sync
step. `flywheel dispatch` is idempotent: a dispatch already alive is
reported and left exactly as it is, so restarting it to pick up a new
channel or env is the operator ending the pane first, then running the
command again. A dispatch pinned to another host is reported, not
driven.

## Talking to dispatch

The plugin ships a `dispatch` MCP server (`.mcp.json` →
`bin/flywheel-dispatch-mcp`), so every plugin-bearing session holds the
same three tools: `relay(items)` for needs-operator escalations,
`triage(items)` for unmilestoned open items, `status()` for presence.
That surface is the ONE way anything talks to dispatch — the fleet
daemon consumes it too, one session per reconcile pass. Today the server
proxies to the dispatch claude session in its herdr pane; when dispatch
becomes a hosted service, the proxy's internals are what change, and
consumers keep the tools. Undeliverability is always a tool result —
`delivered: false` with the reason — never an error: an absent or busy
dispatch is a fact the caller records, and the daemon ledgers every
delivery under `observations/dispatch/`.

## The server

`flywheel server` is the daemon the operator starts on any host they
want in the fleet. Every 60 seconds it reads the tracker and starts one
**loop process** per milestone with a job — `flywheel-bolt-loop` for a
`bolt/*` milestone, `flywheel-intent-loop` for an `intent/*` one — stops
the process for any milestone that no longer has one, and runs a
one-shot archive for a closed milestone whose change still sits in
`openspec/changes/`.

A milestone has a job when it holds an open `state:ready` or
`state:in-progress` item, or a batch the operator moved to Ready on the
board. The loops are stateless: stopping one loses nothing, and a later
job starts a fresh process that re-reads the tracker and the records.

**Multi-host is one server per host, sharing the tracker.** A board Team
routes its milestone through the manifest's `teams:` map, and a server
takes only the loops that map to it; work with no team, or a team no
host claims, runs wherever the server sees it. One server per org per
host — a second would start every loop twice, and the first one's
pidfile is what stops that.

Operator visibility is the server's log, under
`$XDG_STATE_HOME` (or `~/.local/state`) `/flywheel/<org>/` — `server.log`
for the pass, and one `loops/<kind>-<slug>.log` per loop process.
`flywheel status` names both.

