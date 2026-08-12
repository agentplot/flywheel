## Purpose

This repo's merge gate as a configured fact — which worktrunk hook table
the three checks are registered under, how a fresh worktree becomes able to
run them, and what `.config/wt.toml` is allowed to claim about the mechanism
it configures. What the machinery *tells agents* about that gate is the
`flywheel-gate-description` capability's, landing alongside.

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

### Requirement: The configuration is approvable as four templates

The configuration this change leaves SHALL define exactly four worktrunk
hook templates — the three `[pre-merge]` checks and the `[post-start]`
warm-up — so that one interactive `wt config approvals add` in a worktree
carrying this text covers the whole gate.

That `wt config approvals add` enumerates `[post-start]` templates,
`wt step copy-ignored` included, is measured — recorded in
`openspec/changes/merge-gate-remedy/bolt.md`, taken while reviewing #36.
That the same pass re-measured `--yes` **on `wt config approvals add`**
still failing non-interactively and persisting nothing is why the grant
remains an interactive operator step. That is a different command from
`--yes` on `wt merge`, which runs the hooks without persisting the approval;
the two facts are not interchangeable.

The four-template shape itself is **expected, not yet measured**: no
committed tree carries this configuration, so the tree that would be
measured does not exist until this change is built. It is verified at build
time against the tree that will land, and until then it is written as an
expectation.

#### Scenario: The built tree is checked before the grant is requested

- **WHEN** the build session runs `wt hook show` in the worktree carrying
  this change's committed `.config/wt.toml`
- **THEN** exactly four project hook templates are listed, one of them
  `wt step copy-ignored`
- **AND** each reads `(requires approval)`, the grant being #33 and not yet
  taken
- **AND** that reading is reported with the tree it was taken on, because
  it is the first tree on which it can be taken

#### Scenario: A three-row grant listing means the wrong checkout

- **WHEN** the operator runs `wt config approvals add` and sees three
  templates rather than four
- **THEN** the cause is `main`'s three-check shape and the remedy is to
  re-run with cwd in the construction worktree
- **AND** this is a diagnosis rather than an open question, because
  `approvals add` enumerating `[post-start]` has been measured

### Requirement: The configuration's head comment describes the mechanism it configures

The `.config/wt.toml` head comment block SHALL describe the gate as it then
is: the hooks run after the rebase and before the merge to target, on every
shape of `wt merge` including the clean fast-forward, with `HEAD` equal to
the sha that lands and the source worktree as cwd, and a failure aborting
with nothing landed.

Neither of the two sentences the file carries before this change SHALL
appear anywhere in it afterwards: "during `wt merge` before the commit, on
the exact tree that lands", and "All four are independent" over three
checks. The block's count of checks SHALL match the number defined.

The block SHALL NOT assert that the checks run concurrently, and SHALL NOT
assert that they run sequentially.

The reason is that **nothing here has been measured on this tree**, and
ordering cannot be measured until the operator's grant lets the hooks run at
all. Worktrunk's documentation states both answers in two copies carrying
the same version number, and the binary agrees with one of them —
documentation, at documentation strength, recorded in `design.md` with paths
and verbatim quotes. None of it is a measurement of what happens here, which
is the standard `finding.md` set when it ran ten shapes rather than quoting
`wt hook --help`.

Execution order is a named measurement for the acceptance run, once the
grant exists.

#### Scenario: The false sentences are gone, not softened

- **WHEN** `.config/wt.toml` is read after this change
- **THEN** neither false sentence appears, in any partial or reworded form
  that still claims hooks run before the commit or counts four checks

#### Scenario: Execution order is asserted in neither direction

- **WHEN** a reader looks for what order the three checks run in
- **THEN** the file says nothing about it, and the reader is not told
  something the tree has not been measured for

### Requirement: The head comment leaves the config-locus question open

Which worktree's *configuration* supplies the hooks when the source and
target worktrees carry different `.config/wt.toml` files has **not** been
measured. `sessions/2026-08-12-ff-gate-facts/finding.md` measures cwd — the
source worktree — in every row where `pre-merge` ran, and ran symmetric
configuration throughout, so no row distinguishes the two.

The head comment SHALL NOT state or imply that the source worktree's config
governs, and SHALL NOT state or imply that the target's does. A flat
"`wt merge` runs these" reads as source-governs stated as fact and does not
satisfy this requirement.

The block SHALL NOT carry a standing instruction about how to read a merge
that runs zero hooks. Zero hooks has at least two other **measured** causes
— the `nohooks` and `noverify` rows of `finding.md` both ran nothing and
exited 0 — and one further candidate that is documented but **not
measured**: `skills/_reference/herdr.md` warns that a trailing `-C` reads
the wrong directory and reports no hooks, a warning whose only provenance is
that prose, added in `b5d308b`. Either way, naming the asymmetric-config
question as *the* explanation is a false dichotomy, and a standing
instruction to treat an ungated merge as neither a green nor a defect
licenses shrugging at the exact symptom `finding.md` records as
indistinguishable from a gated merge.

The scoped reading — that for this bolt's own merge-back a zero-hook result
is that question answering itself — is
`openspec/changes/merge-gate-remedy/bolt.md`'s, and SHALL be cited there
rather than reproduced.

The same obligation binds `skills/_reference/herdr.md` under the
`flywheel-gate-description` capability, and the two files SHALL carry the
question at the same strength. Flagging it in one and resolving it by
phrasing in the other is the defect this pair of requirements exists to
prevent.

#### Scenario: The two files are read side by side

- **WHEN** the head comment and the reference's gate section are compared
- **THEN** both name the question as open, and neither resolves it
- **AND** neither is more confident than the other about which side's
  config governs
