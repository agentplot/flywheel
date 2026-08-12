## Purpose

This repo's merge gate — the worktrunk hook configuration that makes a
green merge a fact the tool produced rather than a claim an agent made,
and every place the machinery describes that gate to the agents who rely
on it. The capability covers where the checks are registered, what the
prose may say about the mechanism and at what strength, and what an agent
does when the gate cannot run.

## ADDED Requirements

### Requirement: The repo's three checks are registered under `[pre-merge]`, alone

`.config/wt.toml` SHALL register `manifests`, `paths` and `site` under a
`[pre-merge]` table and under no other table. No `[pre-commit]` copy of any
of the three commands SHALL exist, and each of the three command strings
SHALL appear exactly once in the file.

One table means one copy of each command: nothing to drift, and one
approval grant per template rather than two that can silently diverge.
`decisions/gate-runs-under-pre-merge.md` declines the both-tables option
for exactly that reason.

#### Scenario: The explicit gate command stops being a silent pass

- **WHEN** an agent runs `wt hook pre-merge` in a worktree of this repo
- **THEN** three commands run and their failure propagates as exit 1
- **AND** the output is not `No pre-merge hooks configured` with exit 0,
  which is what the same command produces before this change

#### Scenario: The standard merge shape is gated

- **WHEN** `wt merge` runs on a clean rebased strict descendant — the
  fast-forward that is the construction loop's standard merge-back shape
- **THEN** the three checks run before anything lands on the target
- **AND** a failing check aborts the merge with exit 1, the target
  unmoved, and nothing landed

#### Scenario: No second copy survives anywhere in the file

- **WHEN** the file is searched for each of the three command strings
- **THEN** each is found exactly once, and every occurrence is inside the
  `[pre-merge]` table

### Requirement: New worktrees are warmed by a `[post-start]` hook

`.config/wt.toml` SHALL carry a `[post-start]` entry whose command is
`wt step copy-ignored`. The hook exists because `check-site.mjs` needs
`jsdom` from `node_modules`, which no fresh worktree has; the copy is
chosen over a fresh `npm ci` because it is the cheaper path to the same
state.

Any prose describing this hook SHALL state the source at the precision
worktrunk states it: `wt step copy-ignored --help` on `wt 5fba0bd` says
`--from` "Defaults to main worktree", which is narrower than "an existing
worktree".

#### Scenario: A worktree cut by worktrunk is warm

- **WHEN** a worktree is created with `wt switch --create`
- **THEN** the `[post-start]` hook fires and the worktree has the
  gitignored files the gate needs

#### Scenario: A herdr-created worktree is warmed by the same hook, run by hand

- **WHEN** a worktree is created by herdr, which fires no `wt` lifecycle
  hooks at all
- **THEN** the reference's existing instruction to run
  `wt -C <worktree-path> hook post-start` after creating one covers it
  with the same hook, and that instruction stands unchanged

#### Scenario: The warm-up fails closed rather than silently

- **WHEN** the gate runs in a worktree that was never warmed and whose
  source lacked `node_modules`
- **THEN** `check-site.mjs` exits 2 with `jsdom not installed`, which
  aborts the merge rather than passing it

### Requirement: The configuration's head comment describes the mechanism it configures

The `.config/wt.toml` head comment block SHALL describe the gate as it then
is: the hooks run after the rebase and before the merge to target, on every
shape of `wt merge` including the clean fast-forward, with `HEAD` equal to
the sha that lands and the source worktree as cwd, and a failure aborting
with nothing landed.

Neither of the two sentences the file carries before this change SHALL
appear anywhere in it afterwards: "during `wt merge` before the commit, on
the exact tree that lands", and "All four are independent" over three
checks.

The block SHALL NOT assert that the checks run concurrently, and SHALL NOT
assert that they run sequentially. Worktrunk's `hook.md` says pre-\*
commands run sequentially and the binary's generic help says concurrently;
neither is a measurement of this tree, and a doc is not promoted to a
measurement by being the only thing available. The claim is dropped, not
replaced.

#### Scenario: The false sentences are gone, not softened

- **WHEN** `.config/wt.toml` is read after this change
- **THEN** neither false sentence appears, in any partial or reworded form
  that still claims hooks run before the commit or counts four checks

#### Scenario: Execution order is asserted in neither direction

- **WHEN** a reader looks for what order the three checks run in
- **THEN** the file says nothing about it, and the reader is not told
  something the tree has not been measured for

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

### Requirement: The unmeasured config-locus question is left open, and left open identically in both files

Which worktree's *configuration* supplies the hooks when the source and
target worktrees carry different `.config/wt.toml` files has **not** been
measured. `sessions/2026-08-12-ff-gate-facts/finding.md` measures cwd — the
source worktree — in every row where `pre-merge` ran, and ran symmetric
configuration throughout, so no row distinguishes the two.

Both `.config/wt.toml` and `skills/_reference/herdr.md` SHALL carry this at
the same strength. Neither SHALL state or imply that the source worktree's
config governs; neither SHALL state or imply that the target's does. A flat
"`wt merge` runs these" in the config's head comment reads as
source-governs stated as fact and does not satisfy this requirement.

Neither file SHALL carry a standing instruction about how to read a merge
that runs zero hooks. Zero hooks has other measured causes — the `nohooks`
and `noverify` rows of `finding.md` both ran nothing, and a trailing `-C`
reads the wrong directory and reports no hooks, which `herdr.md` itself
already warns about — so naming the asymmetric-config question as *the*
explanation is a false dichotomy. More importantly, a standing instruction
to treat an ungated merge as neither a green nor a defect is a general
licence to shrug at the exact symptom `finding.md` describes as having no
way to tell apart from a gated merge, which is the reason this intent
exists.

The scoped reading — that for this bolt's own merge-back a zero-hook result
is that question answering itself — is `openspec/changes/merge-gate-remedy/bolt.md`'s,
and SHALL be cited there rather than reproduced in either file.

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
- **AND** the causes the tree has actually been measured for — `--no-hooks`,
  `verify = false`, a trailing `-C` — remain available to it as candidates

### Requirement: An agent that cannot run the gate stops and reports

`skills/_reference/herdr.md` SHALL state, beside its existing "Hook approval
is the operator's one-time `wt config approvals add`. **Never bypass with
`--yes`.**" sentence, that an agent which hits
`Cannot prompt for approval in non-interactive environment` stops and
reports the failure to its conductor, and the merge waits for the operator's
grant.

Both named non-options SHALL be named as non-options: `--yes` runs the hooks
without persisting approval, a trust bypass the loop forbids; and
hand-running the underlying check scripts on the landing tree is
verification by assertion — precisely the asserted-green that `wt merge`
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

### Requirement: Approval claims are kept to what has been measured

Prose written by this change SHALL distinguish two facts that are not the
same fact.

Measured: `wt hook show` in a worktree carrying this configuration lists
exactly four project hook templates, each marked `(requires approval)` —
which raises the strength of "the `[post-start]` template requires approval
too".

Not measured: whether `wt config approvals add` *enumerates* `[post-start]`
templates when it lists what it is about to grant. No prose SHALL state or
imply that one interactive `wt config approvals add` covers all four
templates, or that all four are approved "before any of them runs", as
though the add subcommand's enumeration were established.

#### Scenario: A three-row grant listing is not self-diagnosing

- **WHEN** the operator runs `wt config approvals add` and sees three
  templates rather than four
- **THEN** nothing this change writes licenses reading that as a
  wrong-checkout diagnosis
- **AND** the correct response is to stop and establish which cause it is
  before approving

### Requirement: The reference's `--no-hooks` warning keeps the gate as its reason

`skills/_reference/herdr.md`'s `--no-hooks` paragraph SHALL NOT say that
this repo configures no `wt` lifecycle hooks — this change's own
`[post-start]` entry is the first one, so that sentence is falsified by the
same commit that would leave it standing.

The replacement SHALL keep the reason at full strength: with `[pre-merge]`
configured, `--no-hooks` on `wt merge` **skips the gate** — measured, the
`nohooks` row of `finding.md`, which ran nothing and exited 0. A replacement
that narrows the warning to skipping the worktree warm-up gives a smaller
reason for the same prohibition and does not satisfy this requirement.

Any consequence stated about a cold worktree SHALL be stated only at the
strength measured. The chain from `--no-hooks` to `check-site.mjs` exiting 2
holds only where the source worktree has `node_modules` and the destination
would otherwise not, and that conditional has not been exercised.

#### Scenario: An agent learns why the flag is forbidden

- **WHEN** an agent reads the `--no-hooks` paragraph after this change
- **THEN** it learns that the flag skips this repo's merge gate
- **AND** it does not come away believing the worst case is a cold worktree

### Requirement: The construction skill's Build stage states the same mechanism

`skills/construction/SKILL.md`'s Build stage SHALL state the `[pre-merge]`
mechanism, or stop claiming the tree, in place of the phrase "the merge gate
runs on the rebased tree at merge-back" — located by that phrase, never by
line number.

Both halves of that sentence SHALL be deliberate and true. Its first clause,
"The repo's commit checks run on every push", is muddled before this change
and false after it: `[pre-commit]` is empty once the checks move, and what
runs on push is the built repo's CI (`.github/workflows/gates.yml`). The
clause SHALL either say that, or go — it SHALL NOT be left as an incidental
survivor of the rewrite. CI on push is real and agents rely on it.

The Merge stage's "full release gate — full hooks, never weakened" is an
instruction rather than a claim about what runs, and SHALL stand unchanged.

#### Scenario: A build session reads the Build stage after the checks move

- **WHEN** it reads what runs on push and what runs at merge-back
- **THEN** both statements are true of the repo as this change leaves it

### Requirement: Every statement of the gate's shape counts what is configured

Every comment in this repo that counts the gate's checks SHALL match the
number of check commands the `gates` script in `devenv.nix` defines, and any
claim about which runtime runs which check SHALL be true of that script.

The known miscounts, each describing the exact table this change rewrites:

- `.config/wt.toml`'s head comment — "All four are independent" over three
  checks, removed by the head-comment rewrite above.
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

#### Scenario: A reader counts the checks from any caller's comment

- **WHEN** a reader takes the count from `.config/wt.toml`, `devenv.nix`
  (either comment), or `.github/workflows/gates.yml`
- **THEN** all four agree with each other and with the `gates` script

#### Scenario: The "before a merge" phrasing becomes true rather than being edited

- **WHEN** `devenv.nix` and `.github/workflows/gates.yml` describe
  `.config/wt.toml` as running the checks "before a merge"
- **THEN** that phrase is true once the checks are under `[pre-merge]`, and
  needs no edit beyond the count
