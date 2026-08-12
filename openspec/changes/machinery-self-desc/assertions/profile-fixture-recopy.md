# Assertion: A fixture that claims to be a verbatim copy is one

- **Repo:** agentplot/flywheel
- **Item:** #24
- **Raised by:** the research session on agentplot/flywheel#18, at tree
  `2e707e9`.

## The claim

Four eval fixtures under `skills/*/evals/files/` present themselves as
verbatim copies of the corresponding `agents/*.md` profiles. When this is
built each of the four is byte-identical to the profile it copies, taken
from the tree it lands on — including
`profile-flywheel-design-session.md` and
`profile-flywheel-interactive-session.md`, which at `2e707e9` carried
lines with no upstream counterpart at all.

Re-copying is mechanical: the fixtures are replaced from `agents/`, not
hand-reconciled. Where the copy is meant to be partial rather than
verbatim, the fixture says which part it takes and why, so no fixture is
left making a claim the file does not honour.

## Why

A fixture that claims to be a copy and is not trains the wrong behaviour
and masks real profile drift — the eval passes while the profile it is
supposed to hold the machinery to has moved underneath it. The
divergence and the two orphan-line fixtures are #18's finding at
`2e707e9`; re-measure before landing.

## Boundaries

Whether the eval suite runs in CI at all is #23 — this assertion makes
the fixtures honest regardless of that call, and does not depend on it.
The vocabulary the fixtures use is `intent/work-object-vocabulary`'s
prose pass, which re-copies these same four files at the tree it lands
on; whichever lands second re-copies from the tree it finds. No fixture
outside the four verbatim-copy profile fixtures is claimed here.
