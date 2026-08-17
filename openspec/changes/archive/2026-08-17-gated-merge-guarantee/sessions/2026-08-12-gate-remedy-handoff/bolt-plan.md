# Bolt plan — gated-merge-guarantee handoff, 2026-08-12

One bolt. All three assertions land in one repo, at one depth, and two
of them must land in one pass.

## bolt/merge-gate-remedy

- **member**: `bolt-default` — the batch changes the machinery that
  produces the loop's green claim (`.config/wt.toml`), the prose every
  agent reads before merging (`skills/_reference/herdr.md`), and a start
  precondition in `bin/flywheel`. A wrong claim here is not cheap to
  catch: its failure mode is a merge that reports success without
  running the gate, which is the exact silence this intent exists to
  end — so `bolt-quick`'s no-review depth is wrong. `bolt-deep` is
  wrong the other way: its distinguishing depth is personas exercising
  the result as users who are not the author, and this batch's users
  are the loop's own agents and the operator who wrote the decisions.
  `bolt-default`'s three scheduled reads are each load-bearing here: the
  proposal-review reads all three assertions against their decision
  records before any build, which is where the cross-item ordering trap
  below would surface if a spec got it wrong; the adversarial
  code-review reads the built batch; and the batched acceptance run on
  the bolt branch is the first place `wt hook pre-merge` can be shown to
  run three commands instead of printing `No pre-merge hooks
  configured`.
- **owner**: @afterthought — read from #33, the only item in the batch
  carrying an assignee, and the right one: every decision this bolt
  builds on was settled by the operator, and step 2 below is his hands
  at a terminal. **Ask for the plannotator round:** #34, #35 and #36
  carry no assignee. Confirm that @afterthought is the owner of all
  four and the custody move sets it on the three assertion items, or
  name someone else.
- **repos**: `agentplot/flywheel` — the only one. `skills/_reference/herdr.md`
  and "the flywheel plugin's shipped copy" are not two tracked files:
  this repo *is* the plugin (`.claude-plugin/` at its root), there is
  exactly one `herdr.md` under version control, and the installed copy
  at `~/.claude/plugins/cache/flywheel/flywheel/0.8.3/` is a release
  artifact — byte-identical today, and updated by releasing, not by
  editing. A build session should not go hunting for a second file.
- **assertions**:
  - #34 — `assertions/gate-under-pre-merge.md` — the repo's three checks
    are registered under `[pre-merge]` and under no other table, a
    `[post-start]` hook runs `wt step copy-ignored`, and the head
    comment block describes the mechanism it then has.
  - #35 — `assertions/gate-prose-correction.md` — `herdr.md` under
    "Merging through the gate" and `skills/construction/SKILL.md`'s
    Build stage state the `[pre-merge]` mechanism rather than the bare
    guarantee, and the section carries the stop-and-report rule for an
    agent that hits a missing approval.
  - #36 — `assertions/fleet-approval-check.md` — `flywheel up` refuses
    to start actors into a repo whose `.config/wt.toml` templates lack
    grants in `~/.config/worktrunk/approvals.toml`, printing the exact
    remedy; `flywheel status` reports the same as a row; the grant is
    documented as an onboarding step.
- **sequencing**: three ordered steps, plus one item relation to
  **delete**. Detailed below.
- **ADRs**: none. This repo carries no log4brains layout, and the
  material for one already exists as the intent's two decision records
  (`decisions/gate-runs-under-pre-merge.md`,
  `decisions/approvals-are-an-onboarding-grant.md`), which every spec in
  this bolt derives from. Establishing an ADR tree here is not this
  bolt's work.

### The item relation to delete

`#34 blocked-by #33` exists on the tracker today. **Remove it.** The
custody move deletes it; the ordering it stood for moves into the three
steps below.

It is not merely redundant, it is the wrong half of a two-way
dependency. The grant (#33) must be taken on #34's *final* configuration
text, and the merge that lands #34 is itself the first merge subject to
the table #34 adds. As item relations that is a cycle; GitHub can record
only one direction, and the direction recorded reads "do not start #34
until #33 closes" — which inverts the true order, since #33 cannot be
run until #34's text exists.

Two concrete harms from leaving it:

- The bolt's ANALYSE step reads blocked-by relations to group batches.
  A conductor honouring this edge waits for a #33 that cannot be worked
  until #34 is authored: a deadlock, in the machinery, on the first
  batch.
- The handoff birth condition (tracker invariant 6) is "open on the
  intent milestone, no parent batch, no open blockers." With this edge
  standing, #34 was never eligible for handoff — yet the conductor
  birthed #41 naming it and the operator released unit #42. The edge
  contradicts the release that charged this session.

**The reading taken, stated plainly.** Unit #42's body and #41's own
body are correct and the tracker edge is stale: the grant is *inside*
the bolt as a step, not *before* it as a blocker. This is the reading
this plan executes.

### The three steps

**Step 1 — author.** One session pass produces #34's `.config/wt.toml`
edit and #35's prose corrections together, on one construction worktree
off `bolt/merge-gate-remedy`. They are one pass because #35's central
sentence is false before #34 lands and stale-wrong after it. The pass
ends with the work committed on the construction branch and **not
merged**. Its completion signal is the exact template text: the
conductor comments the four template strings verbatim on #33, together
with the construction worktree's path.

**Step 2 — grant.** The operator runs `wt config approvals add`
interactively, with cwd inside the construction worktree from step 1 —
**not in `main`**. `main`'s `.config/wt.toml` still holds the old
`[pre-commit]` shape, so a grant taken there lists three templates and
silently misses the fourth. Before approving, confirm the listing shows
**four** templates and that one of them is `wt step copy-ignored`; a
listing of three is the wrong checkout. This is the moment `needs-operator`
is correctly applied to #33 (tracker invariant 7 — the label marks a
live wait, and the wait becomes live exactly here). While it is
outstanding the conductor keeps working #36, which the grant does not
gate.

Checkable: `~/.config/worktrunk/approvals.toml` gains a
`[projects."github.com/agentplot/flywheel"]` table — it has none today,
alongside six unrelated `WilldanGroup` projects — with four entries.

**Step 3 — merge.** With the grants in place, the step-1 branch merges
back to `bolt/merge-gate-remedy` through the gate. **That merge-back,
not the bolt branch's landing on main, is the first merge the new table
governs** — `[pre-merge]` hooks run in the *source* worktree
(`sessions/2026-08-12-ff-gate-facts/finding.md`, every row), and the
source worktree is the one carrying #34's committed config. A plan that
placed the grant merely "before landing on main" would strand the batch
at merge-back. The bolt branch itself therefore lands on main after the
grant, necessarily and by some margin.

That same merge-back is this bolt's first real evidence: three commands
run where `No pre-merge hooks configured` printed before.

**#36 runs in parallel**, on its own worktree off the bolt branch, and
can merge back either side of step 3. It changes no gate behaviour and
only reads state. If its worktree is cut before step 3 its own config is
still the old shape and its merge-back is ungoverned; if after, the
grant already covers it. Either way nothing waits on it.

### What the sequence does and does not cost the fleet

The stoppage window #42 warns about does not open, because the grant
precedes every merge that carries the new config. The grant is one
machine-level file keyed on the repo identifier, so a single grant
covers every worktree of this repo at once — there is no per-worktree or
per-branch stoppage to stagger. Sibling sessions merging to main during
construction are unaffected until the bolt lands; from that landing they
are covered by the same grant.

Two residuals, at measured strength:

- **Keying.** "Approvals key on template text, so moving a check between
  tables re-keys nothing" is read from the head comment of
  `.config/wt.toml` and is *not* measured — the question record
  (`questions/hook-approvals-never-granted.md`) marks it provisional.
  The sequence above does not depend on it: granting on the final text
  is correct under either keying. Do not shortcut step 2 into "grant now
  against main's text, since three of the four strings are unchanged."
- **`check-site` needs `jsdom`.** `wt step copy-ignored` copies from an
  existing worktree; the primary checkout at
  `.../flywheel/main` has `node_modules` with `jsdom` present today, so
  the decision record's named residual is not currently biting. A
  herdr-created worktree fires no `wt` lifecycle hooks, so the existing
  `wt -C <path> hook post-start` instruction in `herdr.md` is what warms
  those — unchanged by this bolt, and worth the acceptance run's
  attention.

### One observation, the conductor's call

Whether each batch takes a spec-driven change or the no-spec plan-mode
path is per-batch and the bolt conductor's, not this plan's. Noting only
what the material looks like: #34 is a table move and a comment rewrite
in a ~30-line TOML, #35 is prose at three named sites, and #36 is new
behaviour in `bin/flywheel` (679 lines of Python) plus fleet-skill
documentation.

## Held back

Nothing. All three assertions and the operator step move to
`bolt/merge-gate-remedy`.

**One move outside the letter of the handoff skill, flagged for the
round.** #33 is not an assertion — it is the operator's own interactive
step — and the skill's custody move speaks of assertions. This plan
moves #33 to `bolt/merge-gate-remedy` with them, because #41 is right
that the grant is a step inside the bolt: the bolt conductor is who
blocks on it, applies `needs-operator` at the right moment, and resumes
after it. Leaving it on `intent/gated-merge-guarantee` would leave the
intent conductor holding an item only the bolt can sequence, and would
keep the intent milestone open on construction-timed work (tracker
invariant 9). #33 keeps its `state:ready` label and its assignee, and
stays a sub-issue of unit #42 across the move. It gains no `type:*`
label: no session works it, and inventing one is not this session's to
do.
