# Decision draft — flywheel's own design book

Inherits #183 (closed on `intent/onboarding-first-run`, never worked).

## The current state (measured, this machine)

A 13-chapter draft book for flywheel already exists — outside this
repo, at the operator's private
`willdan-blueprints/main/books/flywheel` (STATUS: draft, ROLE:
process), mapped by this machine's `fleet.yaml` `books:` entry. This
repo's own `design/field-notes/2026-08-17-book-gap-audit.md` already
audits the tracker archive against those chapters. So the book exists
and is being used as the destination record — but it is private,
machine-local, and unciteable from anything public: the quickstart, the
tour, and the site cannot point at it, and a writeback session on a
flywheel intent has no in-repo target.

## The decision

**Flywheel's book lives in a new org repo, `agentplot/blueprints`, at
`books/flywheel/`** (operator's direction, folded from the first
annotation round). The org gets one book-carrying repo — the same
shape as willdan-blueprints: `books/<system>/` per system, the shared
tooling (`book-grab.js`, `preview.py`, `check-mermaid.mjs`,
`build-index.py`) at the root — rather than each repo carrying its
own. It is exactly the `books/` convention the writeback skill already
wraps, so writeback sessions on flywheel's intents target it with no
bespoke rules.

- **Why a separate repo and not `books/` inside agentplot/flywheel**:
  the plugin repo stays plugin content only — its install cache never
  drags a book along — and every future agentplot system's book has a
  home from day one instead of re-deciding per repo.
- **The wiring**: this machine's fleet.yaml `books:` entry repoints to
  the blueprints checkout; the site and README link to the built book.
- **Why this intent and not `intent/machinery-self-desc`**: #183
  flagged the possible reassignment. The split that holds: **this
  intent settles the location and the write path** (a
  documentation-set question — the tour and quickstart need something
  citable); backfilling and correcting the book's *content* (the gap
  audit's findings) is machinery self-description and stays with that
  intent.

Rejected in the round:

- **In-plugin-repo `books/flywheel/`** — mixes a book into a
  shippable plugin repo.
- **Leave it in willdan-blueprints** — the durable explanation of a
  public plugin stays in a private client repo; every public doc that
  needs it dead-ends.

## What writes into it, and when

The same contract as any consuming repo's book — nothing bespoke:

- **Writeback sessions on flywheel's own intents** are the writers,
  charged when an intent's decisions have closed and the chapters do
  not say so yet — destination voice, chapters rewritten in full, the
  book's gates green.
- The book never records that work happened; it records how the system
  is. Field notes and gap audits stay in `design/` as working material;
  what they prove out graduates into chapters through writeback.

## Consequences (queued items once the round closes)

- Create `agentplot/blueprints` seeded with the willdan-blueprints
  root tooling (`book-grab.js`, `preview.py`, `check-mermaid.mjs`,
  `build-index.py`, `books/CLAUDE.md`).
- Audit the willdan draft book for client-private content, then move
  it into `agentplot/blueprints:books/flywheel/`.
- Repoint this machine's fleet.yaml `books:` entry to the blueprints
  checkout; link the built book from the site and README.
- Note to `intent/machinery-self-desc` (via the report): the content
  backfill named by the 2026-08-17 gap audit remains its work; the
  location is settled here.
