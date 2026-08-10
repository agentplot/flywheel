# Evals for `flywheel:writeback`

Two kinds of eval live here, and they test different artifacts.

**Type-skill evals (1, 2)** run with `SKILL.md` loaded. Their baseline is a
no-skill run, because this skill has no previous version yet. The next
change to edit this skill has one, and uses it — the no-skill arm is a
property of the skill's state, not a standing choice.

**Profile-alone evals (3, 4)** test
`agents/flywheel-design-session.md`, not this skill. The profile
body travels as the fixture `files/profile-flywheel-design-session.md` and
the prompt withholds every skill, because the claim under test is that a
session reading only its profile still refuses the machinery edit and still
starts unblocked work. An eval that loaded the type skill could not tell a
profile that works from a profile that is redundant. Their baseline is a
run with neither the profile nor the skill.

Eval 4 and eval 2 score the same rule from opposite sides: eval 2 with this
skill loaded and no profile, eval 4 with the profile alone and no skill.
Both artifacts state the rule, so both have to discriminate on their own.

Keep `files/profile-flywheel-design-session.md` in step with
`agents/flywheel-design-session.md` when that profile changes — it
is a fixture copy, and a stale copy silently stops testing the profile that
ships.
