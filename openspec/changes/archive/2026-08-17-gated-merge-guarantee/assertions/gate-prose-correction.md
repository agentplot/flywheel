# Assertion: the reference describes the gate that exists

- **Repo:** agentplot/flywheel
- **Item:** #35
- **Raised by:** `sessions/2026-08-12-gate-remedy/` — the operator's round
  closing #14 and #16, carved by the conductor's fold.

## The claim

`skills/_reference/herdr.md`, under "Merging through the gate", states the
mechanism rather than the bare guarantee: that `wt merge` runs the repo's
`[pre-merge]` hooks after the rebase and before the merge, on every shape of
merge including the fast-forward, with `HEAD` equal to the sha that lands,
and that a failure aborts with nothing landed. The sentence beginning "The
gate runs the repo's `.config/wt.toml` checks on the exact rebased tree that
lands" (`herdr.md:184` at c7697d6 — locate it by that phrase, not the line
number) no longer stands unqualified.

The retry instruction that follows — send the failure back, have the agent
fix and re-run `wt hook pre-merge`, then merge again — is still present and
unchanged in substance.

Beside the existing "Hook approval is the operator's one-time
`wt config approvals add`. **Never bypass with `--yes`.**" the section
states the stop-and-report rule: an agent that hits
`Cannot prompt for approval in non-interactive environment` stops and
reports to its conductor, and hand-running the underlying check scripts on
the landing tree is not a substitute gate.

`skills/construction/SKILL.md` carries the same false claim in its Build
stage — "the merge gate runs on the rebased tree at merge-back"
(`:109` at c7697d6; locate by the phrase) — and states the mechanism, or
stops claiming the tree, in the same pass. Its Merge stage's "full release
gate — full hooks, never weakened" is an instruction rather than a claim
about what runs, and stands unchanged.

`skills/inception/SKILL.md`'s "merge each finished session branch through
the full gate" is likewise an instruction, not a claim about mechanism, and
is out of this assertion's scope.

This repo's `skills/_reference/herdr.md` and the flywheel plugin's shipped
copy are byte-identical at c7697d6 and stay identical through this edit.

## Why

`decisions/gate-runs-under-pre-merge.md` (the mechanism, and the retry path
kept with no standing explicit gate step) and
`decisions/approvals-are-an-onboarding-grant.md` (the stop-and-report rule,
and the two named non-options). The prose is wrong today in both places for
the reason `sessions/2026-08-12-ff-gate-facts/finding.md` establishes: with
the checks under `[pre-commit]` alone, the claimed gate does not run on a
fast-forward and `wt hook pre-merge` is a silent pass.

## Boundaries

Prose only — changes no configuration and no code. It is false until #34
(`assertions/gate-under-pre-merge.md`) lands and stale-wrong after it if
left unedited, so the two land in one pass; sequencing them is the handoff's
call, not this record's. Does not cover the `.config/wt.toml` head comment
block, which #34 rewrites with the config it describes.

The three prose sites named above — `herdr.md`, its shipped copy, and
`skills/construction/SKILL.md` — are what a grep for the gate claim found at
c7697d6, not a proof that no fourth exists. A site found later is a new item
against this assertion, not a silent widening of it.
