# Design — stage-labels-133

## Context

This change answers twenty-two findings filed against `stage-labels-96` by
its own verify, code-review and build sessions. Thirteen of them were
answered inside that change's go-fix rounds before it merged back, so the
first design decision is about **what this change is written against**.

`build/stage-labels-133` is cut from `bolt/stage-labels` at `eae4984`, which
holds `stage-labels-96` merged and archived: `openspec/specs/` carries
`flywheel-stage-labels`, `flywheel-construction-stages`,
`flywheel-release-unit-parent`, `flywheel-bolt-direct` and
`flywheel-design-session-completion` as main specs. The findings, by
contrast, cite paths under `openspec/changes/stage-labels-96/specs/`, which
no longer exist. Every claim carried into this change was therefore re-read
from the tree at `eae4984`, and the citations here are to the live spec files
and to symbols by name — never to the delta paths the items quote and never
to a line number, because both move.

A prior spec-writing session on this same batch raised the andon, correctly:
its worktree was cut from `bolt/stage-labels` at `553c7e3`, which was main's
tree exactly, and the subsystem every item cites was still unmerged on
`build/stage-labels-96`. That condition is cleared. The merge-back happened,
and the tree now holds what the batch talks about.

## Goals / Non-Goals

**Goals.** Correct the four spec statements that describe something the tree
deliberately does otherwise; close the two routes by which an absolute rule
is conditional in practice; and remove the one defect that the pending
rebase onto `main` would create.

**Non-Goals.** No change to the `stage:*` vocabulary, to which loop writes
which label, to the closure vocabulary, or to any bolt type's declared stage
set. No re-litigation of `closed:merged`. Nothing here touches
`flywheel-design-session-completion`, whose two findings were answered
upstream.

## Decisions

### D1 — The spec is corrected to the tree on the unit parent, not the reverse

`flywheel-release-unit-parent` states, over both release paths, that the unit
is created "on the bolt's milestone" with "exactly the items being released"
as sub-issues, and that the handoff path yields "the same shape as the
born-ready release". Neither half holds on the handoff path as built:
`compose_unit` is called with the intent loop's own `Config.milestone`, which
is `intent/<slug>`, and with the handoff item prepended to the released
numbers.

Three neighbours agree with the tree against the requirement — the sibling
requirement in `flywheel-construction-stages` ("On the handoff path the unit
parent sits on the intent milestone, so once the merge boundary has closed
every assertion an open-items-only set is **empty**"), the design record of
`stage-labels-96` now in `openspec/changes/archive/2026-08-14-stage-labels-96/`,
and the literal graph in `skills/_reference/tracker.md`, whose worked example
shows a unit whose sub-issues are the handoff item and the assertion. A whole
requirement of `flywheel-construction-stages` — "The landing keeps a tracker
surface when every assertion is merge-closed" — is **built on** the parent
being off the bolt milestone. Correcting the tree would invalidate it.

The requirement is also wrong in a way that is load-bearing rather than
cosmetic: the handoff item's membership in the unit is what the amend path
recovers the open unit by, so an implementation that honoured "exactly the
items being released" would lose the handle that lets a later settled wave
join an open Backlog batch instead of starting a second one. The spec is
corrected, and the reason the handoff item is there is stated so the next
reader does not tidy it away.

**Alternative considered — make the handoff path match the born-ready
shape.** Rejected on three counts: it invalidates a requirement in a sibling
capability that the landing's escalation surfaces depend on; it removes the
amend path's recovery handle with nothing offered in its place; and the
parent cannot sit on `bolt/<slug>` at birth in any case, because at birth
there is no bolt milestone for it to sit on — the assertions reach one later,
by the handoff session's custody move.

### D2 — The bar's denominator is stated per path rather than corrected

Because the handoff item is a sub-issue and closes at its own design
session's collect — before construction starts — a handoff release of four
assertions shows a bar of 1 of 5 before any construction work happens, and
4 of 5 when every assertion has merged. The finding raises this as a real
question rather than wording.

The bar stays GitHub's own and the spec says what it counts. The alternative
is to compute a corrected figure, and that is refused by a requirement this
same capability already carries: the board is a view and never a second
store, and "no second progress figure exists" is one of its scenarios. Buying
a tidier numerator by standing up the one thing the capability forbids would
be a bad trade for a number the operator reads next to the bolt's name.

### D3 — Re-derivation requires real work behind ancestry, by calling main's predicate

`guard_stages` asks `branch_merged`, which is bare
`git merge-base --is-ancestor`. An untouched branch's tip is an ancestor of
everything it was cut from — the sentence `main`'s `7248857` uses to describe
`#164`, the vacuous landing that closed items over a standing andon on this
very bolt.

Verified on this branch: `batch_merged`, `branch_advanced` and
`refs/flywheel/base` are absent from `bin/`, and `git merge-base --is-ancestor
main HEAD` is false, so the rebase is still ahead. `main` fixed `#164` by
adding a stronger predicate **beside** the weak one rather than hardening
`branch_merged` in place, which is precisely why the rebase will resolve
cleanly and leave this guard on the weak test.

The decision is to **port the call, not the fix**: after the rebase,
`guard_stages` calls the predicate `main` already ships, and no second
implementation of "has this branch really merged" is written. Writing one
inside this batch would produce exactly the conflicting duplicate the finding
warns against.

The severity ordering is worth recording, because it is what makes this the
first task rather than a tidy-up. The guard does not only write a label: at
the merged edge it also closes the item `closed:merged`, and a `closed:merged`
item leaves every open-issue filter. `#164` mis-*landed*; this would
mis-*close*, and a mis-closed batch stops being driven at all.

### D4 — The refusal covers the command line, and the binding stays the record

`refuse_stage_declaration` now closes the declaration door, and
`LoopConfig.validate` now raises on an unknown stage name — both landed in
`stage-labels-96`'s go-fix rounds. The remaining route is the entry point's
own precedence: the type is resolved as the `--type` flag first and the
binding second, while the refusal inspects only the binding. So a flag can
resolve a bolt bound to `bolt-default` as `bolt-direct` and drop verify with
nothing recorded anywhere.

This is asymmetric with the path the spec names as its model — `--plan-mode`
is checked against the bound type and refused — and it contradicts
`read_binding`'s own docstring, which says the binding on disk is what the
loop believes "ahead of anything it was told on the command line".

The decision is to refuse the disagreement rather than to reverse the
precedence. Reversing it would make `--type` silently useless, which is a
worse kind of quiet than the one being fixed. Refusing names the rule, and
the legitimate need behind the flag — a bolt whose binding is wrong — is met
by correcting the binding, which is a recorded act on disk. A bolt with no
binding keeps the flag, because there is no approval for it to contradict.

Scope note, stated rather than assumed: this precedence predates
`stage-labels-96`, and `bin/_flywheel_server.py` never passes `--type`, so
the fleet path cannot reach it. What changed is the consequence — before
`bolt-direct` existed, no `--type` value could drop a stage.

### D5 — The pane's flip becomes a call, not a recipe

`flywheel-stage-labels` requires the one-stage rule to have "exactly one
implementation … and both loops SHALL write through it". Both loops do:
`set_stage` is the single implementation and no `add_label` bypass exists in
`bin/`. The operator's `stage:done` is the one write that does not, because
it is made by a session in a pane, and what the pane is given is a
hand-built `gh issue edit --remove-label stage:in-session --add-label
stage:done` in `skills/_reference/herdr.md`, echoed by both agent profiles and
all six design-session skills.

That command obeys the invariant **by hand** and hard-codes one predecessor.
`dispatch_batch` deliberately leaves an item at `stage:collected` alone when a
later session picks it up, so the documented flip's removal is a no-op there
and the item ends carrying `stage:collected` and `stage:done` at once.

Two shapes were considered. **Widen the recipe** — emit a `--remove-label`
for every other stage name in the one `gh issue edit` — is mechanical and the
reference is already generating the command. **Ship a small command** that
shells the same rule `set_stage` holds is larger by one file and is what the
spec's wording actually asks for: it makes "exactly one implementation" true
rather than aspirational, and it stops the seven copies of the recipe from
being seven places to keep in step. The second is chosen. The prose then
points at the call, and the requirement gains a scenario saying no
hand-built edit is spelled out for a session to copy.

An operator adding the label by hand on GitHub is outside anything the
flywheel writes, and is why D6's sweep matters.

### D6 — The sweep is unconditional; both directions of the cache are invalidated

Two edges in the shared writer, neither of which changes an end state today,
and both of which make an absolute statement conditional:

`set_stage` returns before the sweep when the item already carries the
target, justified by "an item already at the target carries no other stage by
this function's own invariant". That invariant holds only while every writer
goes through the function — and the capability explicitly blesses the
operator adding `stage:done` by hand on GitHub, with no sweep. The early
return is narrowed to "already at the target **and carrying no other**",
which keeps the idempotence the dry-cycle property needs while dropping the
assumption the spec does not license.

`Writer._added` survives the snapshot reassignment that a cycle's re-read
makes, while `_removed` is invalidated. On the normal pane path — dispatch
writes `stage:in-session`, the pane session then writes `stage:done`, which
removes `in-session` on GitHub — the stale addition sends one redundant
`--remove-label` per collect. The end state is right, so this is cost and
misleading recording rather than corruption; both halves are invalidated
together because a cache with one direction invalidated is a cache whose rule
nobody can state.

### D7 — Test hygiene is scoped to what a green suite is asserting

Three items are about the suite. Two are coverage: `bolt-direct` is absent
from the shipped-types enumeration and the cycle test that proves it runs no
verify builds its config by hand, so the schema could be edited to disagree
with both and stay green; and the landing path's session-teardown merge is
exercised only on the resume path, whose tests `c569ed1` added on a
worktree-bearing type. The first gets a requirement, because "what the
shipped schema declares is held on disk" is a property of the capability
rather than of a test file. The second gets a task, because the behaviour is
already specified — `flywheel-design-session-completion`'s "The last item
completes the session" — and what is missing is a case, not a contract.

The third, `tests/test_inbox.py` running `unittest.main()` above a class, is a
task with no spec delta at all. The repo's runner is `unittest discover`,
which imports the module first, so the gate is honest and CI checks
everything; the trap is for a person debugging one file, who is told green
while six tests never ran. That is a real cost and not a behaviour, and
inventing a requirement for it would be inventing a requirement to satisfy
validation.

## Risks / Trade-offs

- **The rebase must come before D3's task.** Porting `guard_stages` to a
  predicate that does not exist on this branch yet is not possible, and
  writing the predicate here is the duplicate the finding warns against. The
  task states the ordering; a build session that finds the rebase has not
  happened should stop rather than improvise a second implementation.
- **D5 adds a command to `bin/`, which an installed plugin puts on a user's
  PATH.** That bar — "nothing goes in `bin/` that is not meant to be a
  command in a stranger's shell" — is met here: a session moving an item's
  stage is exactly the sort of thing a user of this plugin does, and it is
  the same act the loops make.
- **D1 leaves the two release paths visibly different**, which is less tidy
  than the requirement it replaces. The tidiness was fictional; three
  neighbours and a dependent requirement already described the difference.
- **Thirteen items are carried as verification rather than as work.** If any
  of those thirteen turns out to be only partly fixed, the change under-scopes
  it. The mitigation is that the verification is a task run at build time
  against the tree, not a claim resting on this document — and a task that
  finds a gap files it rather than papering over it.
