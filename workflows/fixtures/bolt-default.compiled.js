/*
COMPILED FROM: schemas/bolt-default/schema.yaml apply.instruction
INSTRUCTION SHA256: 6360d1296ad1023b
COMPILED BY: static compile pass, third round - review-2 verdicts
folded: fixture trace, criteria-fix bounds, stage checkout rules. No INVENTED marks remain: models, limits, landing
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

/* Defensive args (#29): a JSON string arriving as args is parsed. */
const A = typeof args === 'string' ? JSON.parse(args) : args
const trace = [] // every stage outcome; in fixture mode this is the verification artifact
const T = A.fixture
  ? `FIXTURE MODE: the file at ${A.fixture} IS the tracker - read state from it and write every tracker update (labels, moves, closes, comments as a comments array) back to that file instead of GitHub; never touch the real tracker; record each write in your outcome detail.`
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

const queryAndGuards = (cycle) => agent(`Read the bolt tracker state and apply the guards, then return the post-guard snapshot as your structured output. ${T}

Milestone: bolt/${A.slug}. Fields per item: number, title, labels, blocked_by (GitHub's dependency edges, read from the API, never inferred), parent_batch, record path, change name.

GUARDS, in order, each idempotent - record every action you take in guard_actions (empty array if none):
0. If openspec/changes/${A.slug} does not exist in ${A.boltWorktree}: scaffold it (/opsx:new ${A.slug}, bind bolt-default), commit, continue.
1. Any unit at board Status Ready with state:queued sub-issues: relabel those sub-issues state:ready.
2. Any state:queued item with no parent_batch: keep it on this bolt ONLY if the bolt cannot land without it; otherwise move it to the intent that owns its subject, or leave it unmilestoned for dispatch. Compose what remains into a unit at Backlog.

Return the snapshot AFTER your guard actions, with status ok. If you cannot read the tracker, mint the token, or resolve these parameters: status failed with the reason in failure, guard_actions empty - the run stops on your word.`,
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
  .then((o) => { trace.push({ stage: label, status: o && o.status, detail: o && o.detail }); return o })

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
  trace.push({ stage: `cycle${cycle}:query+guards`, status: s && s.status, actions: s ? s.guard_actions : null })
  if (!s || s.status === 'failed') { // a failing cycle never loops
    return { slug: A.slug, cycles: cycle, halted: (s && s.failure) || 'query+guards agent lost', trace }
  }
  lastSnapshot = s
  const work = ready(s).filter((i) => unblocked(s, i))
  if (work.length === 0 && s.guard_actions.length === 0) break // STOP: no ready work and the guards changed nothing

  const builtItems = await pipeline(
    work,
    (it) => drive(
      `spec-writing-${it.change}`.slice(0, 32), A.repoDir,
      `/opsx:ff ${it.change}\n\nSpec for item #${it.number} - ${it.title}\nOne spec-driven change for this one assertion, derived from ${it.record} and the decisions it cites. Worktree: wt switch --create build/${it.change} --base ${A.boltBranch} --no-cd in ${A.repoDir}. openspec validate --strict green before it counts. ${T} Flip #${it.number} to state:in-progress. Commit; do not merge or push. Deliver by settling.`,
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
    `Landing session. Read openspec/changes/${A.slug}/bolt.md on ${A.boltBranch}: verify every Merge criterion on that branch - if any fails, land NOTHING and report the failing criterion as status failed. Read its "Landing:" line (absent = merge).\n- Landing: merge -> land ${A.boltBranch} on main through the gate (wt merge, never --yes), one writer to main; comment the landing SHA on each item and close it closed:done.\n- Landing: pr -> push ${A.boltBranch} and open a pull request to main (gh pr create), report its URL; close nothing - items close when the PR merges.\nOn a failing criterion: create ONE fix item born state:ready on this bolt - unless an open fix item for that criterion already exists (then report and stop); a criterion failing again after its fix landed is the andon cord - stop and ask the operator, never another item.\n${T} Deliver by settling.`,
    'land', 0)
  landing = `${land ? land.status + ': ' + land.detail : 'land agent lost'}`
}

return {
  slug: A.slug,
  cycles: cycle,
  landing,
  trace,
  queue: lastSnapshot ? lastSnapshot.items.filter((i) => i.labels.includes('state:queued')).map((i) => `#${i.number} ${i.title}`) : [],
  next: 'blocked or stalled stages: answer the pane, then resume this run (scriptPath + resumeFromRunId)',
}
