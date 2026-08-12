# Question: what makes a `wt merge` ✓ always mean the gate ran?

- **Item:** #14
- **Raised by:** the `bolt-site-refresh` conductor, landing #12

## The question

`wt merge` runs `.config/wt.toml`'s `[pre-commit]` hooks before the
commit it makes. With `ff = true` a branch that is a strict descendant
of its target fast-forwards, no commit is made, and no hook runs — and
the merge prints the same ✓ either way. Undecided: which remedy the loop
takes so that a reported success and a gated tree are the same thing.
Named candidates, none ruled out, and the list is not closed —
`ff = false` (a merge commit on every merge-back, gate always runs);
`verify = true` doing the job it appears named for, if its actual
behaviour turns out to differ from what was observed; an explicit gate
step the conductor runs on the landing tree, with the skills stating
that; or a fix upstream in worktrunk. An answer names one and says what
`skills/_reference/herdr.md` then tells agents.

## What turns on it

The loop's central guarantee. Construction leans on the green being
produced by the tool rather than asserted by whoever wrote the change —
that is why `wt merge` is the landing step at all. On a fast-forward the
guarantee is absent and indistinguishable from present, so a conductor
reading ✓ cannot tell which it got. Each way also has a different cost:
`ff = false` puts a merge commit on every merge-back and changes the
shape of every bolt branch's history; an explicit gate step puts the
burden back on the agent and reintroduces exactly the asserted-green the
tool was chosen to eliminate; an upstream fix is not on this loop's
schedule. And whichever wins, the sentence in
`skills/_reference/herdr.md` under "Merging through the gate" is wrong
as written today and has to move.

## What is already known

- Observed twice on `bolt/site-refresh` at the tree landing as 134e177:
  a merge-back to the bolt branch and the landing on main both printed
  `(no commit/squash/rebase needed)` followed by a clean ✓, and neither
  ran `validate-manifests`, `check-paths` or `check-site`. The evidence
  is quoted in item #14.
- `~/.config/worktrunk/config.toml` on this machine sets `ff = true`,
  `verify = true`, `squash = false`, `commit = true`, `rebase = true`,
  `remove = true`. So `verify = true` was in force for both observed
  merges — whatever it verifies, it did not run the hooks.
- The three hooks are `.config/wt.toml`'s `[pre-commit]` block:
  `manifests`, `paths`, `site`. That file's own comment states they run
  "during `wt merge` before the commit, on the exact tree that lands".
- #12 was not landed ungated: the bolt conductor ran `npm ci` and the
  three scripts directly on the rebased landing tree, all green, before
  pushing.
- Blocked on nothing. Its own answer is what unblocks the doc
  correction and the approvals question's remedy shape.
