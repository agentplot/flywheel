# aidlc-design book

## ADDED Requirements

### Requirement: The book carries the two-loop design

`books/aidlc-design` SHALL describe the flywheel as its conducting practice:
`conducting.md` and `authoring-capabilities.md` rewritten as the actor
model — intent conductors, bolt conductors, the operator's phase gate,
single-writer changes with inbox messaging; `spec-driven-construction.md`
rewritten around pipeline-stage testing (commit stage, merge gate, batched
acceptance on bolt branches, release gate, scheduled) with the
actor-and-branching figure.

#### Scenario: A reader can run the loop from the book

- **WHEN** a reader who has never seen the system reads the rewritten chapters
- **THEN** they can create an intent, run a design session, stage a handoff,
  and describe what a release does — without consulting chat history or
  lavish artifacts

### Requirement: Chapter set matches the flywheel

The book SHALL archive `catalog.md` and `agent-workspaces-plugin.md` (plugin
docs live with plugins), and the `system-design-inception.md` and
`openspec-construction.md` content SHALL merge into the chapters backing
`flywheel-inception` and `flywheel-construction` respectively — no chapter
describes a plugin the flywheel replaces.

#### Scenario: No stale plugin chapters remain

- **WHEN** the book's SUMMARY.md is read after the rewrite
- **THEN** every listed chapter describes the current practice, and archived
  material is outside the `books/` tree

### Requirement: Books drop the proposals chapter

`books/CLAUDE.md` SHALL retire the mandatory per-book `src/proposals.md`
chapter: chapters describe destinations; the build list lives in intents'
handoff tasks; generated proposals in built repos cite chapters directly.
Verification chapters remain mandatory.

#### Scenario: New book scaffolds without proposals.md

- **WHEN** a new system book is added after this change
- **THEN** its required chapter set includes verification but not proposals,
  and existing books' proposals.md chapters are removed as each book is next
  edited
