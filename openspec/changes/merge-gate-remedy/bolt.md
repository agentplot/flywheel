# Bolt: merge-gate-remedy

## Scope

Make this repo's merge gate the thing its prose already claims, and make
the fleet notice when it cannot run. Three released assertions land in
one repo: `.config/wt.toml` moves `manifests`, `paths` and `site` from
`[pre-commit]` to `[pre-merge]` alone, adds a `[post-start]` hook running
`wt step copy-ignored`, and has its head comment block rewritten to
describe the mechanism it then has (#34); `skills/_reference/herdr.md`
under "Merging through the gate" and `skills/construction/SKILL.md`'s
Build stage state the `[pre-merge]` mechanism instead of the bare
guarantee, and the reference gains the stop-and-report rule for an agent
that hits a missing approval (#35); and `bin/flywheel` checks at
`flywheel up`, and reports at `flywheel status`, that every hook template
in a repo's `.config/wt.toml` has its grant in
`~/.config/worktrunk/approvals.toml`, refusing to start actors into a
repo whose gate they cannot run and printing the exact remedy (#36). One
operator step is sequenced inside the bolt rather than before it: #33,
the interactive `wt config approvals add` for this repo, which can only
be taken once #34's configuration text is final and must be taken before
the branch carrying that text merges.

## Sources

- **Intent `gated-merge-guarantee`** (milestone `intent/gated-merge-guarantee`),
  handoff unit #42, handoff item #41. Bolt plan:
  `openspec/changes/gated-merge-guarantee/sessions/2026-08-12-gate-remedy-handoff/bolt-plan.md`
  (a3d7042 on `sess/gate-remedy-handoff`), approved in one plannotator
  round with no annotations.
- **Assertions — the proposals every spec here derives from:**
  - #34 · `openspec/changes/gated-merge-guarantee/assertions/gate-under-pre-merge.md`
  - #35 · `openspec/changes/gated-merge-guarantee/assertions/gate-prose-correction.md`
  - #36 · `openspec/changes/gated-merge-guarantee/assertions/fleet-approval-check.md`
- **Decisions those assertions cite:**
  `openspec/changes/gated-merge-guarantee/decisions/gate-runs-under-pre-merge.md`
  (closes #14) and `.../decisions/approvals-are-an-onboarding-grant.md`
  (closes #16).
- **The measurements behind them:**
  `openspec/changes/gated-merge-guarantee/sessions/2026-08-12-ff-gate-facts/finding.md`
  — ten merge shapes against worktrunk 0.57.0 — and
  `.../questions/hook-approvals-never-granted.md`. Both are marked
  provisional by their own records and are worth re-running on the tree
  that builds this.
- **#33** — the operator's interactive grant. Not an assertion and
  carrying no `type:*` label; it is on this milestone because the bolt
  conductor is who sequences it, blocks on it, and resumes after it.

## Repos

- **agentplot/flywheel** · bolt branch `bolt/merge-gate-remedy` ·
  worktree `~/.herdr/worktrees/.bare/bolt-merge-gate-remedy`

The only repo. This repo is a bare checkout at
`/Users/chuck/Code/github_agentplot/flywheel/.bare` with `main` as a
linked worktree, so bolt and construction worktrees are cut from the bare
path and herdr names the repo `.bare` in the worktree layout. The built
repo and the org's tracker are the same repository.

`skills/_reference/herdr.md` and "the flywheel plugin's shipped copy" are
not two tracked files: this repo *is* the plugin (`.claude-plugin/` at
its root), `git ls-files` finds exactly one `herdr.md`, and the installed
copy under `~/.claude/plugins/cache/flywheel/flywheel/<version>/` is a
release artifact that updates by releasing. No session goes hunting for a
second file.

## Merge criteria

**Ordering, and the strength each part of it is known at.** That
`[pre-merge]` hooks run after the rebase, on every shape of `wt merge`
including the fast-forward, with `HEAD` equal to the landing sha, is
measured — `sessions/2026-08-12-ff-gate-facts/finding.md`, ten shapes.
That the hooks come from the *source* worktree's config is **inference,
not measurement**: the lab exercised only symmetric config, where source
and target carry the same file, so no row distinguishes them. The
inference is strong — `wt merge` is invoked in the source worktree — but
it is not a measurement and this record does not round it up.

The sequence holds either way, which is why it is the sequence. If
source config governs, the first merge the new table governs is the
merge-back of #34/#35's construction branch to the bolt branch, as this
record's acceptance criteria assume. If target config governs, that
merge-back is ungoverned and the bolt branch's landing on main is the
first governed merge, with #33's grant merely taken earlier than it
strictly had to be. Only the locus of the first acceptance evidence
moves; nothing about the order of the three steps changes. **If the
merge-back runs zero hooks, that is the asymmetric-config question
answering itself:** record it as the measurement it is, expect the
landing on main to gate instead, and treat it as neither a green nor a
defect.

#33's grant is therefore taken with cwd inside the construction worktree
carrying #34's final text, never in `main`, whose `.config/wt.toml` still
holds the old `[pre-commit]` shape. Approvals key on verbatim template
text, and that keying is now measured twice over: the ff-gate lab
hand-seeded verbatim templates and the approved hooks ran, and this bolt
measured the case that was open — **moving a granted template between
hook event tables, with its text unchanged, preserves the grant.**
Verified non-destructively in a scratch repo under a relocated `HOME`:
granted under `[pre-commit]`, the hook runs; the same text moved to
`[pre-merge]` with the store untouched, the hook still runs; and the
negative control — one added trailing space — breaks it. That upgrades
what `questions/hook-approvals-never-granted.md` marks provisional, and
it means the table move is not itself what demands a fresh grant.

What demands the grant is that this repo has never had one at all, and
what demands it be taken *last* is that a text edit after a grant
silently un-grants it. So the grant waits not merely for the build but
for the adversarial code-review to clear: a review that names a defect in
`.config/wt.toml` changes the template text, and a grant already taken
would then cover nothing while appearing to cover everything — the exact
shape of silence this bolt exists to end.

**The listing must show four templates, one of them `wt step
copy-ignored`. Three rows is a stop-and-investigate, not a diagnosis.**
The obvious cause is the wrong checkout — `main`'s three-check shape. The
other, unmeasured, is that `wt config approvals add` may not enumerate
`[post-start]` templates at all, in which case three rows is what the
correct worktree produces and the fourth grant has to be got another way.
Either way the grant is not approved from a three-row listing until which
one it is has been established.

**The reads `bolt-default` schedules, all three load-bearing here.** An
independent proposal-review reads every assertion in a batch against its
decision records before that batch is built — the cross-item ordering
above is what it exists to catch. An adversarial code-review reads the
built batch. Batched acceptance runs on the bolt branch before anything
lands on main.

**Acceptance on the bolt branch, before the landing:**

- `wt hook pre-merge` in a worktree of this repo runs three commands
  rather than printing `No pre-merge hooks configured` and exiting 0,
  which is what it does today.
- A `wt merge` of a clean rebased descendant runs them too — the
  fast-forward shape is the hole this bolt closes, and the merge-back in
  the paragraph above is its first real evidence.
- `.config/wt.toml` holds no copy of any of the three commands outside
  `[pre-merge]`, and its head comment's count of checks matches the
  number defined.
- The repo's three named gates green on the tree that lands:
  `sh scripts/validate-manifests.sh`, `node scripts/check-paths.mjs`,
  `node scripts/check-site.mjs`.
- `~/.config/worktrunk/approvals.toml` holds a
  `[projects."github.com/agentplot/flywheel"]` table with four entries.
  It has none today, alongside six unrelated `WilldanGroup` project
  tables.
- `flywheel up` and `flywheel status` behave as #36 claims, exercised
  both ways: against a repo whose templates are ungranted (names them,
  starts nothing, prints `wt config approvals add`) and against this repo
  once #33 is granted (behaves as it does today).
- The prose sites read true against the configuration that then exists.
  The three named in #35 are what a grep found at c7697d6, not a proof
  that no fourth exists; a site found later is a new item, not a silent
  widening.

**The gate is never worked around.** An agent that hits
`Cannot prompt for approval in non-interactive environment` stops and
reports — `--yes` is forbidden, and hand-running the check scripts on the
landing tree is not a substitute gate. That rule is #35's subject matter
and it also binds this bolt's own merges.

**The landing.** With the criteria above holding, `bolt/merge-gate-remedy`
lands on `main` through the full release gate — full hooks, never
weakened, one writer to main at a time.

**The landing is also when #36 starts biting, which is a second and
independent reason the grant precedes it.** From the moment
`fleet-approval-check` is on `main`, `flywheel up` refuses to start
actors into `agentplot/flywheel` until #33 is granted — the assertion
working exactly as written, its own words being that the check's "first
useful act is to fail here". So the grant gates the landing whatever the
answer to the source-vs-target-config question above turns out to be: if
that question resolves the other way and the merge-back runs no hooks,
#36 still stops the fleet at the landing. An ungranted landing is a fleet
stoppage, not a gate failure, and the remedy is the same one command.

**One residual, at measured strength.** `wt step copy-ignored` copies
gitignored files from an existing worktree, so `check-site.mjs`'s `jsdom`
dependency reaches a new worktree only if the source has it. The primary
checkout at `.../flywheel/main` has `node_modules` with `jsdom` present
today, so the failure the decision record names is not currently biting;
where it does bite it fails closed (exit 2, `jsdom not installed`) and one
`npm ci` in the primary checkout remedies it. Herdr-created worktrees fire
no `wt` lifecycle hooks at all, so `wt -C <path> hook post-start` after
creating one is what warms them — an existing instruction in `herdr.md`,
unchanged by this bolt and worth the acceptance run's attention.
