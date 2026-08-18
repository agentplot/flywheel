# The rebased landing tree is red: the landing's two release conditions, and a guard that no longer exists

## Why

`bolt/matches-the-book` is green in isolation and **red the moment it is
rebased onto `main`** — which is the only tree the landing cares about.
The suite on this worktree's tip (`835c0e3`, the bolt branch already
rebased) reports 3 failures and 1 error over 497 tests. Two independent
builds arrived at the same boundary from different sides:

- `main` deleted `guard_route`, and a test that patches it **by name** to
  assert guard ORDER now raises `AttributeError` before it can assert
  anything;
- `main` gates the landing on the operator's milestone close
  (`landing_wanted` refuses while any unlanded item's `milestone_state`
  is `open`, commit `3f16377`), while this bolt added a second gate,
  `holding_cards` — no open `plan` card on the milestone. The
  `LandingHoldTest` fixtures predate `main`'s gate and leave the
  milestone open, so every hold assertion reads `not attempted` and the
  hold under test is never reached.

The second is not a fixture bug alone. Two gates both glossed as "the
operator releases the landing" is the thing to resolve, and the record
resolves it: **both stand, neither subsumes the other, and only one of
them is written down.** The card hold is specified
(`openspec/specs/flywheel-derived-backlog/spec.md`, "The landing is the
bolt's boundary, held by any open unit card"); the milestone-close
release exists only as code and a commit message — no requirement in
`openspec/specs/` states it. This change writes the missing requirement,
states how the two compose, and repairs the tests that the composition
and the removal left stale.

## What Changes

- **The milestone-close release becomes a written requirement.** The
  landing's existing precondition — the operator's close of the bolt
  milestone — is specified in `flywheel-construction-stages` beside the
  landing's other requirements, naming its interaction with `land="force"`
  as the code already implements it.
- **The composition of the two conditions is stated, not left implied.**
  Both release conditions stand. The card hold is asked first and is
  final; the milestone-close gate is one of the "existing preconditions"
  the card-hold requirement already defers to. `land="force"` passes the
  milestone-close gate and does **not** pass the card hold. No gate is
  removed and no landing becomes automatic where it was not.
- **`LandingHoldTest`'s fixtures carry the operator's close.** Its
  `merged()` items get `milestone_state="closed"`, as the fixtures in
  `MergeCloseTest` and the landing tests around line 2003 of
  `tests/test_bolt_loop.py` already do, so the card is once again the
  only thing declining the landing under test.
- **`CharterTest` asserts guard order against the guards that exist.**
  The watch tuple in
  `test_the_charter_guard_runs_after_topology_names_the_worktree` drops
  `guard_route`, which `main` removed, and asserts the order of the
  guards `guards()` actually calls.
- **The stale `guard_route` reference in the loop's own prose goes.** The
  comment in `_defer_predicate`'s neighbourhood ("the same field
  `guard_route` keys on") names a method that no longer exists; it is
  rewritten to name the derivation it meant.
- `sh scripts/test.sh` green on this worktree, which is `bolt/matches-the-book`
  as rebased onto `main`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `flywheel-construction-stages` — gains the requirement that the
  operator's milestone close releases the landing, and states how that
  condition composes with the open-unit-card hold.

## Impact

- `bin/_flywheel_bolt_loop.py` — `landing_wanted` and `holding_cards`
  keep their behavior; their prose is brought into line with the written
  requirement, and one stale comment reference is corrected.
- `tests/test_bolt_loop.py` — `LandingHoldTest` fixtures.
- `tests/test_derived_backlog.py` — `CharterTest` guard-order test.
- `openspec/specs/flywheel-construction-stages/spec.md` — one new
  requirement.
- No change to what the landing does once it runs, to expansion, to the
  defer predicate, or to the server's job filter.

## Sources, and what was read from disk

Read directly, in this worktree, at `835c0e3`:

- `bin/_flywheel_bolt_loop.py` — `landing_wanted`, whose comment reads
  "The landing is the operator's: their milestone close releases it.
  Every item merged and every card ruled is necessary, never sufficient";
  and `holding_cards`, whose docstring reads "Asked before
  `landing_wanted`, and blind to `land`."
- `openspec/specs/flywheel-derived-backlog/spec.md` — the requirement
  "The landing is the bolt's boundary, held by any open unit card",
  containing "Once no open card remains on the milestone, the landing
  SHALL proceed under its existing preconditions and gain no new ones
  from this requirement."
- `openspec/specs/flywheel-construction-stages/spec.md` — searched for a
  requirement stating the milestone-close gate; there is none. The only
  mention of `landing_wanted` is inside "A merge-closed item is still in
  flight until the bolt lands", and it is about counting `closed:merged`
  items, not about the milestone's state.
- `openspec/changes/archive/2026-08-17-the-landing-waits-for-the-cards/proposal.md`
  and `design.md` — both place the operator's milestone close explicitly
  out of scope: "This change leaves that exactly as it is and does not
  make the landing automatic where it was not: it neither adds the
  operator's close nor removes anything standing in for it."
- `tests/test_bolt_loop.py` (`LandingHoldTest`) and
  `tests/test_derived_backlog.py` (`CharterTest`), and the failing run of
  `sh scripts/test.sh`.
- `git show 3f16377`, whose message reads "The landing is the operator's:
  their milestone close releases it — landing_wanted refuses an open
  milestone".

**Relayed, not read.** The three book chapters that name the operator's
close as the release gesture —
`books/flywheel/src/construction-loop.md`,
`books/flywheel/src/bolt-planning.md`,
`books/flywheel/src/lifecycles.md` — are **not present in this repo**;
the book is the design loop's. Their wording reaches this change only
through the verbatim quotation in the archived proposal named above,
which was read from disk. Every claim this change makes about the book
is that quotation and nothing further.
