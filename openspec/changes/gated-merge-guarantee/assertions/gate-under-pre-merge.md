# Assertion: the repo's checks run under `[pre-merge]`, and worktrees start warm

- **Repo:** agentplot/flywheel
- **Item:** #34
- **Raised by:** `sessions/2026-08-12-gate-remedy/` — the operator's round
  closing #14, carved by the conductor's fold.

## The claim

`.config/wt.toml` registers `manifests`, `paths` and `site` under a
`[pre-merge]` table and under no other table — `[pre-commit]` holds none of
them, and no copy of any of the three commands exists anywhere else in the
file. The same file carries a `[post-start]` entry running
`wt step copy-ignored`. Its head comment block describes the mechanism as
it then is: hooks running after the rebase and before the merge, on every
shape of `wt merge` including the fast-forward, on the tree that lands —
and its count of the checks it defines matches the number defined.

Checkable against the tree: `wt hook pre-merge` in a worktree of this repo
runs three commands rather than printing `No pre-merge hooks configured`,
and `wt merge` of a clean rebased descendant runs them too. The two
sentences the current comment block gets wrong — "during `wt merge` before
the commit, on the exact tree that lands", and "All four are independent"
over three checks — appear nowhere in the file.

## Why

`decisions/gate-runs-under-pre-merge.md` settles the table, the absence of
a `[pre-commit]` copy, and the `wt step copy-ignored` warming that replaced
the drafted `npm ci`. The behaviour the claim depends on — `[pre-merge]`
firing on every merge shape with `HEAD` equal to the landing sha, and
`[pre-commit]` firing only where `wt` writes a commit — was established by
experiment in `sessions/2026-08-12-ff-gate-facts/finding.md`, ten shapes
against worktrunk 0.57.0; those measurements are provisional and worth
re-running on the tree that builds this.

## Boundaries

Does not change what the three checks test — the intent puts adding,
removing or retuning checks out of scope. Does not touch
`.github/workflows/gates.yml`. Does not grant the approvals this
configuration then demands: that is #33, the operator's own interactive
step, and it must be granted on this file's final text and before the
branch carrying this assertion merges — the merge that lands this change is
itself the first merge subject to the new table. The prose that describes
the gate to agents is #35 (`assertions/gate-prose-correction.md`), which
lands in the same pass; the fleet-layer check that the grant exists at all
is #36 (`assertions/fleet-approval-check.md`).
