## Why

The loop's merge gate is `wt`'s hook machinery, and `wt` runs a project hook
only once the operator has granted its template text in
`~/.config/worktrunk/approvals.toml`. That grant has never been taken for
`agentplot/flywheel`: measured on this machine while writing this proposal,
the store holds six `[projects."github.com/WilldanGroup/…"]` tables and no
`agentplot` entry, and `wt config approvals add` in this worktree lists the
three `[pre-commit]` templates and stops at `Cannot prompt for approval in
non-interactive environment`.

Today that silence is harmless only because this repo configures no hook that
`wt` is ever about to run. The moment `[pre-merge]` exists (change `#34`,
`bolt/merge-gate-remedy`), every merge in every worktree of this repo aborts
until the grant exists. The failure is closed rather than silent — exit 1,
nothing landed — but it lands mid-merge, on an agent that cannot fix it,
after the fleet has already placed actors into the repo.

`decisions/approvals-are-an-onboarding-grant.md` settles the remedy: granting
is an operator onboarding step, and the fleet layer checks it. A check is what
removes the *silent* from a manual step — the stoppage happens loudly at fleet
start, with the exact remedy in hand, rather than mid-merge.

## What Changes

- `bin/flywheel` gains a **hook-approval precondition** on every repo it is
  about to start an actor into: every hook template defined in that repo's
  `.config/wt.toml` must have a matching entry, byte-for-byte, in the
  `[projects."<identifier>"]` table of `~/.config/worktrunk/approvals.toml`.
- **`flywheel up` refuses to start any actor into a repo that fails the
  check.** It names the ungranted templates and prints the exact remedy —
  `wt config approvals add`, run interactively in that repo — instead of a
  generic failure. Actors whose repos pass are started as they are today.
- **`flywheel status` reports the check as a row per repo**, starting nothing.
- The same precondition guards **`flywheel reconcile`**'s actor starts —
  manifest rows and tracker-driven conductors alike. `reconcile` is the pass
  that actually places actors on an interval; a guard on `up` alone would
  leave the decision's rule ("refuses to start actors into a repo whose gate
  they cannot run") true of the command nobody runs and false of the one that
  runs continuously. See `design.md`, *The reconcile widening*.
- `skills/fleet/SKILL.md` documents the grant as an **onboarding step** for
  bringing a new built repo into a fleet, in its *Setting up a new org*
  section — where an operator setting up a repo will look.

The check **reads**. It parses two TOML files and compares strings. It never
writes the approvals store, never invokes `wt` to determine approval state,
and never runs a hook. A converger that wrote the grants was considered and
declined by `decisions/approvals-are-an-onboarding-grant.md` — the machinery
would be approving its own hooks.

Not breaking. Against a fleet whose repos are granted, every command behaves
exactly as it does today.

## Capabilities

### New Capabilities

- `flywheel-fleet-approvals`: the fleet layer's hook-approval precondition —
  what `bin/flywheel` reads, what it compares, what it refuses, what it
  prints, and the onboarding step the fleet skill documents.

### Modified Capabilities

None. No existing spec under `openspec/specs/` covers `bin/flywheel` or
`skills/fleet/SKILL.md` (read from disk at this change's authoring: the eight
capabilities there cover the schemas, the skills for the two loops, the
session and conductor profiles, and the eval suites).

## Impact

- **`bin/flywheel`** — a new read-only check and its call sites in `status`,
  `up`, and `reconcile`. Python 3.13 is what runs it here, so `tomllib` is in
  the standard library and the file's zero-dependency rule holds.
- **`skills/fleet/SKILL.md`** — one documented onboarding step.
- **`wt`** — invoked read-only, once per candidate repo, for
  `wt config show --format json`'s `project.identifier` and `project.path`.
  This is the tool's own answer to "which project is this, and which config
  file is in force"; deriving it from the git remote would be a
  reimplementation with a non-obvious fallback (measured: a repo with no
  remote keys on its absolute path). It returns no approval state — the
  comparison is still the two TOML files.
- **New spec** `openspec/specs/flywheel-fleet-approvals/spec.md` on sync.
- **Nothing on the merge gate itself.** This change alters no hook, no
  `.config/wt.toml`, and no merge behaviour. It is independent of `#34` and
  `#35` and can land either side of them.
- **The check's first useful act is to fail** on this very repo, and it starts
  passing when `#33` — the operator's interactive grant — is taken.
