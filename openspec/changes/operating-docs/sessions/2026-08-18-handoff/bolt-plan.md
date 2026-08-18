# Bolt plan — operating-docs handoff, 2026-08-18

Item #290, unit #291. The handoff set is #287 and #288 — the two
settled assertions open on `intent/operating-docs` with no parent batch
and no open blocker.

Both land in one repo (`agentplot/flywheel`) and in the same two files
(`README.md`, `site/index.html`), so they are one bolt rather than two.

## bolt/quickstart-and-book-link

- **type**: `bolt-quick` — the work is prose in two files whose claims
  are checkable by reading the repo they describe, so no independent
  proposal-review or adversarial code-review earns its cost. It is
  **not** `bolt-direct`: `bolt-direct` runs no verify stage, and this
  repo's merge gate cannot settle these assertions' correctness. The
  gate is three checks — `scripts/validate-manifests.sh`,
  `scripts/check-paths.mjs`, `scripts/check-site.mjs` — and none of them
  reads the README at all, nor follows an external URL. Nothing in the
  gate would catch a Quickstart step naming a flag `flywheel-setup` does
  not take, or a `blueprints` link pointing at a path that does not
  exist. The quickstart's whole claim is that it is the *shortest honest
  path*, and honesty here is exercised, not linted — so the verify stage
  is the load-bearing step of this bolt and the type must keep it.
  Plan mode is not taken on this bolt: the changes are small and the
  spec step is cheap.
- **landing**: merge — direct to `main` on `agentplot/flywheel`, as
  `bolt/records-and-elaborations` lands. No pull request: the repo has
  one writer and the gate is the review.
- **owner**: @afterthought — neither item carries an assignee, so this
  is read from `fleet.yaml`'s `operator:` for the org rather than from
  the items. Correct it in this round if it is wrong.
- **repos**: `agentplot/flywheel` — bolt branch
  `bolt/quickstart-and-book-link`. Both assertions touch `README.md` and
  `site/index.html`; no other repo is cut. `agentplot/blueprints` is
  *linked to*, never written by this bolt — the book already stands
  there, verified by the decision record.
- **assertions**:
  - #287 — `openspec/changes/operating-docs/decisions/quickstart.md` —
    the README carries a `## Quickstart` section after `## Install`, six
    steps from plugin install to the first design session's report on a
    tracker item, and the site's install panel links to it rather than
    carrying its own copy.
  - #288 — `openspec/changes/operating-docs/decisions/design-book-home.md`
    — the site and the README link flywheel's design book at
    `agentplot/blueprints` `books/flywheel/`.
- **sequencing**: #288 blocked by #287. Both edit the same two files in
  the same region — the README's install/quickstart area and the site's
  install panel — so building them concurrently is a merge conflict by
  construction, and #288's book link reads better placed against a
  Quickstart that already exists than bolted on beside it and moved
  later.
- **ADRs**: none. Both assertions are already carried by settled
  decision records in this intent; neither introduces an architectural
  choice the built repo has to record.

### Merge criteria to carry into `bolt.md`

- `devenv shell -- gates` green on the bolt branch as it would land —
  the same three checks `.config/wt.toml`'s `[pre-merge]` hooks and
  `.github/workflows/gates.yml` run.
- The verify stage exercises the Quickstart's six steps against this
  repo: every command named exists (`bin/flywheel-setup`, `bin/flywheel`,
  `skills/fleet/template-fleet.yaml`), every flag named is one the
  command takes, and every environment variable named is one the code
  reads. The step that ends the path — the first design session's report
  landing on a tracker item — is the stated stopping point and is
  checked as prose, not run.
- Every link added resolves: the site's link into the README anchor, and
  the two links to `agentplot/blueprints` `books/flywheel/`.

## Held back

Nothing from the handoff set. For the record, the other open items on
`intent/operating-docs` are not withheld work — they are unsettled
design: #289 (the operator tour's interactive mockup) is `state:queued`
and its content is still to be drafted, and #277/#292 are the intent's
elaborations. The operator tour hands off in a later wave.
