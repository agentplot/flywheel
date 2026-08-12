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
| hook **events** | exactly ten, enumerated by `wt hook --help`: `pre-`/`post-` × `switch`, `start`, `commit`, `merge`, `remove` |
| `wt hook show --format json` | one record per configured command: `name`, `type`, `source`, `template`, `needs_approval` |
| `source` | `"project"` or `"user"`; user hooks carry `needs_approval: false` — the help's table says approval is *Required* for project hooks and *Not required* for user hooks |
| broken project config | `wt hook show --format json` exits **1** with empty stdout — it does not report zero hooks |
| no project config | exits 0, emitting only `source: "user"` records |

The build session re-runs these; see `tasks.md`, task 1.

### The hook-template grammar

The row above measures which hook **events** exist. It does not measure which
**value shapes** an event accepts, and an earlier revision of this design
generalised from the one shape this repo happens to use — a named table. That
was wrong, and it was the root of a false green: a repo whose hooks are written
in any other shape read as "no hooks configured" and resolved gate-ready.

Measured directly against `wt 5fba0bd`, in isolated fixtures under a relocated
`HOME` so the operator's store was never touched. The project-hook grammar is:

```
<event> = String | Table<name → String> | Array<String | Table<name → String>>
```

The binary states it itself. Given `pre-merge = [["echo a"]]` it refuses to load
the config with:

```
invalid type: sequence, expected a command string "cargo build" or a named table { build = "cargo build" }
```

Every accepted shape, and what `wt hook show --format json` returns for it:

| fixture | shape | records |
|---|---|---|
| `pre-merge = "echo bare"` | bare string | 1, `name: null` |
| `[pre-merge]` + two keys | named table | 2, named |
| `pre-merge = { gamma = "…" }` | inline table | 1, named |
| `pre-merge = ["echo one", "echo two"]` | array of strings | 2, `name: null` |
| `pre-merge = ["echo a", { b = "echo b" }]` | mixed array | 2, one anonymous one named |
| two `[[pre-merge]]` blocks | pipeline | one record per key across all blocks |

`[[event]]` blocks are TOML's array-of-tables spelling of the Array-of-Table
branch, which is why they need no separate grammar rule. They are the form
`wt hook --help` documents under *Hook forms*, and `wt --yes hook pre-merge`
runs them in block order — measured, not inferred.

One trap worth recording, because the first fixture written here fell in it: a
`[[event]]` block's keys are **command names**, not metadata. A block written
`name = "delta"` / `command = "echo delta"` is not a step called `delta` — it is
two commands, one called `name` running `delta` and one called `command`
running `echo delta`, and worktrunk enumerates both. Any hand-written parser has
to know that. This is precisely why the check asks worktrunk instead.

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

### 1. Worktrunk is the authority on its own configuration; the store is the authority on grants

This is the conductor's ruling, drawn once in
`openspec/changes/merge-gate-remedy/bolt.md` under *Where `wt` is the authority,
and where it is not*, and read from disk at this revision. #36 hit the line
twice — at the project identifier and at the hook-template grammar — so the
bolt drew it rather than leaving each call to be re-argued.

**From worktrunk, read-only:** the project identifier, the project config's
location, and the enumeration of configured hooks with their template text —
`wt config show --format json -C <path>` for the first two,
`wt hook show --format json -C <path>` for the third, taking `template` from
each record whose `source` is `"project"`.

**From the approvals store, ours to read and compare:** whether each of those
templates is granted. Parsed with `tomllib`, compared with exact string
equality. `wt hook show`'s `needs_approval` field is approval state and is
exactly what the assertion forbids sourcing from worktrunk — it is ignored.

*Why not re-derive either by hand?* Both proved to have non-obvious branches
that a hand-written version gets wrong silently. The identifier: a repo with no
remote keys on its **absolute path**, not on any `github.com/...` form. The
grammar: five accepted shapes, one of which (`[[event]]` blocks) treats its keys
as command names — measured above, and the trap the first fixture here fell
into. Re-deriving either is the reimplementation of `wt` that #36's own item
body disclaims, and it goes stale silently the day worktrunk changes.

*Why this does not cross the assertion's boundary.* The assertion forbids
invoking `wt` **to determine approval state**, and forbids writing the store.
Neither call returns approval state that this check consumes: `wt config show`
returns none at all (measured — its `user.config.projects` is `{}`), and
`wt hook show`'s one approval field is discarded. The approval determination
remains a comparison against the store, exactly as asserted. The boundary's
purpose is visible in what it still rules out: shelling `wt config approvals
add` and scraping its output, or trusting `needs_approval` — both of which
*are* asking worktrunk for approval state.

*What the enumeration must not swallow.* `wt hook show --format json` exits **1**
with empty stdout when the project config cannot be loaded (measured). Treating
that as "no hooks" would resolve a repo with an unloadable gate config to
gate-ready — a false green. The exit code is load-bearing, not incidental.

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

### 4. A no-project-hooks repo passes; an unreadable one does not

If a repo resolves no project hook, there is no gate for an agent to be unable
to run. Refusing to start actors there would block fleets that use no worktrunk
hooks at all, for no gain. So a repo with no project config, and a repo whose
config carries only user-level hooks, both resolve gate-ready.

The neighbouring case resolves the other way, and the distinction is the whole
point: a project config worktrunk **cannot load** is indeterminate, not
gate-ready. Both present as "the enumeration returned nothing", and only the
exit code tells them apart. Three separate scenarios in the spec keep them from
collapsing into each other.

### 5. Exact string equality, unexpanded

worktrunk keys grants on template text, and the store holds `{{ branch | hash }}`
verbatim (measured). Comparing expanded text would need one grant per branch;
comparing loosely would report granted when worktrunk will refuse. Equality on
the raw string is both correct and the only thing that matches worktrunk's own
behaviour.

The corollary — that moving a granted template between hook events preserves
its grant — is now measured rather than inherited from the head comment of
`.config/wt.toml`. `bolt.md` records the run: granted under `[pre-commit]` the
hook runs; the same text under `[pre-merge]` with the store untouched, it still
runs; and the negative control, one added trailing space, breaks it. That
upgrades what `questions/hook-approvals-never-granted.md` marks provisional, and
it is why the spec's scenario on the table move states a measured fact.

### 6. `status` reports what it can inspect, and names what it skipped

`status` runs on one host and can only read config that is present on it.
Another host's repo is not inspectable from here, and an actor whose working
directory does not resolve on this machine has no config to read. So the gate
rows cover this host's resolvable repos and no more — anything else would be a
claim about a gate the command never looked at, which is the one thing this
capability is built to prevent.

That narrowing creates its own hazard, which is why the spec pairs it with a
requirement rather than leaving it implicit: the per-actor rows and the gate
rows then disagree about how many repos exist. A reader seeing four actor rows
and two gate rows, with nothing saying why, reads the two green gate rows as
covering the fleet. Every skipped actor is therefore accounted for by a stated
reason — placed on another host, or its directory absent here. A gate report
that quietly covers less than it appears to is this intent's own disease, and it
is not allowed to reappear in the report itself.

## Risks / Trade-offs

- **The store format is worktrunk's internal detail** → A format change breaks
  the check. It breaks *closed*: an unparseable or reshaped store yields no
  matches, so the fleet refuses starts and prints the remedy rather than
  starting agents into an ungated repo. The parse failure is reported as an
  indeterminate check, not as ungranted templates.
- **Both worktrunk JSON schemas are internal too** → Same fail-closed
  direction: a missing `project.identifier`, a non-zero exit, or records without
  a `template` field are an indeterminate check, never gate-ready. The
  dependency this accepts is deliberate — decision 1 records why re-deriving
  either fact by hand proved worse, and both failure modes are measured rather
  than assumed.
- **The grammar could grow a sixth shape** → This is the risk that already bit
  once, when a definition was generalised from the single shape this repo uses.
  Sourcing templates from worktrunk's own enumeration is what makes a new shape
  a non-event: a shape worktrunk resolves is a record it emits, and the check
  reads records. A hand-written parser would silently under-report it as a
  gate-ready repo.
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

None that gate the build. The two calls that were live when this change was
first written are both settled: reading worktrunk for its own configuration is
the conductor's ruling in `bolt.md` (decision 1), and the `reconcile` widening
(decision 2) stands. Neither is deferred.

One thing is deliberately left unmeasured, and it is safe to leave: whether
worktrunk's grammar will grow a shape beyond the five measured here. The check
does not depend on the answer, because it reads worktrunk's enumeration rather
than the grammar — see the last risk above.
