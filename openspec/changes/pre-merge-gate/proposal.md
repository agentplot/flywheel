## Why

This repo's prose tells every agent that `wt merge` runs the
`.config/wt.toml` checks on the exact rebased tree that lands. It does not.
The three checks are registered under `[pre-commit]`, which never fires on
the clean fast-forward that is the loop's standard merge shape, so the
standard merge runs zero hooks, exits 0, and — as
`openspec/changes/gated-merge-guarantee/sessions/2026-08-12-ff-gate-facts/finding.md`
records — is indistinguishable from a gated merge. The guarantee the whole
construction loop rests on is asserted in three places and produced in none.

This change is the configuration half: it makes the gate real. It derives
from `openspec/changes/gated-merge-guarantee/assertions/gate-under-pre-merge.md`
(#34) and the decision that assertion cites,
`decisions/gate-runs-under-pre-merge.md`.

## What Changes

- **`.config/wt.toml` registers `manifests`, `paths` and `site` under
  `[pre-merge]` and under no other table.** `[pre-commit]` keeps no copy —
  one table, one copy of each command, one grant per template, nothing to
  drift.
- **A `[post-start]` entry runs `wt step copy-ignored`**, warming a new
  worktree from the main worktree's gitignored files rather than paying a
  fresh `npm ci`. It is this repo's first `wt` lifecycle hook.
- **The head comment block describes the mechanism it then configures** —
  after the rebase, before the merge to target, on every shape of
  `wt merge` including the clean fast-forward, `HEAD` equal to the sha that
  lands, cwd the source worktree, failure aborting with nothing landed —
  and its count of checks matches the number defined. Two false sentences
  go: "during `wt merge` before the commit, on the exact tree that lands",
  and "All four are independent" over three checks. The "so they run
  concurrently" ordering claim is **dropped rather than restated**: nothing
  about ordering has been measured on this tree, it cannot be measured until
  the grant lets the hooks run, and worktrunk's own documentation states
  both answers in two same-versioned copies (see `design.md`).
- **The block names the unmeasured config-locus question as open** rather
  than resolving it by phrasing.

## Co-landing

This change lands in the same pass, on the same branch, as
`gate-prose-correction` (#35), which corrects the prose that describes this
gate. Neither is landable alone: #35's central sentence is false before this
change lands and stale-wrong after it, so there is no ordering of the two
that leaves the repo correct in between. They are two changes because the
change grain is the assertion — `skills/construction/SKILL.md`, Spec stage:
"the change grain is the assertion: its record binds one change id and one
landing ref" — and one merge-back because the repo must never be caught in
between.

## Capabilities

### New Capabilities

- `flywheel-merge-gate`: what makes this repo's merge gate real — which
  worktrunk hook table the checks are registered under, how a fresh worktree
  becomes able to run them, and what the configuration file is allowed to
  claim about the mechanism it configures.

### Modified Capabilities

<!-- none: no existing capability under openspec/specs/ carries a requirement
     about which hook table this repo's checks are registered under. -->

## Impact

- **`.config/wt.toml`** — the hook tables and the head comment. Nothing
  else. This file's text is what worktrunk's approval store keys on, so
  editing it after the operator's grant (#33) silently un-grants the hooks.
  The grant is taken on this change's final text, after review, and nothing
  touches the file afterwards.
- **Every merge in this repo, from the moment this lands.** The merge that
  carries this change is itself the first merge the new table can govern,
  and unapproved hooks fail closed: exit 1, nothing landed. The ordering is
  the bolt record's (`openspec/changes/merge-gate-remedy/bolt.md`): author →
  the operator's grant (#33) → merge.
- Not in this change: what the three checks test; any prose file; the
  operator's grant (#33); the fleet-layer check that the grant exists (#36).
