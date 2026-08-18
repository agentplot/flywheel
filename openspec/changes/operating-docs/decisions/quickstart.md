# Decision — the quickstart

Closed 2026-08-18, plannotator round on
`../sessions/2026-08-18-docs-set/quickstart.md` (item #275; inherits
#182). No corrections were raised.

**The quickstart is one README section (`## Quickstart`, after
`## Install`) in agentplot/flywheel; the site's install panel links to
it and never carries its own copy.** It is the shortest honest path
from install to one turn of the design loop's crank:

1. `/plugin marketplace add agentplot/flywheel` +
   `/plugin install flywheel@flywheel`
2. `flywheel-setup --org <org> --repo <tracker>`
3. `template-fleet.yaml` → org-root `fleet.yaml`, filled
4. `wt config approvals add` per built repo
5. `herdr --session <org>`, `flywheel up`
6. one raw idea to dispatch; watch the tracker and the board

It assumes Claude Code, herdr, worktrunk, an org and its GitHub App
(`FLYWHEEL_GH_APP_ID`/`_KEY`/`_ORG`); it does not assume Discord. It
stops when the first design session's report lands on a tracker item,
with pointers onward to the tour, the fleet skill, and the board flip.
Construction is not in it.

Maintained like any README claim: a change that alters a step updates
the section in the same change. Full rationale in the session draft.
