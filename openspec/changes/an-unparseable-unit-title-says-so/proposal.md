## Why

`guard_charter` writes one `units/<slug>.md` file per approved unit, named
by the slug the card's title carries. When the title carries no slug, the
guard drops the unit without a word:

```python
slug = inbox.PlanCard(number=item.number, title=item.title).slug
if not slug or f"{slug}.md" in sealed:
    continue
```

`PlanCard.slug` matches `^\s*(?:Unit|Plan|Bolt):\s*([a-z0-9][a-z0-9-]*)\s*$`
and answers `None` for anything else — a title with a capital letter, an
underscore, a space inside the name, a trailing period, or no `Unit:`
prefix at all. A card the operator approved then expands into a unit, its
items are born, its work is specced, built, verified and merged — and the
one artifact that makes the approval durable prose in git is never
written. Nothing says so. The guard's own comment says the case "is the
subject of a sibling change and is left alone here"; this is that change.

The silence is what the failure costs. `books/flywheel/src/construction-loop.md`
states the rule the guard breaks: "The loop pauses — never guesses — when
judgment runs out ... A paused bolt states its reason in the run record and
waits; the operator reads it in the run report." Skipping the unit is a
guess — the guess that a card whose title does not parse is a card that
does not matter — and it is made where nobody can see it. `guard_charter`
appends only the writes it made, so a pass that dropped a unit and a pass
that had nothing to write are the same pass in the report: no action, a
clean dry cycle.

The consequence surfaces at the far end, if at all.
`books/flywheel/src/observation.md` says facts "originate in the record and
nowhere else", and the record holds no fact about the dropped unit. The
landing verifies merge criteria, not unit files, so the bolt can land with
its record carrying no document for an approval the operator made — and
the next planning run reads a record that never says a unit existed.

## What Changes

- **A unit title that parses no slug halts the cycle with its reason.**
  The guard stops treating an unnameable unit as nothing to do. It returns
  a reason string — the pause every other guard's failure uses — so the
  cycle halts, the reason reaches the run record, and the run report shows
  it. The loop never guesses which unit the operator meant.
- **The reason names what a person needs to fix it**: every offending unit
  on the milestone in item order, each by number and by its title verbatim,
  and what a unit title must carry to name a file. One pause reports every
  unnameable unit on the milestone, not the first one.
- **The nameable units of the same pass are still written.** A card whose
  title parses is written and committed exactly as today; the pause follows
  the pass's writes. One misnamed card does not hold another approval's
  durable prose hostage, and the guard keeps writing only what is missing.
  Where the pass also failed a commit, that failure is the reason returned
  — it names a torn record — and the unnameable unit is reported on the
  next pass, both states being sticky until a hand clears them.
- **The pause is reported wherever the guard reports**, `--dry-run`
  included: a dry run over a milestone carrying an unnameable unit says the
  bolt would pause and why, and halts, because a dry run that reported
  "nothing to write" over a dropped unit would be the silence this change
  closes. Under a fixture tracker — which writes no tree — the reason is
  still returned, because reporting is a read of the tracker, not a write.
- **The parse itself is unchanged.** `PlanCard.slug` stays the one place a
  unit title is parsed; this change adds a reader of its answer, never a
  second parser.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `flywheel-derived-backlog`: the unit-artifact requirement gains the case
  it never named — a unit whose title parses no slug — and states that the
  loop pauses with a reason naming it rather than passing over it.

## Impact

- `bin/_flywheel_bolt_loop.py` — `guard_charter`: the unit scan, the
  `--dry-run` and fixture-tracker branches, and the reason it returns.
  `guards()` and `cycle()` already turn a returned reason into
  `result.halted`, and `run()` already notes it to the ledger; those are
  read as they stand and are not changed.
- `bin/_flywheel_inbox.py` — `PlanCard.slug` is read, not changed.
- `tests/test_derived_backlog.py` — `CharterTest`, its `unit_item` helper
  (which builds `Unit: <slug>` titles and needs a sibling that does not),
  and `FakeGit`.
- **Out of scope**: a unit whose body is empty, which today is logged and
  skipped; two unit cards whose titles parse to the same slug, where the
  second is skipped as already-sealed; and any change to what makes a title
  parseable. All three are recorded as findings, not fixed here.
