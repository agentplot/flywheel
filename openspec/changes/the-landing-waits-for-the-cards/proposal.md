## Why

Under bolt-of-units a milestone carries several unit cards, and the book
makes the landing the bolt's boundary rather than a unit's: "the landing
to main runs once — after every merged item awaits it, no unit card on
the milestone is still open" (`books/flywheel/src/bolt-planning.md`,
"Board approval and expansion"), "the landing holds while any unit card
on the milestone is still open — the bolt lands once, when its units are
done" (`books/flywheel/src/construction-loop.md`, "Stages"), and "the
landing runs once for the bolt … and the loop closes the units
`closed:done` after it" (`books/flywheel/src/lifecycles.md`, "The plan
card and its bolt").

Two of those three writes are in the tree and neither is in the record.
`Bolt.run`'s tail in `bin/_flywheel_bolt_loop.py` already collects the
milestone's open `plan` cards and returns before the landing when it
finds any — the code `planner-owns-the-milestone` left behind — and
`close_unit_parents` already closes every `unit` batch on the milestone.
No requirement under `openspec/specs/` states either: a grep for the
hold across the specs finds nothing, and `flywheel-release-unit-parent`
still speaks of "that release's unit parent", singular, from the shape
where a card was a whole bolt. Behaviour that only the code knows is
behaviour the next change removes by accident.

One live defect rides along. The hold writes a log line and a ledger
note but leaves `RunReport.landing` at its default `"not attempted"`,
and `bin/flywheel-bolt-loop` prints that string and puts it in its
`--json`. An operator reading a run cannot tell "this bolt is waiting on
your ruling of card #231" from "there was nothing to land" — the one
report line that exists to carry the answer says neither.

## What Changes

- The landing is stated as the **bolt's** boundary: one landing per
  `bolt/<slug>` milestone, however many units it carries, and a unit
  expanded later does not buy a second one.
- **An open unit card on the milestone holds the landing.** Any open
  `plan` card whose milestone is this bolt's — unapproved at Backlog,
  approved but not yet expanded, or stale — holds it, ahead of the
  landing's expectation gate and its session. Ruling the card is the
  operator's way past the hold: approving it (which expands it into a
  unit) or closing it. A card on another milestone, or on none, holds
  nothing.
- **A held landing says so.** The run report's landing line reports the
  hold and names the holding cards, in place of the default "not
  attempted"; the run record keeps the note it writes today.
- **The landing closes every unit on the milestone**, not "the release's
  unit parent": each open `unit` batch on the bolt's milestone, plus a
  handoff parent reached through a landed item's parentage, ends
  `closed:done` with the landing SHA in its closing comment. No
  sub-issue is touched by those closes.
- No change to what the landing does once it runs: the merge criteria,
  the mode, the upgrade of each assertion from `closed:merged` to
  `closed:done`, and the two refusals ahead of it are exactly as they
  are.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `flywheel-derived-backlog`: gains "The landing is the bolt's boundary,
  and an open unit card holds it" — the card's last act, after filing,
  approval and expansion, which this capability already covers end to
  end.
- `flywheel-release-unit-parent`: "A landed bolt's unit parent is
  closed, and stops being a job" is restated over a milestone carrying
  several units, so the close at the landing reaches all of them.

## Impact

- `bin/_flywheel_bolt_loop.py` — `Bolt.run`'s tail, where the `planned`
  block holds the landing and returns the report unchanged; and
  `close_unit_parents`, whose behaviour already covers several units
  while its docstring still says "the release's unit parent".
- `bin/flywheel-bolt-loop` — prints `landing: {report.landing}` and
  carries the same string in its `--json`; it needs no change once the
  report line is written, and the held wording is what it will print.
- `tests/test_bolt_loop.py` — nothing exercises the hold today, and
  `LandingTest.with_unit` builds exactly one unit on the milestone.
- `openspec/specs/flywheel-derived-backlog/spec.md` and
  `openspec/specs/flywheel-release-unit-parent/spec.md`.
- **Out of scope, and a finding rather than a gap this change fills**:
  all three chapters name a *third* release condition — "The landing is
  the operator's: their milestone close releases it"
  (`books/flywheel/src/construction-loop.md`, "Stages"), "and the
  operator closes the milestone. The close is the release gesture"
  (`books/flywheel/src/bolt-planning.md`), "released by the operator's
  milestone close" (`books/flywheel/src/lifecycles.md`). The assertion
  this change derives from names only the two conditions above, and
  nothing in the tree or the record gates the landing on the milestone's
  state. This change leaves that exactly as it is and does not make the
  landing automatic where it was not: it neither adds the operator's
  close nor removes anything standing in for it.
