# Finding: what `wt merge` actually runs, on every shape of merge

- **Item:** #14 · **Type:** research · **Question record:**
  `../../questions/fast-forward-gate-hole.md`
- **Exercised, not read:** worktrunk 0.57.0 (`wt 5fba0bd`,
  `/nix/store/i5zr65bbyaxdvzgq750ydp7c3g6pwl2d-worktrunk-0.57.0/bin/wt`) on
  this machine, against a purpose-built lab repo whose hooks record that they
  fired and on which tree. Harness and raw output in `lab/`.

## The answer in one line

`[pre-merge]` hooks run on **every** shape of `wt merge`, including the
fast-forward where `[pre-commit]` does not — after the rebase, in the source
worktree, with `HEAD` equal to the exact commit that lands — and a failing one
aborts the merge with exit 1 and nothing landed.

## What runs, by shape

Each row is one lab run. `[pre-commit]` and `[pre-merge]` were both configured
throughout; the columns say which fired. Evidence file in `lab/evidence/`.

| Shape of merge | `pre-commit` | `pre-merge` | Outcome | Evidence |
| --- | --- | --- | --- | --- |
| Clean, rebased, strict descendant — **the loop's standard shape** | — | **ran** | ff, ✓ exit 0 | `ff-clean-2` |
| Same, with `pre-merge` exiting 1 | — | **ran** | **aborted, exit 1, target unmoved** | `ff-failgate2` |
| Uncommitted changes (`wt` makes the commit) | **ran** | **ran** | ✓ exit 0 | `dirty` |
| Target moved ahead (rebase needed) | — | **ran, after the rebase** | ff, ✓ exit 0 | `diverged` |
| `--no-ff` on a clean descendant | — | **ran** | merge commit, ✓ exit 0 | `noff` |
| Two commits, `squash = false` | — | **ran** | ff, ✓ exit 0 | `multi` |
| Two commits, `squash = true` | **ran** | **ran** | ✓ exit 0 | `squash` |
| Nothing to merge (already up to date) | — | **ran** | no-op, ✓ exit 0 | `noop` |
| `--no-hooks` | — | — | ✓ exit 0 | `nohooks` |
| `verify = false` | — | — | ✓ exit 0 | `noverify` |

Two properties hold in every row where `pre-merge` ran:

- **cwd is the source worktree** — the same directory `pre-commit` gets. Moving
  a check from one to the other does not change where it runs, only when.
- **`HEAD` at hook time is the sha that lands.** In `diverged`, the hook
  recorded `head=6adbaec` and `main` ended at `6adbaec` — the *rebased* tree,
  not the pre-rebase one. This is the "exact tree that lands" the loop's prose
  claims, and `pre-merge` is where it is true.

Ordering, from `wt hook --help` and confirmed in `dirty` and `squash`:
`pre-commit → post-commit → pre-merge → pre-remove → post-remove + post-merge`.
`pre-*` block; `post-*` are backgrounded and gate nothing.

## The named candidates, costed

**`ff = false` — ruled out by evidence.** It does not do the job it was
proposed for. `--no-ff` creates the merge commit and `[pre-commit]` *still does
not run* (`lab/evidence/noff.txt`): `pre-commit` gates the commit `wt` makes
*of the branch's own changes* (a squash, or committing a dirty tree), not the
merge commit. Paying a merge commit on every merge-back would buy nothing.

**`verify = true` — ruled out; it is already doing its job.** `verify` is the
master on/off for merge hooks, not a selector: `verify = false` runs nothing at
all, exactly like `--no-hooks` (`noverify` vs `nohooks`). With `verify = true`
in force, `wt` ran every hook it had. It had none to run.

**An upstream fix — nothing to fix.** worktrunk 0.57.0 already ships the
mechanism. `wt hook --help` describes `pre-merge` as "Tests, security scans,
build verification — runs after rebase, before merge to target", and that is
precisely how it behaves. This candidate is off the list on capability grounds.

**An explicit gate step the conductor runs — available, and today a green
no-op.** `wt hook pre-merge` runs the hooks on demand in the current worktree
and propagates the failure (`exit=1`, verified). But it only gates if
`[pre-merge]` hooks exist. In this repo today:

```
$ wt hook pre-merge
▲ No pre-merge hooks configured
rc=0
```

`skills/_reference/herdr.md:197-199` already instructs agents to "fix and
re-run `wt hook pre-merge`" after a gate failure. That instruction is a silent pass
today. An explicit step built on `wt hook pre-commit` instead needs the
approvals of #16 and reintroduces the asserted-green the tool was chosen to
eliminate.

**One candidate the record did not name.** `[pre-commit]` and `[pre-merge]` are
not exclusive. Configuring both gates the commit `wt` writes *and* the tree that
lands; the cost is the checks running twice on the shapes where `wt` commits
(~1.2 s here). This is the option that closes the set.

## What any `[pre-merge]` remedy costs in this repo

- **Approvals must exist, or every merge aborts.** Unapproved project hooks in a
  non-interactive environment do not land ungated — the merge fails closed:
  exit 1, target unmoved, nothing run (`lab/evidence/unapproved.txt`). Safe, but
  it means #16 stops being a convenience the moment any hook fires on a
  fast-forward. `--yes` *runs* the hooks without persisting approval
  (`yesbypass`) — it is a trust bypass, not a gate bypass.
- **`node_modules` must be present in the merging worktree.** Run in a fresh
  worktree with no `npm ci`, `scripts/check-site.mjs` exits **2** with
  `check-site: jsdom not installed — run \`npm ci\``. `validate-manifests.sh`
  (0.68 s) and `check-paths.mjs` (0.05 s) pass without it; `check-site.mjs`
  costs 0.46 s once `node_modules` exists, and `npm ci` is 2.0 s. This repo's
  `.config/wt.toml` defines no `pre-start`, so no session worktree has
  `node_modules` unless someone installs it. The cost is *latent today*, not
  created by the remedy — the same hook would fail the same way under
  `[pre-commit]`; nobody has ever seen it fire.
- **History is unchanged.** No merge commit, no branch-shape change.

## Corroboration: the observed event, reproduced exactly

A lab repo configured the way this one is — three `[pre-commit]` hooks, no
`[pre-merge]`, no approval entry — merging a clean rebased descendant:

```
◎ Merging 1 commit to main @ 5628dba (no commit/squash/rebase needed)
✓ Merged to main (1 commit, 1 file, +1, -1)
--- wt exit code = 0
--- hooks that fired: (NONE)
```

No hook, no approval prompt, no way to tell it apart from a gated merge
(`lab/evidence/flywheel-shaped.txt`). This also explains why the missing
approvals of #16 have never surfaced in practice: `wt` asks for approval only
for the hooks it is about to run, and it has never been about to run any.

## Corrections to the record

- **The approvals file is `~/.config/worktrunk/approvals.toml`, and it is not
  empty.** #14 and #16 both name `~/.local/share/worktrunk/approvals.toml`;
  that path does not exist on this machine. The real file holds approvals for
  six `WilldanGroup` projects and **no entry for
  `github.com/agentplot/flywheel`** — which is the identifier `wt config show`
  reports for this repo. The gap is real; its location is not where the items
  say.
- **`wt config approvals add` cannot be run non-interactively — even with
  `--yes`.** Both `wt config approvals add` and `wt config approvals add --yes`
  exit 1 with `Cannot prompt for approval in non-interactive environment`,
  writing nothing. The hint the tool prints ("to pre-approve commands, run
  `wt config approvals add`") is circular. The only non-interactive path is
  writing `approvals.toml` by hand — a plain TOML file keyed by project
  identifier holding the verbatim template text, which is how this lab seeded
  its own. Evidence for #16, not acted on here.
- **`skills/_reference/herdr.md:184-187`** claims the gate "runs the repo's
  `.config/wt.toml` checks on the exact rebased tree that lands". False today
  for every fast-forward. **Lines 197-199** tell agents to re-run `wt hook
  pre-merge`, which currently prints `No pre-merge hooks configured` and exits
  0. Both sentences are in this intent's scope; the second is not named in the
  question record.
- **`.config/wt.toml`'s comment says "All four are independent and seconds
  long"** while defining three hooks. Left for the writeback that rewrites the
  block.

## What this decides

The option set is closed and two of its four named members are eliminated on
evidence. What remains is a choice between configuring `[pre-merge]` (alone or
alongside `[pre-commit]`) and an explicit conductor-run step — and the explicit
step presupposes the configuration, since `wt hook pre-merge` gates nothing
until `[pre-merge]` exists. **The remedy is the operator's word in a later
planning session; this session does not pick it.**

## Caveats on the evidence

The lab repo has no remote (identifier `/private/tmp/wtlab/proj`) and its
approvals were hand-seeded; `[merge]` settings mirrored this machine's
(`squash = false`, `commit = true`, `rebase = true`, `remove = true`,
`verify = true`, `ff = true`) via `--config`, leaving the real user config
untouched. Hook commands were markers, not the real checks; the real checks were
timed separately in this worktree. `--no-rebase` was not exercised.
