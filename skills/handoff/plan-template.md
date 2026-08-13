# Bolt plan — <intent-slug> handoff, <YYYY-MM-DD>

One section per bolt — a handoff cuts more than one when assertions
land in unrelated repos or warrant different bolt types.

## bolt/<slug>

- **type**: bolt-quick | bolt-default | bolt-deep — <why this type,
  from what the assertions touch, never from their count>
- **landing**: merge | pr — how the bolt reaches main; carried into
  bolt.md's Merge criteria as its Landing line
- **owner**: @<login> — whose word settles the bolt's decisions, read
  from the items' assignee
- **repos**: <the built repos this bolt cuts branches in>
- **assertions**:
  - #<item> — `assertions/<slug>.md` — <the claim, one line>
- **sequencing**: <blocked-by relations to wire between the items, or
  "none">
- **ADRs**: <architecture decision records the bolt conductor writes
  directly: repo, decision, sources — or "none">

## Held back

- #<item> — <why it is not ready to hand off; queued back, never
  quietly dropped>
