# skills/

Empty on purpose. The flywheel's skills are still under active edit in
`willdan-blueprints`, and moving a tree that is about to churn is a merge
problem. They land here when the split runs.

Seven arrive: the two loop skills — `inception` and `construction` — and the
five design-session type skills: `interactive`, `prototype`, `research`,
`review`, `writeback`. Each brings its `evals/` directory with it, which is
what `claude plugin eval` runs.

The `flywheel-` prefix drops on the way in. A plugin skill invokes as
`/<plugin>:<skill>`, so the plugin name supplies the prefix and the directory
name sheds it: `flywheel-inception` becomes `flywheel:inception`, living at
`skills/inception/`.
