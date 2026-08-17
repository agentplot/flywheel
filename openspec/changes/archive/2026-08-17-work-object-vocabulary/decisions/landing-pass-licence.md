# Decision: What the landing pass is licensed to touch

## Decision

The vocabulary landing pass holds two licences beyond plain prose
substitution. First, it rewrites the hero's two lines in
`site/index.html` — the walkthrough copy at the lines reading "One
intent agent holds the goal and its units" and "Units become bolts" at
`2e707e9` (`index.html:465`, `:470`) — into the settled vocabulary of
`work-object-names.md`, worded so the page states what is true: the
intent agent holds the goal and its assertions, and assertions are
released to bolts that each track many, dropping the 1:1 claim-to-bolt
mapping. The hero's settled design (#12) — geometry, palette, type, the
SVG — is untouched; the licence is for these two lines' words, and the
edit closes #21's content defect in the same pass rather than a
separate round. Second, the two session-type skill directories are
named for the claim: `skills/assertion-writing/` and
`skills/assertion-review/`, making the slash commands
`/flywheel:assertion-writing` and `/flywheel:assertion-review`, with
their inbound references and type labels renamed to match.

## Context

- Map: none — this repo ships no context map; `site/index.html` and
  `skills/**` are surfaces in `../intent.md`'s Map.
- Produced by: `../sessions/2026-08-12-naming-call/work-object-naming.html`
  — the page's two rider controls; the operator's word landed in the
  annotation round ("just fix the wording on the hero. say it as it
  is.", and the rename control), confirmed in the same round, recorded
  on item #13
  (<https://github.com/agentplot/flywheel/issues/13#issuecomment-5271266083>).
- The directory rename's blast radius is measured in #18's inventory at
  tree `2e707e9`, identifier family 3, which is the enumeration to copy:
  10 inbound files / 15 lines, plus the two never-applied
  `type:proposal-writing` / `type:proposal-review` labels. No eval pins
  either command string.

## Consequences

- The landing pass carries the hero edit and the directory rename as
  in-scope work; neither needs a further operator round.
- #21 is resolved by the hero edit — its fold is the conductor's, on
  the landed wording.
- The slash commands change: anything typing `/flywheel:proposal-writing`
  or `/flywheel:proposal-review` — operator muscle memory, saved
  invocations — retypes against the new names once the pass lands.
- `bin/flywheel-setup`'s `TYPE_KINDS` and `bin/flywheel-migrate`'s
  `TYPE_WORDS` move in the same commit as the label renames, per the
  code-before-labels ordering in `work-object-names.md`.
