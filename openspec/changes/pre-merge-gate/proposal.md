## Why

This repo's prose tells every agent that `wt merge` runs the
`.config/wt.toml` checks on the exact rebased tree that lands. It does not.
The three checks are registered under `[pre-commit]`, which never fires on
the clean fast-forward that is the loop's standard merge shape, so the
standard merge runs zero hooks, exits 0, and — as
`openspec/changes/gated-merge-guarantee/sessions/2026-08-12-ff-gate-facts/finding.md`
records — is indistinguishable from a gated merge. The guarantee the whole
construction loop rests on is asserted in three places and produced in none.

Two released assertions close that gap in one pass, because either alone
leaves the repo wrong: `assertions/gate-under-pre-merge.md` (#34) makes the
gate real, and `assertions/gate-prose-correction.md` (#35) makes the prose
describe it. #35's central sentence is false before #34 lands and
stale-wrong after it.

## What Changes

- **`.config/wt.toml` registers `manifests`, `paths` and `site` under
  `[pre-merge]` and under no other table.** `[pre-commit]` keeps no copy —
  one table, one copy of each command, one grant per template, nothing to
  drift.
- **A `[post-start]` entry runs `wt step copy-ignored`**, warming a new
  worktree from the main worktree's gitignored files rather than paying a
  fresh `npm ci`. It is this repo's first `wt` lifecycle hook.
- **The `.config/wt.toml` head comment block describes the mechanism it
  then has** — after the rebase, before the merge to target, on every shape
  of `wt merge` — and its count of checks matches the number defined. Two
  false sentences go: "during `wt merge` before the commit, on the exact
  tree that lands", and "All four are independent" over three checks. The
  "so they run concurrently" ordering claim is **dropped rather than
  restated**: worktrunk's docs and its own help disagree, and neither is a
  measurement of this tree.
- **`skills/_reference/herdr.md` under "Merging through the gate" states the
  `[pre-merge]` mechanism** instead of the bare guarantee, and names which
  parts of it are measured and which are not. The retry instruction —
  re-run `wt hook pre-merge`, then merge again — stays in substance and
  becomes functional for the first time.
- **The same file gains the stop-and-report rule** beside its existing
  "Never bypass with `--yes`" sentence: an agent that hits
  `Cannot prompt for approval in non-interactive environment` stops and
  reports; hand-running the check scripts on the landing tree is not a
  substitute gate.
- **The same file's `--no-hooks` paragraph stops saying this repo
  configures no lifecycle hooks** — this change's own `[post-start]` entry
  falsifies that sentence — and keeps the reason that matters at full
  strength: with `[pre-merge]` configured, `--no-hooks` skips the gate.
- **`skills/construction/SKILL.md`'s Build stage states the same
  mechanism**, and its muddled first clause about checks running on every
  push is made deliberate and true.
- **Three count claims about this repo's gates are corrected to three** —
  two in `devenv.nix` ("Two gates … node runs both checks" in the packages
  comment, and "the same two commands" in the `gates` script comment) and
  one in `.github/workflows/gates.yml` ("The same four checks"). Same
  defect class as the "All four" this change removes from `.config/wt.toml`.

Not in this change: what the three checks test, `.github/workflows/gates.yml`
beyond its comment count, the operator's `wt config approvals add` grant
(#33), and the fleet-layer check that the grant exists (#36).

## Capabilities

### New Capabilities

- `flywheel-merge-gate`: what makes this repo's merge gate real — which
  worktrunk hook table the checks are registered under, what the machinery
  tells agents about the mechanism and at what strength, what an agent does
  when the gate cannot run, and the rule that every statement of the gate's
  shape counts what is actually configured.

### Modified Capabilities

<!-- none: no existing capability under openspec/specs/ carries a requirement
     about the merge gate's mechanism or its description.
     `flywheel-construction-skill` governs the skill's review and bolt
     requirements and says nothing about the Build stage's gate sentence;
     its "checks that run against the tree that lands" phrase is a claim
     that becomes true when this change lands and needs no edit. -->

## Impact

- **`.config/wt.toml`** — the hook tables and the head comment. This file's
  text is what worktrunk's approval store keys on, so editing it after the
  operator's grant (#33) silently un-grants the hooks. The grant is taken on
  this change's final text, after review, and nothing touches the file
  afterwards.
- **`skills/_reference/herdr.md`** — shipped reference read by every
  conductor and session. One tracked file; the copy under
  `~/.claude/plugins/cache/flywheel/` is a release artifact that updates by
  releasing, not by editing.
- **`skills/construction/SKILL.md`** — the Build stage's mechanism sentence.
- **`devenv.nix`, `.github/workflows/gates.yml`** — comments only; no
  behavior, no CI change.
- **Every merge in this repo, from the moment this lands.** The merge that
  carries this change is itself the first merge the new table can govern,
  and unapproved hooks fail closed: exit 1, nothing landed. The ordering is
  the bolt record's (`openspec/changes/merge-gate-remedy/bolt.md`): author →
  the operator's grant (#33) → merge.
