/*
COMPILED FROM: schemas/flywheel-intent/schema.yaml apply.instruction
INSTRUCTION SHA256: 59f69e09c1bc96f4
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

/* Defensive args (#29): a JSON string arriving as args is parsed. */
const A = typeof args === 'string' ? JSON.parse(args) : args
const trace = [] // every stage outcome; in fixture mode this is the verification artifact
const T = A.fixture
  ? `FIXTURE MODE: the file at ${A.fixture} IS the tracker - read state from it and write every tracker update (labels, moves, closes, comments as a comments array) back to that file instead of GitHub; never touch the real tracker; record each write in your outcome detail.`
  : `Tracker writes run as the app: GH_TOKEN=$("${A.pluginRoot}/bin/flywheel-token" --org ${A.org}); if the token cannot mint, stop and return status failed - never ambient credentials.`

/* MODELS - the instruction's tiers. */
const DRIVER_OPTS = { model: 'sonnet', effort: 'low' }
const SESSION_MODEL = {
  planning: 'fable', interactive: 'fable',
  research: 'opus[1m]',
  prototype: 'opus', writeback: 'opus', handoff: 'opus',
  merge: 'sonnet',
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
    status: { type: 'string', enum: ['ok', 'failed'] },
    failure: { type: ['string', 'null'] },
  },
  required: ['items', 'batches', 'guard_actions', 'status'],
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

GUARDS, in order, each idempotent - guard_actions records ONLY the writes you make; a check that changed nothing records NOTHING (an empty array is the normal, correct result):
0. If openspec/changes/${A.slug} does not exist in ${A.repoDir}: scaffold it (/opsx:new ${A.slug}, bind flywheel-intent), commit, continue.
1. Any batch at board Status Ready with state:queued sub-issues: relabel those sub-issues state:ready. The flip is spent; the labels carry the release.
2. COMPOSE: any state:queued item with no parent_batch -> group the orphans into proposed batches (${A.pluginRoot}/bin/flywheel-batch) at Backlog, by thread. Composing is not releasing.

Return the snapshot AFTER your guard actions, with status ok. If you cannot read the tracker, mint the token, or resolve these parameters: status failed with the reason in failure, guard_actions empty - the run stops on your word.`,
  { label: `cycle${cycle}:query+guards`, phase: 'Cycle', schema: SNAPSHOT, ...DRIVER_OPTS })

/* HERDR.MD mechanics; the SCRIPT owns all waiting - the loop's
   arithmetic is the clock. Each helper agent returns exactly once.
   checkout: a work session gets a fresh sess/* worktree; a merge
   stage runs in the existing checkout and never cuts one. */
const WAITR = {
  type: 'object',
  properties: {
    state: { type: 'string', enum: ['settled_done', 'settled_blocked', 'still_working', 'gone'] },
    detail: { type: 'string' },
  },
  required: ['state', 'detail'],
}

const launch = (type, name, order, label, checkout) => {
  const cwdStep = checkout
    ? `1. Your session cwd is ${checkout} - the existing checkout; cut NO worktree.\n2. herdr tab create --cwd "${checkout}" --label "${name}" --no-focus  (tab label IS the agent name)`
    : `1. In ${A.repoDir}: wt switch --create sess/${name} --base main --no-cd; resolve the worktree path (wt list).\n2. herdr tab create --cwd "<worktree>" --label "${name}" --no-focus  (tab label IS the agent name)`
  return agent(`Launch one herdr session; deliver its order; return WITHOUT waiting. Idempotent: if an agent named "${name}" already exists (herdr agent list), reuse it - never create a duplicate; if the pane shows this order already delivered or worked, return done.
${cwdStep}
3. herdr agent start "${name}" --kind claude --pane <pane-id> -- --agent ${SESSION_PROFILE(type)} --model ${SESSION_MODEL[type]} --dangerously-skip-permissions
4. Prompt "/rename ${name}" alone; poll the title until it converges.
5. Deliver the work order between the markers as ONE prompt; verify the session goes working. Then return {status:'done', detail:'delivered'}.
WORK_ORDER>>>
${order}
<<<WORK_ORDER`,
    { label: `launch:${label}`, phase: 'Cycle', schema: OUTCOME, ...DRIVER_OPTS })
}

const waitOnce = (name, label, n) => agent(`Run exactly one bounded wait on the herdr session "${name}": herdr agent wait "${name}" (single invocation - it returns when the session settles or the command cap ends). Then herdr agent get "${name}" and report: settled_done for idle/done, settled_blocked for blocked, still_working otherwise, gone if the agent no longer exists.`,
  { label: `wait${n}:${label}`, phase: 'Cycle', schema: WAITR, model: 'haiku', effort: 'low' })

const readClose = (name, label) => agent(`The herdr session "${name}" has settled. Read its pane (herdr agent read "${name}" --source recent-unwrapped --lines 120) and extract its report - composer ghost text is not input. Then herdr tab close its tab. Return the outcome with the report condensed to its facts.`,
  { label: `read:${label}`, phase: 'Cycle', schema: OUTCOME, ...DRIVER_OPTS })

async function drive(type, name, order, label, itemNumber, checkout) {
  const l = await launch(type, name, order, label, checkout)
  if (!l || l.status !== 'done') return { status: 'failed', detail: 'launch: ' + (l ? l.detail : 'agent lost') }
  const canStall = !OPERATOR_ROUND_TYPES.includes(type)
  for (let chunk = 0; ; chunk++) {
    if (chunk === NOTIFY_CHUNKS && !A.fixture) {
      await agent(`${T} Comment on issue #${itemNumber}: session ${name} has been working ~90 minutes; add the needs-operator label (a live wait; dispatch relays).`,
        { label: `notify:${label}`, phase: 'Cycle', schema: OUTCOME, ...DRIVER_OPTS })
    }
    if (canStall && chunk >= STALL_CHUNKS) return { status: 'stalled', detail: `script clock: ${chunk} chunks; pane left open` }
    const w = await waitOnce(name, label, chunk)
    if (!w || w.state === 'gone') return { status: 'failed', detail: 'session gone: ' + (w ? w.detail : 'wait agent lost') }
    if (w.state === 'settled_blocked') return { status: 'blocked', detail: w.detail }
    if (w.state === 'settled_done') break
  }
  return await readClose(name, label)
}

const typeOf = (i) => (i.labels.find((l) => l.startsWith('type:')) || 'type:research').slice(5)
const ready = (s) => s.items.filter((i) => i.labels.includes('state:ready'))
const unblocked = (s, i) => i.blocked_by.every((b) => !s.items.some((x) => x.number === b))

let lastSnapshot = null
let cycle = 0
while (true) {
  cycle++
  const s = await queryAndGuards(cycle)
  trace.push({ stage: `cycle${cycle}:query+guards`, status: s && s.status, actions: s ? s.guard_actions : null })
  if (!s || s.status === 'failed') { // a failing cycle never loops
    return { slug: A.slug, cycles: cycle, halted: (s && s.failure) || 'query+guards agent lost', trace }
  }
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
      .then((outcome) => { trace.push({ stage: `${ty}:${nums}`, status: outcome && outcome.status, detail: outcome && outcome.detail }); return { items, ty, outcome } })
  })
  const finished = await parallel(sessions)

  /* Merge each finished session branch through the gate; close
     finished items on the evidence. The session created its records
     and discoveries; this stage creates nothing. */
  for (const r of (finished || []).filter(Boolean)) {
    if (!r.outcome || r.outcome.status !== 'done') continue // blocked/stalled surface in the report; answer and RESUME
    await drive('merge', `merge-${r.ty}`.slice(0, 32),
      `Merge the session branch for the ${r.ty} batch. In ${A.repoDir}: wt merge sess/<its branch> - never --yes. On green: ${A.fixture ? 'report what you would close' : `close the finished items (${r.items.map((i) => '#' + i.number).join(', ')}) closed:done with the evidence in a comment`}. On red: fix nothing; report the gate output verbatim. ${T} Deliver by settling.`,
      `merge:${r.ty}`, r.items[0].number, A.repoDir).then((o) => { trace.push({ stage: `merge:${r.ty}`, status: o && o.status, detail: o && o.detail }); return o })
  }
}

return {
  slug: A.slug,
  cycles: cycle,
  trace,
  queue: lastSnapshot ? lastSnapshot.items.filter((i) => i.labels.includes('state:queued')).map((i) => `#${i.number} ${i.title}`) : [],
  next: 'blocked or stalled stages: answer the pane, then resume this run (scriptPath + resumeFromRunId)',
}
