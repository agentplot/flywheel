# schemas/

The four OpenSpec workflow schemas the loops track their work under:

- `flywheel-intent` — one design thread: decisions, questions,
  assertions, sessions, typed tasks, and the intent loop's shape in
  `apply.instruction`.
- `bolt-default` · `bolt-quick` · `bolt-deep` — one construction
  iteration each; the member picked at creation IS the review depth, and
  only `apply.instruction` differs between them. (`bolt-no-spec` is
  deliberately not a schema: plan mode replaces the spec step.)

Install them machine-wide with `bin/install-schemas`, which copies them
to `~/.local/share/openspec/schemas/` where `openspec` resolves them by
name for any repo. A repo's own `openspec/schemas/` copy shadows the
user copy when an in-place edit loop is wanted.
