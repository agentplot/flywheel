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
- Term counts across the tree, measured at 294e3b6: *assertion* concentrated in `skills/` and the schemas; *proposal* concentrated in `openspec/specs/` (~105 uses across six specs) plus `README.md` and `site/index.html`; *unit* thin outside the batch kind and the hero.
- **`openspec/specs/` is drifted and #13's body does not say so.** This repo's own settled specs still say *proposal* throughout, including the specs of the very skills that now say *assertion* — so the vocabulary is inconsistent one layer below the surfaces #13 enumerates, and any pass that fixes only the enumerated surfaces leaves the specs contradicting the skills they spec.
- The hero study's design is settled and out of scope for reopening (#12); its *words* are what is in question.
- Not constrained by `intent/gated-merge-guarantee` (#14/#16/#17) — different subject, neither gates the other.
- The full blast radius has not been inventoried exhaustively; the counts above are a survey, not the list a landing pass can be driven from.
