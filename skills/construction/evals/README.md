# How this eval set is run

`evals.json` is in the `skill-creator` schema. Fixtures live in `files/`
and are referenced from each eval's `files` list.

**The baseline is the previous version of this skill**, not an unloaded
skill — the current text is what carried both unqualified "wait on the
operator" sentences. Snapshot the prior version before editing
(`git show <ref>:skills/construction/SKILL.md`) and point
the baseline run at the snapshot. A no-skill run may be kept as a floor; it
is not the only baseline. Any expectation that passes in both
configurations is rewritten.

**Eval 7 tests the bolt conductor profile body, not this skill**, and the
withheld arm cannot be made fully real. `skill-creator`'s runner requires
`--skill-path`, has no flag for withholding a skill, and has no concept of
an agent profile at all, so it will load this skill on every run. The
closest executable substitute is used in two parts: the profile under test
is attached as a fixture (`files/bolt-conductor-profile.md`, a verbatim
copy of `agents/flywheel-bolt-conductor.md`), and the prompt names
it as the executor's only steering document while carrying none of the
skill's guidance itself. The first expectation is that the run did not read
or quote `SKILL.md`, which is checkable from the transcript; a run where
that fails measures the skill and does not count toward the profile's
coverage.

The fixture is a copy, so it can drift: re-copy the profile into `files/`
whenever the profile body changes.

**Evals 8, 9 and 10 have adversarial prompts on purpose.** Eval 8 asks for
the next review round, eval 9 states a per-proposal three-read process as
the process to follow, and eval 10 hands over a line number. A run that
follows the prompt fails the rule, which is what makes the baseline able to
fail: a neutrally worded version of any of the three would pass with or
without the skill. The negative expectations carry the grading —
"no third round dispatched", "no fifteen-review plan", "no line number in
the output".

**Not yet run.** The eval executions — `skill-creator` over the skill,
including its description pass, and every eval in both configurations —
have not been performed. Each run is a subagent per eval per
configuration plus grading, which is a fleet operation and not this
change's build step. The set is written to be run; running it is
outstanding.
