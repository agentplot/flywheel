## MODIFIED Requirements

### Requirement: The page links to no file the repository does not yet hold

Every relative `href` and `src` in `site/index.html` SHALL resolve to a file
that exists in `site/`, so that `node scripts/check-site.mjs` reports no dead
reference.

Where the page points a reader at a deeper tour that a later unit will build,
it SHALL do so by absolute URL or by unlinked text — never by a relative link
to a file not yet on disk.

The Overview destination SHALL be reachable. `site/overview.html` now exists,
so that destination SHALL be the relative `overview.html`, and the stand-in
that stood in its place — the project README by absolute URL — SHALL be gone
from the topbar.

#### Scenario: The merge criterion passes on this change alone

- **WHEN** `node scripts/check-site.mjs` runs against a tree carrying this
  change and `overview.html` but no tour page
- **THEN** it reports every reference resolving, and exits 0

#### Scenario: The reader is never pointed at nothing

- **WHEN** a reader looks for the operator reference this page sheds
- **THEN** the page offers a destination that loads

#### Scenario: The Overview link is a relative reference

- **WHEN** the topbar's Overview link is read out of `site/index.html`
- **THEN** its `href` is `overview.html`
- **AND** no absolute README URL stands in for it
