# How this eval set is run

`evals.json` is in the `skill-creator` schema. Fixtures live in `files/`
and are referenced from each eval's `files` list.

**The baseline is the previous version of this skill**, not an unloaded
skill. The current text is what shipped all three conductor failures, so an
expectation that passes against it is measuring nothing this rewrite adds.
Snapshot the prior version before editing —
`git show <ref>:skills/inception/SKILL.md` — and point the
baseline run at the snapshot, per `skill-creator`'s improve mode. A
no-skill run may be kept as a floor; it is not the only baseline. Any
expectation that passes in both configurations is rewritten.

**Evals 10 and 11 test the conductor profile body, not this skill.** The
profile-alone condition is the one all three failures were committed under,
and an eval that loads the skill alongside the profile cannot tell a
profile that works from a profile that is redundant.

**The withheld arm cannot be made fully real, and that is recorded rather
than papered over.** `skill-creator`'s runner requires `--skill-path`, has
no flag for withholding a skill, and has no concept of an agent profile at
all — so it will load this skill on every run, including these two. The
closest executable substitute is used instead, in two parts: the profile
under test is attached as a fixture
(`files/intent-conductor-profile.md`, a verbatim copy of
`agents/flywheel-intent-conductor.md`), and the prompt names it as
the executor's only steering document while carrying none of the skill's
guidance itself. The first expectation of each eval is that the run did not
read or quote `SKILL.md`, which is checkable from the transcript. A run
where that expectation fails measures the skill and does not count toward
the profile's coverage.

The fixture is a copy, so it can drift: re-copy the profile into
`files/` whenever the profile body changes.

**Evals 12 and 13 test the state-claim rule, and their prompts hand the
executor the wrong move.** Eval 12's fixture carries a gate measurement
inside a settled record, which a run without the rule reports as current;
eval 13's prompt supplies a line number, which a run without the rule
copies into the task line. Both are written so the baseline can fail them:
a prompt that merely asks for a task line would pass in either
configuration.

**Not yet run.** The eval executions — `skill-creator` over the skill,
including its description pass, and every eval in both configurations —
have not been performed. Each run is a subagent per eval per
configuration plus grading, which is a fleet operation and not this
change's build step. The set is written to be run; running it is
outstanding.
