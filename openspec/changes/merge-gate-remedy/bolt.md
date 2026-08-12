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

**Ordering, which is a fact about the tool and not a preference.**
`[pre-merge]` hooks run in the *source* worktree after the rebase
(`sessions/2026-08-12-ff-gate-facts/finding.md`, every row where they
ran), and the source worktree is the one carrying #34's committed
`.config/wt.toml`. So the first merge governed by the new table is the
merge-back of #34/#35's construction branch to the bolt branch — not the
bolt branch's landing on main. #33's grant therefore precedes that
merge-back, taken with cwd inside that construction worktree: `main`'s
`.config/wt.toml` still holds the old `[pre-commit]` shape, so a grant
taken there lists three templates and misses the `[post-start]` one. The
listing must show **four**, one of them `wt step copy-ignored`; a listing
of three is the wrong checkout. Approvals key on verbatim template text,
so the grant is taken only on final text — the claim that moving a check
between tables re-keys nothing is read from the old head comment and is
**not measured** (`questions/hook-approvals-never-granted.md` marks it
provisional), and this ordering does not depend on it either way.

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
