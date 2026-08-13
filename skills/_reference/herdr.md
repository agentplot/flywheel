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

No `--no-hooks`. On this command the flag skips the `[post-start]` warm-up
and leaves the worktree cold — that is the whole reason here. `[pre-merge]`
is not among the hooks `wt switch --create` runs, so the merge gate is not
what is at stake at this step; the flag's effect on `wt merge` is under
"Merging through the gate" below.

A herdr-created worktree fires no `wt` lifecycle hooks. Run the repo's hook
yourself right after creating one:

```bash
wt -C <worktree-path> hook post-start
```

`-C` precedes the subcommand. A trailing `-C` reads the wrong directory and
reports no hooks.

## Starting an agent, and naming it before you send its work order

**The name IS the classification.** The roster must read at a glance:
dispatch is `dispatch`, and every session starts with its session type
— the FULL type name, exactly as the `type:*` label spells it: `research-<topic>`,
`planning-<topic>`, `interactive-<topic>`, `prototype-<topic>`,
`writeback-<topic>`, `handoff-<topic>`, `proposal-writing-<topic>`,
`proposal-review-<topic>`, `spec-writing-<topic>`, `build-<topic>`,
`test-<topic>`, `code-review-<topic>`, `human-code-review-<topic>`.
Never a shorthand: `review-<topic>` cannot say which review type it is,
and one bolt runs several. A loop's own mechanical sessions are named
for the stage that launched them — `scaffold-`, `route-`, `plan-`,
`verify-`, `merge-`, `land-` — and no type name collides with those or
with `dispatch`, so the prefix alone says what a row is.
herdr caps names at 32 characters — the long type prefixes leave the
topic little room, so keep topics to a word or two. **The tab label is the agent name,
the same string** — a tab labeled one thing holding an agent named
another is how a session becomes unfindable.

```bash
herdr tab create --cwd <worktree-path> --label "<the agent name>" --no-focus
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
Dispatch, the one standing agent, runs `opus[1m]`, set on its fleet
row; a loop's sessions take the model its stage names.

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

**A work order is one prompt, invocation first.** When the type has a
canonical invocation — `/opsx:ff <slug>` for spec-writing,
`/opsx:apply <change>` for a build session applying a specced change —
it is the work order's FIRST line, and the brief rides below it in the
same prompt. A slash command buried mid-body never loads the skill (this
is how a spec agent came to run without `/opsx:apply` loaded), and a
command sent bare with the brief chasing it as a second prompt is the
same defect mirrored: the invocation fires without its work order, and
the session improvises from the command alone.

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

**The message follows the repo's stated convention** (its CLAUDE.md);
where the repo states none, default to Conventional Commits —
`type(scope): subject`, imperative. **Footer-reference every tracker
item the commit serves** — `Refs: #34` — and NEVER a closing keyword
(`Closes`/`Fixes`): a push must not close an item as a side effect;
items close through the loop, with evidence and a `closed:*` reason.

**Push what you commit, immediately.** Records are shared state:
dispatch, other hosts, and the operator reading GitHub all resolve
record pointers against origin, so an unpushed record is a dead link
on its own tracker item. `git pull --rebase` first when origin moved,
then push. (Worktree branches merge through the gate instead — this
rule is for commits made directly on a shared branch.)

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

The gate is the repo's `[pre-merge]` hooks. `wt merge` runs them after the
rebase and before the merge to the target, with `HEAD` equal to the sha that
lands, on every shape of merge **that does not suppress them** — the clean
fast-forward included; a failure aborts with exit 1 and nothing landed. That
is measured across ten merge shapes against worktrunk 0.57.0 —
`openspec/changes/gated-merge-guarantee/sessions/2026-08-12-ff-gate-facts/finding.md`
— and it is what makes the green produced by the tool rather than claimed by
the agent that wrote the work. `--no-remove` keeps the worktree; teardown is
a separate step.

**No `--no-hooks` here either, and here it is the gate at stake.** On
`wt merge` the flag runs **zero** hooks and exits 0 — measured, that lab's
`nohooks` row — so it skips this repo's merge gate outright. `verify = false`
does the same. The qualifier above is those two shapes and nothing else: a
bare "every shape" would be refuted by the very finding cited for it.

Which worktree's *configuration* supplies those hooks, when the source and
the target carry different `.config/wt.toml` files, has **not** been
measured: that lab measured cwd — the source worktree — and ran symmetric
configuration throughout, so no row of it distinguishes the two. Assume
neither side. A merge that ran zero hooks does not settle it either — the
two suppressing flags above and a misplaced trailing `-C` produce that same
result, so zero hooks is evidence of nothing until those are excluded. Where
a bolt's own merge-back turns on the answer, how to read that one merge
belongs to its `bolt.md` and is cited from there rather than reproduced
here; that reasoning has already moved once.

`wt merge` on this machine squashes by default and generates the message with
a headless `claude` that is not logged in. Pass `--no-squash` unless a
squash is what you want.

Hook approval is the operator's one-time `wt config approvals add`, keyed on
the verbatim template text. **Never bypass with `--yes`.** Two different
commands, two different facts, and they are not interchangeable: `--yes` on
`wt merge` **runs** the hooks without persisting the approval — a trust
bypass rather than a gate bypass, which is exactly what makes it tempting —
while `--yes` on `wt config approvals add` **fails** non-interactively and
persists nothing, so it is not a route to the grant either.

An agent that hits `Cannot prompt for approval in non-interactive
environment` **stops, says so on its item, and settles**, and the merge waits
on the operator's grant. Running the repo's check scripts by hand on the
landing tree and reporting them green is not a substitute gate: that is
verification by assertion, precisely the asserted-green `wt merge` exists to
eliminate, however honest the hands. Treat the stoppage as a work stoppage
and not a hazard — unapproved hooks abort with exit 1 and nothing landed, so
a missing grant never produces an ungated green.

One writer to the base branch at a time — serialize merges.

On gate failure the merge aborts with nothing landed and the worktree intact.
Send the failure output back to the worktree's agent, have it fix and re-run
`wt hook pre-merge`, then merge again.

## Tearing down

```bash
herdr worktree remove --workspace <workspace-id>
herdr agent list                  # confirm the agents are gone
```

**Delivery is settling, never waiting.** A charged session delivers by
commenting its items, printing its report as its final message, and
settling — the loop that launched it is parked on exactly that settle
and reads the pane. There is nobody to prompt: no session, loop or
server ever messages another, so a session that parks a background wait
to hand its report upward later delivers nothing and holds its stage
open. The comment and the settle are the whole delivery.

**A settled session's pane closes at the merge step.** When a session's outcome
is returned and its items are commented, close its tab
(`herdr tab close <tab-id>`): the pane's job ended with the report, and
a settled pane left open makes the roster lie about what is running.
The pane is not the worktree — the worktree and branch live until the
merge step lands them, and their removal is the separate teardown
below. A session the loop will re-prompt — a plan-mode build awaiting
approval, a review awaiting a bounce — keeps its pane; close means
finished.

A herdr-removed worktree skips `post-remove`, so whatever that hook would
have reclaimed is the teardown's own job. Kill processes **by PID or port,
never by pattern** — `pkill -f <name>` reaches into sibling worktrees' runs.
Record PIDs at spawn, or resolve them with `lsof -ti :<port>`, and kill
exactly those.

## Spawning a design session — the whole sequence

```bash
wt switch --create sess/<slug> --base main --no-cd   # only if the session edits files
herdr tab create --cwd <worktree-path> --label "<type>-<topic>" --no-focus
herdr agent start <type>-<topic> --kind claude --pane <pane-id> \
  -- --agent flywheel-design-session --model <model>
herdr agent prompt <type>-<topic> "/rename <type>-<topic>"
# confirm the title, then send the work order
```

An interactive-design session takes `--agent flywheel-interactive-session`
instead; the other five design types run under `flywheel-design-session`.
**A session that edits no files gets no worktree** — skip the `wt switch`,
start it in the launch directory, and skip the merge and teardown too.

**The permission mode is the launcher's to set** — append it after the
`--`. Fleet agents run unattended: `--dangerously-skip-permissions` for
every ordinary session (the fleet layer passes it for the actors it
starts). The one exception is a plan-mode build session, started with
`--permission-mode plan` instead: plan mode blocks every edit until
the plan is approved. Approval is a judgment, so it is asked of a
session and never taken by the launcher itself: an approver session gets
the pane as the session produced it plus the items' claims, and answers
one parsed line — `APPROVED: …` or `RETURNED: …`. The launcher drives the
plan dialog on that verdict with `herdr agent send-keys <name> <key>`
(enter on approval; the mismatch prompted back on a return), and two
returns on one batch pause it with `needs-operator` rather than bouncing
again. Parked on `herdr agent wait` afterwards, a `blocked` settle is a
real permission ask, not a plan.

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

A construction assertion closes twice over, and the bolt loop does both —
never a session. At the merge-back it closes `closed:merged` with the merge
SHA, which is what advances the unit parent's native bar; at the landing the
reason is **upgraded** on the already-closed item, so it never carries both
reasons or neither:

```bash
GH_TOKEN=$tok gh issue edit <n> --repo <org>/<tracker> \
  --add-label closed:done --remove-label closed:merged
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

Composing a proposed batch is one call — parent issue, sub-issues,
project, Status **Backlog** (moving it to **Ready** on the board is
the operator's approval, and nothing else moves it). `--kind unit`
releases construction work; `--kind elaboration` authorizes design
sessions:

```bash
<plugin-root>/bin/flywheel-batch --kind unit --org <org> --repo <tracker> \
  --milestone "bolt/<slug>" --title "<the batch, imperatively>" <item> <item> ...
```

Every release creates one unit parent, the born-ready one included. On a
born-ready release the operator's word at triage IS the approval, so the
parent goes to Ready from birth — `flywheel-batch` puts it at Backlog and
never writes Ready, so the Ready move belongs here, in the release path:

```bash
<plugin-root>/bin/flywheel-batch --kind unit --org <org> --repo <tracker> \
  --milestone "bolt/<slug>" --title "<the batch, imperatively>" <item> <item> ...
<plugin-root>/bin/flywheel-board --org <org> --repo <tracker> \
  --status Ready <the unit parent's number>
```

The parent is the board row. The released items are NOT added to the
board beside it — one row per bolt is what the parent buys, and it is
lost if the sub-issues appear too.

Finding the batches the operator has released:

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
number fails opaquely. An item joins exactly one batch — attaching a
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
names, by the sequence above. Each commits its own artifacts by pathspec
and neither merges nor pushes; the loop merges the branch back through
the gate only once that agent has settled — "finished" is a property of
the agent, not of the spec.
