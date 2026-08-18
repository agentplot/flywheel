## Context

See `proposal.md` — Why. The current state, read from disk at writing
time:

- `bin/_flywheel_bolt_loop.py`, `guard_scaffold` (docstring "0 —
  scaffold-if-missing") builds the work order that writes `bolt.md`. Its
  only precondition is `self.params.change_dir.exists()`, and its only
  post-check is that same test. The order's body names one thing to
  write: the lowest-numbered `unit`-labeled issue's body under a
  `# Unit: <slug>` heading, "otherwise write bolt.md from what the
  milestone and its items say".
- `BoltParams` carries no milestone description. `bin/flywheel-bolt-loop`,
  `build_loop`, reads `description = (milestone or {}).get("description", "")`
  and passes it to `plan_mode_declared` alone; it never reaches
  `BoltParams`, so no guard can see it.
- `merge_criteria()` searches `^##\s+Merge criteria\s*$` with a lookahead
  of `^#{1,2}\s`, so a `# Unit:` heading correctly ends the section — the
  ordering fix `guard_charter` relies on is already in place. It returns
  `""` when the record is absent or the heading never matches.
- `landing_mode()` searches `merge_criteria() or ""` for
  `Landing:\s*(merge|pr)` and returns `"merge"` on no match. An empty
  charter and a charter that says `Landing: merge` are the same value.
- `land_stage` has two refusals before it drives anything: a live
  `needs-operator` wait on any item, and `branch_advanced`. It reads
  `merge_criteria()` only indirectly, through `landing_mode()`.
- `tests/test_bolt_loop.py`, `LandingTest.program` assigns
  `program.merge_criteria = lambda: criteria` on every landing test, so
  no test today reaches the real reader from `land_stage`.
  `ReadingTest.test_the_merge_criteria_section_is_read_from_the_record_on_disk`
  reads the archived `loop-server` charter and skips when absent.

Constraints the shape has to respect:

- The loop is stateless and re-derives from the tracker and the tree.
  Nothing here may introduce a stored flag.
- A guard must keep its dry-cycle property: a pass with nothing to do
  writes nothing and reports nothing.
- Committed prose in the charter outranks mutable tracker state
  (`guard_charter`'s own rule), so nothing may rewrite a charter section a
  session or a hand already wrote.

## Goals / Non-Goals

**Goals:**

- The scaffold session is told what a charter is, in the schema
  template's own section names, and is given the milestone description to
  write it from.
- The loop verifies the charter rather than trusting a settle.
- A charter the landing cannot read stops the landing, loudly.

**Non-Goals:**

- Repairing the two sectionless charters already committed. Named in the
  proposal's Impact; a guard that rewrote them would contradict the
  durable-prose rule.
- Editing any `schemas/*/templates/bolt.md`. The template already names
  the sections; the bolt plan's "Left out" says so explicitly.
- The content of any particular bolt's merge criteria. That is the
  planner's summary and the operator's to annotate.
- The two sibling failure modes in this same unit — a change directory
  with no `bolt.md`, and a unit title that parses no slug.

## Decisions

**The description is carried on `BoltParams`, not re-fetched.**
`build_loop` already holds it. Adding a field is one hop and keeps the
guard free of tracker calls; the alternative — having `guard_scaffold`
call `tracker.milestone()` itself — costs an API round trip on every pass
for a value the entry point already read, and would fail differently
under `FixtureTracker`, whose `milestone()` returns a stub with no
description. Under a fixture the field is simply empty, which is the
"milestone carries no description" path the spec already covers.

**The work order names the sections; the template stays the authority for
their content.** The order lists the four section headings and the
`Landing:` line and points the session at
`openspec instructions bolt --change <slug>` for the rest, rather than
inlining the template. Inlining would put a second copy of the template
in the loop program, and the two would drift the first time a schema
version moves.

**The post-settle check is the reader, not a new parser.** The guard
calls `merge_criteria()` — the same function the landing reads through —
so "the guard passed" and "the landing can read it" cannot disagree. A
separate regex in the guard would be a second definition of the same
question, and the failure this change exists to close is precisely two
readers disagreeing about what a charter says.

**The landing refusal lives with the landing's other two refusals, not
with the release conditions.** The release conditions (open unit card,
milestone close) answer "may this bolt land yet"; they hold, and the
operator's gesture releases them. A charter with no criteria answers
"is there anything to verify"; nothing the operator does on the board
fixes it, so it fails rather than holds — the same shape as
`branch_advanced`'s "nothing to land, nothing closed". Placing it there
also gives it the forced-landing behaviour the spec asks for for free:
those refusals are evaluated inside `land_stage`, which a force reaches.

**Checking the scaffold's output does not make `guard_scaffold`
non-idempotent.** The check runs on the path where the guard just drove a
session. A pass that finds the directory already present returns before
it, exactly as today — so the dry-cycle property is untouched, and a
charter that is missing its sections on a later pass is caught by the
landing refusal rather than by a guard that would have to rewrite
committed prose to fix it.

## Risks / Trade-offs

- **A bolt already mid-flight with a sectionless charter now cannot
  land.** `bolt/loop-boundaries` — this bolt — is one. → This is the
  intended behaviour: it converts a silent wrong landing into a legible
  refusal naming the file. The way past it is to write the sections into
  the charter, which is a one-file edit the operator or a session makes
  directly.
- **The scaffold session could still write four empty headings and
  settle.** The check tests the merge-criteria section's body, so an
  empty one fails; an all-heading-no-content scope or sources section
  would pass. → Accepted: the check exists to protect the two readers,
  and only the merge-criteria section has readers. Judging the prose
  quality of a scope paragraph is the annotation round's job, not a
  guard's.
- **The order now carries the milestone description into a prompt.** A
  long description makes a long work order. → Bounded by what the planner
  writes: the milestone description is the bolt summary — the delivery in
  three sentences, the unit sequence, the price.
- **`merge_criteria()` used as a gate means its regex is now
  load-bearing in two places.** → It already was, through `landing_mode()`;
  this makes the dependency visible and adds tests that exercise it from
  `land_stage` rather than stubbing it.
