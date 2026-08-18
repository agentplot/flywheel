# Importing a messy repo — five decisions, round 3

You point flywheel at an old repo full of planning docs. It reads
everything, sorts it, converts what's worth keeping, and files the
rest. Round 2's corrections are folded in below; the two big ones
reshape sections 1 and 2, so please re-read those closely.

## 1. Better sorting buckets (#278)

**The question:** the original plan sorted every doc into three
buckets — *trash it*, *it's finished history*, *it's still to-do*.
The test showed three buckets aren't enough. What are the right ones?

**Proposed:** four buckets, and one rule from your round-2 note that
changes what "processing" means for all of them:

**The import is a move, not a copy** *(folded from round 2)*. As each
artifact is processed it is **removed from the source repo**, and the
untouched original is stored in a flywheel state folder
(`~/.local/state/flywheel/<org>/imports/<repo>/originals/`) so
nothing is ever lost. The source repo visibly shrinks as the import
progresses — "processed vs remaining" is literal, and nothing sits
converted in two places at once.

The buckets:

- **Trash** — no conversion; the original goes to the state folder
  like everything else, the row records why.
- **Never copy** — live AWS account numbers, network IDs,
  credentials (the test found real ones). These must not appear in
  our records at all: the row says "there were AWS identifiers here"
  and nothing more. Their originals stay only in the state folder.
- **Finished history** — decisions and findings worth keeping. Two
  questions before converting each one:
  1. *Is it already in the design books?* The test caught a doc
     claiming its write-up was still owed when someone had already
     written it into the books — converting it blind would duplicate
     a chapter. Check the books first; "already written, here's the
     chapter" is a recorded verdict, not a skip.
  2. *Is it still true?* The spike's own log admits older entries
     describe a replaced design. Stale-but-kept notes are filed as
     history with a dated warning — they never overwrite the books.
- **Still to-do** — routed by kind, not all to the tracker *(folded
  from round 2)*: design-level direction and forward intent go
  **into the design books** — bolt planning reads the books and
  carves bolt unit plans on demand, so the books are where future
  work belongs by default. Only work that is already a concrete,
  actionable item becomes a tracker item — at Backlog, never
  auto-approved.

Three rules the test forced, unchanged from round 2:

- **"Only copy" check.** Before skipping anything because "a summary
  exists elsewhere", search the main doc to confirm the content is
  actually repeated there (a link is not a repeat), then read it to
  judge worth. 42% of the test repo was the only copy of its
  information. Anything that is the only copy gets adopted whole
  into the destination design repo before the source repo can be
  retired.
- **Diagrams get saved whole** — approved round 2. Hand-drawn
  diagrams can't be summarized into text and no search detects them;
  keep the file as-is.
- **Split sections that change mid-way.** "Settled" docs routinely
  end with a "still open" tail — that tail is to-do work and gets
  its own row.

**Operating docs** (READMEs, how-to-run) *(reworked per round 2)*:
they are not left in place and not trashed. If the repo lives on,
they stay out of the import entirely. If the repo is being imported
out of existence, they are removed with everything else and their
originals kept in the state folder — recoverable, never lost, but
not converted into records they don't contain.

This all gets written into the promise document
(`../../decisions/onboarding-promise.md`) replacing its old
three-bucket paragraph.

## 2. Whose flywheel runs the import? (#267 — reframed per round 2)

Round 2 corrected the premise: **willdan has its own flywheel**,
pointing at willdan-blueprints. So the question was never "how does
agentplot import a willdan repo" — it's:

**Proposed: an import always runs inside the corpus org's own
flywheel.** The willdan flywheel imports kb-spike; records land in
willdan-blueprints, items land on willdan's tracker, originals land
in willdan's state folder. Nothing from a client corpus ever crosses
into another org's repos, public or private. What agentplot owns is
only the *process* — the import skill ships in the flywheel plugin,
and every org's fleet runs it on its own corpora.

Two consequences:

- **The #270 conversion into agentplot/flywheel was a mistake** —
  your words, round 2. A cleanup item is queued: remove the quoted
  willdan conversion content from the (public) agentplot/flywheel
  tree; the re-conversion happens later, inside the willdan flywheel,
  as that import's own work.
- **Small setup gap, not a design question:** willdan's fleet.yaml
  has no `tracker:` entry yet, so the to-do bucket has no landing
  spot there until that's configured. One checklist line, done when
  the willdan import actually runs.

## 3. Do we ever write specs into the client's old repo? (#268)

**Proposed: no, never.** A spec file only means something when
there's machinery reading it — sessions that build from it, a loop
that checks it. The old repo has none of that; a spec dropped there
goes stale, which is exactly the doc-rot this import exists to clean
up. If real construction later happens in that repo, specs get
written fresh at that point, from the imported records.

## 4. Turning a repo's roadmap into tracker items without making a mess (#269)

**Proposed** (table-review approved round 2; session-type note
folded):

- **You review one table, once.** The sorting report ends with a
  table of proposed items. Each row carries: a title, where it came
  from (repo, commit, file, lines), where it should be filed —
  **and which session type will work it** (research / planning /
  prototype / writeback, or "book material — reaches construction
  via bolt planning, no item at all"). You mark up that table; then
  the items get created in bulk, all at Backlog.
- **Trust the repo's own bookkeeping to skip finished work.** Repos
  track their own progress (a phasing section, a status file); the
  test caught a roadmap listing as "next" a phase the status log had
  marked done. We read the repo's own ledger first and drop what's
  already done.
- **Check against existing tracker items by reading, not string
  matching.** One query pulls all open items; a proposed item that's
  really the same work as an existing one becomes a comment on the
  existing item, not a duplicate.
- **Every created item says where it came from** — repo, commit,
  file, line range in its body. No new label system.

## 5. The instruction manual for all of this (#266)

**Proposed:** the process becomes `skills/import/` in the flywheel
plugin — full text drafted in `carrier-skill.md` beside this file,
with every round-2 correction baked in: the move-not-copy rule and
originals folder, the to-do routing into books vs tracker, the
session-type column in the items table, and the import running in
the corpus org's own fleet. If you approve this round, that draft
gets installed as-is.

One detail settled here: **the progress log lives in git, not on one
machine.** The log of what's-been-processed is a committed file in
the import's change directory
(`openspec/changes/<intent>/import/<repo>/processed.jsonl`). The
test showed why: the spike repo kept its own progress file in git,
and that's what let us compute "30 commits and 12 documents since
the last sweep" in seconds. A committed log is visible to you,
survives a machine change, and lets any fresh session resume where
the last stopped. (The *originals* folder from §1 is machine-local
state; the *log* is git.)
