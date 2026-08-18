## Context

See proposal.md — Why. The state that shapes this design, read from disk
in this worktree at `835c0e3` (`bolt/matches-the-book` already rebased
onto `main`):

- `sh scripts/test.sh` reports 3 failures and 1 error over 497 tests.
- `bin/_flywheel_bolt_loop.py` already implements **both** release
  conditions and already orders them correctly: `run` calls
  `holding_cards` first and returns on a hold, then calls
  `landing_wanted`, whose milestone-state test is bypassed by
  `land == "force"`. Nothing about the shipped behavior is wrong.
- What is wrong is written down in two places: a test that names a
  method `main` deleted, and a fixture set that predates `main`'s gate.
  And one thing is not written down at all: no requirement in
  `openspec/specs/` states the milestone-close gate.

## Goals / Non-Goals

**Goals:**

- Close the spec gap that let two gates be built independently: the
  milestone-close release becomes a requirement, and the composition of
  the two conditions is stated where a future change will read it.
- Repair the two stale tests so the suite is green on the tree that
  would actually land.
- Leave the loop's runtime behavior unchanged.

**Non-Goals:**

- Changing what the landing does once it runs, or changing expansion,
  the defer predicate, or the server's job filter.
- Rewriting `holding_cards` or `landing_wanted`. Their behavior is the
  behavior this change specifies; only prose and comments move.
- Reconciling the book itself. The book is the design loop's, is not
  present in this repo, and this change does not touch it.

## Decisions

**Both release conditions stand; neither is removed.** The item that
charged this change asked which of the two survives. The record answers
it, and the answer is "both":

- `openspec/specs/flywheel-derived-backlog/spec.md`, in the requirement
  "The landing is the bolt's boundary, held by any open unit card",
  says the landing then "SHALL proceed under its existing preconditions
  and gain no new ones from this requirement". That sentence is written
  as an *addition* to whatever else gates the landing — it neither
  claims nor implies exclusivity.
- `openspec/changes/archive/2026-08-17-the-landing-waits-for-the-cards/proposal.md`
  and its `design.md` put the operator's close explicitly out of scope
  and say the change "neither adds the operator's close nor removes
  anything standing in for it". The card hold was never offered as a
  replacement.
- `bin/_flywheel_bolt_loop.py`'s `landing_wanted` states the intent of
  the older gate in one line: "The landing is the operator's: their
  milestone close releases it. Every item merged and every card ruled is
  necessary, never sufficient." That sentence already names *both*
  conditions and calls each insufficient alone.

*Alternative considered — collapse them, keeping only the card hold.*
Rejected: it would make the landing automatic the moment the last card
is ruled and the last item merges, which is exactly what `3f16377` was
written to prevent, and it contradicts the three book chapters quoted in
the archived proposal.

*Alternative considered — collapse them, keeping only the milestone
close.* Rejected: an operator who closes the milestone while an unruled
card sits on it would land a bolt that is still being planned, and the
distinct, card-numbered report line that
`the-landing-waits-for-the-cards` built would have nothing to say.

**The requirement lands in `flywheel-construction-stages`, not
`flywheel-derived-backlog`.** The card hold is a statement about the
*backlog* — cards, expansion, what is still being planned — and lives
where the rest of the card lifecycle does. The milestone-close release
is a statement about the *landing stage*, and `flywheel-construction-stages`
already holds the landing's other requirements and already names
`landing_wanted`. The composition statement rides with the newer, weaker
requirement rather than being pushed into the older one, so the existing
`flywheel-derived-backlog` text is not disturbed.

*Alternative considered — a MODIFIED delta on the card-hold requirement.*
Rejected: MODIFIED with partial content loses detail at archive time, and
the card-hold requirement's behavior does not change. This change adds a
concern beside it; ADDED is the right operation.

**The fixture repair, not a production change, is what turns
`LandingHoldTest` green.** The three failures are all one cause: the
fixtures leave `milestone_state` at its `"open"` default, so
`landing_wanted` refuses before `holding_cards` is consulted and the
hold under test is never exercised. Setting `milestone_state="closed"`
on `LandingHoldTest.merged` puts the fixture at the state its own
docstring already claims — "the landing is otherwise wanted, so anything
that declines it here is the hold and nothing else". The pattern is
already in this file: the fixtures near `tests/test_bolt_loop.py`'s
`MergeCloseTest` and the landing tests that build items with
`milestone_state="closed"` do exactly this, one of them with the comment
"the operator's close released the landing".

`test_a_hold_is_reported_while_released_work_is_still_in_flight` builds
its own snapshot rather than calling `at_the_landing`, and asserts
`landing_wanted` is **False** for a different reason — released work
still in flight. It passes today and must keep passing; the released-work
test comes before the milestone-state test in `landing_wanted`, so the
fixture change does not disturb it either way.

**`CharterTest` asserts the guard order it exists to assert, over the
guards that exist.** The test watches a tuple of guard names and asserts
only `seen[:4]`. `guard_route` is in that tuple and `main` removed it, so
`getattr` raises before any assertion runs. The repair is to watch the
guards `guards()` actually calls — `guard_expand`, `guard_scaffold`,
`guard_topology`, `guard_charter`, `guard_flip_consume`, `guard_stages` —
and keep the `seen[:4]` assertion, which is the proposition the test was
written for: the charter guard runs after topology has named the
worktree, because otherwise it commits into the main worktree with the
suite green.

*Alternative considered — delete `guard_route` from the tuple and stop
there.* That alone turns the error green, but leaves the tuple as a list
nobody maintains. Watching exactly the called guards makes the next
removal fail loudly at the tuple rather than silently in the assertion.

**One adjacent comment is corrected in the same commit.** A comment in
`bin/_flywheel_bolt_loop.py`'s defer predicate reads "the same field
`guard_route` keys on", naming a method that no longer exists. It is
prose about a removed thing inside the scope this change already touches;
correcting it is work, not a finding.

## Risks / Trade-offs

- **[The new requirement over-specifies a `force` bypass that was never
  deliberate.]** → The bypass is in `landing_wanted` and is explained in
  its own comment as "for the operator or the server resuming a run that
  died between the last merge and the landing". The requirement states it
  in those terms and nothing wider, and pins the asymmetry with the card
  hold in a scenario, so a later change that wants to remove it has to
  say so.
- **[The book's wording is relayed, not read.]** → The three chapters are
  not in this repo. Everything this change asserts about the book is the
  verbatim quotation in the archived proposal, and proposal.md says so
  explicitly. If the book's current text disagrees, the design loop owns
  that reconciliation and the spec written here is what it would amend.
- **[The fixture change hides a real regression.]** → It cannot hide the
  milestone-close gate itself: the new requirement's scenarios pin that
  gate directly, and the tasks add coverage for an open milestone
  declining an automatic landing rather than relying on `LandingHoldTest`
  to have covered it by accident.
- **[The bolt branch drifts from `main` again before the landing.]** →
  The verification that counts is `sh scripts/test.sh` on this worktree,
  which is the bolt branch as rebased onto `main`. The tasks name that,
  not a green run in isolation.
