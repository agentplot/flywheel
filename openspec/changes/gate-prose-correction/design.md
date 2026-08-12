## Context

See `proposal.md` — Why. What this section adds is the evidence ledger and
the scope rulings, because almost every defect available in this change is a
strength error: writing a sentence more confidently than the tree has been
measured for, or writing a scoped instruction as standing prose.

`pre-merge-gate` (#34) carries the same ledger for the configuration half.
The two co-land.

### What is measured, and where

| Fact | Strength | Source |
| --- | --- | --- |
| `[pre-merge]` hooks run on every shape of `wt merge`, including the clean fast-forward, after the rebase, with `HEAD` equal to the sha that lands and cwd the source worktree; a failure aborts with exit 1 and nothing landed | **measured**, ten shapes | `openspec/changes/gated-merge-guarantee/sessions/2026-08-12-ff-gate-facts/finding.md` |
| `--no-hooks` on `wt merge` runs **zero** hooks and exits 0 — with `[pre-merge]` configured, it skips the gate | **measured** | same, `nohooks` row |
| `verify = false` does the same | **measured** | same, `noverify` row |
| A trailing `-C` reads the wrong directory and reports no hooks | **PROSE ONLY, not measured** — its sole provenance is `skills/_reference/herdr.md`, added in `b5d308b` | filed for measurement as #64 |
| Unapproved project hooks in a non-interactive environment abort with exit 1 and nothing landed — never an ungated green | **measured** | `finding.md`, `lab/evidence/unapproved.txt` |
| `--yes` on **`wt merge`** runs the hooks without persisting the approval — a trust bypass, not a gate bypass | **measured** | `finding.md`, `yesbypass` |
| `--yes` on **`wt config approvals add`** fails non-interactively and persists nothing — a different command and a different fact | **measured**, twice — the ff-gate lab and this bolt | `finding.md`'s corrections to the record; `openspec/changes/merge-gate-remedy/bolt.md` |
| `wt config approvals add` **does** enumerate `[post-start]` templates | **measured**, this bolt, while reviewing #36 | `bolt.md` |
| The installed `wt 5fba0bd` **is** worktrunk 0.57.0 — the same nix store build the ten shapes were measured on | **measured** | `finding.md`, its "Exercised, not read" bullet |
| A worktree carrying the new configuration lists exactly four project hook templates | **EXPECTED, not measured** — see below | `pre-merge-gate` task 2.7 |
| Which worktree's *config* supplies the hooks when source and target differ | **NOT measured** — the lab ran symmetric config throughout | see below |
| What order the three `[pre-merge]` entries actually run in **on this tree** | **NOT measured**, and not measurable until the grant lets the hooks run | see below |
| Worktrunk's own documentation states **both** answers for a pre-\* hook table, in two copies both labelled version 1.0.0 | **documented, and self-contradictory** — quoted with paths in `pre-merge-gate`'s `design.md` | the two `hook.md` copies and `wt hook --help` on `wt 5fba0bd` |
| That a cold worktree leads to `check-site.mjs` exiting 2 | **conditional, unexercised** — holds only where the source has `node_modules` and the destination would not | — |

The version fact is in the table because a previous session raised an alarm
that the installed binary differs from the one the finding measured. It is
false. `finding.md` names the same nix store path. Any restatement of that
alarm in this change is a defect, not a caution.

### The four-template reading is expected, not measured

An earlier revision of this spec stated at measured strength that
`wt hook show` on the new configuration lists four `(requires approval)`
templates, and cited `bolt.md`. `bolt.md` carries no such measurement, and
**no committed tree carries the four-template configuration** — so the tree
that would have been measured does not exist yet. A claim about the tree
that lands cannot rest on a tree that will not.

The reading itself is real, but its provenance is: `wt hook show` under
`wt 5fba0bd` on the **discarded** plan-mode branch `build/gate-remedy` at
`37118d9`, by a session that was subsequently stood down. That is
corroboration and nothing more; it is recorded here with full provenance and
is cited nowhere as evidence for the landing tree. `pre-merge-gate`'s task
2.7 produces the measurement on the tree that will actually land.

### The two unmeasured facts, and why each is handled the way it is

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
two other causes of a zero-hook merge are measured (`nohooks`, `noverify`),
and a third — the trailing `-C` — is warned about in this very file at
**prose strength only**, its sole provenance being that paragraph, added in
`b5d308b`. Keep the warning; do not label it measured. Cite `bolt.md` for
the scoped reading; do not reproduce it.

**Execution order.** Dropped, because nothing about ordering has been
measured on this tree and it cannot be measured until the grant lets the
hooks run. Worktrunk's own documentation states both answers in two copies
both labelled version 1.0.0, with the binary agreeing with one of them;
`pre-merge-gate`'s `design.md` quotes all three with their paths.
Documentation is not a measurement here, and self-contradictory
documentation only sharpens the point. `.config/wt.toml` carries the
requirement; this change must not reintroduce the claim in prose, in either
direction.

## Goals / Non-Goals

**Goals:**

- Make every sentence the machinery says about the gate true at the strength
  it is known at.
- Leave every claim re-checkable: cite by anchor or quoted phrase, never by
  line number.
- Land nothing that the co-landing sibling's own commit falsifies.

**Non-Goals:**

- Any configuration or code. This change is prose only.
- `.config/wt.toml` — that is `pre-merge-gate` (#34), co-landing.
- The operator's grant (#33), and the fleet-layer check that the grant
  exists (#36).
- Resolving either unmeasured fact above.

## Decisions

### Two changes, one branch, one merge-back

`skills/construction/SKILL.md`'s Spec stage sets the grain: "one
spec-driven change per assertion … a session may write several changes, but
the change grain is the assertion: its record binds one change id and one
landing ref." So #34 and #35 are two change ids.

They co-land on one branch in one pass, because this change's central
sentence is false before #34 lands and stale-wrong after it: there is no
ordering of the two that leaves the repo correct in between. What the design
rejects is *sequencing* them, not separating them. Co-landing satisfies both
the grain rule and the one-pass necessity.

### A capability of its own, split from the gate

`openspec/specs/` was read for an existing home. No capability carries a
requirement about how the gate is described. `flywheel-construction-skill`
governs the skill's review bounds, bolt rules and state claims; its
Build-stage gate sentence is under none of its requirements. So this is
`flywheel-gate-description`, new — sibling to `flywheel-merge-gate` (#34),
which is the gate itself, and to `flywheel-fleet-approvals` (#36), which
checks that its grants exist.

### The config-locus requirement is stated in both changes, deliberately

It is a property of a *pair* of files, and the grain rule puts each file in
a different change. Each change states its own file's obligation and
cross-references the other, so neither is landable while satisfying its own
requirement and violating the joint one. A reviewer checking only one change
still sees the joint constraint.

### The `--no-hooks` paragraph is fixed here, not deferred

The paragraph says "This repo configures no `wt` lifecycle hooks today, so
the flag suppresses nothing and would silently skip the first one added."
#34's `[post-start]` entry **is** that first hook, so the co-landing sibling
is what falsifies the sentence.

It is fixed in this change rather than #34 because it is prose in this
change's file. It is not the "fourth site" #35's boundary reserves — that
boundary is about pre-existing gate-claim sites a grep missed, and it does
not license landing a sentence the same pass makes false.

The replacement's reason must be the gate, not the warm-up. `--no-hooks`
skipping the gate is measured (`nohooks` row). A previous framing narrowed
the paragraph to the warm-up and lost that.

### The count corrections are conductor-authorized adjacent scope

`devenv.nix`'s two miscounts and `.github/workflows/gates.yml`'s one are not
derived from #35's assertion, which is prose-about-the-gate at three named
sites. They are the conductor's direct-edit allowance for the loop's own
machinery where the change is small and self-evident, ratified explicitly,
and delegated into this pass so the count claims and the table they describe
become true together.

They ride in this change rather than #34 because #34's own boundary says it
"does not touch `.github/workflows/gates.yml`", and because they are
comments — the same species as the `--no-hooks` fix above. Recorded here so
code-review reads them as authorized rather than as unasserted scope.

`devenv.nix`'s packages comment needs more than a numeral: with three gates,
"node runs both checks" is wrong twice over, since `validate-manifests.sh`
runs under `sh`. The spec requires the runtime claim to be true of the
`gates` script, not merely the count.

### Gate-claim sites that need no edit — ruled, so nobody re-opens them

Read from disk on this branch after the rebase onto `f38a7bd`:

- `AGENTS.md` — "The same three run in `.config/wt.toml` before a merge"
  (locate by "before a merge"). Count already correct; the phrase becomes
  true when #34 lands.
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
  `wt config show` reports `[merge] squash = false` (verified by this spec
  session on this machine), so the sentence is false and its instruction a
  no-op. It is pre-existing, it is not a gate claim, and the conductor has
  filed it as its own item. **Leave it alone** even though the edit to the
  section above sits directly against it.
- **`openspec/changes/add-flywheel-loops/design.md`** carries the old
  "merge gate on the rebased tree at merge-back" phrasing. That is another
  open change's design material — a design-loop finding for its intent, not
  this change's edit.
- **`openspec/changes/gated-merge-guarantee/questions/hook-approvals-never-granted.md`**
  marks the table-move keying provisional, and this bolt has measured it.
  Upgrading that record is the design loop's, not this batch's; the fact is
  carried in `bolt.md`.

## Risks / Trade-offs

**Prose written to a tree that moved.** → Every neighbour this change
asserts anything about is re-read from disk at build time before the claim
is trusted. Siblings on this bolt are live, and `main` has already moved
under this branch once — the rebase onto `f38a7bd` brought a new Spec-stage
rule and new measurements into `bolt.md`, both of which changed this spec.

**Line numbers drift, and phrases wrap.** → Every site is anchored by
heading or quoted phrase. `herdr.md`'s gate sentence was `:184` at
`c7697d6`, `:202` before the rebase, and `:215` after — three positions
inside one bolt. Separately, the two quoted Build-stage phrases in
`skills/construction/SKILL.md` are **line-wrapped in the source**: "The
repo's commit / checks run on every push" and "the merge gate runs on the
rebased tree at / merge-back". A literal single-line `grep` for either
returns nothing and reads as "the phrase is gone". Search on a fragment that
does not span the break.

**A reader takes the scoped zero-hook reading as standing guidance.** → The
spec forbids it in prose and requires `bolt.md` be cited instead. This is
the one place where correcting a previous framing was the point of the
round, so a reviewer should check it directly rather than assume it.

**The `--no-hooks` replacement quietly loses the gate.** → The spec names
the smaller reason and rules it insufficient, because that is exactly what a
previous framing did.

## Migration Plan

Not a deployment. The ordering is the bolt's, and it is
`openspec/changes/merge-gate-remedy/bolt.md`'s to state. This change carries
no freeze of its own — the frozen file is `.config/wt.toml`, which belongs
to `pre-merge-gate` — but it shares that change's merge-back, so its edits
are committed and held until the operator's grant lands.

Rollback is `git revert` of the commits; prose only, nothing external.

## Open Questions

None that block this change. The unmeasured facts above are named in the
spec as things the prose must *not* resolve, and both are named measurements
for this bolt's acceptance run.
