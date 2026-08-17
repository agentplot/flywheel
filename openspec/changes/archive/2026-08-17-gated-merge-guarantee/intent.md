# Intent: gated-merge-guarantee

## Destination

A merge that reports success has run the repo's gate on the exact tree
that landed. The loop's central guarantee — *the green claim is produced
by the tool rather than asserted by whoever wrote the change* — holds for
every merge a conductor performs, with no shape of merge for which it is
silently absent, and no ✓ that means one thing on Monday and another on
Tuesday.

An agent that needs to run the gate explicitly can run it. The
approvals a `wt` hook template requires are in place before any actor
needs them, so running the gate is never a choice between
`Cannot prompt for approval in non-interactive environment` and the
`--yes` bypass the loop forbids.

Where the guarantee has a boundary, the documentation states the
boundary rather than the guarantee. `skills/_reference/herdr.md` today
tells every agent that `wt merge` "runs the repo's `.config/wt.toml`
checks on the exact rebased tree that lands"; at the destination that
sentence is true as written, or it names the case where it is not and
says what the agent does instead.

**Books.** This repo carries no `books/` tree, so this intent cites no
chapters. Its prose destinations are `skills/_reference/herdr.md`
("Merging through the gate"), `skills/construction/SKILL.md` and
`skills/inception/SKILL.md` where they lean on the gate, and the comment
block at the head of `.config/wt.toml`.

## Map

This repo carries no `context-map/` tree, so this intent moves no map
nodes. If a context map is established for the flywheel machinery while
this intent is open, the nodes covering the merge gate and the
construction loop's landing step are the ones it moves, and this
section is rewritten to name them.

## Scope

**In scope.**

- The fast-forward hole: `wt merge` with `ff = true` making no commit,
  therefore running no `[pre-commit]` hook, and reporting the same ✓ as
  a gated merge (item #14).
- Which remedy the loop takes — worktrunk configuration (`ff`,
  `verify`), an explicit gate step the conductor runs on the landing
  tree, an upstream fix, or some combination — and what the loop's
  skills then say.
- The approvals gap: `wt config approvals add` never run for this
  repo's three hook templates, leaving a non-interactive agent unable to
  run the gate at all.
- Correcting every sentence in the loop's own prose that asserts the
  guarantee more broadly than it holds.

**Out of scope.**

- What the gate checks. The three hooks in `.config/wt.toml` are this
  intent's given; adding, removing or retuning checks is other work.
- CI in `.github/workflows/gates.yml` as a substitute for the local
  gate. This intent is about the guarantee at merge time in the loop's
  own hands.
- Any other property of `wt merge` — squash defaults, commit-message
  generation, the rebase step — except where a remedy here changes it.
- The construction loop's branch topology. Where merge-backs land is
  settled work; this intent asks only whether they were gated.
