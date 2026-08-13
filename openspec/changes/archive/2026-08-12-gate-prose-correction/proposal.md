## Why

The machinery tells every agent that the merge gate runs the repo's
`.config/wt.toml` checks on the exact rebased tree that lands. Until
`pre-merge-gate` (#34) lands, that is false: the checks sit under
`[pre-commit]`, which never fires on the clean fast-forward. Once #34 lands
it becomes true by accident rather than by description — a bare guarantee
with no mechanism behind it, which is what let it stay wrong unnoticed
through an entire intent.

This change is the prose half. It derives from
`openspec/changes/gated-merge-guarantee/assertions/gate-prose-correction.md`
(#35) and the two decisions that assertion cites,
`decisions/gate-runs-under-pre-merge.md` and
`decisions/approvals-are-an-onboarding-grant.md`.

## What Changes

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
  configures no lifecycle hooks** — #34's `[post-start]` entry, landing in
  the same pass, falsifies that sentence — and keeps the reason that matters
  at full strength: with `[pre-merge]` configured, `--no-hooks` skips the
  gate.
- **`skills/construction/SKILL.md`'s Build stage states the same
  mechanism**, and its muddled first clause about checks running on every
  push is made deliberate and true.
- **Three count claims about this repo's gates are corrected to three** —
  two in `devenv.nix` and one in `.github/workflows/gates.yml`.
  Conductor-authorized adjacent scope, not derived from #35's assertion;
  see `design.md`.

## Co-landing

This change lands in the same pass, on the same branch, as `pre-merge-gate`
(#34), which makes the gate this prose describes. Neither is landable alone:
this change's central sentence is false before #34 lands and stale-wrong
after it, so there is no ordering of the two that leaves the repo correct in
between. They are two changes because the change grain is the assertion —
`skills/construction/SKILL.md`, Spec stage: "the change grain is the
assertion: its record binds one change id and one landing ref" — and one
merge-back because the repo must never be caught in between.

## Capabilities

### New Capabilities

- `flywheel-gate-description`: what the machinery tells agents about this
  repo's merge gate — the mechanism, the strength each part of it is known
  at, what an agent does when the gate cannot run, and the rule that every
  statement of the gate's shape counts what is actually configured.

### Modified Capabilities

<!-- none: no existing capability under openspec/specs/ carries a requirement
     about how the gate is described. `flywheel-construction-skill` governs
     the skill's review bounds, bolt rules and state claims; its Build-stage
     gate sentence is under none of its requirements, and its "checks that
     run against the tree that lands" phrase is a claim that becomes true
     when #34 lands and needs no edit. -->

## Impact

- **`skills/_reference/herdr.md`** — shipped reference read by every
  conductor and session. One tracked file; the copy under
  `~/.claude/plugins/cache/flywheel/` is a release artifact that updates by
  releasing, not by editing.
- **`skills/construction/SKILL.md`** — the Build stage's mechanism sentence
  only. The Merge stage and the Spec stage are untouched.
- **`devenv.nix`, `.github/workflows/gates.yml`** — comments only; no
  behavior, no CI change.
- Changes no configuration and no code. Not in this change: `.config/wt.toml`
  (that is #34, co-landing), the operator's grant (#33), the fleet-layer
  check that the grant exists (#36).
