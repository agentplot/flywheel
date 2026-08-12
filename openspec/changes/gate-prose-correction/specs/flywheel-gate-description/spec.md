## Purpose

What the machinery tells agents about this repo's merge gate — the
mechanism rather than the bare guarantee, the strength each part of it is
known at, what an agent does when the gate cannot run, and the rule that
every statement of the gate's shape counts what is actually configured. The
gate itself is the `flywheel-merge-gate` capability's, landing alongside.

## ADDED Requirements

### Requirement: The reference states the gate's mechanism rather than the bare guarantee

`skills/_reference/herdr.md`, under the "Merging through the gate" heading,
SHALL state that the gate is the repo's `[pre-merge]` hooks and that
`wt merge` runs them after the rebase and before the merge to target, on
every shape of merge including the clean fast-forward, with `HEAD` equal to
the sha that lands, and that a failure aborts with nothing landed.

The sentence beginning "The gate runs the repo's `.config/wt.toml` checks on
the exact rebased tree that lands" — located by that phrase, never by line
number — SHALL NOT stand unqualified.

The retry instruction that follows — send the failure output back to the
worktree's agent, have it fix and re-run `wt hook pre-merge`, then merge
again — SHALL remain present and unchanged in substance. It becomes a
functional instruction for the first time with this change; before it, the
command it names is a green no-op.

#### Scenario: An agent reading the reference can predict what a merge does

- **WHEN** an agent reads the section to find out what `wt merge` will run
- **THEN** it learns which hook table supplies the checks, when in the
  merge they run, and what tree they run against
- **AND** it does not have to infer the mechanism from a guarantee stated
  without one

#### Scenario: The retry path survives the rewrite

- **WHEN** the section is read after this change
- **THEN** the fix-and-re-run-`wt hook pre-merge`-then-merge-again path is
  still there

### Requirement: The reference leaves the config-locus question open, at the same strength the configuration does

Which worktree's *configuration* supplies the hooks when the source and
target worktrees carry different `.config/wt.toml` files has **not** been
measured. `sessions/2026-08-12-ff-gate-facts/finding.md` measures cwd — the
source worktree — in every row where `pre-merge` ran, and ran symmetric
configuration throughout, so no row distinguishes the two.

`skills/_reference/herdr.md` SHALL NOT state or imply that the source
worktree's config governs, and SHALL NOT state or imply that the target's
does.

The reference SHALL NOT carry a standing instruction about how to read a
merge that runs zero hooks. Zero hooks has at least two other **measured**
causes — the `nohooks` and `noverify` rows of `finding.md` both ran nothing
and exited 0 — and one further candidate that is documented but **not
measured**: this same file's warning that a trailing `-C` reads the wrong
directory and reports no hooks, whose only provenance is that prose, added
in `b5d308b`. So naming the asymmetric-config question as *the* explanation
is a false dichotomy. More importantly, a standing
instruction to treat an ungated merge as neither a green nor a defect is a
general licence to shrug at the exact symptom `finding.md` records as having
no way to tell apart from a gated merge, which is the reason this intent
exists.

The scoped reading — that for this bolt's own merge-back a zero-hook result
is that question answering itself — is
`openspec/changes/merge-gate-remedy/bolt.md`'s, and SHALL be cited there
rather than reproduced.

The same obligation binds `.config/wt.toml`'s head comment under the
`flywheel-merge-gate` capability, and the two files SHALL carry the question
at the same strength. Flagging it in one and resolving it by phrasing in the
other is the defect this pair of requirements exists to prevent.

#### Scenario: A reader of either file gets the same strength

- **WHEN** the config head comment and the reference section are read side
  by side
- **THEN** both name the question as open, and neither resolves it
- **AND** neither is more confident than the other about which side's
  config governs

#### Scenario: An agent meeting a zero-hook merge is not pre-told what it means

- **WHEN** an agent sees a merge complete with no hooks having run
- **THEN** the reference gives it no standing instruction to accept that as
  normal
- **AND** the measured causes — `--no-hooks` and `verify = false` — remain
  available to it as candidates, alongside the documented-but-unmeasured
  trailing `-C`, each at its own strength

### Requirement: An agent that cannot run the gate stops and reports

`skills/_reference/herdr.md` SHALL state, beside its existing "Hook approval
is the operator's one-time `wt config approvals add`. **Never bypass with
`--yes`.**" sentence, that an agent which hits
`Cannot prompt for approval in non-interactive environment` stops and
reports the failure to its conductor, and the merge waits for the operator's
grant.

Both named non-options SHALL be named as non-options, and the two distinct
`--yes` facts SHALL NOT be merged into one, because they belong to different
commands:

- `--yes` on `wt merge` **runs** the hooks without persisting the approval
  (`finding.md`, the `yesbypass` evidence). That is the trust bypass the
  loop forbids — it is not a gate bypass, which is exactly why it is
  tempting.
- `--yes` on `wt config approvals add` **fails** non-interactively and
  persists nothing (`finding.md`'s corrections to the record, and re-measured
  this bolt per `openspec/changes/merge-gate-remedy/bolt.md`). So it is not
  a route to the grant either.

And hand-running the underlying check scripts on the landing tree is
verification by assertion, precisely the asserted-green that `wt merge`
exists to eliminate, however honest the hands.

The stoppage SHALL be described as a work stoppage rather than a hazard: the
failure is already closed — exit 1, nothing landed — so a missing approval
never produces an ungated green.

#### Scenario: A session hits the approval prompt mid-merge

- **WHEN** a construction session's merge-back aborts with
  `Cannot prompt for approval in non-interactive environment`
- **THEN** the reference tells it to report to its conductor and wait
- **AND** it finds no sanctioned way to proceed on its own

#### Scenario: The honest workaround is named and closed

- **WHEN** an agent reasons that it could just run the three check scripts
  itself and report them green
- **THEN** the reference has already named that as verification by
  assertion and refused it

### Requirement: The reference's `--no-hooks` warning keeps the gate as its reason

`skills/_reference/herdr.md`'s `--no-hooks` paragraph SHALL NOT say that
this repo configures no `wt` lifecycle hooks — the `[post-start]` entry
landing in the same pass is the first one, so that sentence is falsified by
this batch's own commit.

This is not the "fourth site" #35's boundary reserves as a new item. That
boundary is about pre-existing gate-claim sites a grep missed; it does not
license landing a sentence the same pass makes false.

The replacement SHALL keep the reason at full strength: with `[pre-merge]`
configured, `--no-hooks` on `wt merge` **skips the gate** — measured, the
`nohooks` row of `finding.md`, which ran nothing and exited 0. A replacement
that narrows the warning to skipping the worktree warm-up gives a smaller
reason for the same prohibition and does not satisfy this requirement.

Any consequence stated about a cold worktree SHALL be stated only at the
strength measured. The chain from a cold worktree to `check-site.mjs`
exiting 2 holds only where the source worktree has `node_modules` and the
destination would otherwise not, and that conditional has not been
exercised.

#### Scenario: An agent learns why the flag is forbidden

- **WHEN** an agent reads the `--no-hooks` paragraph after this change
- **THEN** it learns that the flag skips this repo's merge gate
- **AND** it does not come away believing the worst case is a cold worktree

### Requirement: The construction skill's Build stage states the same mechanism

`skills/construction/SKILL.md`'s Build stage SHALL state the `[pre-merge]`
mechanism, or stop claiming the tree, in place of the phrase "the merge gate
runs on the rebased tree at merge-back" — located by that phrase, never by
line number, and noting that the phrase is line-wrapped in the source, so a
literal single-line search for it returns nothing.

Both halves of that sentence SHALL be deliberate and true. Its first clause,
"The repo's commit checks run on every push", is muddled before this pass
and false after it: `[pre-commit]` is empty once the checks move, and what
runs on push is the built repo's CI (`.github/workflows/gates.yml`). The
clause SHALL either say that, or go — it SHALL NOT be left as an incidental
survivor of the rewrite. CI on push is real and agents rely on it.

The Merge stage's "full release gate — full hooks, never weakened" is an
instruction rather than a claim about what runs, and SHALL stand unchanged.
So SHALL the Spec stage, which this pass does not touch.

#### Scenario: A build session reads the Build stage after the checks move

- **WHEN** it reads what runs on push and what runs at merge-back
- **THEN** both statements are true of the repo as this pass leaves it

### Requirement: Every statement of the gate's shape counts what is configured

Every comment in this repo that counts the gate's checks SHALL match the
number of check commands the `gates` script in `devenv.nix` defines, and any
claim about which runtime runs which check SHALL be true of that script.

The known miscounts, each describing the exact table `pre-merge-gate` (#34)
rewrites:

- `devenv.nix`'s packages comment — "Two gates and a preview server … node
  runs both checks", where three gates exist and `node` runs two of the
  three (`validate-manifests.sh` runs under `sh`).
- `devenv.nix`'s `gates` script comment — "the same two commands
  `.config/wt.toml` runs before a merge".
- `.github/workflows/gates.yml`'s head comment — "The same four checks
  `.config/wt.toml` runs before a merge".

Both `devenv.nix` miscounts SHALL be corrected. They are eight lines apart
in one file and are the same defect; correcting one of two identical
miscounts in a single file is not a finished fix.

`.config/wt.toml`'s own "All four are independent" is the fourth instance
and belongs to `flywheel-merge-gate`, which removes it in the same pass.

#### Scenario: A reader counts the checks from any caller's comment

- **WHEN** a reader takes the count from `.config/wt.toml`, `devenv.nix`
  (either comment), or `.github/workflows/gates.yml`
- **THEN** all four agree with each other and with the `gates` script

#### Scenario: The "before a merge" phrasing becomes true rather than being edited

- **WHEN** `devenv.nix` and `.github/workflows/gates.yml` describe
  `.config/wt.toml` as running the checks "before a merge"
- **THEN** that phrase is true once the checks are under `[pre-merge]`, and
  needs no edit beyond the count

### Requirement: Approval claims are kept to what has been measured

Prose written by this change SHALL state approval facts at the strength each
is known at, distinguishing three cases.

Measured, recorded in `openspec/changes/merge-gate-remedy/bolt.md`:
`wt config approvals add` enumerates `[post-start]` templates,
`wt step copy-ignored` included; and `--yes` **on that same subcommand**
fails non-interactively and persists nothing. The separate fact that `--yes`
**on `wt merge`** runs the hooks without persisting the approval is
`finding.md`'s (`yesbypass`), and the two SHALL NOT be stated as one.

Expected but not yet measured: that a worktree carrying the new
configuration lists exactly four project hook templates. No committed tree
carries that configuration until this pass lands, so the tree that would be
measured does not exist. `pre-merge-gate`'s task 2.7 produces it. Prose
SHALL NOT present the four-template shape as an established reading of any
tree.

#### Scenario: A reader is told what has been checked and what has not

- **WHEN** the reference describes what the operator's grant covers
- **THEN** the enumeration fact is stated as measured
- **AND** the four-template count of this repo's configuration is not
  presented as a reading already taken
