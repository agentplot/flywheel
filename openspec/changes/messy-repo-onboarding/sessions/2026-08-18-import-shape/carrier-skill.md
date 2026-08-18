# Carrier skill draft — proposed `skills/import/SKILL.md`

The text below is the proposed skill, verbatim. On approval of
`round.md` §5 it lands at `skills/import/SKILL.md` unchanged; until
then this file is the draft under annotation. Frontmatter follows the
plugin's skill conventions.

---

```markdown
---
name: import
description: >
  Run the messy-repo import a flywheel import-charged design session
  works — inventory a corpus of planning docs, cut it against the
  destination books, convert artifact by artifact into flywheel-native
  records, and mark each processed in the intent's committed ledger.
  Use whenever a design session's work order charges an import, a cut,
  or a conversion batch over an onboarded corpus.
---

# Flywheel import — the cut and the conversions

You are a design session charged with an import batch. The governing
promise is the intent's `decisions/onboarding-promise.md`; this skill
is the process shape it writes down once. The cut and every
conversion are judgment every time — this skill structures that
judgment and replaces none of it.

**An import runs inside the corpus org's own flywheel.** The org that
owns the corpus runs the import against its own design repo, tracker,
and state — corpus content never crosses into another org's repos.
What is shared across orgs is this skill, nothing corpus-specific.

**An import is a move, not a copy.** As each artifact is processed it
is removed from the source repo, and the untouched original is stored
at `$XDG_STATE_HOME/flywheel/<org>/imports/<repo>/originals/<path>`
(default `~/.local/state`), so nothing is lost and nothing sits
converted in two places. The shrinking source repo is the visible
progress; the ledger (step 4) is its committed record.

## The two inputs

An import reads **two** trees, always:

- the **corpus** — the source repo, pinned at a sha your report names;
- the **destination books** — pinned the same way.

No settled-history row is assignable until the books are read. Where
the destination books do not exist yet, say so in the cut's header;
the lane is then assignable from the corpus alone.

## Step 1 — Inventory

- Enumerate with `git ls-files`, **never `find`** — a filesystem walk
  inflates the corpus with vendored trees (measured: 2.3×).
- Every tracked file, not a file-type guess: classify by type and
  **report what you set aside** rather than silently excluding it — a
  corpus has kept its import-state in a `.json` nobody would have
  listed.
- Date everything: `git log -1 --format=%ad -- <path>` per file. Date
  clusters map onto lanes; a derived artifact older than its source
  is stale by construction.
- **Find the corpus's own progress ledger before reading anything
  long**: a phasing section, a roadmap page, a findings sink, a state
  file. Do not go looking for the file the operator named — the
  operator's pointer is seed evidence, and a seed that misses is not
  a corpus defect. Where renderings of the ledger disagree, the one
  the corpus names as its source of truth wins, and the disagreement
  is triage evidence.
- Pin corpus sha and books sha in the cut's header.

## Step 2 — The cut

A durable triage report, committed in the intent's change directory.
Granularity: file-or-section, **and below a section wherever a
trailing subsection changes lane** — a settled block's "writeback
hook" / "still open" / "what has to change" tail is live work by
default; two rows for one section is normal.

Read in this order:

1. **Harvest the corpus's own lane markers first** — status lines,
   `(settled)` headers, DONE stamps — and spend the reading budget on
   the unmarked regions.
2. **Confirm markers against the corpus's named source of truth
   before laning.** A marker states the author's intent at writing,
   not current truth.

Each row: artifact/span, lane, one-line reason, checkable pointer.
The lanes:

| lane | meaning | conversion consequence |
| --- | --- | --- |
| `discard` | the row is the record that it was seen | none beyond the originals folder |
| `withhold` | seen, must not be carried forward | none; row records the **class** (account id, network id, credential path, IAM grant) and **quotes nothing** — never an excerpt, never a line range that invites a look; the original exists only in the state folder |
| `settled-history` | a concluded decision, design, or finding | convert per the two qualifiers below |
| `live-work` | work still to do | routed by kind — design-level direction and forward intent go **into the design books** (bolt planning carves bolt unit plans from the books on demand); only already-concrete, actionable work becomes queued tracker items, all at Backlog |

`settled-history` carries two qualifiers, both mandatory:

- **coverage**: `unwritten` (convert) or `already-in-books` (record
  provenance, cite the chapter — converting duplicates a chapter that
  exists). The corpus may assert the opposite of the truth here; only
  the books settle it.
- **currency**: `current` (eligible to update the books) or
  `superseded` (a historical record with a dated caveat, **never** a
  books update). The corpus's own disclaimers and its date clusters
  are the evidence.

Any row may carry the **`sole-holder` flag**: the corpus is the only
copy. The flag's consequence is preservation — the artifact is
**adopted whole** into the import's archive before the corpus can be
retired — which is a separate act from conversion, owed even when
nobody has to read the thing today.

*Restated elsewhere* is a claim you check, never infer from the
presence of a summary. Two steps, neither substituting for the other:

1. **The restatement check (filter):** grep the live document for
   references to the artifact and read whether they carry the content
   or merely name it. A pointer is not a restatement.
2. **The read (verdict):** what the filter passes still needs a
   reader — unrestated material can settle nothing and be discard
   anyway.

**Form check:** an artifact whose form its supposed source cannot
express — hand-authored SVG in an HTML report, against a markdown
source — is a sole holder by construction and no grep will find it.
Ask what form each artifact carries; adopt diagrams whole rather than
converting them.

**Operating documentation** — how to run the thing as it stands — is
none of the lanes. Ask the operator **once per corpus**: if the repo
lives on, it is out of the import's scope entirely; if the repo is
being imported out of existence, it is removed with everything else
and its originals kept in the state folder — recoverable, never
converted into records it does not contain.

**A lane is a disposition for the corpus, never a judgment about
whether anyone should read the artifact.** Where a row is prior art
for flywheel's own work, say so in your report regardless of its
lane.

Rows you cannot settle become queued questions on the intent — never
a silently chosen lane.

## Step 3 — Convert

One artifact at a time, thoroughly:

- **Settled history** → flywheel-native records: a session-under-
  intent record and a decision record in the destination change
  directory, plus a **per-artifact books-verdict** — updated, or an
  explicit verdict with the chapter cited. "Already written, here is
  the chapter" is a first-class verdict. Superseded material converts
  with its dated caveat in the record's first lines.
- **Live work** → routed by kind. Design-level direction and forward
  intent are written **into the design books** — bolt planning reads
  the books and creates bolt unit plans on demand, so the books are
  the default destination for future work. Already-concrete,
  actionable work becomes queued tracker items: title, provenance
  pointer (corpus repo@sha + span + cut row), proposed route, and
  **the session type that will work it**. Bulk mechanics: the cut's
  proposed-items table is the operator's one review pass — each row
  names its destination (book vs item) and its session type; dedupe
  against the corpus's own progress ledger and the currency
  qualifier first; collision with open items is judged in-session
  against one `gh issue list` pull, and a colliding row becomes a
  pointer comment on the existing item.
- **Sole holders and diagrams** → adopt the artifact whole into the
  destination design repo, unmodified, beside a one-line index
  entry — durable and shared, unlike the machine-local originals
  folder.
- **Removal** closes each conversion: the processed artifact leaves
  the source repo (its original already in the state folder), in the
  same commit series that records it processed.

## Step 4 — Mark processed

The ledger is
`openspec/changes/<intent>/import/<source-org>-<corpus>/processed.jsonl`
— committed, append-only, one row per processed artifact:

```json
{"kind": "processed", "import": "<org>/<corpus>", "corpus_ref": "<sha>",
 "artifact": "<file>#<section>", "span": "L…-L…",
 "content_sha256": "<prefix>", "lane": "settled-history",
 "coverage": "already-in-books", "currency": "current",
 "sole_holder": false, "converted_to": [{"kind": "decision",
 "path": "…", "repo": "…"}], "books_verdict": {"verdict":
 "no-change-needed", "reason": "…", "chapters": ["…"],
 "books_ref": "<sha>"}, "residue": [{"span": "L…-L…", "lane":
 "live-work", "disposition": "queued", "note": "…"}],
 "session": "<tracker>#<item> sessions/<dir>", "landed": false,
 "landing_blocked_by": "<item> — <reason>", "recorded_at": "<date>"}
```

Omit fields that do not apply; never omit `lane`, `corpus_ref`, or
`recorded_at`. Withhold discipline applies to the ledger as to every
row: class, never content. Processed vs remaining against the
inventory is the import's progress measure, and the ledger plus the
corpus sha is what lets a fresh session resume with zero handoff.

## What you report

The cut's header facts (file count, line count, shas, exclusions),
the lane totals, the verdicts recorded, the items proposed, the rows
queued as questions, and — always — anything in the corpus that is
prior art for flywheel itself, whatever lane it fell in.
```
