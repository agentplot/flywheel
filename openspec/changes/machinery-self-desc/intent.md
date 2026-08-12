# Intent: machinery-self-desc

## Destination

Every claim the loop's own machinery makes about itself is true of what
the repo ships. An agent that copies an invocation out of
`skills/_reference/herdr.md` runs it and gets the effect the reference
promises; a tool that is handed the wrong argument shape says which
shape it wants; a spec that enumerates an artifact set enumerates the
set the schemas declare; a fixture that calls itself a verbatim copy is
one; a CI step that reads as coverage actually runs; and the project
context injected into every apply run describes this repo as it is.

The failures this intent retires all have one shape: the machinery
describes a version of itself that the tree does not contain, and the
gap is silent. Nothing errors, nothing fails a gate — the reader simply
carries a false fact forward and pays for it later, in a fleet-wide
teardown, a run whose every prompt says `undefined`, or a gate that has
never fired on any commit. The destination is that each of those claims
is either true or removed, and where a tool can catch the mismatch, it
catches it at the call rather than leaving it to prose.

This repo ships no book and no context map, so there is no chapter to
cite and none to write against. `openspec/specs/` is the settled prose
this intent must leave coherent, and `skills/_reference/` is the shared
operational text every actor reads.

## Map

No `system-context-map.html` exists in this repo — the map is a thing the
flywheel schemas ask consuming repos for, and agentplot/flywheel has not
built its own. The surfaces this intent moves, standing in for map nodes:

- `skills/_reference/herdr.md` — the one shared copy of every herdr and
  worktrunk invocation — **candidate**: its teardown command is correct
  only for `herdr worktree create` provenance, and its `flywheel-batch`
  line carries the `--repo <org>/<tracker>` shape from the `gh` examples
  above it
- `bin/flywheel`, `bin/flywheel-batch` — **candidate**: neither refuses a
  bad argument with a message naming the shape it wants
- `skills/inception/SKILL.md`, `skills/construction/SKILL.md`, and the
  four schemas' `apply` instruction — **candidate**: all four now bind
  the apply loop to a dynamic workflow, and none warns that `args` must
  be a JSON value
- `skills/_reference/tracker.md` and dispatch's milestone-creation
  practice — **candidate**: milestone slugs are born with no length rule,
  and conductor agent names are derived from them
- `skills/*/evals/files/profile-*.md` — **candidate**: four fixtures
  claim to be verbatim copies of `agents/*.md` and have diverged
- `openspec/config.yaml` context prose — **open**: asserts this repo does
  not bind the flywheel schemas, which it does
- `.github/workflows/gates.yml` evals step — **open**: globs
  `skills/*/evals/**/case.yaml` while the repo ships `evals.json` plus
  `files/*.md`; fix-or-drop is undecided
- `openspec/specs/flywheel-schema-instructions/spec.md` and the
  `proposals` registry it specs — **open**: a `proposals` artifact id,
  an `openspec instructions proposals` invocation and roughly fifteen
  eval strings describe a registry no shipped schema declares;
  retire-or-respec is undecided

## Scope

**In scope.** Every claim the repo's own operational text, tools, specs,
fixtures and CI make about the repo, and the tools' behaviour where a
tool can catch a mismatch the prose currently leaves to the reader.
That includes both ends of a defect: the reference sentence that misled,
and the command that could have refused. Where a claim describes
machinery the repo does not ship, deciding whether the machinery or the
claim goes is in scope.

**Out of scope.**

- The vocabulary of the work objects — which word names the released
  claim, and what the batch kinds are called. That is
  `intent/work-object-vocabulary`, and a rename bundled into a
  truth-correction would silently carry two different calls.
- The gated-merge promise and what the skills may claim about it — that
  is `intent/gated-merge-guarantee`.
- The behaviour or design of either loop. This intent makes the
  machinery's self-description true; it changes no mechanic, no state
  machine, and no session type's job.
- herdr's and worktrunk's own behaviour. Where their limits are the
  defect — the 32-character agent-name ceiling, a tab's workspace
  inheritance — this intent makes the flywheel side live within them and
  say so, rather than asking those tools to change.
- Other repos' bound changes, their records and their trackers.
