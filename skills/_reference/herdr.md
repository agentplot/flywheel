# herdr and worktrunk — the invocations, spelled out

The one shared copy, at the flywheel plugin's `skills/_reference/herdr.md`; every skill
that needs these invocations points here rather than bundling its own.

Every command here is written out because it was rediscovered by trial and
error at least once. Verify syntax you do not find here with
`herdr <group> --help` or `wt <command> --help`, never from memory.

## Preconditions

```bash
test "${HERDR_ENV:-}" = 1        # you are inside a herdr session
command -v wt                    # worktrunk manages worktrees, merges and gates
```

If `HERDR_ENV` is unset you cannot start or address agents. Say so and stop
rather than falling back to the `Agent` tool.

## The pieces

- A **workspace** groups the tabs and panes of one worktree. `herdr worktree
  create` makes the worktree and its workspace together and returns both ids.
- A **pane** is one terminal. An agent runs in a pane, and a pane holds one
  agent.
- An **agent** is a named interactive session — `herdr agent start` attaches
  one to a pane that is sitting at its shell prompt.

Names are the addressing scheme. An agent you cannot name is an agent you
cannot prompt, wait on, or tear down.

## Cutting a worktree

```bash
herdr worktree create --cwd <the repo's parent workspace path> \
  --base main --branch <branch> --label "<short title>" --no-focus --json
```

`--cwd` takes the path of the repo the worktree is cut from — **not the path
of another worktree.** A worktree path returns `linked_worktree_source`; ten
calls across four sessions failed exactly this way. Read the workspace id,
the root pane id and the checkout path out of the `--json` output.

Worktrunk's own path does the same job and fires this repo's lifecycle hooks:

```bash
wt switch --create <branch> --base <base> --no-cd
```

No `--no-hooks`. This repo configures no `wt` lifecycle hooks today, so the
flag suppresses nothing and would silently skip the first one added.

A herdr-created worktree fires no `wt` lifecycle hooks. Run the repo's hook
yourself right after creating one:

```bash
wt -C <worktree-path> hook post-start
```

`-C` precedes the subcommand. A trailing `-C` reads the wrong directory and
reports no hooks.

## Starting an agent, and naming it before you send its work order

```bash
herdr tab create --cwd <worktree-path> --label "<short title>" --no-focus
herdr agent start <name> --kind claude --pane <pane-id> -- --agent <profile>
```

`--kind` takes one of: `pi, claude, codex, gemini, cursor, devin, agy, cline,
omp, mastracode, opencode, copilot, kimi, kiro, droid, amp, grok, hermes,
kilo, qodercli, maki`. Everything after `--` is passed to the agent binary,
which is how a profile (`--agent <profile>`) and a model (`--model <name>`)
are selected.

**Every session launch names its model.** The session type's definition
carries the default — the one enumeration is the type table in the
plugin's `openspec/specs/flywheel-session-type-skills/spec.md`: fable
for planning, interactive and proposal-review; `opus[1m]` for research,
spec-writing, build, test, code-review and human-code-review; opus for
prototype, writeback, handoff and proposal-writing — and a work order or
invocation may override it; pass whichever applies as `--model <name>`.
The standing actors — dispatch and both conductor kinds — run
`opus[1m]`, set on their fleet rows.

The pane must be at its interactive shell prompt before `agent start`.

**Rename, confirm, then send the work order — in that order, every time.**

```bash
herdr agent prompt <name> "/rename <name>"
herdr agent get <name>            # poll .terminal_title_stripped until it is <name>
herdr agent prompt <name> "<the work order>"
```

Two back-to-back prompts race in the composer. If the `/rename` has not
submitted when the work order arrives they concatenate and submit as one line —
the session takes a garbage name and the work order is never delivered. When the
title will not converge the composer is holding it unsubmitted:
`herdr agent send-keys <name> enter`, then re-check.

Recovery from a mangled rename: send `/rename <name>` alone, confirm the
title, then read the pane to find out whether the work order ever submitted.
Re-send it if not; never assume it did.

**A slash command typed as prose inside a work order body never loads the skill.**
Send it as its own prompt. This is how a spec agent came to run without
`/opsx:apply` loaded.

**Never queue a second prompt before the first one's effect is observed.**

## Watching an agent

```bash
herdr agent list                                   # every agent and its state
herdr agent wait <name>                            # park until it settles
herdr agent read <name> --source recent-unwrapped --lines 120
```

`herdr agent wait` **without `--until`** matches `idle`, `done` or `blocked`
— which is what "tell me when it needs me" means. A wait pinned to
`--until idle` never fires on an agent that settled at `done`, and `done` is
exactly what a finished agent shows when its tab was never focused. Pass
`--until` only for a genuinely state-specific wait. The same applies to
`herdr agent prompt --wait`, which already uses the settled defaults.

**Verify that a prompt submitted.** A multi-line prompt can land in the
composer as a pasted block without submitting — the pane shows
`[Pasted text …]` at the `❯` prompt and the agent stays settled. Check that
the agent goes `working`; submit with `herdr agent send-keys <name> enter`
if it did not.

**Composer text in a pane read is not input.** A read renders whatever sits
at the `❯` prompt, including Claude Code's ghost-text suggestions, which look
exactly like typed-but-unsent messages. Act only on messages that were
actually submitted. Clear the composer with
`herdr agent send-keys <name> ctrl+u` before prompting if it is in the way.

## Committing

```bash
git add <your paths>
git commit -m "<subject>" -- <your paths>
```

Never `-a`, never `add -A` or `add .`, never a pathspec-less commit. Agents
share a working tree and therefore a git index; a pathspec-less commit takes
whatever a sibling has staged.

**Every flag goes before the `--`.** Everything after `--` is a pathspec, so
`git commit -- <paths> -m "<msg>"` fails with
`error: pathspec '-m' did not match any file(s) known to git` — git looked
for a file named `-m` and another named after the whole message. Eight
sessions have each paid this once, this reference's own author included.

Anything tree-wide — `git stash`, `git reset --hard`, `git checkout .` —
reaches a sibling's uncommitted work the same way.

## Catching up on the base branch

```bash
wt step rebase                    # defaults to the default branch
wt step rebase <target>
```

Rebase rather than drifting. `wt merge` runs this anyway, so a branch that
rebases as it goes meets no surprises at merge time. A construction worktree
catches up on its bolt branch; a bolt branch catches up on main.

## Merging through the gate

```bash
wt merge --no-remove -C <worktree-path>              # to the default branch
wt merge <bolt-branch> --no-remove -C <worktree-path>  # merge-back to the bolt branch
```

The gate runs the repo's `.config/wt.toml` checks on the exact rebased tree
that lands, so the green is produced by the tool rather than claimed by the
agent that wrote the work. `--no-remove` keeps the worktree; teardown is a
separate step.

`wt merge` on this machine squashes by default and generates the message with
a headless `claude` that is not logged in. Pass `--no-squash` unless a
squash is what you want.

Hook approval is the operator's one-time `wt config approvals add`. **Never
bypass with `--yes`.** One writer to the base branch at a time — serialize
merges.

On gate failure the merge aborts with nothing landed and the worktree intact.
Send the failure output back to the worktree's agent, have it fix and re-run
`wt hook pre-merge`, then merge again.

## Tearing down

```bash
herdr worktree remove --workspace <workspace-id>
herdr agent list                  # confirm the agents are gone
```

A herdr-removed worktree skips `post-remove`, so whatever that hook would
have reclaimed is the teardown's own job. Kill processes **by PID or port,
never by pattern** — `pkill -f <name>` reaches into sibling worktrees' runs.
Record PIDs at spawn, or resolve them with `lsof -ti :<port>`, and kill
exactly those.

## Spawning a design session — the whole sequence

```bash
wt switch --create sess/<slug> --base main --no-cd   # only if the session edits files
herdr tab create --cwd <worktree-path> --label "<slug>" --no-focus
herdr agent start <slug>-session-<n> --kind claude --pane <pane-id> \
  -- --agent flywheel-design-session --model <model>
herdr agent prompt <slug>-session-<n> "/rename <slug>-session-<n>"
# confirm the title, then send the work order
```

An interactive-design session takes `--agent flywheel-interactive-session`
instead; the other five design types run under `flywheel-design-session`.
**A session that edits no files gets no worktree** — skip the `wt switch`,
start it in the launch directory, and skip the merge and teardown too.

The work order is four things: the change id, the session type, the item
numbers of its batch, and one or two plain sentences of goal. Worktree,
session directory and model are launch mechanics, not work order content.

## The tracker

Every machinery write to the tracker runs as the app. The plugin's
`bin/` is not on `PATH`: your loaded skill or profile carries the
plugin root — `${CLAUDE_PLUGIN_ROOT}`, substituted at load — and
`<plugin-root>` below means that absolute path. `flywheel-token`
caches for the hour, so calling it per command is free:

```bash
tok=$(<plugin-root>/bin/flywheel-token --org <org>)   # FLYWHEEL_GH_APP_ID / _KEY / _ORG configure it
GH_TOKEN=$tok gh issue list --repo <org>/<tracker> --milestone "intent/<slug>" \
  --label state:ready --state open --json number,title,labels
GH_TOKEN=$tok gh issue create --repo <org>/<tracker> --title "<the work, imperatively>" \
  --body "<goal + pointer to its record>" --label "type:research" --label "state:queued" \
  --milestone "intent/<slug>"
GH_TOKEN=$tok gh issue edit <n> --repo <org>/<tracker> \
  --remove-label state:ready --add-label state:in-progress
GH_TOKEN=$tok gh issue comment <n> --repo <org>/<tracker> --body "<what happened>"
GH_TOKEN=$tok gh issue edit <n> --repo <org>/<tracker> --add-label closed:done
GH_TOKEN=$tok gh issue close <n> --repo <org>/<tracker> --comment "<landing SHA / outcome>"
```

Blocked on the operator's word — comment the one-line question, label it,
keep working what it does not gate (dispatch DMs the assignee; whoever
applies the answer removes the label):

```bash
GH_TOKEN=$tok gh issue comment <n> --repo <org>/<tracker> \
  --body "<question — options if any — evidence pointer>"
GH_TOKEN=$tok gh issue edit <n> --repo <org>/<tracker> --add-label needs-operator
```

A handoff session's custody move — the assertion item leaves the intent's
milestone for the bolt's, and that move IS the bolting:

```bash
GH_TOKEN=$tok gh issue edit <n> --repo <org>/<tracker> \
  --milestone "bolt/<slug>" --remove-label state:queued --add-label state:ready
```

Composing a proposed release batch is one call — parent issue, sub-issues,
project, Status **Backlog** (moving it to **Ready** on the board is
the operator's approval, and nothing else moves it):

```bash
<plugin-root>/bin/flywheel-epic --org <org> --repo <tracker> --milestone "bolt/<slug>" \
  --title "<the batch, imperatively>" <item> <item> ...
```

Finding the epics the operator has released:

```bash
GH_TOKEN=$tok gh api graphql -f query='
{ organization(login: "<org>") { projectsV2(first: 5, query: "Flywheel") { nodes {
    items(first: 100) { nodes {
      fieldValueByName(name: "Status") { ... on ProjectV2ItemFieldSingleSelectValue { name } }
      content { ... on Issue { number title state } } } } } } } }' \
  --jq '.data.organization.projectsV2.nodes[0].items.nodes[]
        | select(.fieldValueByName.name == "Ready" and .content.state == "OPEN")
        | "#\(.content.number) \(.content.title)"'
```

**Sub-issues and dependencies take the database id, not the number.**
`gh api /repos/<o>/<r>/issues/<n> --jq .id` fetches it; passing the issue
number fails opaquely. An item joins exactly one epic — attaching a
sub-issue that already has a parent is a 422:

```bash
GH_TOKEN=$tok gh api /repos/<org>/<tracker>/issues/<blocked>/dependencies/blocked_by \
  --input - <<< '{"issue_id": <database id of the blocker>}'
```

`<plugin-root>/bin/flywheel-setup --org <org> --repo <tracker>` converges labels, the
project and its fields, idempotently — run it once per org, or any time
the shape is in doubt.

## The bolt's own topology

One bolt branch and worktree per involved built repo, alive for the bolt's
lifetime:

```bash
herdr worktree create --cwd <built-repo-root> --base main \
  --branch bolt/<slug> --label "bolt <slug>" --no-focus --json
wt -C <worktree-path> hook post-start
```

Construction runs on nested worktrees cut off the bolt branch, one per
proposal being built:

```bash
wt switch --create build/<proposal-slug> --base bolt/<slug> --no-cd
```

Spec, apply and testing agents start in those worktrees under their own
names, by the sequence above. A spec agent's artifacts are landed by the
conductor, by pathspec, and only once that agent is idle — "finished" is a
property of the agent, not of the spec.
