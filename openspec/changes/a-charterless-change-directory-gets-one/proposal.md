## Why

`guard_scaffold`'s docstring states its idempotency in one sentence —
"Idempotent: the directory existing is the whole test" — and the code
says the same: `if self.params.change_dir.exists(): return None`. That
test was written when the directory and the charter were born in the same
breath, so it reads a directory as a charter.

They are not the same thing, and the tree already knows it. The guard's
own post-settle check exists precisely because a settle is not a charter:
it drives the session, and then reads `merge_criteria()` and returns a
failure when the charter says nothing. But that check "runs only on the
path where a session was just driven" — its own words — and the directory
exists the moment `openspec new change` returns. So a scaffold session
that creates the change and settles without writing `bolt.md` fails the
check on the pass that drove it, and then passes every pass after it:
`change_dir.exists()` is true, the guard returns `None` above the check,
and the loop walks a charterless record through expansion, the stages, and
every merge. `tests/test_bolt_loop.py` asserts this outright —
`test_a_present_change_directory_returns_before_the_check` makes a bare
directory and asserts "no bolt.md here, and the guard still passes".

The next reader of that charter is `land_stage`, whose refusal names the
three ways the criteria come back empty — "No section, an empty body, or
no bolt.md at all — the reader answers `""` to all three". So the failure
is caught, once, at the last boundary: after every item in the bolt has
been specced, built, verified and merged, with the operator's milestone
close already given. `books/flywheel/src/construction-loop.md` names that
close as the landing's release — "waiting for a board tap would hold a
released landing on the very work it just demanded" — and the charter the
landing needs is exactly the thing no guard was willing to write.

Nor could the guard simply stop returning early. Its order's invocation is
`/opsx:new <slug>`, and `/opsx:new`'s own guardrail is "If a change with
that name already exists, suggest using `/opsx:continue` instead" — an
order a session cannot obey on a directory that is already there. The
charterless case is not a missing branch; it is a case with no order
written for it.

`books/flywheel/src/lifecycles.md` states the birth this closes: the bolt's
change is "the charter `bolt.md` plus one `units/<slug>.md` per approved
unit", the charter born "at scaffold, from the milestone's description".
Between that birth and the landing that reads it, no stage writes a
charter — so a record that reaches the stages without one never gains one.

## What Changes

- **The scaffold guard's test becomes the charter, not the directory.** A
  change directory that exists without `bolt.md` is this guard's case: it
  drives a session that writes the charter into the change that is already
  there, and applies the same post-settle check the created-from-nothing
  path applies. A charterless record never reaches the stages.
- **The order for an existing change continues it rather than creating
  it.** The invocation is the one that adds the missing artifact to a
  change that exists; the bolt-level content of the order — the four
  sections, the `Landing:` line, the milestone description as the stated
  source, and no unit's plan document — is one text both paths carry, so
  the two orders cannot drift apart.
- **A `bolt.md` that is present is never this guard's business.** A
  charter that exists but reads back no criteria keeps its committed prose
  and reaches the landing's refusal, exactly as today. The guard writes a
  charter only where there is none to overwrite.
- **The dry-cycle property holds on both paths.** A record whose charter is
  present drives no session, writes nothing and records no action; under
  `--dry-run` each path reports what it would do and launches nothing.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `flywheel-derived-backlog`: the charter requirement gains the case it
  never named — the charter is written wherever it is absent, not assumed
  present because its directory is — and states the boundary that keeps
  the guard off committed prose.

## Impact

- `bin/_flywheel_bolt_loop.py` — `guard_scaffold`: its early return, its
  invocation, and the order text the two paths share. `merge_criteria()`,
  `landing_mode()` and `land_stage`'s charter refusal are read as they
  stand and are not changed by this.
- `tests/test_bolt_loop.py` — `ScaffoldCharterTest`, whose
  `test_a_present_change_directory_returns_before_the_check` asserts the
  behaviour this change removes, and `SettlingScaffold`, which models the
  session that writes a charter and needs a sibling that finds the
  directory already there.
- **Out of scope**: a unit title that parses no slug
  (`an-unparseable-unit-title-says-so`) and the defer predicate's reading
  of a closed unit (`the-defer-predicate-reads-a-closed-unit`), both
  siblings in this unit; and rewriting a charter that exists, which the
  record's own rule forbids and the landing's refusal already names.
