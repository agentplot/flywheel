# Assertion: The identifiers carry the settled names, code landing before labels

- **Repo:** agentplot/flywheel
- **Item:** #30
- **Raised by:** `sessions/2026-08-12-naming-call/` — the operator's call
  on #13, carved into the landing pass by the conductor's fold.

## The claim

The non-prose half of the vocabulary landing. When this is built, the
tree and tracker check out as follows:

- `skills/assertion-writing/` and `skills/assertion-review/` exist and
  `skills/proposal-writing/` and `skills/proposal-review/` do not; each
  `SKILL.md`'s `name:` line matches its directory, so the slash commands
  are `/flywheel:assertion-writing` and `/flywheel:assertion-review`.
  Every inbound reference resolves to the new names — the enumeration to
  copy is #18's identifier family 3 at `2e707e9` (10 files / 15 lines,
  spanning `agents/`, two bolt schemas, `bin/`, two spec files,
  `site/index.html`, `skills/README.md`, `skills/_reference/herdr.md`);
  re-measure before landing.
- In `bin/`: `flywheel-setup`'s `TYPE_KINDS` enumerates
  `assertion-writing` and `assertion-review` and its `LABELS` therefore
  defines `type:assertion-writing` and `type:assertion-review`;
  `flywheel-migrate`'s `TYPE_WORDS` maps its review words to the new
  type names. The batch-kind machinery is byte-for-byte untouched:
  `flywheel-batch --kind` accepts exactly `unit|elaboration` and writes
  the flag value through as the label, `bin/flywheel`'s compose
  predicate still tests `unit`/`elaboration`, and `flywheel-migrate`'s
  record-directory regex still matches `assertions/` — the artifact id
  keeps its name.
- On the tracker: `type:proposal-writing` and `type:proposal-review`
  are renamed in place to `type:assertion-writing` and
  `type:assertion-review` (both had zero issues ever at `2e707e9`);
  `unit`, `elaboration`, and `type:assertion` keep their names, colours
  and ids.
- Ordering: the `bin/` edits merge before any label rename runs.
  `flywheel-setup`'s `ensure_labels` is create-if-missing and never
  renames, so a tracker migrated ahead of the code silently regrows the
  old labels beside the new ones; the code edit is a prerequisite of the
  tracker edit staying done, not a follow-up.

## Why

`decisions/work-object-names.md` settles the names and the
code-before-labels ordering; `decisions/landing-pass-licence.md` grants
the directory rename. The blast radius and the create-if-missing trap
are measured in #18's inventory at `2e707e9`
(<https://github.com/agentplot/flywheel/issues/18#issuecomment-5270769621>).

## Boundaries

Prose is not covered here: `README.md`, `site/index.html`, skills and
schema instruction text, agent profiles and eval fixtures are #31;
`openspec/specs/**` is #32. Consuming repos' trackers and any other
repo's records are out of scope per the intent. Archived change records
and the vendored `.claude/**` are untouched by design.
