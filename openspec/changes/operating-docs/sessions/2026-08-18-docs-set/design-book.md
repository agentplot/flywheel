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

**Option A (recommended): adopt the book into agentplot/flywheel, at
`books/flywheel/`.** The plugin repo becomes a book-carrying repo
exactly like the repos it serves — the same `books/` convention its own
writeback skill wraps (`books/CLAUDE.md`, `preview.py --check`,
`check-mermaid.mjs`). `books/` joins `scripts/` in the never-shipped
tier: in the repo, never on the user's PATH, not plugin content. The
fleet.yaml `books:` entry repoints to the checkout; the site and README
link to the built book.

- **Why here and not `intent/machinery-self-desc`**: #183 flagged the
  possible reassignment. The split that holds: **this intent settles
  the location and the write path** (a documentation-set question —
  the tour and quickstart need something citable); backfilling and
  correcting the book's *content* (the gap audit's findings) is
  machinery self-description and stays with that intent.

Alternatives, for the annotation round:

- **B — leave it in willdan-blueprints**, write through the fleet
  mapping. Zero migration, but the durable explanation of a public
  plugin stays in a private client repo, and every public doc that
  needs it dead-ends.
- **C — fresh public book seeded chapter-by-chapter** from the draft.
  Right if the draft carries client context that cannot simply move;
  otherwise it is option A with extra steps.

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

- Audit the willdan draft for client-private content (gates option A
  vs C).
- Move (or seed) the book into `books/flywheel/`; repoint this
  machine's fleet.yaml `books:` entry; link it from the site and
  README.
- Note to `intent/machinery-self-desc` (via the report): the content
  backfill named by the 2026-08-17 gap audit remains its work; the
  location is settled here.
