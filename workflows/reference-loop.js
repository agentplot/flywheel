/*
THE MECHANICS CONTRACT, as a worked compilation.

This file is not launched by name in production - it is what a
compiled loop looks like, and the normative source for the mechanics
every compilation copies VERBATIM: the driver sequence, the outcome
schema, blocked/stalled handling, serialized merge, fixture mode,
resume-instead-of-rebuild, and the run report shape. A conductor
compiling any bolt type's script (per its schema's apply instruction)
takes those parts from here unchanged and swaps only the stage plan
for the one its instruction states. The compiled script lands at
openspec/changes/<slug>/workflow.js with the instruction's hash in
its header; it is recompiled only when the instruction changes -
editing the apply instruction is how loop behavior changes.

This copy doubles as the isolated harness: launch it directly with
tracker:false and fixture items to watch the mechanics run with no
tracker, no operator, no landing, no end-to-end.
*/
export const meta = {
  name: 'reference-loop',
  description: 'Mechanics contract and worked compilation of the stripped bolt-default instruction: per assertion spec, build, serialized merge-back, then landing when bolt.md merge criteria hold',
  phases: [
    { title: 'Spec', detail: 'one spec-driven change per assertion, via /opsx:ff in a herdr session' },
    { title: 'Build', detail: 'apply each change, via /opsx:apply in a herdr session' },
    { title: 'Merge', detail: 'serialized: session branch -> bolt branch through the gate, then archive' },
    { title: 'Land', detail: 'bolt branch -> main through the full gate, when bolt.md merge criteria hold; never in fixture mode' },
  ],
}

/*
The mechanics contract this script IS:

- The script never touches a shell; every herdr act goes through a
  driver agent (the "double call"). Drivers are thin and never do the
  work: create pane, start session, rename, deliver ONE prompt with
  the invocation as its first line, park on the settle, read the pane,
  close the pane, return an outcome object.
- Spec and build for different assertions pipeline independently; the
  merge stage is a plain serialized loop, because the bolt branch has
  one writer.
- A blocked or stalled session does not sink the run: the driver
  returns the outcome and the run completes with it in the report. The
  conductor answers the pane, then RESUMES this run
  (Workflow {scriptPath, resumeFromRunId}) - finished items replay
  from cache; only the unfinished continue. A correction is the same
  move. One run lineage per bolt; no waves.

args = {
  change:      "merge-gate-remedy",          // the bolt's change slug
  boltBranch:  "bolt/merge-gate-remedy",
  repoDir:     "/abs/path/of/built/repo/main",   // wt commands run here
  boltWorktree:"/abs/path/of/bolt/branch/worktree",
  org:         "agentplot",                  // for flywheel-token
  pluginRoot:  "/abs/path/of/plugin/root",   // bin/ + skills/_reference
  tracker:     true,                         // false = fixture mode: no gh writes, no landing
  items: [ { number: 34, change: "pre-merge-gate",
             title: "Move the merge gate to [pre-merge] ...",
             record: "openspec/changes/merge-gate-remedy/assertions/gate-under-pre-merge.md" } ],
}

Isolated harness (no flywheel, no tracker): from any session in the
built repo, launch with tracker:false and one fixture item whose
record is any small claim file. You watch the panes appear, work, and
close in herdr; the run report is the result. Fixture mode never
writes the tracker and never lands.
*/

const A = args
const OUTCOME = {
  type: 'object',
  properties: {
    status: { type: 'string', enum: ['done', 'blocked', 'stalled', 'failed'] },
    session: { type: 'string' },
    detail: { type: 'string' },
  },
  required: ['status', 'session', 'detail'],
}

const trackerRules = A.tracker
  ? `Tracker writes run as the app: GH_TOKEN=$("${A.pluginRoot}/bin/flywheel-token" --org ${A.org}). ` +
    `If the token subshell fails, STOP and return status failed - never fall back to ambient gh credentials.`
  : `FIXTURE MODE: make no tracker writes of any kind.`

const driverRules = (name, cwd, order) => `You are a WORK driver. You never do the work yourself; you drive one herdr session and report.

Exact sequence (invocations reference: "${A.pluginRoot}/skills/_reference/herdr.md"):
1. herdr tab create --cwd "${cwd}" --label "${name}" --no-focus   (the tab label IS the agent name)
2. herdr agent start "${name}" --kind claude --pane <pane-id from step 1> -- --agent flywheel-construction-session --dangerously-skip-permissions
3. Prompt "/rename ${name}" alone; confirm the title converged before anything else.
4. Deliver the work order as ONE prompt - it follows verbatim between the WORK_ORDER markers. Verify the session goes working; if the composer shows a pasted block, send one enter and re-verify.
5. Park on: herdr agent wait "${name}"  (re-invoke when the 10-minute command cap expires; count the chunks).
6. On settle done/idle: read the pane (herdr agent read "${name}" --source recent-unwrapped --lines 120), extract the session's report. Composer ghost text is not input.
7. herdr tab close <tab-id>  - the pane's job ended with the report; the worktree and branch stay for the merge.
8. Return {status:'done', session:'${name}', detail:<the report, condensed to its facts>}.

Deviations: settle blocked -> do NOT answer anything; return {status:'blocked', session:'${name}', detail:<what the pane is asking>} and leave the pane OPEN. More than 9 wait chunks -> return {status:'stalled', session:'${name}', detail:<pane tail>} and leave the pane open. Any step fails twice -> status failed with what you saw.

WORK_ORDER>>>
${order}
<<<WORK_ORDER`

function specOrder(it) {
  return `/opsx:ff ${it.change}

Work order: spec-writing for item #${it.number} - ${it.title}
THE ASSERTION IS THE PROPOSAL. Derive this one spec-driven change from the assertion record at ${it.record} and the decision records it cites - never from a restatement. First create your worktree: in ${A.repoDir} run wt switch --create build/${it.change} --base ${A.boltBranch} --no-cd, and work there. openspec validate --strict must be green. Commit on the branch (Conventional Commits, footer Refs: #${it.number}); do not merge, do not push. ${trackerRules}${A.tracker ? ` Comment "spec landed: <change id, commit>" on issue #${it.number} and flip its label to state:in-progress.` : ''}
Deliver by settling: print your report as your final message and stop. Never wait on your conductor.`
}

function buildOrder(it) {
  return `/opsx:apply ${it.change}

Work order: build for item #${it.number} - ${it.title}
Apply the spec-driven change ${it.change} on the existing worktree of branch build/${it.change} (find it via wt list in ${A.repoDir}). Re-read every neighbour the spec claims something about from disk before trusting the claim. Commit on the branch; do not merge, do not push. A finding beyond your spec is ${A.tracker ? 'a queued item (bolt milestone ONLY if this bolt cannot land without it; otherwise the intent that owns its subject)' : 'a line in your report'} - never an in-place fix. ${trackerRules}${A.tracker ? ` Comment "build done: <commit>" on issue #${it.number}.` : ''}
Deliver by settling: print your report as your final message and stop.`
}

function mergeOrder(it) {
  return `Work order: merge-back for item #${it.number} - ${it.change}
In the bolt branch worktree ${A.boltWorktree}: wt merge build/${it.change} - hooks run on the exact tree; NEVER --yes; pass --no-squash unless a squash is wanted. On green: openspec archive ${it.change} in this checkout and commit the archive. ${trackerRules}${A.tracker ? ` Comment the merge-back commit on issue #${it.number}.` : ''} On red: fix nothing; report the gate output verbatim.
Deliver by settling: print your report as your final message and stop.`
}

/* Spec -> Build pipeline: item B's spec runs while item A builds. */
phase('Spec')
const built = await pipeline(
  A.items,
  (it) => agent(
    driverRules(`spec-writing-${it.change}`.slice(0, 32), A.repoDir, specOrder(it)),
    { label: `drive:spec:${it.change}`, phase: 'Spec', model: 'sonnet', effort: 'low', schema: OUTCOME },
  ),
  (spec, it) => {
    if (!spec || spec.status !== 'done') return { it, spec, build: null }
    return agent(
      driverRules(`build-${it.change}`.slice(0, 32), A.repoDir, buildOrder(it)),
      { label: `drive:build:${it.change}`, phase: 'Build', model: 'sonnet', effort: 'low', schema: OUTCOME },
    ).then((build) => ({ it, spec, build }))
  },
)

/* Merge-back: strictly serialized - the bolt branch has one writer. */
phase('Merge')
const merged = []
for (const r of built.filter(Boolean)) {
  if (!r.build || r.build.status !== 'done') { merged.push({ ...r, merge: null }); continue }
  const merge = await agent(
    driverRules(`merge-${r.it.change}`.slice(0, 32), A.boltWorktree, mergeOrder(r.it)),
    { label: `drive:merge:${r.it.change}`, phase: 'Merge', model: 'sonnet', effort: 'low', schema: OUTCOME },
  )
  merged.push({ ...r, merge })
}

/* Land: the condition is bolt.md's merge criteria, verified by the
   landing agent itself - it refuses to land when any criterion fails.
   Fixture mode never lands. */
phase('Land')
let landing = 'not attempted'
if (!A.tracker) {
  landing = 'fixture mode - landing never runs'
} else if (!merged.every((r) => r.merge && r.merge.status === 'done')) {
  landing = 'withheld - unmerged or blocked stages remain; answer panes and resume this run'
} else {
  const land = await agent(
    `Landing agent. First read the Merge criteria section of openspec/changes/${A.change}/bolt.md on ${A.boltBranch} and verify each criterion holds on that branch; if any does not, land NOTHING and return status failed with the failing criterion as the detail. When all hold: in ${A.repoDir}, land ${A.boltBranch} on main through the full release gate (wt merge, all hooks, never --yes) - one writer to main. ${trackerRules} Comment the landing SHA on each item and close it closed:done. Report the SHA.`,
    { label: 'land', phase: 'Land', model: 'sonnet', schema: OUTCOME },
  )
  landing = land ? `${land.status}: ${land.detail}` : 'land agent lost'
}

/* The run's report: complete, including what did NOT finish - the
   conductor answers open panes, then RESUMES this run by id. */
return {
  change: A.change,
  items: merged.map((r) => ({
    number: r.it.number,
    change: r.it.change,
    spec: r.spec ? r.spec.status : 'skipped',
    build: r.build ? r.build.status : 'skipped',
    merge: r.merge ? r.merge.status : 'skipped',
    detail: [r.spec, r.build, r.merge].filter((o) => o && o.status !== 'done')
      .map((o) => o.session + ': ' + o.detail).join(' | ') || 'clean',
  })),
  landing,
  next: 'answer any blocked/stalled pane, then resume this run (scriptPath + resumeFromRunId); finished stages replay from cache',
}
