## Context

See `proposal.md` — *Why*. The constraints that shape the approach:

- **`bin/flywheel` has zero third-party dependencies.** Its module docstring
  advertises a manifest parser written "without a YAML dependency" for exactly
  this reason. Python here is 3.13.12 (measured on this machine), so `tomllib`
  is standard library and TOML parsing costs no dependency.
- **The approvals store's format is not a settled interface.**
  `decisions/approvals-are-an-onboarding-grant.md` says so in as many words:
  the file's "format and keying therefore stay facts on the question record,
  not a settled interface." Anything this change reads out of it is a fact
  about worktrunk today, re-measured, not a contract.
- **`questions/hook-approvals-never-granted.md` marks its facts provisional
  and asks to be re-checked.** Everything below under *Measured* was re-run in
  this worktree, `~/.herdr/worktrees/.bare/build-fleet-approval-check`, at
  branch `build/fleet-approval-check` on `ea5d0c6`, against `wt 5fba0bd`.
- **Three commands start actors, not one.** `up` starts manifest rows;
  `reconcile` calls `up` and then starts tracker-driven conductors of its own;
  `status` starts nothing. Read from `bin/flywheel` on disk at authoring — the
  `reconcile` function's step 1 comment reads "the manifest's standing rows"
  and its body calls `up(...)` directly.

### Measured, on this tree

Re-measurement of the provisional facts, plus what this design newly rests on.
Every claim below was produced by running the command named.

| what | measured |
|---|---|
| `~/.config/worktrunk/approvals.toml` | exists; six `[projects."github.com/WilldanGroup/…"]` tables; **no** `agentplot` entry |
| store shape | `[projects."<identifier>"]` with `approved-commands = [ … ]`, a TOML array of strings |
| grant text | stored **unexpanded** — entries contain `{{ branch \| hash }}` verbatim, confirming keying on template text |
| `wt config approvals add` in this worktree | lists the three `[pre-commit]` templates, then `✗ Cannot prompt for approval in non-interactive environment`; writes nothing |
| its own hint | suggests `--yes` — circular, and forbidden by the loop |
| `wt config show --format json` | returns `project.identifier`, `project.path`, `project.exists`, `project.config` (the parsed hook tables) |
| identifier here | `github.com/agentplot/flywheel`, from both HTTPS and SSH remote forms (checked across the WilldanGroup repos on this machine) |
| identifier with no remote | worktrunk falls back to the repo's **absolute path** (observed on a local-only repo) |
| outside any repo | `project.exists: false`, `identifier: null`, no error |
| hook event tables | exactly ten, enumerated by `wt hook --help`: `pre-`/`post-` × `switch`, `start`, `commit`, `merge`, `remove` |

The build session re-runs these; see `tasks.md`, task 1. The last two rows are
the load-bearing ones for the decision below.

## Goals / Non-Goals

**Goals:**

- One check, computed once per repo per pass, consulted by every path that
  starts an actor.
- Fail closed and legible: an unrunnable check never reports "ready".
- Zero behaviour change against a fleet whose repos are granted.

**Non-Goals:**

- **Granting.** Declined by the decision record, and not reachable anyway:
  `wt config approvals add` cannot grant non-interactively by any invocation
  (measured above), so the only automated path is writing the TOML by hand —
  which is the trust inversion that was declined.
- **Project aliases.** worktrunk's approval mechanism also covers project
  aliases (`wt config approvals --help`: "Project hooks and project aliases
  prompt for approval on first run"). The assertion and its decision are about
  the *gate*, and aliases are not the gate. Out of scope, and filed as a
  discovery item rather than silently widened.
- **Reimplementing worktrunk's approval evaluation.** The comparison is string
  equality on two files, nothing more.

## Decisions

### 1. Ask worktrunk for the identifier; read the two TOML files for the state

The check resolves a repo's project identifier and project-config path with
one read-only `wt config show --format json -C <path>` per candidate repo, then
parses that config file and the approvals store itself with `tomllib` and
compares strings.

*Why not derive the identifier from the git remote?* It is a reimplementation
of a worktrunk rule with a non-obvious branch: measured above, a repo with no
remote keys on its **absolute path**, not on any `github.com/...` form. A
divergent derivation fails loud rather than silent — a wrong key finds no
table, so the check reports "ungranted" and refuses a start it should have
allowed — but that is a fleet stoppage for a reason that is not true, which is
the failure mode this whole intent exists to remove.

*Why this does not cross the assertion's boundary.* The assertion forbids
invoking `wt` **to determine approval state**, and forbids writing the store.
`wt config show --format json` returns no approval state at all — measured, its
`user.config.projects` is `{}` and the approvals store is not among the files
it reports. The approval state still comes from reading the two TOML files and
comparing them, exactly as asserted. The boundary's purpose is visible in what
it rules out: shelling `wt config approvals add` and scraping its output, which
*is* asking worktrunk for approval state.

**This is the one call the proposal-review should rule on.** It is flagged in
the session report rather than buried here.

*Alternative held in reserve:* if review rejects the subprocess, derive
`<host>/<owner>/<repo>` from `origin` and fall back to the repo root's absolute
path when there is no remote. Same spec, same scenarios; only the *Indeterminate
check* requirement loses its "worktrunk unavailable" trigger.

### 2. The guard sits at the actor-start boundary, so `reconcile` is covered

**The reconcile widening — read this before building.**

The assertion names `flywheel up` and `flywheel status`. It does not name
`flywheel reconcile`, and neither does the decision record. This design
nonetheless guards `reconcile`'s starts, and the reason is that the decision
states a *rule about starting actors*, not a rule about one subcommand: the
fleet "refuses to start actors into a repo whose gate they cannot run."

`reconcile` starts actors two ways — it calls `up` for the manifest's standing
rows, and it starts tracker-driven conductors of its own — and it is the pass
designed to run continuously (`--interval`). Guarding `up` alone would satisfy
the assertion's literal text while leaving the fleet's actual placement path
unguarded: the assertion's checkable claim would hold and the decision's rule
would not. That is precisely the shape of silence this intent was opened to
end.

The widening is in the direction the decision states and is recorded here, in
the spec, in the session report, and as a tracker item, so it is a visible
extension and not a silent one. If the conductor or the proposal-review rules
that `reconcile` belongs in its own assertion, drop the requirement *`flywheel
reconcile` is bound by the same precondition* and its three scenarios; nothing
else in the spec depends on it.

Mechanically: one function computes a repo's readiness, one per-pass cache
keyed on the resolved repo root keeps it to one evaluation per repo, and every
start site consults it. That shape is what makes the widening a call site
rather than a rewrite — and what makes dropping it a deletion rather than a
rework.

### 3. Group by repo, not by actor

Several actors share one repo in practice — the agentplot manifest's `dispatch`
row and its `conductors_cwd:` both resolve to `flywheel/main` (read from
`/Users/chuck/Code/github_agentplot/fleet.yaml`; the manifest is machine-local
and not in git). Reporting per actor would print the same four templates once
per actor. The spec requires one evaluation and one report per repo.

The repo's identity for caching is the worktrunk project config path's parent,
or the resolved working directory when there is no project config — not the git
toplevel, so that the cache key and the thing checked cannot disagree.

### 4. A no-hooks repo passes

If a repo defines no hook templates, there is no gate for an agent to be unable
to run. Refusing to start actors there would block fleets that use no worktrunk
hooks at all, for no gain. This is why the *no worktrunk project config* case
resolves to gate-ready rather than to the indeterminate branch — stated as its
own scenario so the two are not confused.

### 5. Exact string equality, unexpanded

worktrunk keys grants on template text, and the store holds `{{ branch | hash }}`
verbatim (measured). Comparing expanded text would need one grant per branch;
comparing loosely would report granted when worktrunk will refuse. Equality on
the raw string is both correct and the only thing that matches worktrunk's own
behaviour.

Note the standing caveat from `questions/hook-approvals-never-granted.md`:
"approvals key on template text, so moving a check between tables re-keys
nothing" is read from the head comment of `.config/wt.toml` and is **not
measured**. The spec states it as a requirement scenario; task 1 measures it
rather than inheriting it.

## Risks / Trade-offs

- **The store format is worktrunk's internal detail** → A format change breaks
  the check. It breaks *closed*: an unparseable or reshaped store yields no
  matches, so the fleet refuses starts and prints the remedy rather than
  starting agents into an ungated repo. The parse failure is reported as an
  indeterminate check, not as ungranted templates.
- **`wt config show --format json`'s schema is also internal** → Same
  fail-closed direction: a missing `project.identifier` is an indeterminate
  check. Decision 1 records the dependency-free alternative if this proves
  unstable.
- **A repo can be granted and still fail to merge** → The check proves the
  grants exist; it does not prove the hooks pass. That is what the gate itself
  is for, and it is out of scope.
- **This change's first act is to fail on its own repo** → Intended, and
  named by the assertion. Until `#33` is granted, `flywheel up` in the
  agentplot fleet will refuse to start actors into `agentplot/flywheel`. The
  build session must land this on a branch and **not** merge it, and the
  conductor must know that landing it before `#33` stops the fleet. Recorded
  in `tasks.md` as an explicit hand-off note rather than left to be discovered.
- **Grouping by project-config parent rather than git toplevel** → A repo whose
  actors sit in different worktrees of the same repository is evaluated once
  per worktree. That is correct, not wasteful: each worktree has its own
  `.config/wt.toml` content, and this bolt's own sequencing turns on exactly
  that (`bolt.md`, *Merge criteria*: a grant taken in `main` lists three
  templates, one taken in the construction worktree lists four).

## Open Questions

None that gate the build. The two live judgment calls — the `wt config show`
subprocess (decision 1) and the `reconcile` widening (decision 2) — are stated
as decisions with their reversal spelled out, not deferred as questions,
because leaving either open would change the specs and the task breakdown.
Both are flagged in the session report for the conductor and the
proposal-review.
