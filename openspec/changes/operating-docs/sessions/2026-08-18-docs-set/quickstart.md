# Decision draft — the quickstart

Inherits #182 (closed on `intent/onboarding-first-run`, never worked).

## The decision

The quickstart is **one README section** (`## Quickstart`, directly
after `## Install`) in agentplot/flywheel, and the site's install panel
links to it the way it already links the install section ("Read this in
full in the README"). The README is canonical; the site excerpts and
links, and never carries its own copy of the command list.

It is the shortest **honest** path: every step below is one the
operator genuinely cannot skip today. Nothing is elided to look easy,
and nothing optional is included.

## What it assumes already exists

- Claude Code, herdr, and worktrunk installed and working.
- A GitHub org the operator admins (a personal account works the same
  way), and a GitHub App on it — `FLYWHEEL_GH_APP_ID`, `_KEY`, `_ORG`
  configured so `flywheel-token` can mint.
- **Not** Discord. The relay is a richer setup, pointed to from the end
  of the quickstart, never a step in it.

## The path

1. In Claude Code: `/plugin marketplace add agentplot/flywheel`, then
   `/plugin install flywheel@flywheel`.
2. Choose or create the org's tracker repo; run
   `flywheel-setup --org <org> --repo <tracker>` — labels, the org
   Project and its fields, idempotently.
3. Copy `template-fleet.yaml` (beside the fleet skill) to the org
   folder root as `fleet.yaml`; fill `tracker:`, `loops_cwd:`, the
   host, and the dispatch row.
4. Once per built repo: `wt config approvals add` in a terminal inside
   that repo — the merge gate's standing grant. `flywheel up` refuses
   to start work into an ungranted repo, so this cannot be deferred.
5. `herdr --session <org>`, then `flywheel up` — dispatch and the
   server come up; `flywheel status` shows the roster.
6. Tell dispatch one raw idea. Watch the tracker: dispatch files the
   intent milestone and its first items, the batch appears on the board
   at Backlog.

## Where it stops

The crank has turned once when **the first design session settles and
its report lands as a comment on a tracker item** — idea in, routed,
worked, evidence back on the bus. The quickstart ends there, on that
observable, with three pointers onward: the operator tour (what a
normal turn looks like from the outside), the fleet skill (multi-host,
parking, Discord relay), and releasing work to construction (the board
flip). Construction is deliberately **not** in the quickstart: it needs
a built repo, a bolt, and the merge gate, and a first-run user has none
of those stakes yet.

## Who writes into it

The same rule as any README claim: a construction session whose change
alters a step (a `flywheel-setup` flag, a fleet.yaml field, an install
path) updates the section in the same change — the quickstart is part
of the surface its spec verifies. No writeback session owns it; it is
operating instructions, not the design book.

## Consequences (queued items once the round closes)

- Draft the README quickstart section on this decision, and add the
  site install panel's link to it.
- The operator tour draft (`operator-tour.md` in this session) takes
  this path as its transcript source — the tour item is blocked by the
  quickstart draft existing.
