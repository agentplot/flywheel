# How this eval set is run

`evals.json` is in the `skill-creator` schema. Fixtures live in `files/`
and are referenced from each eval's `files` list.

**The baseline is the previous version of this skill**, not an unloaded
skill. The current text is what shipped all three driver failures, so an
expectation that passes against it is measuring nothing this rewrite adds.
Snapshot the prior version before editing —
`git show <ref>:skills/inception/SKILL.md` — and point the
baseline run at the snapshot, per `skill-creator`'s improve mode. A
no-skill run may be kept as a floor; it is not the only baseline. Any
expectation that passes in both configurations is rewritten.

**The withheld arm cannot be made fully real, and that is recorded rather
than papered over.** `skill-creator`'s runner requires `--skill-path` and
has no flag for withholding a skill, so it loads this skill on every run.
Where an eval means to measure a steering document other than this skill,
that document is attached as a fixture and the prompt names it as the
executor's only guidance, and the first expectation is that the run did not
read or quote `SKILL.md` — checkable from the transcript. A run where that
expectation fails measures the skill and does not count.

A fixture that copies a shipped file can drift: re-copy it whenever the
original changes.

**The state-claim evals hand the executor the wrong move.** One fixture
carries a gate measurement inside a settled record, which a run without
the rule reports as current; another prompt supplies a line number, which
a run without the rule copies into the task line. Both are written so the
baseline can fail them: a prompt that merely asks for a task line would
pass in either configuration.

**Not yet run.** The eval executions — `skill-creator` over the skill,
including its description pass, and every eval in both configurations —
have not been performed. Each run is a subagent per eval per
configuration plus grading, which is a fleet operation and not this
change's build step. The set is written to be run; running it is
outstanding.
