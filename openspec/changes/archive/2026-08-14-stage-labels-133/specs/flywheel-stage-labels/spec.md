## MODIFIED Requirements

### Requirement: An item carries exactly one `stage:*` label, and one writer enforces it for both loops

Writing any `stage:*` label SHALL remove every other `stage:*` label from
that item, so an item's stage names its **leading edge**. This SHALL hold
for every name in the set, whichever loop writes it: the bolt loop's four,
the intent loop's two, and the operator's `stage:done` when a session writes
it on the operator's word.

The rule SHALL have exactly one implementation, living beside the vocabulary
itself, and **every writer SHALL write through it — including the session
that writes `stage:done` from a pane**. A sweep implemented inside one loop
would be a rule about that loop rather than about the set; a sweep copied by
hand into a session's instructions is the same defect in a slower form,
because a copy states the rule for the cases its author had in mind and the
set is what it is for all of them.

Concretely, the one implementation SHALL be reachable from a pane without
importing the loops' internals, so that a session told an item is done runs
the same sweep the loops run rather than a two-label edit naming one
predecessor to remove. Naming a single predecessor is wrong wherever the
item's actual predecessor is a different stage — an item picked up by a
later session while at `stage:collected` keeps that label deliberately, and
a flip that removes only `stage:in-session` leaves it carrying
`stage:collected` and `stage:done` at once, which is the state this
requirement says is unreachable. Any prose that shows a session how to make
the flip SHALL show that one call, and SHALL NOT spell out a hand-built
label edit for it to copy.

**The sweep SHALL run whenever the item's stage set is not already exactly
the target**, and not only on a transition the writer believes is new. An
item that already carries the target and also carries another stage SHALL
end the write carrying the target alone. Skipping the sweep for an item
already at the target assumes every stage label on the tracker was written
through this implementation, and the operator adding a label by hand on
GitHub — which this capability permits — is exactly the case that assumption
does not cover.

The write SHALL be idempotent and SHALL report whether it wrote: an item
already at the target stage **and carrying no other** is left alone and
nothing is recorded, which is what keeps a second cycle over an unchanged
tracker writing nothing.

A label surface that answers "does this item carry X" from a cached snapshot
SHALL NOT report a label removed earlier in the same cycle, or the sweep
would re-remove what it has already taken off. **Symmetrically, it SHALL NOT
report a label added earlier in the cycle once its snapshot has been
re-read**: a re-read is the loop learning what the world now says, and a
cache of the writer's own earlier additions surviving it makes the surface
answer from a state that no longer exists — which sends a removal for a
label the pane has already taken off. Both directions of the cache SHALL be
invalidated together, whenever the snapshot behind them is replaced.

Nothing in this rule SHALL touch a `closed:*` label. `stage:merged` and
`closed:merged` are written at the same boundary and are not the same act.

#### Scenario: A design item reaches the end of its session

- **WHEN** the intent loop has written `stage:in-session`, the operator has
  flipped `stage:done`, and the loop then collects the item
- **THEN** the item carries `stage:collected` and no other `stage:*` label,
  and a reader asking for its leading edge is answered `stage:collected`

#### Scenario: A stage is written twice

- **WHEN** a loop writes the stage an item already carries, and the item
  carries no other stage
- **THEN** no label is added or removed and the cycle records no write

#### Scenario: An item already at the target carries a second stage

- **WHEN** a stage write runs on an item that already carries the target
  stage and also carries another `stage:*` label
- **THEN** the other label is removed and the item ends carrying the target
  alone, rather than the write returning early on the strength of the
  target already being present

#### Scenario: The pane writes the operator's flip

- **WHEN** a design session is told by the operator that an item is done
- **THEN** it makes the flip through the one implementation of this rule,
  and the item ends carrying `stage:done` and no other `stage:*` label —
  whatever stage it carried before

#### Scenario: An item picked up at `stage:collected` is flipped done

- **WHEN** a later session carries an item that is already at
  `stage:collected`, and the operator flips it done
- **THEN** the item ends carrying `stage:done` alone, with `stage:collected`
  removed

#### Scenario: The rule is stated once and copied nowhere

- **WHEN** the skills, profiles and references a session reads are searched
  for how to write `stage:done`
- **THEN** each points at the one call, and none of them spells out a
  hand-built label edit naming which predecessor to remove

#### Scenario: A cached label surface outlives its snapshot

- **WHEN** a cycle writes a stage label, then re-reads its snapshot, then
  asks the same surface whether the item carries that label
- **THEN** the answer comes from the re-read snapshot, so a label the pane
  removed in between is not reported as present and is not removed a second
  time

#### Scenario: The closure labels are untouched by a stage write

- **WHEN** any stage write runs on an item carrying a `closed:*` label
- **THEN** that `closed:*` label is unchanged
