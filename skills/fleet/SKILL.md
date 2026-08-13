---
name: fleet
description: Drive an org's flywheel fleet from its manifest — flywheel up starts dispatch and the server that runs the loops, flywheel server is that daemon, flywheel status reports every row against the live roster and every milestone with a job. Use when the operator asks to bring the fleet up, check on the fleet, join a host to the fleet, park or place an actor, or set up a new org's fleet.yaml.
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
"${CLAUDE_PLUGIN_ROOT}"/bin/flywheel status  # rows vs the roster, and the tracker's jobs
"${CLAUDE_PLUGIN_ROOT}"/bin/flywheel up      # dispatch, then the server, detached
"${CLAUDE_PLUGIN_ROOT}"/bin/flywheel server  # the daemon itself, in the foreground
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
hostnames, and the dispatch row.

`loops_cwd:` is the checkout the loop processes run in, relative to the
org folder — the repo holding `openspec/changes/`. Without it the server
has nowhere to start a loop and says so rather than starting nothing
quietly.

An actor row's `prompt:` is delivered as its own message rather than
folded into a longer one, which is what makes a slash command in it
load.

### Grant each built repo's hook approvals

Once per built repo, before bringing the fleet up, the operator runs — in
a terminal, with the working directory inside that repo:

```
wt config approvals add
```

`wt` runs a project hook only against a standing grant, so a repo whose
`.config/wt.toml` hooks are ungranted is a repo whose merge gate its
agents cannot run. `flywheel up` checks this before starting an actor
and the server checks it before starting a loop process — both **refuse
to start work into a repo that fails it**, naming the ungranted
templates and this command;
`flywheel status` reports it as a row per repo. Ungranted, the stoppage
would otherwise land mid-merge, on an agent with no way to fix it.

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

## What this command never does

It never decides ownership (the tracker items' assignee does), never
stops a manifest row (dispatch and any hand-placed actor are the
manifest's), and never starts a `parked` row — parked is a statement
that requests wait as queued items and comments until the actor is next
started. Rows on other hosts are reported, not driven.

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

After hand-starting an actor outside this command, record it in
`fleet.yaml` — the manifest is placement's one record, and an actor it
does not carry is invisible to `flywheel status`.
