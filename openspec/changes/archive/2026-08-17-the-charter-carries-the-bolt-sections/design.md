## Context

See `proposal.md` — Why. What the tree bears out at HEAD, read from the
files named. A build session has already applied the charter half, so
part of this shape is on disk:

- `schemas/bolt-default/schema.yaml` declares one artifact, `bolt` →
  `bolt.md`, with `template: bolt.md`. Its instruction says "**Output:**
  bolt.md with exactly these sections", lists Scope, Sources, Repos,
  Merge criteria, says "EXACTLY these four sections, and nothing else",
  and then adds "What follows those four sections is not narrative and is
  not yours to compose: one `# Unit: <slug>` section per unit …". All
  four members carry that paragraph — `grep -l` finds it in
  `bolt-default`, `bolt-quick`, `bolt-adversarial` and `bolt-direct` —
  and each declares exactly one artifact.
- `schemas/bolt-default/templates/bolt.md` is `# Bolt: [name]` plus those
  four headings and a `Landing: merge` line — the four sections and
  nothing else, already the shape the book asks for. Only that member's
  template shows the `Landing:` line, which is why the work order asks
  for it rather than leaving it to the template.
- `bin/_flywheel_bolt_loop.py`:
  - `BoltParams.description` exists and carries the milestone's
    description, empty under `--fixture`.
  - `guard_scaffold` names `CHARTER_SECTIONS` — `## Scope`, `## Sources`,
    `## Repos`, `## Merge criteria` — in its order, asks for the
    `Landing:` line under every schema, and puts the description in the
    order as the charter's stated source. Then: "BELOW them: if the
    milestone carries any `unit`-labeled issue, copy the LOWEST-NUMBERED
    one's body into bolt.md verbatim, under a `# Unit: <slug>` heading …
    Either way the bolt's own `## Merge criteria` stays the FIRST such
    heading in the file". Its post-settle check calls `merge_criteria()`
    and fails with a reason when it is empty.
  - `guard_charter` ("0.6") appends `# Unit: <slug>` sections to
    `bolt.md`, comparing `UNIT_HEADING` matches in the file at HEAD
    against the milestone's `unit`-labeled issues, then `git add --` /
    `git commit --` by pathspec. It already reads HEAD rather than the
    working tree to survive a torn commit, already leaves a section it
    finds in the working tree alone and re-runs only the commit, and
    already skips itself under `--dry-run` and under `FixtureTracker`.
  - `merge_criteria()` matches `^##\s+Merge criteria\s*$` with a
    lookahead of `^#{1,2}\s`; its docstring says the `#` is there because
    `guard_charter` appends `# Unit:` headings. It searches the whole
    file, so the first such section anywhere in it wins.
  - `landing_mode()` searches `merge_criteria() or ""` for
    `Landing:\s*(merge|pr)` and returns `"merge"` on no match.
  - `land_stage` carries three refusals before it drives anything: a live
    `needs-operator` wait, an empty `merge_criteria()`, and
    `branch_advanced` — with the comment stating why all three sit there
    rather than beside the release conditions.
- `bin/_flywheel_inbox.py`, `PlanCard.slug`, parses the card title as
  `^\s*(?:Unit|Plan|Bolt):\s*([a-z0-9][a-z0-9-]*)\s*$` — so a slug is
  already a safe file name, and `units/<slug>.md` needs no sanitising.
- `tests/test_bolt_loop.py`: `LandingTest.program` assigns
  `program.merge_criteria = lambda: criteria` on every landing test; and
  `ReadingTest`'s one real-reader test reads
  `openspec/changes/loop-server/bolt.md`, which no longer exists outside
  `openspec/changes/archive/`, so it takes its `skipTest` branch.

What is left is entirely the record's shape: one artifact where the book
says two, a work order that still asks for a unit document inside the
charter, a guard that appends into it, and a reader that searches the
whole file.

Constraints the shape has to respect:

- The loop is stateless and re-derives from the tracker and the tree. No
  stored flag.
- Every guard keeps its dry-cycle property: a pass with nothing to do
  writes nothing and reports nothing.
- Durable prose in git outranks the mutable tracker state it came from —
  `guard_charter`'s own rule — so nothing rewrites a record a session or
  a hand already wrote.

## Goals / Non-Goals

**Goals:**

- The record splits the way the book states: the charter is the bolt's,
  the unit file is the approval's.
- The scaffold session is told what a charter is, in the template's own
  section names, and is given the milestone description to write it from.
- The loop verifies the charter rather than trusting a settle.
- A charter the landing cannot read stops the landing, loudly.
- The records already on disk in the older shape stay valid to move
  forward from without any of them being rewritten.

**Non-Goals:**

- Editing any `schemas/*/templates/bolt.md`. The template already carries
  the four sections and nothing else.
- The content of any particular bolt's merge criteria — the planner's
  summary and the operator's to annotate.
- Repairing the two `bolt.md` files that carry a `# Unit:` section.
- The two sibling failure modes in this unit: a change directory with no
  `bolt.md`, and a unit title that parses no slug.

## Decisions

**The unit's file is named by the card's parsed slug, under `units/`.**
`PlanCard.slug` already yields `[a-z0-9][a-z0-9-]*`, which is both the
book's `<slug>` and a safe file name, and it is the same value
`guard_charter` uses for its heading today. The alternative — naming by
issue number — would survive an unparseable title, but the book names the
file by slug and the sibling change
`an-unparseable-unit-title-says-so` is where a title that parses no slug
gets its answer. A card whose title parses no slug is that change's
subject and is left alone here.

**`guard_charter`'s idempotency test moves from headings-at-HEAD to
files-at-HEAD.** It keeps the property that made it correct: the question
is what the record carries **committed**, never what the working tree
holds, so an interrupted commit is retried rather than read as done. What
changes is only what is inspected — `git ls-tree` over `units/` instead
of `UNIT_HEADING` matches in a blob. The torn-write repair keeps its
shape: if the file is on disk but not at HEAD, leave the content and
re-run the add and the commit.

**Records in the older shape self-heal on the unit half and refuse on the
charter half.** Because the test is "does `units/<slug>.md` exist at
HEAD", a record whose unit prose lives in `bolt.md` simply has no unit
file, so the guard writes one — the same code path, no migration step,
no special case. The stale `# Unit:` section in `bolt.md` is left where it
is. Rewriting it would break the durable-prose rule, and deleting prose
the loop no longer reads buys nothing. What it must not do is masquerade
as the charter, which the region rule below prevents.

**The merge-criteria reader takes the charter's region, not the whole
file.** The region is the file up to the first `# Unit:` heading, and the
whole file when there is none. The existing `^#{1,2}\s` lookahead stops
the *section* at such a heading but still lets a `## Merge criteria`
appearing **inside** a unit's document be found first when the charter
above has none — precisely the state both stale records are in. Bounding
the region first makes "the bolt's criteria" mean the charter's, and
makes the absent case genuinely absent so the guard's check and the
landing's refusal both fire on it. Once the scaffold stops writing unit
prose into `bolt.md`, this matters only for records already in the older
shape — which is exactly why it is not enough to fix the writer.

**The post-settle check calls `merge_criteria()`, not a new parser.** So
"the guard passed" and "the landing can read it" cannot disagree. The
failure this change exists to close is two readers disagreeing about what
a charter says; adding a third definition of the question would be the
same mistake in a new place.

**The description is carried on `BoltParams`, not re-fetched.**
`build_loop` already holds it, so this is one hop and keeps the guard
free of tracker calls. Having `guard_scaffold` call `tracker.milestone()`
itself would cost an API round trip every pass for a value already read,
and would behave differently under `FixtureTracker`, whose `milestone()`
returns a stub with no description. Under a fixture the field is simply
empty — the "milestone carries no description" path the spec covers.

**The work order names the sections; the schema stays the authority for
their content.** The order lists the four headings and the `Landing:`
line and points the session at
`openspec instructions bolt --change <slug>` for the rest. Inlining the
instruction would put a second copy in the loop program, and the two
would drift the first time a schema version moves.

**The landing refusal lives with the landing's other two refusals, not
with the release conditions.** The release conditions answer "may this
bolt land yet" — they hold, and the operator's gesture releases them. A
charter with no criteria answers "is there anything to verify"; nothing
on the board fixes it, so it fails rather than holds, in the same shape
as `branch_advanced`'s "nothing to land, nothing closed". Placing it
there also gives it the forced-landing behaviour for free: those refusals
sit inside `land_stage`, which a force reaches.

**The charter half already on disk is verified, not rebuilt.**
`BoltParams.description`, the work order's `CHARTER_SECTIONS` paragraph,
the post-settle check and `land_stage`'s charter refusal are already as
the specs here state. The build's job for them is to confirm the file
bears the claim out and to leave them alone; the specs carry them into
`openspec/specs/` at archive, which is the only reason they appear as
requirements at all.

## Risks / Trade-offs

- **A bolt mid-flight with a sectionless charter cannot land** —
  `bolt/loop-boundaries`, this bolt, is one, and `bolt/matches-the-book`
  is the other. The refusal is already in the tree; bounding the reader
  to the charter's region makes it fire on a record whose unit prose
  carries a `## Merge criteria` of its own. → Intended: a silent wrong
  landing becomes a legible refusal naming the file. The way past it is
  to write the four sections into that charter, a one-file edit.
- **`guard_charter` writing files rather than appending changes what a
  half-applied change looks like.** A record could end with the unit file
  written and the stale `# Unit:` section still in `bolt.md`, so the same
  prose sits twice. → Accepted and bounded: only the unit file is read by
  anything, and only for the two records in the older shape.
- **The scaffold session could still write four empty headings and
  settle.** The check tests the merge-criteria section's body, so an empty
  one fails; an empty scope or sources heading would pass. → Accepted:
  the check exists to protect the readers, and only the merge-criteria
  section has readers. Judging a scope paragraph is the annotation
  round's job, not a guard's.
- **Four schema files change together.** A member left behind would
  declare one artifact while the loop writes two. → The spec requires all
  four, and the task list treats them as one task.
- **`merge_criteria()` becomes load-bearing in three places** — the
  landing mode, the scaffold check, and the landing refusal. → It was
  already load-bearing through `landing_mode()` with no test reaching it
  from `land_stage`; the tests here exercise it unstubbed.
