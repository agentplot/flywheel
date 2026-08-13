# schemas/

The four OpenSpec workflow schemas the loops track their work under:

- `flywheel-intent` — one design thread: decisions, questions,
  assertions, sessions, typed tasks, and the intent loop's shape in
  `apply.instruction`.
- `bolt-default` · `bolt-quick` · `bolt-adversarial` — one construction
  iteration each; the member picked at creation IS the bolt type, and
  what differs between them is the `loop:` block — the type as a named
  config — and `apply.instruction`, the review steps the loop schedules.
  (`bolt-no-spec` is
  deliberately not a schema: plan mode replaces the spec step, and is
  `bolt-quick`'s option alone.)

The `loop:` block is a stub in all three: declared, nothing built. It is
also invisible to `openspec`, whose workflow-schema validator strips
unknown top-level keys rather than rejecting or keeping them — so the
programs that come to read it read `schema.yaml` themselves, and
`openspec schema fork` erases it from the copy it writes. Each schema's
own comment carries the measurement.

Install them machine-wide with `bin/install-schemas`, which copies them
to `~/.local/share/openspec/schemas/` where `openspec` resolves them by
name for any repo. A repo's own `openspec/schemas/` copy shadows the
user copy when an in-place edit loop is wanted.
