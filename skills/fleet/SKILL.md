---
name: fleet
description: Drive an org's flywheel fleet from its manifest — flywheel up starts every running-state actor into the org's named herdr session, flywheel status reports every row against the live roster. Use when the operator asks to bring the fleet up, check on the fleet, park or place conductors, or set up a new org's fleet.yaml.
---

# Fleet — the org's conductors, placed and restored

One fleet per GitHub org, in its own named herdr session. The manifest is
`fleet.yaml` at the **org folder root** — the directory above the org's
repos — and it is not checked into git: placement is machine-local, and
`cwd:` entries are relative to that folder.

## The command

An installed plugin's `bin/` is on your `PATH`, so the command is bare:

```bash
flywheel status   # every row vs the live roster
flywheel up       # start running-state rows on this host
```

When `bin/` is not on `PATH` (a checkout, `--plugin-dir` development),
run it as `${CLAUDE_PLUGIN_ROOT}/bin/flywheel status`.

Both take `--fleet <path>` when invoked outside the org tree, and
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
`fleet.yaml`, then fill in the hosts' hostnames and the actor rows. A
conductor row's `prompt:` is the whole load-bearing invocation, slash
command included:

```
/opsx:apply build a dynamic workflow with the instructions for <change>
```

Sent as prose inside a longer message it loads nothing — the prompt field
is delivered as its own message, which is why it works.

## What this command never does

It never decides ownership (a change's `.openspec.yaml` `owner:` does),
never tears an actor down (teardown is deliberate), and never starts a
`parked` row — parked is a statement that requests wait in the change's
`inbox/` until the actor is next started. Rows on other hosts are
reported, not driven: herdr remote first, ssh + prompt as fallback,
inbox + waker when neither reaches.

After hand-starting a conductor outside this command, record it in
`fleet.yaml` — the manifest is placement's one record, and an actor it
does not carry is invisible to `flywheel status`.
