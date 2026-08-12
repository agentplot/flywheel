## Context

See `proposal.md` — Why. What this section adds is the evidence ledger,
because almost every defect available in this change is a strength error:
writing a sentence more confidently than the tree has been measured for, or
writing a scoped instruction as standing prose.

### What is measured, and where

| Fact | Strength | Source |
| --- | --- | --- |
| `[pre-merge]` hooks run on every shape of `wt merge`, including the clean fast-forward, after the rebase, with `HEAD` equal to the sha that lands and cwd the source worktree; a failure aborts with exit 1 and nothing landed | **measured**, ten shapes | `openspec/changes/gated-merge-guarantee/sessions/2026-08-12-ff-gate-facts/finding.md` |
| `[pre-commit]` fires only where `wt` itself writes a commit — never on the clean fast-forward, and not even on `--no-ff` | **measured** | same, `noff` and `ff-clean-2` rows |
| `--no-hooks` and `verify = false` each run **zero** hooks and exit 0 | **measured** | same, `nohooks` and `noverify` rows |
| A trailing `-C` reads the wrong directory and reports no hooks | **measured**, and already documented | `skills/_reference/herdr.md`, the `-C` paragraph |
| Unapproved project hooks in a non-interactive environment abort with exit 1 and nothing landed — never an ungated green | **measured** | `finding.md`, `lab/evidence/unapproved.txt` |
| The installed `wt 5fba0bd` **is** worktrunk 0.57.0 — the same nix store build the ten shapes were measured on | **measured** | `finding.md`, its "Exercised, not read" bullet |
| Moving a granted hook template between hook event tables, with its text unchanged, **preserves the grant**; one added trailing space breaks it | **measured**, this bolt, negative control included | `openspec/changes/merge-gate-remedy/bolt.md` |
| `wt hook show` on this configuration lists exactly four project templates, each marked `(requires approval)` | **measured**, this bolt | `bolt.md` |
| `wt step copy-ignored --help`: `--from` "Defaults to main worktree" | **measured**, `wt 5fba0bd` | the binary's own help |
| Which worktree's *config* supplies the hooks when source and target differ | **NOT measured** — the lab ran symmetric config throughout | see below |
| Whether the three `[pre-merge]` entries run sequentially or concurrently | **NOT measured** — worktrunk's `hook.md` and the binary's generic help disagree | see below |
| Whether `wt config approvals add` enumerates `[post-start]` templates | **NOT measured** | see below |

The version fact is in the table because a previous session raised an alarm
that the installed binary differs from the one the finding measured. It is
false. `finding.md` names the same nix store path. Any restatement of that
alarm in this change is a defect, not a caution.

### The three unmeasured facts, and why each is handled the way it is

**Config locus.** The spec forbids resolving it in either direction and
forbids a standing instruction about how to read a zero-hook merge. The
reasoning is worth keeping where a builder will read it: the scoped
reading — "for *this* bolt's merge-back, zero hooks is the asymmetric-config
question answering itself, neither a green nor a defect" — is correct as an
instruction about one merge, and it is what `bolt.md` says. Transplanted
into `skills/_reference/herdr.md` it becomes a general licence telling every
future agent to shrug at an ungated merge. That is the precise symptom
`finding.md` records as having "no way to tell it apart from a gated merge",
and it is why this intent exists at all. It would also be a false dichotomy:
three other causes of a zero-hook merge are measured. Cite `bolt.md`; do not
reproduce it.

**Execution order.** Dropped rather than replaced with worktrunk's docs. A
doc is not a measurement of this tree, and the two docs disagree with each
other. It is a named measurement for the acceptance run, once the grant
exists.

**Grant enumeration.** `wt hook show` listing four `(requires approval)`
templates is a fact about `hook show`, not about `approvals add`. Keeping
them apart is what stops a three-row grant listing from being read as a
wrong-checkout diagnosis when it might instead be `approvals add` not
enumerating `[post-start]` at all.

## Goals / Non-Goals

**Goals:**

- Make the gate real, and make every sentence about it true at the strength
  it is known at.
- Leave every claim re-checkable: cite by anchor or quoted phrase, never by
  line number. Line numbers in these exact files have already drifted once
  inside this bolt.
- Land the configuration and the prose in one pass, so the repo is never in
  a state where the prose is wrong in a new way.

**Non-Goals:**

- Adding, removing, or retuning what the three checks test.
- The operator's grant (#33) — sequenced by the bolt conductor, not by this
  change.
- The fleet-layer check that the grant exists (#36) — its own assertion, its
  own spec, already in flight on this bolt.
- Resolving any of the three unmeasured facts above. A change that resolves
  one of them is asserting past its evidence.

## Decisions

### One change, not two

#34 and #35 are separate assertions but a single change. #35's central
sentence is false before #34 lands and stale-wrong after it: there is no
ordering of two changes that leaves the repo correct in between. The bolt
plan batched them for the same reason.

*Alternative considered:* two changes with a strict order. Rejected — every
intermediate state is a repo that lies about its own gate, and the window is
exactly as long as a review round.

### One new capability rather than a delta on an existing spec

`openspec/specs/` was read for an existing home. No capability carries a
requirement about the merge gate's mechanism or its description.
`flywheel-construction-skill` governs the skill's review bounds, bolt rules
and state claims; its Build stage's gate sentence is not under any of its
requirements. So this is `flywheel-merge-gate`, new — sibling to
`flywheel-fleet-approvals` (#36), which checks that the gate's grants exist.

### The two count corrections in `devenv.nix` and the one in `gates.yml` are in scope

Each is a one-word claim about the exact table this change rewrites, and
each is the same defect class as the "All four" the head-comment rewrite
removes. The conductor authorized them. `devenv.nix` carries **two** such
miscounts, eight lines apart — the packages comment's "Two gates … node runs
both checks" and the `gates` script comment's "the same two commands." Both
are in the spec; fixing one and leaving the other in the same file is not a
finished fix.

Note the packages comment needs more than a numeral: with three gates, "node
runs both checks" is wrong twice over, since `validate-manifests.sh` runs
under `sh`. The spec requires the runtime claim to be true of the `gates`
script, not merely the count.

### `herdr.md`'s `--no-hooks` paragraph is fixed in this pass

The paragraph says "This repo configures no `wt` lifecycle hooks today, so
the flag suppresses nothing and would silently skip the first one added."
This change's `[post-start]` entry **is** that first hook, so this change's
own commit is what falsifies the sentence.

This is not the "fourth site" #35's boundary reserves. That boundary is
about pre-existing gate-claim sites a grep missed; it does not license
landing a sentence your own commit makes false.

The replacement's reason must be the gate, not the warm-up. `--no-hooks`
skipping the gate is measured (`nohooks` row). A previous framing narrowed
the paragraph to the warm-up and lost that.

### Gate-claim sites that need no edit — ruled, so nobody re-opens them

Read from disk on this branch at `ea5d0c6`:

- `AGENTS.md` — "The same three run in `.config/wt.toml` before a merge"
  (locate by "before a merge"). Count already correct; the phrase becomes
  true when this change lands.
- `README.md` — the Gates section's "`.config/wt.toml` before a merge".
  Same.
- `openspec/specs/flywheel-construction-skill/spec.md` — "checks that run
  against the tree that lands: the merge gate, the bolt's merge criteria,
  and the acceptance evidence all still bind" (locate by "the tree that
  lands"). Becomes true on the landing.

A prior sweep ruled no edit on all three, and this design carries that
ruling so a build session does not re-open it. If a build session finds one
of these false rather than merely un-true-yet, that is a stop-and-report,
not a widening.

### Explicitly not this change's, though adjacent

- **`herdr.md`'s squash sentence** — "`wt merge` on this machine squashes by
  default … Pass `--no-squash` unless a squash is what you want."
  `wt config show` reports `[merge] squash = false`, so the sentence is
  false and its instruction a no-op. It is pre-existing, it is not a gate
  claim, and the conductor has filed it as its own item. **Leave it alone**
  even though the edit to the section above sits directly against it.
- **`openspec/changes/add-flywheel-loops/design.md`** carries the old
  "merge gate on the rebased tree at merge-back" phrasing. That is another
  open change's design material — a design-loop finding for its intent, not
  this change's edit.
- **`openspec/changes/gated-merge-guarantee/questions/hook-approvals-never-granted.md`**
  marks the table-move keying provisional, and this bolt has measured it.
  Upgrading that record is the design loop's, not this batch's; the fact is
  carried here and in `bolt.md`.

## Risks / Trade-offs

**Editing `.config/wt.toml` after the operator's grant silently un-grants
the hooks.** → Approvals key on verbatim template text, measured twice over.
From the moment this change's template text is reported for #33, nothing
touches the file — not a typo fix, not a rebase fixup — until the grant is
taken. "Grant on final text" means final *after review*, not merely after
build. A build session that discovers it wants to change a template string
after the report stops and tells its conductor.

**The merge that lands this change is the first merge the new table can
govern.** → Unapproved hooks fail closed (exit 1, nothing landed), so the
failure mode is a stoppage rather than an ungated green. The sequence is the
bolt record's: author → grant (#33) → merge. It holds under either answer to
the config-locus question — if source config governs, the merge-back gates;
if target config governs, the landing on main does, and the grant was merely
taken earlier than it strictly had to be.

**A zero-hook merge-back could be read as a defect and worked around.** →
The spec forbids the standing instruction that would license shrugging at
it, and the bolt record carries the scoped reading for this one merge. The
acceptance run records what actually happened; it does not decide it in
advance.

**Line numbers drift.** → Every site in the spec is anchored by heading or
quoted phrase. They have already moved once inside this bolt: `herdr.md`'s
gate sentence was `:184` at `c7697d6` and `:202` on this branch. A build
session that locates by number will edit the wrong thing.

**Prose written to a tree that moved.** → Every neighbour this change
asserts anything about is re-read from disk at build time before the claim
is trusted. Siblings on this bolt are live.

## Migration Plan

Not a deployment. The ordering that matters is the bolt's, and it is
`openspec/changes/merge-gate-remedy/bolt.md`'s to state:

1. Author and commit this change's edits on the construction branch. Do not
   merge.
2. Report the four hook template strings verbatim, with the worktree path,
   for #33. From that moment `.config/wt.toml` is frozen.
3. The operator grants interactively, cwd inside that worktree. The listing
   must show four templates, one of them `wt step copy-ignored`. **Three
   rows is stop-and-investigate**, not a diagnosis: the wrong checkout is
   one cause, `approvals add` not enumerating `[post-start]` is another, and
   which one it is has to be established before approving.
4. Merge back.

Rollback is `git revert` of the commits; nothing outside the repo changes
except the operator's approvals store, which is additive and keyed on text
that would no longer exist.

## Open Questions

None that block this change. The three unmeasured facts above are named in
the spec as things the prose must *not* resolve, and two of them —
execution order, and whether the merge-back gates at all — are named
measurements for this bolt's acceptance run.
