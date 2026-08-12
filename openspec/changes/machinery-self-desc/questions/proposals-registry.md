# Question: Does the `proposals.md` bolt registry get retired or re-specced?

- **Item:** #26
- **Raised by:** the research session on agentplot/flywheel#18, at tree
  `2e707e9`; triaged into this intent by dispatch.

## The question

The three bolt schemas each declare exactly one artifact — `bolt`,
generating `bolt.md`. Yet `openspec/specs/flywheel-schema-instructions/spec.md`
still asserts the artifact set is "exactly bolt, proposals, and tasks", a
`proposals` artifact id and an `openspec instructions proposals`
invocation are specced across two spec files, and roughly fifteen eval
strings are built around the registry — fixture filenames, a registry
table header, an eval case name.

An answer is recognizable when it says whether the bolt's registry of
released claims is a thing the schemas should declare — in which case the
schemas gain the artifact and the specs are already close to right — or
a thing that was designed and never shipped, in which case the specs,
the invocation and the eval strings go, and the bolt's registry function
is described by whatever actually performs it today.

## What turns on it

This is spec-versus-shipped drift, not vocabulary drift. If the registry
is real, three schemas gain an artifact and every consuming repo bound to
them gains a record directory. If it is not, roughly fifteen eval strings
and two spec files lose a concept, and the question of how a bolt
enumerates the claims it carries needs an answer that does not point at a
file no schema generates.

Either way the call must be made on its own terms and not folded into a
rename: `intent/work-object-vocabulary` is separately deciding what the
released claim is *called*, and a rename that swept these strings would
silently bundle two different decisions — which is why dispatch routed
this here rather than there.

## What is already known

- The drift is #18's finding at tree `2e707e9`; the shipped bolt schemas
  declare one artifact each. Re-measure the string counts before acting.
- `intent/work-object-vocabulary` explicitly excludes this call and
  leaves the registry's strings to be settled here.
- Whatever the answer, `../assertions/workflow-args-warning.md` edits the
  same four schemas' `apply` instruction; a session touching schema files
  should expect to meet it.
