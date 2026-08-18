# The two compiled loops — review round 2

Both compiled from their schema's apply.instruction alone (bolt `72349a167518c7d1`, intent `691d1430fe04c9fe`), all prior rulings folded: explicit MODELS and LIMITS in both instructions, landing as a driven session with the mode from bolt.md's `Landing:` line, no cycle bound, reference-loop.js deleted. (`node --check` complains about top-level `return` — Workflow scripts run in an async body where that's legal.)

## Open questions

**Q1 — Landing finds merge criteria unmet.** Today: the landing session refuses, reports the failing criterion, run ends. What next? (a) the fix is born `state:ready` on the bolt — your original flip covers making the batch meet its stated criteria; new scope still queues (my recommendation); (b) current rules: queued item → unit → your flip — a failing bolt strands silently at rest; (c) needs-operator ask on the bolt so you rule per instance.

**Q2 — Intent sessions and panes.** The instruction allows "pure read-and-report may run in-process," but the compile gives every design session a pane and a `sess/*` worktree, because every type writes its session directory. Keep it that way, or let research queries that produce no files run as in-process subagents?

**Q3 — The intent merge/close stage** is compiled as a driven session (same as landing, which you ruled you liked). Confirm, or should merging session branches stay a conductor-side act outside the script?

## bolt-default.compiled.js

```js
/*
COMPILED FROM: schemas/bolt-default/schema.yaml apply.instruction
INSTRUCTION SHA256: 72349a167518c7d1
COMPILED BY: static compile pass, second round - operator rulings of
2026-08-12 folded. No INVENTED marks remain: models, limits, landing
mode, and the landing actor are now the instruction's own words.
Mechanics marked "HERDR.MD:" are delegated to
skills/_reference/herdr.md, the maintained mechanics source.

args = {
  slug:        "sandbox-loop",              // the bolt's change slug
  boltBranch:  "bolt/sandbox-loop",
  repoDir:     "/abs/path/of/built/repo",
  boltWorktree:"/abs/path/of/bolt/worktree",
  org:         "agentplot",
  pluginRoot:  "/abs/path/of/plugin",
  fixture:     null,                        // path to a bolt-tracker.json -> isolated run: read it instead of gh, write nothing, never land
}
*/
export const meta = {
  name: 'bolt-default-sandbox-loop',
  description: 'Compiled bolt-default loop: guards then spec/build pipelined and merge serialized, repeating until no ready work and quiet guards; landing per bolt.md',
  phases: [
    { title: 'Cycle', detail: 'query -> guards -> work -> merge, repeated' },
    { title: 'Land', detail: 'per bolt.md: Landing merge (default) or pr; never in fixture mode' },
  ],
}

const A = args
const T = A.fixture
  ? `FIXTURE MODE: read the tracker snapshot from ${A.fixture}; make NO tracker writes; report what you would have written.`
  : `Tracker writes run as the app: GH_TOKEN=$("${A.pluginRoot}/bin/flywheel-token" --org ${A.org}); if the token cannot mint, stop and return status failed - never ambient credentials.`

/* MODELS - the instruction's tiers, explicit in every call. */
const DRIVER_OPTS = { model: 'sonnet', effort: 'low' }
const SESSION_MODEL = 'sonnet' // construction sessions while mechanics are pinned; reviews will re-raise

/* LIMITS - construction: 90 min -> comment + needs-operator, keep
   waiting; 4 h -> stalled, pane open. In 10-minute wait chunks. */
const NOTIFY_CHUNKS = 9
const STALL_CHUNKS = 24

const SNAPSHOT = {
  type: 'object',
  properties: {
    items: { type: 'array', items: { type: 'object', properties: {
      number: { type: 'number' }, title: { type: 'string' },
      labels: { type: 'array', items: { type: 'string' } },
      blocked_by: { type: 'array', items: { type: 'number' } },
      parent_batch: { type: ['number', 'null'] },
      record: { type: ['string', 'null'] }, change: { type: ['string', 'null'] },
    }, required: ['number', 'title', 'labels', 'blocked_by', 'parent_batch'] } },
    batches: { type: 'array', items: { type: 'object', properties: {
      number: { type: 'number' }, status: { type: 'string' },
      sub_issues: { type: 'array', items: { type: 'number' } },
    }, required: ['number', 'status', 'sub_issues'] } },
    guard_actions: { type: 'array', items: { type: 'string' } },
  },
  required: ['items', 'batches', 'guard_actions'],
}
const OUTCOME = {
  type: 'object',
  properties: {
    status: { type: 'string', enum: ['done', 'blocked', 'stalled', 'failed'] },
    detail: { type: 'string' },
  },
  required: ['status', 'detail'],
}

const queryAndGuards = (cycle) => agent(`Read the bolt tracker state and apply the guards, then return the post-guard snapshot as your structured output. ${T}

Milestone: bolt/${A.slug}. Fields per item: number, title, labels, blocked_by (GitHub's dependency edges, read from the API, never inferred), parent_batch, record path, change name.

GUARDS, in order, each idempotent - record every action you take in guard_actions (empty array if none):
0. If openspec/changes/${A.slug} does not exist in ${A.boltWorktree}: scaffold it (/opsx:new ${A.slug}, bind bolt-default), commit, continue.
1. Any unit at board Status Ready with state:queued sub-issues: relabel those sub-issues state:ready.
2. Any state:queued item with no parent_batch: keep it on this bolt ONLY if the bolt cannot land without it; otherwise move it to the intent that owns its subject, or leave it unmilestoned for dispatch. Compose what remains into a unit at Backlog.

Return the snapshot AFTER your guard actions.`,
  { label: `cycle${cycle}:query+guards`, phase: 'Cycle', schema: SNAPSHOT, ...DRIVER_OPTS })

/* HERDR.MD: the driver recipe - one-prompt order, invocation first
   line, rename-then-confirm, wait semantics, ghost text is not
   input, close the pane when the outcome is read. */
const drive = (name, cwd, order, label, itemNumber) => agent(`Drive one herdr session; never do its work yourself.
1. herdr tab create --cwd "${cwd}" --label "${name}" --no-focus  (tab label IS the agent name)
2. herdr agent start "${name}" --kind claude --pane <pane-id> -- --agent flywheel-construction-session --model ${SESSION_MODEL} --dangerously-skip-permissions
3. Prompt "/rename ${name}" alone; poll the title until it converges.
4. Deliver the work order between the markers as ONE prompt; verify the session goes working (one enter if a pasted block sits at the composer).
5. herdr agent wait "${name}" - re-invoke on the 10-minute command cap, counting chunks. At ${NOTIFY_CHUNKS} chunks (~90 min): ${A.fixture ? 'note the long wait in your outcome detail' : `comment the wait on issue #${itemNumber} and add the needs-operator label - a live wait; dispatch relays`} - then KEEP waiting. At ${STALL_CHUNKS} chunks (~4 h): return status stalled with the pane tail; leave the pane open.
6. On settle done/idle: read the pane; composer ghost text is not input. On settle blocked: return status blocked with what the pane asks; leave the pane open.
7. herdr tab close <tab-id>; return the outcome.
WORK_ORDER>>>
${order}
<<<WORK_ORDER`,
  { label, phase: 'Cycle', schema: OUTCOME, ...DRIVER_OPTS })

const ready = (s) => s.items.filter((i) => i.labels.includes('state:ready'))
const unblocked = (s, i) => i.blocked_by.every((b) => !s.items.some((x) => x.number === b))

/* No cycle bound: the ready set cannot refill itself (new items are
   queued, never ready, without an operator flip) and the guards are
   idempotent, so guard_actions drains and STOP fires. Revisit when
   review stages return. */
let lastSnapshot = null
let cycle = 0
while (true) {
  cycle++
  const s = await queryAndGuards(cycle)
  lastSnapshot = s
  const work = ready(s).filter((i) => unblocked(s, i))
  if (work.length === 0 && s.guard_actions.length === 0) break // STOP: no ready work and the guards changed nothing

  const builtItems = await pipeline(
    work,
    (it) => drive(
      `spec-writing-${it.change}`.slice(0, 32), A.repoDir,
      `/opsx:ff ${it.change}\n\nSpec for item #${it.number} - ${it.title}\nOne spec-driven change for this one item, derived from ${it.record} and the decisions it cites. Worktree: wt switch --create build/${it.change} --base ${A.boltBranch} --no-cd in ${A.repoDir}. openspec validate --strict green before it counts. ${T} Flip #${it.number} to state:in-progress. Commit; do not merge or push. Deliver by settling.`,
      `spec:${it.change}`, it.number),
    (spec, it) => (spec && spec.status === 'done')
      ? drive(
          `build-${it.change}`.slice(0, 32), A.repoDir,
          `/opsx:apply ${it.change}\n\nBuild for item #${it.number} - ${it.title}\nApply the change on the build/${it.change} worktree. Re-read every neighbour the spec claims something about from disk. ${T} Commit; do not merge or push. Deliver by settling.`,
          `build:${it.change}`, it.number).then((build) => ({ it, spec, build }))
      : { it, spec, build: null },
  )

  for (const r of builtItems.filter(Boolean)) {
    if (!r.build || r.build.status !== 'done') continue // blocked/stalled surfaces in the report; answer the pane and RESUME this run
    await drive(
      `merge-${r.it.change}`.slice(0, 32), A.boltWorktree,
      `Merge-back for item #${r.it.number}. In ${A.boltWorktree}: wt merge build/${r.it.change} - never --yes. On green: openspec archive ${r.it.change}, commit. ${T} On red: fix nothing; report the gate output verbatim. Deliver by settling.`,
      `merge:${r.it.change}`, r.it.number)
  }
}

/* LAND - a driven session like every stage. Mode from bolt.md:
   "Landing: merge" (default) or "Landing: pr". */
let landing = 'not attempted'
if (A.fixture) {
  landing = 'fixture mode - landing never runs'
} else if (lastSnapshot && ready(lastSnapshot).length === 0) {
  const land = await drive(
    'land', A.repoDir,
    `Landing session. Read openspec/changes/${A.slug}/bolt.md on ${A.boltBranch}: verify every Merge criterion on that branch - if any fails, land NOTHING and report the failing criterion as status failed. Read its "Landing:" line (absent = merge).\n- Landing: merge -> land ${A.boltBranch} on main through the gate (wt merge, never --yes), one writer to main; comment the landing SHA on each item and close it closed:done.\n- Landing: pr -> push ${A.boltBranch} and open a pull request to main (gh pr create), report its URL; close nothing - items close when the PR merges.\n${T} Deliver by settling.`,
    'land', 0)
  landing = `${land ? land.status + ': ' + land.detail : 'land agent lost'}`
}

return {
  slug: A.slug,
  cycles: cycle,
  landing,
  queue: lastSnapshot ? lastSnapshot.items.filter((i) => i.labels.includes('state:queued')).map((i) => `#${i.number} ${i.title}`) : [],
  next: 'blocked or stalled stages: answer the pane, then resume this run (scriptPath + resumeFromRunId)',
}

```

## flywheel-intent.compiled.js

```js
/*
COMPILED FROM: schemas/flywheel-intent/schema.yaml apply.instruction
INSTRUCTION SHA256: 691d1430fe04c9fe
COMPILED BY: static compile pass for review - not yet run. Mechanics
marked "HERDR.MD:" delegated to skills/_reference/herdr.md.

args = {
  slug:       "sandbox-design",             // the intent's change slug
  repoDir:    "/abs/path/of/blueprints/main", // where the change and sess/* worktrees live
  org:        "agentplot",
  pluginRoot: "/abs/path/of/plugin",
  fixture:    null,                         // path to an intent-tracker.json -> isolated run, no tracker writes
}
*/
export const meta = {
  name: 'flywheel-intent-sandbox-design',
  description: 'Compiled intent loop: guards (flip-consume, handoff birth, compose) then typed session batches, merged as they finish, until no ready work and quiet guards',
  phases: [
    { title: 'Cycle', detail: 'query -> guards -> typed session batches -> merge, repeated' },
  ],
}

const A = args
const T = A.fixture
  ? `FIXTURE MODE: read the tracker snapshot from ${A.fixture}; make NO tracker writes; report what you would have written.`
  : `Tracker writes run as the app: GH_TOKEN=$("${A.pluginRoot}/bin/flywheel-token" --org ${A.org}); if the token cannot mint, stop and return status failed - never ambient credentials.`

/* MODELS - the instruction's tiers. */
const DRIVER_OPTS = { model: 'sonnet', effort: 'low' }
const SESSION_MODEL = {
  planning: 'fable', interactive: 'fable',
  research: 'opus[1m]',
  prototype: 'opus', writeback: 'opus', handoff: 'opus',
}
const SESSION_PROFILE = (type) =>
  type === 'interactive' ? 'flywheel-interactive-session' : 'flywheel-design-session'

/* LIMITS - operator-round types notify at 90 min and never stall;
   the others notify at 90 min and stall at 4 h. */
const OPERATOR_ROUND_TYPES = ['planning', 'interactive', 'handoff']
const NOTIFY_CHUNKS = 9
const STALL_CHUNKS = 24

const SNAPSHOT = {
  type: 'object',
  properties: {
    items: { type: 'array', items: { type: 'object', properties: {
      number: { type: 'number' }, title: { type: 'string' },
      labels: { type: 'array', items: { type: 'string' } },
      blocked_by: { type: 'array', items: { type: 'number' } },
      parent_batch: { type: ['number', 'null'] },
      record: { type: ['string', 'null'] },
    }, required: ['number', 'title', 'labels', 'blocked_by', 'parent_batch'] } },
    batches: { type: 'array', items: { type: 'object', properties: {
      number: { type: 'number' }, kind: { type: 'string' },
      status: { type: 'string' },
      sub_issues: { type: 'array', items: { type: 'number' } },
    }, required: ['number', 'status', 'sub_issues'] } },
    guard_actions: { type: 'array', items: { type: 'string' } },
  },
  required: ['items', 'batches', 'guard_actions'],
}
const OUTCOME = {
  type: 'object',
  properties: {
    status: { type: 'string', enum: ['done', 'blocked', 'stalled', 'failed'] },
    detail: { type: 'string' },
  },
  required: ['status', 'detail'],
}

const queryAndGuards = (cycle) => agent(`Read the intent tracker state and apply the guards, then return the post-guard snapshot as your structured output. ${T}

Milestone: intent/${A.slug}. Fields per item: number, title, labels (type:* and state:*), blocked_by (GitHub's dependency edges, read from the API, never inferred), parent_batch, record path. Batches carry kind (unit | elaboration), board Status, sub_issues.

GUARDS, in order, each idempotent - record every action in guard_actions (empty if none):
0. If openspec/changes/${A.slug} does not exist in ${A.repoDir}: scaffold it (/opsx:new ${A.slug}, bind flywheel-intent), commit, continue.
1. Any batch at board Status Ready with state:queued sub-issues: relabel those sub-issues state:ready. The flip is spent; the labels carry the release.
2. COMPOSE: any state:queued item with no parent_batch -> group the orphans into proposed batches (${A.pluginRoot}/bin/flywheel-batch) at Backlog, by thread. Composing is not releasing.

Return the snapshot AFTER your guard actions.`,
  { label: `cycle${cycle}:query+guards`, phase: 'Cycle', schema: SNAPSHOT, ...DRIVER_OPTS })

/* HERDR.MD: the driver recipe. Design sessions have no slash
   invocation; the work order's first line names the type and the
   session's skill loads from it. */
const drive = (type, name, order, label, itemNumber) => {
  const notify = A.fixture
    ? 'note the long wait in your outcome detail'
    : `comment the wait on issue #${itemNumber} and add needs-operator (a live wait; dispatch relays)`
  const stall = OPERATOR_ROUND_TYPES.includes(type)
    ? 'This type holds operator rounds: never return it stalled; keep waiting.'
    : `At ${STALL_CHUNKS} chunks (~4 h): return status stalled with the pane tail; pane stays open.`
  return agent(`Drive one herdr session; never do its work yourself.
1. In ${A.repoDir}: wt switch --create sess/${name} --base main --no-cd; resolve the worktree path (wt list).
2. herdr tab create --cwd "<worktree>" --label "${name}" --no-focus  (tab label IS the agent name)
3. herdr agent start "${name}" --kind claude --pane <pane-id> -- --agent ${SESSION_PROFILE(type)} --model ${SESSION_MODEL[type]} --dangerously-skip-permissions
4. Prompt "/rename ${name}" alone; poll the title until it converges.
5. Deliver the work order between the markers as ONE prompt; verify the session goes working.
6. herdr agent wait "${name}" - re-invoke on the 10-minute cap, counting chunks. At ${NOTIFY_CHUNKS} chunks (~90 min): ${notify} - then KEEP waiting. ${stall}
7. On settle done/idle: read the pane; ghost text is not input. On blocked: return status blocked with what the pane asks; pane stays open.
8. herdr tab close <tab-id>; return the outcome.
WORK_ORDER>>>
${order}
<<<WORK_ORDER`,
  { label, phase: 'Cycle', schema: OUTCOME, ...DRIVER_OPTS })
}

const typeOf = (i) => (i.labels.find((l) => l.startsWith('type:')) || 'type:research').slice(5)
const ready = (s) => s.items.filter((i) => i.labels.includes('state:ready'))
const unblocked = (s, i) => i.blocked_by.every((b) => !s.items.some((x) => x.number === b))

let lastSnapshot = null
let cycle = 0
while (true) {
  cycle++
  const s = await queryAndGuards(cycle)
  lastSnapshot = s
  const work = ready(s).filter((i) => unblocked(s, i))
  if (work.length === 0 && s.guard_actions.length === 0) break // STOP

  /* Batch by type label - one session type per batch; prototypes
     always alone. Computed from the fields, not reasoned. */
  const byType = {}
  for (const it of work) {
    const ty = typeOf(it)
    if (ty === 'prototype') { (byType[`prototype:${it.number}`] = []).push(it) }
    else { (byType[ty] = byType[ty] || []).push(it) }
  }

  const sessions = Object.entries(byType).map(([key, items]) => {
    const ty = key.startsWith('prototype') ? 'prototype' : key
    const topic = `${ty}-${A.slug}`.slice(0, 32)
    const nums = items.map((i) => `#${i.number}`).join(', ')
    const order = `${ty} session for intent ${A.slug} - items ${nums}
Change: ${A.slug}. Your session directory: openspec/changes/${A.slug}/sessions/<date>-<topic>/ - you are its sole writer. Work the items; write your records (decisions, questions, the session README) in your worktree; queue your own discoveries as items (${T.startsWith('FIXTURE') ? 'report them instead' : 'whoever finds queues'}); comment each item you worked. ${T}
Deliver by settling: print your report as your final message and stop. Never wait on your conductor.`
    return () => drive(ty, topic, order, `${ty}:${nums}`, items[0].number)
      .then((outcome) => ({ items, ty, outcome }))
  })
  const finished = await parallel(sessions)

  /* Merge each finished session branch through the gate; close
     finished items on the evidence. The session created its records
     and discoveries; this stage creates nothing. */
  for (const r of (finished || []).filter(Boolean)) {
    if (!r.outcome || r.outcome.status !== 'done') continue // blocked/stalled surface in the report; answer and RESUME
    await drive('research', `merge-${r.ty}`.slice(0, 32),
      `Merge the session branch for the ${r.ty} batch. In ${A.repoDir}: wt merge sess/<its branch> - never --yes. On green: ${A.fixture ? 'report what you would close' : `close the finished items (${r.items.map((i) => '#' + i.number).join(', ')}) closed:done with the evidence in a comment`}. On red: fix nothing; report the gate output verbatim. ${T} Deliver by settling.`,
      `merge:${r.ty}`, r.items[0].number)
  }
}

return {
  slug: A.slug,
  cycles: cycle,
  queue: lastSnapshot ? lastSnapshot.items.filter((i) => i.labels.includes('state:queued')).map((i) => `#${i.number} ${i.title}`) : [],
  next: 'blocked or stalled stages: answer the pane, then resume this run (scriptPath + resumeFromRunId)',
}

```
