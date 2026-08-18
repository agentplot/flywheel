# Decision draft — what the flywheel page teaches a stranger, and in what order

Item #274 · intent/site-teaches-the-system · planning session 2026-08-18

## The reader this page is for

Someone who has installed nothing. They arrived from a link — a README, a
tweet, a search — and they will give the page one scroll before deciding
whether flywheel is for them. They do not yet hold the two-loop model, the
vocabulary (intent, bolt, gate), or any reason to care about either.

**Proposed: the home page addresses this stranger and nobody else.** The
returning operator already has the README, the skills, and the tracker; the
page's job is done for them. Everything on the home page is judged by one
test: does it move a stranger from "what is this" to "I see how it works and
whether I want it"?

## The page's job

Show the system working; never describe it at reference depth. The README is
the reference and already says everything twice as precisely — the page that
competes with it loses on both fronts. What the README cannot do is *show*:
one idea moving through the machinery, the rings turning, the human's hand on
the rim. That is the page's whole franchise.

## The teaching order

Five beats, in the order a stranger needs them. Each beat earns the next:

### 1. What it is, in one plain sentence — above the fold

The name, and one sentence a stranger can parse with no flywheel vocabulary,
framing what the thing *is*: **an AI-DLC harness** — roughly *"An AI-DLC
harness for Claude Code: teams of agents on two coupled loops, design and
construction, built on OpenSpec."* The identity is the harness, the loops and
the teams, grounded in OpenSpec; the gate is taught later, at beat 4, where
it can land as the answer to "what does this cost me". The current deck
("Intent falls inward until it is code…") is the poem, and it can stay — but
it teaches only after the model is held, so it rides beside a plain sentence,
never instead of one. The hero plate (the rings) stays as the identity and
the first picture of the mechanism; it is the *illustration* of beat 1, not
its text.

### 2. The problem — why one conversation fails

Before any mechanism: the pain. Design and construction answer to different
things; fused in one chat you design under build pressure or build against a
moving design. A stranger recognizes this failure from their own sessions —
this is the beat that makes them lean in. It exists today as "Why two loops"
and mostly needs to move up and shrink, not be rewritten.

### 3. The mechanism, walked — one idea, end to end

The core teach, and it is shown rather than described: one raw sentence
("the export button loses the filters") walked through dispatch → an intent →
a design session → a decision → the gate → a bolt → merged, with the
artifact each step leaves behind. This is the concept tour (#179): its
subject is **one idea's journey**, not the architecture. Architecture
diagrams (actors, write scopes, state machines) describe the machine from
outside; the journey teaches it from inside, and vocabulary lands as each
word arrives with the thing it names.

### 4. Your place in it — the gate, and how little it costs

What the human actually does: plans and diffs open in a browser, you
annotate or approve, one word releases a whole batch, and past the gate it
runs without you. This is the beat that answers the stranger's real
question — "what does this cost *me*?" — and it is the differentiator:
oversight priced at one approval per batch, not one question per step.

### 5. Install — two commands, last

By now they either want it or they don't. Two commands, the pointer to the
README for everything deeper, done.

## What leaves the home page

The actor table, the write-scope diagram, the bolt state machine, and the
"working on the flywheel itself" section are operator reference, not
stranger teaching. They move behind one link (an Overview / docs layer per
the operator's proposal on #181) or defer wholly to the README. The home
page keeps at most one architecture picture — the hero plate itself.

## Consequences (become items once this closes)

1. **#181's mock-ups take this order as their brief**: the few top-level
   sections are the five beats; current tab detail (actors, bolt states)
   moves under Overview. Nav must be visible without scrolling — beat 1's
   screen carries it.
2. **#179's tour concepts are beat 3**: each concept walks one idea end to
   end; a tour of the architecture is out of brief.
3. **The hero keeps the plate but gains the plain sentence**; the ratio
   cells ("1 : 6", "1 : 24") are beat-3 material and may move down or into
   the tour.

## Open questions for this round

- **Q1 — audience**: home page for the stranger only, operator content
  demoted to a link? (Proposed: yes.)
- **Q2 — where beat 3 lives**: the walked journey embedded on the home page
  (scrolling), or a separate tour page the home page opens? (Proposed:
  the home page carries a compact walk; #179's tour pages go deeper.)
- **Q3 — order of beats 2 and 3**: problem before mechanism (proposed), or
  lead with the walk and let the problem emerge from it?
