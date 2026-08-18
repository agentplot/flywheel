# Decision draft — flywheel's own design book

Inherits #183 (closed on `intent/onboarding-first-run`, never worked).
Closed on the second annotation round, 2026-08-18.

## The decision

**Flywheel's book lives in the org's book-carrying repo,
`agentplot/blueprints`, at `books/flywheel/`** — public, described as
"agentplot design books and the flywheel intent/bolt records". One
repo holds every agentplot system's book, with the shared tooling at
the root, rather than each repo carrying its own; the plugin repo
stays plugin content only, so its install cache never drags a book
along. It is exactly the `books/` convention the writeback skill
already wraps, so writeback sessions on flywheel's intents target it
with no bespoke rules.

**This is the standing state, verified in-repo 2026-08-18**: the
13-chapter book is at `agentplot/blueprints:books/flywheel/src/`, the
repo is public, this machine's fleet.yaml `books:` entry points at
`/Users/chuck/Code/github_agentplot/blueprints/main/books/flywheel`,
and a scan of the moved chapters found no client-private references
(willdan/client/system-name patterns, zero hits).

- **Why this intent and not `intent/machinery-self-desc`**: #183
  flagged the possible reassignment. The split that holds: **this
  intent settles the location and the write path** (a
  documentation-set question — the tour and quickstart need something
  citable); backfilling and correcting the book's *content* (the
  2026-08-17 gap audit's findings) is machinery self-description and
  stays with that intent.

Rejected in the rounds:

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
  is. Field notes and gap audits stay in the plugin repo's `design/`
  as working material; what they prove out graduates into chapters
  through writeback.

## Consequences (queued items once the round closes)

- Link the built book from the site and the README, so the quickstart
  and tour have something citable.
- Note to `intent/machinery-self-desc` (via the report): the content
  backfill named by the 2026-08-17 gap audit remains its work; the
  location is settled here.
