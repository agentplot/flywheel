# Question: What is the released claim called, and what are the batch kinds called?

- **Item:** #13
- **Raised by:** `site-refresh-build-1`, rebuilding the landing page under `bolt/site-refresh` (#12); triaged into this intent by dispatch.

## The question

Three names are live in the tree for one object — the durable claim of
what must be built, which a bolt's spec agents work from: the skills and
the tracker say **assertion**, the landing page body prose and this
repo's own `openspec/specs/` say **proposal**, and the settled hero study
says **unit**. One of them wins everywhere.

The call is coupled to a second one and cannot be made alone. 8b8a1a3
made **unit** and **elaboration** the names of the two *batch kinds* —
what approving a batch authorizes. So "unit" is simultaneously bidding
for the claim (in the hero's *"Units become bolts"*) and already holding
the batch kind. An answer is recognizable when it assigns a distinct
name to each of: the released claim, the batch kind that releases claims
for construction, and the batch kind that authorizes design — and no
name appears twice.

## What turns on it

The name reaches further than prose. It is the tracker's `type:assertion`
label object, with live issues attached including closed #12; it is the
batch-kind values `unit` and `elaboration` that `flywheel-batch --kind`
accepts; it is two session-type labels, `type:proposal-writing` and
`type:proposal-review`; and it is two skill *directory* names, which are
the slash commands `/flywheel:proposal-writing` and
`/flywheel:proposal-review`. Renaming the claim therefore ranges from a
text pass to a coordinated label migration plus a command rename that
breaks anyone's muscle memory, and the three candidates differ sharply in
that cost.

It also decides whether the settled hero copy has to move. If the claim
is not called *unit*, `site/index.html`'s walkthrough sentence *"Units
become bolts"* is wrong on a page whose design the operator ruled settled
(#12) — which is a question to put to the operator rather than a licence
this intent holds.

## What is already known

- The split's origin is 8b8a1a3, which renamed the batch kinds to AI-DLC vocabulary without touching `site/`; #13's body traces it.
- **The blast radius is inventoried.** #18's research session measured it exhaustively at tree 2e707e9 and posted the table, the per-surface cost read and the identifier migration list as a comment on #18 — <https://github.com/agentplot/flywheel/issues/18#issuecomment-5270769621>, trailed at `sessions/2026-08-12-blast-radius-inventory/`. That comment is the list a landing pass is driven from; the facts below are its load-bearing conclusions, and every count in it carries the tree it was taken on. Re-measure rather than trusting these numbers if the tree has moved.
- Term distribution at 2e707e9, excluding the vendored `.claude/`: *assertion* 159, concentrated in `skills/` and the schemas; *proposal* 253, concentrated in `openspec/specs/` (119 uses across eight spec files) plus `README.md` and `site/index.html`; *unit* 51 and *elaboration* 21, both thin outside the batch kinds and the hero.
- **The cost is not in the prose, it is in the identifiers.** Renaming the claim moves label objects, two skill *directory* names (which are the slash commands), a schema artifact id and its generated record directory (`assertions/**/*.md`, breaking for every consuming repo already bound), template file paths, eval fixture filenames and eval case names, and requirement-heading keys in `openspec/specs/`. The prose is a text pass; these are migrations.
- **A GitHub label rename is rename-in-place.** The label object keeps its id and every attached issue follows automatically, closed ones included — zero per-issue edits, no reopen. Only historical `labeled` timeline events keep the old string, because that payload carries an id-less snapshot, so tracker history cannot be cleaned. Evidence is structural rather than documented; #18's comment states the reasoning.
- **The tracker migration is several operations, not one.** The label and batch-kind strings are hard-coded in `bin/` where a rename cannot reach: `flywheel-batch` (the `--kind` choice list, and the flag value written through verbatim as the label name), `flywheel` (the predicate that decides a milestone has a batch — a silent failure if it lags), `flywheel-setup` (the label definitions), `flywheel-migrate`. `flywheel-setup`'s `ensure_labels` is create-if-missing and never renames, so a tracker migrated ahead of the code silently regrows the old label beside the new one. The code edit is a prerequisite of the tracker edit staying done.
- **The live tracker weight is almost nil.** Of the five candidate-word labels three have never been applied to any issue — `unit` among them, so the word driving the collision costs one command to move. The entire live migration is #12 (closed), #17 and #19. No project field, option, view filter, workflow or milestone title names a candidate word.
- The hero study's design is settled and out of scope for reopening (#12); its *words* are what is in question. Separately, the hero's *"Units become bolts"* asserts a 1:1 claim-to-bolt mapping that contradicts the README's registry of many per bolt — a content defect the naming call does not fix, tracked on its own item.
- Not constrained by `intent/gated-merge-guarantee` (#14/#16/#17) — different subject, neither gates the other.
