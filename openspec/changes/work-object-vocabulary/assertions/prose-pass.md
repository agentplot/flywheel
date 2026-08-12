# Assertion: The prose says assertion, and the hero says what is true

- **Repo:** agentplot/flywheel
- **Item:** #31
- **Raised by:** `sessions/2026-08-12-naming-call/` — the operator's call
  on #13, carved into the landing pass by the conductor's fold.

## The claim

The prose half of the vocabulary landing, outside `openspec/specs/**`.
When this is built, every work-object claim reference in `README.md`,
`site/index.html`, `skills/**` (the `SKILL.md`s and `_reference/`
files), the schemas' `instruction` text, `agents/*.md`, and the skills'
eval fixtures reads **assertion**, and no surface uses *proposal* for
the claim — counts at `2e707e9`, re-measure before landing: README 7,
site body 9, skills 22, schema instruction text 8, agents 7, evals 77.
Three rewrites inside that sweep are sentences, not substitutions: the
"the assertion is the proposal" axiom in three agent profiles and in
`schemas/flywheel-intent/schema.yaml`'s assertions instruction is
restated without using *proposal* as the claim's name; the shared
`<meta name="description">` sentence moves identically in `README.md`
and `site/index.html`; and the hero's two walkthrough lines
(`site/index.html:465`, `:470` at `2e707e9`) are rewritten per
`decisions/landing-pass-licence.md` — the intent agent holds the goal
and its assertions, and assertions are released to bolts that each
track many — so the false 1:1 claim-to-bolt mapping is gone and #21's
defect closes with this edit. The eval fixtures carry the same
vocabulary, their `proposals`-named fixture files and case names
renamed with their citing strings, and the four verbatim-copy agent
profile fixtures are re-copied from `agents/`, not hand-edited. The
batch-kind words `unit` and `elaboration` are untouched throughout,
as is the CSS comment about SVG layout units in `site/index.html` and
every incidental-English use #18 classifies INC.

## Why

`decisions/work-object-names.md` settles the names;
`decisions/landing-pass-licence.md` licenses the hero edit and sets its
wording direction. Per-surface counts, the fused-sentence sites and the
INC classifications are #18's inventory at `2e707e9`
(<https://github.com/agentplot/flywheel/issues/18#issuecomment-5270769621>).

## Boundaries

Identifiers are not covered here — directory and command renames, their
inbound reference lines, `bin/` strings and tracker labels are #30;
`openspec/specs/**` is #32. The hero's settled design (#12) — geometry,
palette, type, the SVG — stays untouched; the licence covers the two
lines' words. The eval suite's deeper defects stay on their items: the
gate that has never fired is #23, and the fixtures' divergence from the
profiles they copy is #24 — this pass re-copies them at the tree it
lands on, it does not adjudicate the drift.
