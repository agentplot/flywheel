# Question: what makes a `wt merge` ✓ always mean the gate ran?

- **Item:** #14
- **Raised by:** the `bolt-site-refresh` conductor, landing #12
- **Evidence:** `sessions/2026-08-12-ff-gate-facts/finding.md`, and the
  lab harness and raw per-scenario output beside it
- **Decided:** `../decisions/gate-runs-under-pre-merge.md`

## The question

`.config/wt.toml` registers this repo's three checks under `[pre-commit]`
alone, and `[pre-commit]` gates only a commit `wt` itself writes. On the
loop's standard shape — a clean rebased descendant — `wt` writes no such
commit, so no check runs, and the merge prints the same ✓ as a gated one.

Decided — `../decisions/gate-runs-under-pre-merge.md`: the three checks
move to `[pre-merge]`, alone; no standing explicit gate step, with the
fix-and-re-run `wt hook pre-merge` retry path kept; and new worktrees are
warmed by a `[post-start]` hook running `wt step copy-ignored` so the
checks' dependencies exist in the merging worktree.

## What turns on it

The loop's central guarantee. Construction leans on the green being
produced by the tool rather than asserted by whoever wrote the change —
that is why `wt merge` is the landing step at all. On a fast-forward the
guarantee is absent and indistinguishable from present, so a conductor
reading ✓ cannot tell which it got.

The costs now differ from what this record first supposed. An explicit
step still puts the burden back on the agent and reintroduces exactly the
asserted-green the tool was chosen to eliminate; configuring `[pre-merge]`
costs no merge commit and no history change, and its real cost is
operational — see the two preconditions below.

Two sentences in `skills/_reference/herdr.md` are wrong as written and
move with the remedy (queued as #35, same pass as #34):

- Under "Merging through the gate", the claim that `wt merge` "runs the
  repo's `.config/wt.toml` checks on the exact rebased tree that lands".
  True of `[pre-merge]`; false today, when only `[pre-commit]` is
  configured.
- The instruction to fix and re-run `wt hook pre-merge` after a gate
  failure. A silent pass today, for the same reason.

The comment block at the head of `.config/wt.toml` also describes the
hooks as running "during `wt merge` before the commit, on the exact tree
that lands", and says "all four are independent" while defining three.
#34 rewrites that block with the config change.

## What is already known

Established by exercising worktrunk 0.57.0 on this machine against a
purpose-built lab repo, ten merge shapes with both hook kinds
configured. Full table and raw output in the finding.

- **`[pre-merge]` runs on every shape**, including the clean
  fast-forward, the no-op, and the rebase-needed case — after the
  rebase, in the source worktree (the same cwd `[pre-commit]` gets), with
  `HEAD` equal to the exact sha that lands. A failing one aborts: exit 1,
  target unmoved, nothing landed.
- **`[pre-commit]` fired only where `wt` itself makes a commit** — a
  dirty tree, or `squash = true`.
- **`ff = false` is ruled out by evidence.** `--no-ff` makes the merge
  commit and `[pre-commit]` still does not run: it gates the commit `wt`
  writes of the branch's own changes, not the merge commit. The merge
  commit on every merge-back would buy nothing.
- **An upstream fix is ruled out.** worktrunk already ships the
  mechanism and behaves as its own `--help` documents.
- **`verify` is the on/off master for merge hooks, not a selector.**
  `verify = false` is identical to `--no-hooks`. It was in force and
  doing its job throughout; it had nothing to run.
- Observed twice in production on `bolt/site-refresh` at the tree landing
  as 134e177, and once more folding this very session's branch: a clean
  ✓ on a fast-forward with none of `validate-manifests`, `check-paths` or
  `check-site` run, and no approval prompt. #12 and this session's branch
  were both verified by hand on the landing tree instead.

Two preconditions any `[pre-merge]` remedy inherits, neither created by
it:

- **Approvals must exist for this repo, or every merge aborts** — but it
  fails *closed*: unapproved hooks non-interactively give exit 1 with
  nothing landed, never an ungated green. This is #16's question.
- **`node_modules` must be present in the merging worktree.**
  `scripts/check-site.mjs` exits 2 without `jsdom`, and this repo
  configures no `post-start` hook to install it. Latent today because
  nothing runs the checks at merge time. Timings on this machine:
  `npm ci` 2.0 s; manifests 0.68 s, paths 0.05 s, site 0.46 s.

Its answer narrowed #16's remedy shape as expected; both closed in the
same planning round, and the doc corrections are queued (#34, #35).
