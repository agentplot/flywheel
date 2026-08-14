## Why

`stage-labels-96` landed the `stage:*` vocabulary, the merge-time close, the
unit parent and `bolt-direct`, and its verify, code-review and build sessions
filed twenty-two findings against it. Its own go-fix rounds then answered
thirteen of them before the batch merged back — so this change is written
against the tree as it stands at `eae4984`, not against the branch the
findings were filed on, and it carries only what a fresh read of that tree
still shows.

Nine survive, and they fall into three kinds:

- **The spec is wrong and the tree is right.** `flywheel-release-unit-parent`
  requires a shape the handoff path deliberately does not produce, and
  `flywheel-construction-stages` has no scenario for a stage that was
  *skipped* rather than one that *failed* — a distinction the plan-mode
  repair at `ecad0e5` already turned on.
- **A rule the specs state absolutely is conditional in the tree.** "Writing
  any `stage:*` label removes every other" has one implementation the loops
  share and one hand-written copy the operator's flip uses; "no program
  downgrades the scrutiny the release approved" is enforced against a bolt's
  binding and not against the `--type` flag that outranks it.
- **A defect the merge creates that neither parent has.** `guard_stages`
  re-derives `stage:merged` — and *closes* items `closed:merged` — from bare
  git ancestry, which `#164` proved wrong on `main`; `main` fixed it by adding
  a stronger predicate beside the weak one rather than hardening it, so the
  pending rebase resolves cleanly and leaves the guard calling the weak check.

Doing nothing costs most on the last of those: an empty build branch satisfies
bare ancestry, and a mis-close removes the item from every open-issue filter,
so the batch stops being driven at all.

## What Changes

- **The unit-parent requirement is corrected to the two shapes that exist.**
  The born-ready release puts the parent on the bolt milestone with exactly
  the released assertions as sub-issues; the handoff release puts it on the
  intent milestone with the handoff item among the sub-issues, because the
  amend path recovers the unit through that item's own parent. The native
  bar's denominator is stated for each path rather than asserted as one
  number.
- **A unit parent has a closer.** Nothing closes one today, so a born-ready
  bolt's parent stays open at Status Ready and its milestone reports a job on
  every server sweep — before the landing, after the landing, and after the
  operator closes the milestone, where it collides with the archive job the
  same sweep adds.
- **Re-derivation requires real work behind ancestry.** An item's branch being
  an ancestor of the bolt branch SHALL NOT by itself mean merged, because an
  untouched branch's tip is an ancestor of everything it was cut from. This is
  the rule `main` already implements; the requirement states it so the rebase
  cannot leave a caller behind.
- **A skipped stage writes no label**, stated as its own scenario beside the
  failed-stage one. The code is already right; the spec cannot say so.
- **The scrutiny refusal covers the command line.** A `--type` that disagrees
  with the binding on disk is refused, the way a `stages:` declaration in the
  binding already is and the way `--plan-mode` already is.
- **The operator's flip goes through the one implementation.** The pane-written
  `stage:done` is a hand-built two-label `gh issue edit` that hard-codes
  `stage:in-session` as the predecessor to remove; an item picked up at
  `stage:collected` by a later session therefore ends carrying two stages. The
  sweep becomes something a pane can run without importing Python.
- **The shared writer's early return stops skipping the sweep**, and a label
  surface's cached additions are invalidated when its snapshot is re-read.
- **Two coverage gaps and one collection trap in the suite** — `bolt-direct`'s
  shipped strategy is asserted nowhere, the landing path's session teardown
  merge is never exercised, and `tests/test_inbox.py` runs `unittest.main()`
  above a class so a direct run silently skips it.

Nothing here changes the `stage:*` vocabulary, the closure vocabulary, or
which loop writes which label.

## Capabilities

### New Capabilities

None. Every behaviour at issue belongs to a capability `stage-labels-96`
already created.

### Modified Capabilities

- `flywheel-release-unit-parent` — the two release shapes, the bar's
  denominator on each, and who closes a unit parent and when.
- `flywheel-construction-stages` — re-derivation requires real work behind
  ancestry; a skipped stage writes no label.
- `flywheel-bolt-direct` — the refusal covers the command line, and the
  shipped type's declared strategy is pinned on disk.
- `flywheel-stage-labels` — the sweep is unconditional, the one
  implementation is reachable from a pane, and a cached label surface does not
  outlive its snapshot.

`flywheel-design-session-completion` is **not** modified: the two findings
against it — the pause that left siblings collectable, and the teardown that
never fired for a later flip — were both answered inside `stage-labels-96`
(`34d94e3`, `c569ed1`), and its requirements read correctly against the tree.

## Impact

- `bin/_flywheel_bolt_loop.py` — the re-derivation guard's predicate, and the
  refusal at the entry point in `bin/flywheel-bolt-loop`.
- `bin/_flywheel_inbox.py` — the shared stage writer's sweep, and the server
  filter's Ready-batch branch.
- `bin/_flywheel_intent.py` — the unit parent's milestone and sub-issue set are
  already as this change specifies; the label surface's cached additions are
  not.
- `bin/` gains one command — the stage move a pane can run — and
  `skills/_reference/herdr.md` and the six design-session skills stop carrying
  a hand-built copy of the rule.
- `tests/test_bolt_loop.py`, `tests/test_intent_loop.py`, `tests/test_inbox.py`.
- No schema `loop:` block changes, and no change to what any bolt type
  declares.

## Sources

Twenty-two released assertions on `bolt/stage-labels`, each item's own body
being the assertion — `openspec/changes/stage-labels/bolt.md` records that no
item of this bolt carries an assertion record file. Every claim below was
re-read from disk on `build/stage-labels-133` at `eae4984`, because the
findings were filed against `build/stage-labels-96` at `fea1354`, `f725d27`
and `e0f98fb`, and that branch's own go-fix rounds are now merged back.

**Carried into this change** — `#142`, `#147`, `#151` (one of its two halves),
`#154`, `#155`, `#156`, `#173`, `#175`, `#176`.

**Already satisfied on this tree, and specced nowhere here** — `#133`, `#134`,
`#135`, `#136`, `#143`, `#144`, `#145`, `#146`, `#148`, `#149`, `#150`,
`#157`, `#158`. Each item's comment carries the evidence read for it; the
verification of those thirteen is a task of this change so the claim is
re-checked at build time rather than trusted from here.
