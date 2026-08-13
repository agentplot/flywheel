/*
COMPILED FROM: schemas/bolt-quick/schema.yaml apply.instruction (user copy at
  ~/.local/share/openspec/schemas/bolt-quick, identical to repo main at facc42a)
INSTRUCTION SHA256: 24e48110dd7ef0db
  (sha256 of `openspec instructions apply --change loop-server` between the
  "### Instruction" and "### Project Context" markers, first 16 hex chars.
  Recompile only when this changes.)
MECHANICS: skills/_reference/herdr.md - the one maintained mechanics source.
  Driver/outcome/wait-chunk/serialized-merge/fixture/resume/report shapes follow
  the repo's own worked example, workflows/fixtures/bolt-default.compiled.js.

COMPILE DECISIONS - bolt-quick's instruction carries no MODELS or LIMITS block
(bolt-default's does; this type's does not), so these are stated here rather
than left implicit:
  - Build sessions run opus[1m] - the build type's default in the one
    enumeration, openspec/specs/flywheel-session-type-skills/spec.md. The
    fixture's `sonnet` is bolt-default's own pinning and does NOT carry here.
  - Landing runs opus[1m] (it verifies every merge criterion); the mechanical
    merge-back runs sonnet; workflow drivers sonnet/low; the bounded wait
    haiku/low; plan approval sonnet/medium - it judges a plan against a claim.
  - Wait limits taken from the sibling type's instruction: 9 chunks (~90 min)
    -> comment + needs-operator and keep waiting; 24 (~4 h) -> stalled, pane
    left open. The chunk counter RESETS after each plan approval: the session
    starts working again at that moment.
  - Plan rounds are capped at 2 returns per batch, then blocked +
    needs-operator - the design record's two-rounds-then-pause shape.

THE PLAN-MODE PATH (this bolt's release declares it in the milestone
description): no spec-driven change is written for these items. One BUILD
session per batch, started --permission-mode plan; the CONDUCTOR is the
approver - it reads the plan from the pane, checks it against the item's claim,
and drives the plan dialog with send-keys, or returns it with the mismatch
named. A plan-mode session awaiting approval KEEPS its pane; close means
finished.

ANALYSE (instruction step 2 - reads and writes nothing) is compiled below as
WAVES. The six items carry NO blocked-by edges on the tracker, and true edges
would deadlock this loop: blocked_by clears when a blocker CLOSES, and items
close at landing, after every merge. So the coupling is expressed as waves
instead - #75 (the runner) and #76 (the filters) are the substrate both loop
programs import, #72/#73 are the two programs, #74 is the server that spawns
them, and #77 is disjoint schema/skill text. Sessions inside a wave run in
parallel; a wave starts when no earlier wave's item is still ready.

args = {
  slug, boltBranch, repoDir, boltWorktree, org, pluginRoot,
  fixture: null,   // path to a bolt-tracker.json -> isolated run: read it instead of gh, write nothing, never land
}
*/
export const meta = {
  name: 'bolt-loop-server',
  description: 'Compiled bolt-quick loop for bolt/loop-server: guards, then plan-mode build sessions per wave with conductor plan approval, merges serialized to the bolt branch, landing per bolt.md',
  phases: [
    { title: 'Setup', detail: 'bolt branch and worktree, idempotent' },
    { title: 'Cycle', detail: 'query -> guards -> plan-mode build wave -> merge, repeated' },
    { title: 'Land', detail: 'per bolt.md Landing: merge; never in fixture mode' },
  ],
}

/* Defensive args (#29): a JSON string arriving as args is parsed. */
const A = typeof args === 'string' ? JSON.parse(args) : args
const trace = []
const T = A.fixture
  ? `FIXTURE MODE: the file at ${A.fixture} IS the tracker - read state from it and write every tracker update (labels, closes, comments as a comments array) back to that file instead of GitHub; never touch the real tracker; record each write in your outcome detail.`
  : `Tracker writes run as the app: GH_TOKEN=$("${A.pluginRoot}/bin/flywheel-token" --org ${A.org}); if the token cannot mint, stop and return status failed - never ambient credentials.`

const DRIVER_OPTS = { model: 'sonnet', effort: 'low' }
const BUILD_MODEL = 'opus[1m]'
const MERGE_MODEL = 'sonnet'
const LAND_MODEL = 'opus[1m]'

const NOTIFY_CHUNKS = 9
const STALL_CHUNKS = 24
const MAX_PLAN_RETURNS = 2

/* ANALYSE, compiled: batch -> one session. See header. */
const WAVES = [
  { wave: 1, slug: 'substrate', items: [75, 76],
    goal: 'The substrate both loop programs import: the session-runner abstraction (#75) and the inbox filters (#76). Read each item body - it IS the claim - and design/loop-programs.md sections "Sessions and runners" and "Inboxes"/"The andon cord".' },
  { wave: 1, slug: 'bolt-types', items: [77],
    goal: 'The bolt types as named loop configs, bolt-adversarial replacing bolt-deep everywhere, and the loop: block landing in schema.yaml as a parsed-but-unbuilt stub. Read #77 and design/loop-programs.md sections "The bolt types" and "What the schemas remain for". Rename the schemas/bolt-deep directory, never copy it.' },
  { wave: 2, slug: 'bolt-loop', items: [72],
    goal: 'bin/flywheel-bolt-loop, the construction loop as an ordinary program on the substrate that landed in wave 1. Read #72 and design/loop-programs.md section "The bolt loop".' },
  { wave: 2, slug: 'intent-loop', items: [73],
    goal: 'bin/flywheel-intent-loop, the design loop as its own separate program on the same substrate. Read #73 and design/loop-programs.md section "The intent loop". Its completion signal is operator-driven and R1 is OPEN - if the work turns on R1, comment the question on #73 with needs-operator and build what it does not gate.' },
  { wave: 4, slug: 'eval-recast', items: [101],
    goal: 'Re-cast the seven bolt-conductor prompts and the one conductor expectation in skills/construction/evals/evals.json to the unnamed protagonist, exactly as #74 did for skills/inception/evals/, leaving every expectation\'s substance untouched. Read #101 for the measurement. Do NOT touch bin/_flywheel_server.py\'s docstring or bin/flywheel\'s conductors_cwd matcher - both name the old role deliberately - and do NOT touch openspec/specs/, which is #93\'s and scoped out by the operator. What the suites should measure now is #95\'s open question: do not answer it here.' },
  { wave: 3, slug: 'server', items: [74],
    goal: 'flywheel server: the daemon whose 60s reconcile starts one loop process per milestone with a job and stops those without. Read #74 and design/loop-programs.md sections "Decision" and "Supersedes".' },
]
const waveOf = (n) => (WAVES.find((b) => b.items.includes(n)) || { wave: 99 }).wave

const SNAPSHOT = {
  type: 'object',
  properties: {
    items: { type: 'array', items: { type: 'object', properties: {
      number: { type: 'number' }, title: { type: 'string' }, body: { type: 'string' },
      labels: { type: 'array', items: { type: 'string' } },
      blocked_by: { type: 'array', items: { type: 'number' } },
      parent_batch: { type: ['number', 'null'] },
      merged: { type: 'boolean' },
    }, required: ['number', 'title', 'labels', 'blocked_by', 'parent_batch', 'merged'] } },
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
const WAITR = {
  type: 'object',
  properties: {
    state: { type: 'string', enum: ['settled_done', 'settled_blocked', 'still_working', 'gone'] },
    detail: { type: 'string' },
  },
  required: ['state', 'detail'],
}
const PLANR = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['approved', 'returned', 'not_a_plan_dialog', 'failed'] },
    detail: { type: 'string' },
  },
  required: ['verdict', 'detail'],
}

/* SETUP - the bolt's own topology (herdr.md), idempotent. */
const setup = () => agent(`Establish this bolt's topology in the built repo, idempotently. Report what you CHANGED; if everything already existed, say so and change nothing.
1. If branch ${A.boltBranch} and a worktree for it do not exist: herdr worktree create --cwd "${A.repoDir}" --base main --branch ${A.boltBranch} --label "bolt ${A.slug}" --no-focus --json
2. Then: wt -C "<the worktree path>" hook post-start   (a herdr-created worktree fires no wt lifecycle hooks)
3. Report the worktree's absolute path in detail. Expected: ${A.boltWorktree}
Create no build worktrees and start no sessions.`,
  { label: 'setup:topology', phase: 'Setup', schema: OUTCOME, ...DRIVER_OPTS })

const queryAndGuards = (cycle) => agent(`Read the bolt tracker state and apply the guards, then return the post-guard snapshot as your structured output. ${T}

Milestone: bolt/${A.slug}. Fields per item: number, title, body (the FULL body - on this bolt there are no assertion record files and the body IS the claim), labels, blocked_by (GitHub's dependency edges, read from the API, never inferred), parent_batch, and merged.

merged is TRUE only if the item's comments record a merge-back of its work onto ${A.boltBranch} with a SHA. Read the comments; do not infer it from a label. state:in-progress does NOT mean merged - an item is flipped to in-progress when its build session STARTS, and it keeps that label until the landing closes it, so the label says nothing about whether any code landed. When in doubt, return false: the loop lands only on merged, and a false positive here lands a tree missing that item's work.

GUARDS, in order, each idempotent - guard_actions records ONLY the writes you make; a check that changed nothing records NOTHING (an empty array is the normal, correct result):
0. If openspec/changes/${A.slug} does not exist in the bolt worktree: scaffold it (/opsx:new ${A.slug}, bind bolt-quick), commit, continue. (It exists today; expect to record nothing.)
1. Any unit at board Status Ready with state:queued sub-issues: relabel those sub-issues state:ready.
2. Any state:queued item with no parent_batch: keep it on this bolt ONLY if the bolt cannot land without it; otherwise move it to the intent that owns its subject, or leave it unmilestoned for dispatch. Compose what remains into a unit at Backlog.

Return the snapshot AFTER your guard actions, with status ok. If you cannot read the tracker, mint the token, or resolve these parameters: status failed with the reason in failure, guard_actions empty - the run stops on your word.`,
  { label: `cycle${cycle}:query+guards`, phase: 'Cycle', schema: SNAPSHOT, ...DRIVER_OPTS })

/* HERDR.MD mechanics; the SCRIPT owns all waiting. Each helper returns once. */
const launch = (name, cwd, order, label, planMode) => agent(`Launch one herdr session; deliver its order; return WITHOUT waiting. Idempotent: if an agent named "${name}" already exists (herdr agent list), reuse it - never create a duplicate; if its pane shows this order already delivered or worked, return done without re-sending.
1. herdr tab create --cwd "${cwd}" --label "${name}" --no-focus   (the tab label IS the agent name)
2. herdr agent start "${name}" --kind claude --pane <pane-id> -- --agent flywheel-construction-session --model ${planMode ? BUILD_MODEL : MERGE_MODEL} ${planMode ? '--permission-mode plan' : '--dangerously-skip-permissions'}
3. Prompt "/rename ${name}" ALONE; poll herdr agent get until terminal_title_stripped converges. Never queue the order before the rename submitted - they concatenate and the order is lost.
4. Deliver the work order between the markers as ONE prompt; verify the session goes working (send-keys enter once if a pasted block sits at the composer). Then return {status:'done', detail:'delivered'}.
${planMode ? 'This session is in PLAN MODE: it will settle at a plan dialog rather than editing. That is expected - do not approve it, do not answer it; just confirm the order was delivered and return.' : ''}
WORK_ORDER>>>
${order}
<<<WORK_ORDER`,
  { label: `launch:${label}`, phase: 'Cycle', schema: OUTCOME, ...DRIVER_OPTS })

const waitOnce = (name, label, n) => agent(`Run exactly one bounded wait on the herdr session "${name}": herdr agent wait "${name}" - a SINGLE invocation, which returns when the session settles or the command's own cap ends. Do not loop, do not sleep, do not park a monitor. Then herdr agent get "${name}" and report: settled_done for idle/done, settled_blocked for blocked, still_working otherwise, gone if the agent no longer exists.`,
  { label: `wait${n}:${label}`, phase: 'Cycle', schema: WAITR, model: 'haiku', effort: 'low' })

/* The conductor is the approver. This driver reads and approves; it never
   does the session's work. */
const planApprove = (name, label, claims) => agent(`The plan-mode session "${name}" has settled. YOU ARE THE CONDUCTOR'S APPROVER for its plan; you do none of the work yourself.

1. Read the pane: herdr agent read "${name}" --source recent-unwrapped --lines 250. Composer ghost text and unsent suggestions are NOT input - act only on what the session actually produced.
2. If what you find is NOT a plan awaiting approval (an ordinary permission ask, a question, or a finished report), return not_a_plan_dialog with what it actually is - do not send keys.
3. If it IS the plan dialog: check the plan against the items' claims, quoted verbatim below. The standard is narrow - does the plan do WHAT THE CLAIM SAYS, on the files the claim names? Not whether you would have designed it that way.
4. Approve: drive the dialog with herdr agent send-keys "${name}" <key> - arrows plus enter, picking the ACCEPT-EDITS option. Return approved with the plan condensed to its facts.
5. Return it instead when the plan contradicts a claim, silently drops one of the items, or would edit outside what the claims name: pick the reject option and prompt the feedback with the MISMATCH NAMED - which claim, which part of the plan, in one or two sentences. Return returned.

CLAIMS>>>
${claims}
<<<CLAIMS`,
  { label: `plan:${label}`, phase: 'Cycle', schema: PLANR, model: 'sonnet', effort: 'medium' })

const readClose = (name, label) => agent(`The herdr session "${name}" has settled and is finished. Read its pane (herdr agent read "${name}" --source recent-unwrapped --lines 200) and extract its report - composer ghost text is not input. Then close its tab (herdr tab close <tab-id>): a settled pane left open makes the roster lie. Leave the worktree and branch alone - the merge step lands them.

THE STATUS YOU RETURN IS THE SESSION'S OUTCOME, NEVER YOURS. You will almost always succeed at reading and closing a pane; that is not what status means. If the session reports that its work FAILED - a merge that did not land, a gate that came back red, a build it could not finish - return status failed and put its verbatim reason in detail. Return done ONLY when the session itself reports the work succeeded. A failed stage read as done is how the loop comes to believe a branch merged that did not, and it will land on that belief.`,
  { label: `read:${label}`, phase: 'Cycle', schema: OUTCOME, ...DRIVER_OPTS })

const notify = (label, itemNumbers, name) => agent(`${T} On EACH of issues ${itemNumbers.map((n) => '#' + n).join(', ')}: comment that session ${name} has been working ~90 minutes without settling, and add the needs-operator label. This is a live wait - dispatch relays it. Make no other change.`,
  { label: `notify:${label}`, phase: 'Cycle', schema: OUTCOME, ...DRIVER_OPTS })

const pause = (label, itemNumbers, reason) => agent(`${T} On EACH of issues ${itemNumbers.map((n) => '#' + n).join(', ')}: comment the pause reason verbatim - ${JSON.stringify(reason)} - and add the needs-operator label. Make no other change.`,
  { label: `pause:${label}`, phase: 'Cycle', schema: OUTCOME, ...DRIVER_OPTS })

/* A plan-mode build: launch, then wait/approve rounds, then read and close. */
async function driveBuild(batch, claims) {
  const name = `build-${batch.slug}`
  const label = batch.slug
  const items = batch.items
  const order = [
    '/flywheel:build',
    '',
    `PLAN-MODE PATH - read this before the skill's own steps. This bolt writes NO spec-driven change for these items, so the skill's /opsx:apply step does not apply and there is no change id to open. You are started in --permission-mode plan: every edit is blocked until your plan is approved by the conductor, and your APPROVED PLAN is the spec surrogate. Present the plan, wait, then build exactly it.`,
    '',
    `Session type: build. Change: none (plan-mode). Items: ${items.map((n) => '#' + n).join(', ')} on milestone bolt/${A.slug}.`,
    '',
    `Goal: ${batch.goal}`,
    '',
    `Each item's BODY IS ITS CLAIM - there are no assertion record files on this bolt. Read the bodies from the tracker and the decision record design/loop-programs.md, and derive the work from those, never from a restatement. Where the record and an item body disagree, the item body governs and the disagreement is worth a comment.`,
    '',
    `Worktree: in "${A.repoDir}" run  wt switch --create build/${batch.slug} --base ${A.boltBranch} --no-cd  and work in that worktree. Re-read from disk every neighbour your plan claims something about, at build time - claims made from memory are how this loop breaks.`,
    '',
    `${T} Flip each of your items to state:in-progress as you start, and record progress as comments on them - what you built, what you measured, what you left. Commit by pathspec (git add <your paths>; git commit -- <your paths>); never -a, never add -A, never a tree-wide git operation - sibling agents share this checkout's neighbourhood.`,
    '',
    `Do not merge and do not push - the loop merges. This repo has no test harness today (package.json declares no test script); if your items need one, building it is part of the work, and say so in your report.`,
    '',
    `ANDON CORD: if the work is wrong in a way no further round fixes - a claim contradicts the decision record it cites, or the tree contradicts the claim - stop, say so plainly in your report and on the item, and settle without building. Stopping on a defect is expected behaviour, not failure.`,
    '',
    `Deliver by settling: comment your items, print your report as your final message, and settle. Never wait on the conductor.`,
  ].join('\n')

  const l = await launch(name, A.repoDir, order, label, true)
  if (!l || l.status !== 'done') return { status: 'failed', detail: 'launch: ' + (l ? l.detail : 'agent lost') }

  let returns = 0
  let chunk = 0
  for (;;) {
    if (chunk === NOTIFY_CHUNKS && !A.fixture) await notify(label, items, name)
    if (chunk >= STALL_CHUNKS) return { status: 'stalled', detail: `script clock: ${chunk} chunks without settling; pane left open` }
    const w = await waitOnce(name, label, chunk)
    chunk++
    if (!w || w.state === 'gone') return { status: 'failed', detail: 'session gone: ' + (w ? w.detail : 'wait agent lost') }
    if (w.state === 'still_working') continue

    /* Settled: either the plan dialog, or finished. */
    const p = await planApprove(name, label, claims)
    trace.push({ stage: `plan:${label}`, verdict: p && p.verdict, detail: p && p.detail })
    if (!p || p.verdict === 'failed') return { status: 'blocked', detail: 'plan approval failed: ' + (p ? p.detail : 'approver lost') }
    if (p.verdict === 'not_a_plan_dialog') {
      if (w.state === 'settled_blocked') return { status: 'blocked', detail: p.detail } // a real permission ask - the operator's pane to answer
      break // settled finished
    }
    if (p.verdict === 'returned') {
      returns++
      if (returns > MAX_PLAN_RETURNS) {
        if (!A.fixture) await pause(label, items, `Plan returned ${returns} times on the same batch; the loop paused it rather than bouncing again. Last mismatch: ${p.detail}`)
        return { status: 'blocked', detail: `plan returned ${returns}x; paused with needs-operator` }
      }
    }
    chunk = 0 // approved or returned: the session starts working again, so the clock restarts
  }
  return await readClose(name, label)
}

async function driveMerge(batch) {
  const name = `merge-${batch.slug}`
  const order = `Merge-back for items ${batch.items.map((n) => '#' + n).join(', ')}.
In "${A.boltWorktree}" run:  wt merge build/${batch.slug} --no-remove   - NEVER --yes, --no-hooks or --no-verify; the three pre-merge hooks ARE this repo's gate and are never suppressed or hand-substituted.
On green: comment the merge SHA on each item. Do not close the items - they close at the landing. There is no spec-driven change to archive on this bolt.
On red: fix NOTHING. Report the gate output verbatim as status failed.
If you hit "Cannot prompt for approval in non-interactive environment": stop and report it - never work around the gate.
${T} Deliver by settling.`
  const l = await launch(name, A.boltWorktree, order, `merge:${batch.slug}`, false)
  if (!l || l.status !== 'done') return { status: 'failed', detail: 'launch: ' + (l ? l.detail : 'agent lost') }
  for (let chunk = 0; ; chunk++) {
    if (chunk >= STALL_CHUNKS) return { status: 'stalled', detail: 'merge session did not settle; pane left open' }
    const w = await waitOnce(name, `merge:${batch.slug}`, chunk)
    if (!w || w.state === 'gone') return { status: 'failed', detail: 'session gone: ' + (w ? w.detail : 'wait agent lost') }
    if (w.state === 'settled_blocked') return { status: 'blocked', detail: w.detail }
    if (w.state === 'settled_done') break
  }
  return await readClose(name, `merge:${batch.slug}`)
}

const ready = (s) => s.items.filter((i) => i.labels.includes('state:ready'))
const claimsOf = (s, batch) => batch.items
  .map((n) => s.items.find((i) => i.number === n))
  .filter(Boolean)
  .map((i) => `#${i.number} ${i.title}\n${i.body || '(body empty - read it from the tracker before judging)'}`)
  .join('\n\n---\n\n')

/* SETUP once per run; idempotent, so a resume re-runs it harmlessly. */
const topo = await setup()
trace.push({ stage: 'setup:topology', status: topo && topo.status, detail: topo && topo.detail })
if (!topo || topo.status !== 'done') {
  return { slug: A.slug, halted: 'topology: ' + (topo ? topo.detail : 'setup agent lost'), trace }
}

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

  const readyNumbers = ready(s).map((i) => i.number)
  if (readyNumbers.length === 0 && s.guard_actions.length === 0) break // STOP - nothing left to START

  /* The wave that owns the lowest-numbered ready wave; its batches run together. */
  const currentWave = Math.min(...readyNumbers.map(waveOf))
  const batches = WAVES.filter((b) => b.wave === currentWave && b.items.some((n) => readyNumbers.includes(n)))
  if (batches.length === 0) {
    trace.push({ stage: `cycle${cycle}`, note: `ready items belong to no compiled wave: ${readyNumbers.join(',')}` })
    break
  }
  log(`cycle ${cycle}: wave ${currentWave} - ${batches.map((b) => b.slug + ' [' + b.items.map((n) => '#' + n).join(' ') + ']').join(', ')}`)

  const built = await parallel(batches.map((b) => () =>
    driveBuild(b, claimsOf(s, b)).then((o) => { trace.push({ stage: `build:${b.slug}`, status: o && o.status, detail: o && o.detail }); return { b, o } })))

  /* MERGE serialized - the bolt branch has one writer. */
  let merged = 0
  for (const r of built.filter(Boolean)) {
    if (!r.o || r.o.status !== 'done') continue // blocked/stalled surfaces in the report; answer the pane and RESUME this run
    const m = await driveMerge(r.b)
    trace.push({ stage: `merge:${r.b.slug}`, status: m && m.status, detail: m && m.detail })
    if (m && m.status === 'done') merged++
  }
  if (merged === 0) {
    trace.push({ stage: `cycle${cycle}`, note: 'no batch merged this cycle - stopping rather than re-driving the same wave' })
    break
  }
}

/* LAND - a driven session like every stage. bolt.md declares "Landing: merge".
   THE GATE IS "EVERY ITEM MERGED", NOT "NOTHING READY". An item leaves the
   ready set when its build session STARTS, so an empty ready set is satisfied
   while that session is still building - and a landing fired then lands a tree
   missing that item's work. This ran for real: a restarted loop found #74
   already in-progress under a session it had not launched, read the empty
   ready set as done, and started a landing while the build was live. Only the
   merge record on each item is evidence that code landed. */
/* Only the ASSERTIONS carry work that merges. A discovery queued on this
   milestone (type:build, state:queued) is guard 2's to route and will never
   have a merge record, so counting it here would block the landing forever. */
const unmerged = lastSnapshot
  ? lastSnapshot.items.filter((i) => i.labels.includes('type:assertion') && !i.merged)
  : []
let landing = 'not attempted'
if (A.fixture) {
  landing = 'fixture mode - landing never runs'
} else if (unmerged.length > 0) {
  landing = `NOT LANDING - ${unmerged.length} item(s) carry no merge record: ${unmerged.map((i) => '#' + i.number).join(', ')}. A session may still be building them, or a merge failed. Land only when every item's work is on the bolt branch.`
} else if (lastSnapshot && ready(lastSnapshot).length === 0) {
  const name = 'land-loop-server'
  const order = `Landing session for bolt/${A.slug}, in the main checkout "${A.repoDir}".
Read openspec/changes/${A.slug}/bolt.md on ${A.boltBranch} and VERIFY every one of its Merge criteria on that branch, by running them, not by reading the code. If any fails: land NOTHING and report the failing criterion as status failed.
Its "Landing:" line reads merge: land ${A.boltBranch} on main through the gate (wt merge, never --yes / --no-hooks / --no-verify), one writer to main at a time. Then comment the landing SHA on each of ${WAVES.flatMap((b) => b.items).map((n) => '#' + n).join(', ')} and close each closed:done. There is no spec-driven change to archive on this bolt.
On a failing criterion: create ONE fix item, born state:ready on this bolt, unless an open fix item for that criterion already exists - then report and stop. A criterion failing AGAIN after its fix landed is the andon cord: stop and ask the operator, never another item.
${T} Deliver by settling.`
  const l = await launch(name, A.repoDir, order, 'land', false)
  if (!l || l.status !== 'done') landing = 'launch failed: ' + (l ? l.detail : 'agent lost')
  else {
    let out = null
    for (let chunk = 0; chunk < STALL_CHUNKS; chunk++) {
      const w = await waitOnce(name, 'land', chunk)
      if (!w || w.state === 'gone') { out = { status: 'failed', detail: 'session gone' }; break }
      if (w.state === 'settled_blocked') { out = { status: 'blocked', detail: w.detail }; break }
      if (w.state === 'settled_done') { out = await readClose(name, 'land'); break }
    }
    landing = out ? `${out.status}: ${out.detail}` : 'stalled: landing session never settled; pane left open'
    trace.push({ stage: 'land', status: out && out.status, detail: out && out.detail })
  }
}

return {
  slug: A.slug,
  cycles: cycle,
  landing,
  trace,
  queue: lastSnapshot ? lastSnapshot.items.filter((i) => i.labels.includes('state:queued')).map((i) => `#${i.number} ${i.title}`) : [],
  next: 'blocked or stalled stages: answer the pane, then RESUME this run (scriptPath + resumeFromRunId) - never a rebuilt workflow',
}
