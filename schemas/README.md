# schemas/

The five OpenSpec workflow schemas the loops track their work under:

- `flywheel-intent` — one design thread: decisions, questions,
  sessions, typed tasks, and the intent loop's shape in
  `apply.instruction`.
- `bolt-direct` · `bolt-default` · `bolt-quick` · `bolt-adversarial` —
  one construction
  iteration each; the member picked at creation IS the bolt type, and
  what differs between them is the `loop:` block — the type as a named
  config — and `apply.instruction`, the review steps the loop schedules.
  `bolt-direct` is the no-verify type: its `loop:` block declares the
  stage set `spec, build, merge, land`, so its items go from
  `stage:built` to `stage:merged` and never carry `stage:verified`. The
  repo's own merge gate is not a function of the type and runs
  unweakened on all four.
  (`bolt-no-spec` is
  deliberately not a schema: plan mode replaces the spec step, and is
  `bolt-quick`'s option alone.)

The `loop:` block is **read**: `bin/_flywheel_bolt_loop.py`'s
`read_schema_config` parses it into a `LoopConfig`, and the loop runs the
strategy and the stage set it finds there — which is what makes
`bolt-direct` a named config rather than a branch in the loop's code. It
is invisible to `openspec`, whose workflow-schema validator strips
unknown top-level keys rather than rejecting or keeping them — which is
why the programs that read it read `schema.yaml` themselves, and why
`openspec schema fork` erases it from the copy it writes. Each schema's
own comment carries the measurement.

Install them machine-wide with `bin/install-schemas`, which copies them
to `~/.local/share/openspec/schemas/` where `openspec` resolves them by
name for any repo. A repo's own `openspec/schemas/` copy shadows the
user copy when an in-place edit loop is wanted.
