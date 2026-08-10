# skills/

The flywheel's skills. A plugin skill invokes as `/<plugin>:<skill>`, so
the plugin name supplies the `flywheel` prefix and each directory sheds
it: what developed as `flywheel-inception` invokes here as
`flywheel:inception`, living at `skills/inception/`.

Seventeen directories:

- the two loop skills — `inception` (the design loop) and `construction`
  (the bolt loop);
- the thirteen session-type skills, one per type across both loops —
  design: `interactive`, `planning`, `research`, `prototype`,
  `writeback`, `handoff`; construction: `proposal-writing`,
  `proposal-review`, `spec-writing`, `build`, `test`, `code-review`,
  `human-code-review`;
- `fleet` — wraps `bin/flywheel`, the per-org fleet command;
- `_reference/` — the shared herdr/worktrunk invocation reference every
  skill points at rather than bundling its own copy.

Each skill that has an `evals/` directory brought it along. The suites
are in a legacy `evals.json` format that `claude plugin eval` does not
yet read — converting them to the runner's `case.yaml`/`prompt.md`
format is open work, as are suites for the nine skills that have none:
the seven construction types, `handoff`, and `fleet`. Both are tracked
in the source intent.
