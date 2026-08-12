# Assertion: The injected project context describes this repo as it is

- **Repo:** agentplot/flywheel
- **Item:** #25
- **Raised by:** the research session on agentplot/flywheel#18, at tree
  `2e707e9`.

## The claim

`openspec/config.yaml`'s `context` block states that the two flywheel
schemas "are not this repo's own workflow, and no project copy of them
lives here". The first half is false: this repo binds them. When this is
built, that paragraph says what is true — that agentplot/flywheel
publishes the flywheel schemas for consuming repos *and* binds them for
its own outer-loop work, resolving to the installed user copies rather
than a project copy, while its construction-side work runs under
`spec-driven`.

The correction is one paragraph. The rest of the `context` block — the
"what lands where" table and the repo's description — is not restated.

## Why

At `2e707e9` two live changes bound `schema: flywheel-intent`
(`work-object-vocabulary`, `gated-merge-guarantee`) and the archive bound
`bolt-quick`; this change makes a third `flywheel-intent` binding. The
prose is injected into every apply and continue run as project context,
so the false sentence reaches every agent that reads it. Re-measure the
binding list before landing — it grows as intents open.

## Boundaries

Whether this repo *should* bind the flywheel schemas for its own work is
not reopened; it does, and the prose follows the tree. The "what lands
where" enumeration in the same block is not audited here. The specs'
own drift about artifact sets is #26.
