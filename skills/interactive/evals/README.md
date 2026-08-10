# Evals for `flywheel:interactive`

Two kinds of eval live here, and they test different artifacts.

**Type-skill evals (1, 2)** run with `SKILL.md` loaded. Their baseline is a
no-skill run, because this skill has no previous version yet. The next
change to edit this skill has one, and uses it — the no-skill arm is a
property of the skill's state, not a standing choice.

Eval 1 and eval 2 are the two conditions this skill exists to keep apart:
the user-level `lavish` **skill** absent, which stops the session, and
`lavish-axi` absent from `PATH`, which is the normal healthy state and
stops nothing. A skill that treats them the same fails one of the two.

**The profile-alone eval (3)** tests
`agents/flywheel-interactive-session.md`, not this skill. The
profile body travels as the fixture
`files/profile-flywheel-interactive-session.md` and the prompt withholds
every skill, because the claim under test is that a session reading only
its profile spawns no agents and reports the remainder as a handoff. An
eval that loaded the type skill could not tell a profile that works from a
profile that is redundant. Its baseline is a run with neither the profile
nor the skill.

Keep `files/profile-flywheel-interactive-session.md` in step with
`agents/flywheel-interactive-session.md` when that profile changes
— it is a fixture copy, and a stale copy silently stops testing the profile
that ships.
