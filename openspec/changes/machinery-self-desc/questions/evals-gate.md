# Question: Does the CI evals step get fixed or dropped?

- **Item:** #23
- **Raised by:** the research session on agentplot/flywheel#18, at tree
  `2e707e9`; triaged into this intent by dispatch.

## The question

`.github/workflows/gates.yml`'s "Skill evals" step guards itself with
`compgen -G "skills/*/evals/**/case.yaml"` and
`compgen -G "skills/*/evals/*/prompt.md"`, and falls through to
`no evals under skills/ yet — nothing to run`. The repo ships neither
layout: every skill's evals are an `evals.json` plus a `files/`
directory. The step has therefore never run on any commit.

An answer is recognizable when it says which of two things the repo
does: teach the step the shipped layout so it actually runs the evals it
finds, or delete the step. Choosing to fix it also has to say what
"running an `evals.json`" means in CI — what invokes it, and what a
failure looks like — because the current step has never had to answer
that.

## What turns on it

A gate that cannot fail reads as coverage. Every actor that looks at
`gates.yml` to learn what this repo enforces sees a skill-evals gate and
concludes the eval fixtures are held to the profiles they copy. They are
not — which is the neighbouring defect #24 records, and which survived
precisely because nothing ran.

Fixing it means committing to a runner for the eval suite and to the
suite passing on every commit; the fixtures' current divergence means
the first green is not free. Dropping it means saying plainly that the
evals are authored material, not enforced material, and that nothing in
CI holds them to the profiles.

## What is already known

- The step's guard and message are at `.github/workflows/gates.yml`
  lines 41–51 at `c7c29ee`; the shipped layout is
  `skills/<name>/evals/evals.json` plus `skills/<name>/evals/files/*.md`,
  present under at least `research`, `inception`, `planning`,
  `prototype`, `writeback` and `interactive`. Re-measure before landing.
- The fixtures the gate would run have diverged from the profiles they
  claim to copy — #24, and `../assertions/profile-fixture-recopy.md`,
  which makes them honest independently of this call.
- `intent/work-object-vocabulary`'s prose pass rewrites eval fixture
  content and filenames, so a fix that pins CI to specific fixture paths
  meets that pass.
