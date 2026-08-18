# Importing a messy repo — five decisions, round 2

You point flywheel at an old repo full of planning docs. It reads
everything, sorts it, converts what's worth keeping, and files the
rest. Last week we tested that process on the willdan
knowledgebase-spike repo, and the test broke the sorting scheme in a
few specific ways. This round fixes the scheme and settles four
decisions that were waiting on the test.

Each section below is one decision. Say yes, or mark up what's wrong.

## 1. Better sorting buckets (#278)

**The question:** the original plan sorted every doc into three
buckets — *trash it*, *it's finished history*, *it's still to-do*.
The test showed three buckets aren't enough. What are the right ones?

**Proposed:** four buckets, plus two follow-up questions asked about
anything in the "finished history" bucket:

- **Trash** — noted that we saw it, then ignored.
- **Never copy** — things like live AWS account numbers, network IDs,
  and credentials that were in the spike repo. These must not get
  copied into our records at all. We write down "there were AWS
  identifiers here" and nothing more. (The test found real ones.)
- **Finished history** — decisions and findings worth keeping. But
  before converting each one, answer two questions:
  1. *Is it already in the design books?* The test found a design doc
     that claimed its write-up was still owed — but someone had
     already written it into the books. Blindly converting it would
     have created a duplicate chapter. So: check the books first.
  2. *Is it still true?* The spike's own log admits its older entries
     describe a design that was later replaced. Old-but-kept notes
     get filed as history with a "this was true as of July" warning —
     they never overwrite the current books.
- **Still to-do** — becomes tracker items, all waiting for your
  approval, none auto-approved.

Three extra rules the test forced:

- **"Only copy" warning.** Several times, a doc looked safe to skip
  because "a summary exists elsewhere" — and the summary turned out
  to be just a link, not the content. 42% of the repo was the *only
  copy* of its information. So before skipping anything, we actually
  search the main doc to confirm the content really is repeated
  there, then read it to see if it's worth keeping. Anything that's
  the only copy gets saved whole before the old repo is deleted —
  even if nobody needs to read it today.
- **Diagrams get saved whole.** Five reports had hand-drawn diagrams.
  You can't "summarize" a diagram into text, and no search will
  detect that. Diagrams are always the only copy — keep the file
  as-is instead of converting it.
- **Split sections that change mid-way.** Docs marked "settled"
  routinely ended with a "still open" or "what has to change" tail —
  that tail is to-do work even though the section says settled. Sort
  those tails separately.

And one small call: READMEs and how-to-run docs aren't history or
to-do — they're the repo's operating manual. One question to you per
import: if the repo is being torn down, trash them; if it lives on,
leave them alone entirely.

This all gets written into the promise document
(`../../decisions/onboarding-promise.md`) replacing its old
three-bucket paragraph.

## 2. Where does imported work end up when the repo belongs to a client org? (#267)

**The question:** the spike repo belongs to WilldanGroup, not
agentplot. When we convert its history into records and to-do items —
whose repos and whose tracker do those land in?

**Proposed: they land in the client's org.** Records go in the
client's design repo (willdan-blueprints), to-do items go on a
willdan tracker. Reasons: the converted records are all *about*
willdan's design and reference willdan's books — filing them in
agentplot's tracker would pile up work agentplot agents can't act on,
and would permanently copy client material into our org.

Willdan doesn't have a flywheel tracker set up yet. Until it does,
conversions get done fully but **parked**: each converted file says
exactly where it will land, and a log marks it "not landed yet,
waiting on #267 setup". Once the willdan tracker exists (a small
setup checklist, not a design problem), landing is mechanical.

**One thing you specifically need to rule on:** the agentplot
`flywheel` repo is **public on GitHub**, and last week's test
committed converted willdan design content — quoted at length — onto
its main branch. Going forward I propose: parked conversions for a
client corpus live in *the client's* design repo (private, and we
already have access), and nothing quoted from a client corpus goes in
our public repo. But the willdan content already sitting on public
main is your call: leave it, or scrub it.

## 3. Do we ever write specs into the client's old repo? (#268)

**The question:** flywheel keeps records in its own format. Should an
import also write OpenSpec spec files into the source repo itself?

**Proposed: no, never.** A spec file only means something when
there's machinery reading it — sessions that build from it, a loop
that checks it. The old repo has none of that. A spec dropped in
there would just sit and go stale — which is exactly the kind of doc
this whole import process exists to clean up. If someone later does
real construction work in that repo, specs get written fresh at that
point, from the imported records.

## 4. Turning a repo's roadmap into tracker items without making a mess (#269)

**The question:** a repo's roadmap can imply dozens of to-do items.
How do we create those in bulk without duplicates, without re-queuing
work that's already done, and without you approving them one at a
time?

**Proposed:**

- **You review one table, once.** The sorting report ends with a
  table of proposed items — each with a title, where it came from,
  and where it should be filed. You mark up that table; then the
  items get created in bulk, all at Backlog.
- **Trust the repo's own bookkeeping to skip finished work.** The
  test showed repos track their own progress (a phasing section, a
  status file) — and one roadmap page listed as "next" a phase the
  status log had already marked done. We read the repo's own ledger
  and drop anything already done before it ever reaches the table.
- **Check against existing tracker items by reading, not string
  matching.** One query pulls all open items; if a proposed item is
  really the same work as an existing one, it becomes a comment on
  the existing item instead of a duplicate.
- **Every created item says where it came from** — repo, commit,
  file, and line range in its body. No new label system.

## 5. The instruction manual for all of this (#266)

**The question:** the promise says the import process gets written
down once as a skill — the checklist a session follows each time.
Where does it live, and what does it say?

**Proposed:** it becomes `skills/import/` in the flywheel plugin. The
full text is drafted in `carrier-skill.md` next to this file — it's
the four steps (inventory → sort → convert → log) with every rule
from section 1 baked in. If you approve this round, that draft gets
installed as-is.

One detail settled here: **the progress log lives in git, not on one
machine.** The promise guessed the log of what's-been-converted would
sit in flywheel's local state folder. The test argued otherwise: the
spike repo kept its own progress file *in git*, and that's precisely
what let us compute "30 commits and 12 documents have landed since
the last sweep" in seconds. A log in git is visible to you, survives
a machine change, and lets any fresh session resume where the last
one stopped. So: the log is a committed file in the import's change
directory.
