## ADDED Requirements

### Requirement: A charter with no readable merge criteria is not landable

The landing verifies the bolt's merge criteria by running them, so a
charter that states none gives it nothing to verify. The bolt loop SHALL
refuse the landing when the bolt's `bolt.md` states no merge criteria —
no such section in the charter's own region, a section whose body is
empty, or no `bolt.md` at all. The refusal SHALL come ahead of any
landing session and ahead of anything reaching the main branch: nothing
is verified, no item is closed, and no item is upgraded to
`closed:done`.

The refusal SHALL name the charter's path and say that its merge criteria
could not be read, so the operator's next act is obvious. A landing
refused this way SHALL be legible as refused wherever the run reports its
landing, and SHALL NOT read as a landing that was never reached for.

**A forced landing does not pass this refusal.** Forcing is a claim about
the operator's release — that the milestone close has been made or is
being made by the same hand — and it says nothing about whether the
charter states criteria. An empty criteria list is not a green landing
under any flag.

This is a refusal within the landing, not a third release condition: it
is asked after the open-unit-card hold and the milestone-close condition
have been satisfied, alongside the landing's existing refusals — a live
operator wait on any item, and a bolt branch that carries no work beyond
its cut point. Unlike a release condition it cannot be answered on the
board; the charter is what has to change.

#### Scenario: a charter that states no merge criteria

- **WHEN** every release condition is satisfied and the bolt's `bolt.md`
  states no merge criteria in the charter's own region
- **THEN** no landing session runs, nothing reaches the main branch, no
  item is closed or upgraded, and the run's landing line names the
  charter and says its merge criteria could not be read

#### Scenario: an empty merge criteria section

- **WHEN** the charter carries the merge criteria heading with no body
  under it
- **THEN** the landing is refused exactly as for a charter that carries
  no such section at all

#### Scenario: a forced landing over an unreadable charter

- **WHEN** a landing is forced on a bolt whose charter states no merge
  criteria
- **THEN** it is refused exactly as an automatic landing would be

#### Scenario: a charter that states its criteria

- **WHEN** the charter carries a merge criteria section with a body
- **THEN** the landing proceeds under its existing preconditions and
  gains nothing from this requirement
