# Draft: where an intent's records live, and how every design write lands

Item #322, raised by the writeback of #320: the flywheel book lives in
`agentplot/blueprints`, this intent's records live in
`agentplot/flywheel`, and the book contradicts itself about how a
record reaches main. Two coupled decisions and one naming call.

## The facts on the ground

- `fleet.yaml` homes the flywheel book at `blueprints/main/books/flywheel`
  with `repo: flywheel/main` — the intent loop binds to the flywheel
  repo, worktrees it for every design session, and never touches
  blueprints.
- #320's writeback therefore pushed its chapters **straight to
  `agentplot/blueprints@main`** under ordinary git credentials — no
  branch, no gate — because no `sess/*` branch of the flywheel repo can
  carry blueprints files.
- The book says three incompatible things:
  - `lifecycles.md` *The intent's change directory*: records live in
    "the book's own repo", and "the record is written onto the book
    repo's main as the sessions work … nothing of it waits on a branch".
  - `sessions.md` *Worktrees*: "the session never merges its own branch
    and never writes main directly" — everything goes `sess/*` → gate.
  - `design-loop.md` names the escape: work is queued for "a chapter in
    a repo the session holds no worktree for".
- The machinery (`_flywheel_intent.py`) matches `sessions.md`: it
  worktrees, launches, and merges the `sess/*` branch through `wt merge`.
  Nothing anywhere writes a record to any main directly.
- The naming disagrees too: the loop scaffolds and prompts
  `openspec/changes/<slug>/`; the book says `intent-<slug>` twice
  (`lifecycles.md`, `design-loop.md`), mirroring the milestone.

## Decision 1 — where the records live

**Option A (recommended): records follow the book; the loop worktrees
the book repo.** `openspec/changes/intent-<slug>/` lives in the repo
that holds the intent's book — for the flywheel's own intents, that is
`agentplot/blueprints`. The intent loop's session worktree is cut from
the **book repo**, not the fleet's built repo: the session's records
and its chapter rewrites ride one `sess/*` branch through one gate.
`fleet.yaml`'s book entry already names both repos; the loop learns to
worktree the book side. The current filing of flywheel intents in
`agentplot/flywheel` becomes a known anomaly, migrated per-intent when
each is next touched (or at milestone close), never by a big-bang move.

**Option B: records live beside the loop, the book rule is amended.**
Records stay in the fleet's repo (where the machinery already
worktrees); `lifecycles.md` is rewritten to say records live beside the
*loop*, and the "no worktree for the book repo" exception becomes the
permanent, normal path for every chapter write of a remote book. That
institutionalizes what #320 did: every book write for this fleet is an
ungated push to another repo's main, in flat contradiction of
`sessions.md` — which would then also need an amendment carving out
remote books. Two write paths, forever.

Why A: the book already states it ("the records follow the book, never
the other way"); it makes the #320 shape impossible rather than
routine; one write path survives; and the blueprints repo's gate
(mdbook build, mermaid parse) actually runs on chapter writes instead
of being bypassed. The cost is a loop change — worktree source moves
from `repo:` to the book's repo — and a records migration, both
assertion-sized.

## Decision 2 — how the write lands

**One write path (recommended, forced by A): everything a design
session produces — records and chapters — rides its `sess/*` branch,
and the loop merges it through the repo's gate.** The `lifecycles.md`
sentence "written onto the book repo's main as the sessions work —
nothing of it waits on a branch" is the wrong one of the pair and is
rewritten: the record waits on the branch exactly as long as the
session runs; the merge at settle is what makes it live. Liveness for
sibling sessions and the planner is main-at-merge, same as chapters
today — one writer per branch, merged at each session's close, is
prompt enough for a corpus read between sessions, not during them.

The `design-loop.md` escape ("a chapter in a repo the session holds no
worktree for") survives as the genuine remainder: a settlement that
stales a chapter of a *different* book — another intent's, another
fleet's — still queues an item on that book's home. It stops being the
normal path for the intent's own book.

## Decision 3 — the directory name

**`intent-<slug>` stands; the machinery is fixed.** The book's mirror
rule (`intent-<slug>`, `bolt-<slug>`, matching the milestones) earns
its keep once records land in blueprints, where one
`openspec/changes/` namespace holds intent records beside bolt records.
The loop's bare-slug scaffold and work-order prompt are one assertion
to fix. Existing bare-slug directories rename at migration.

## Consequences (queued if this closes)

- Assertion: the intent loop worktrees the book repo named in
  `fleet.yaml` for design sessions; `repo_dir` splits into
  fleet-repo (tracker-side operations) and book-repo (worktrees,
  records, merges).
- Assertion: the loop's scaffold and work-order prompt say
  `openspec/changes/intent-<slug>/`.
- Chapter rewrite (this session's own close, if within reach — else
  queued): `lifecycles.md` *The intent's change directory* loses the
  straight-to-main sentence; `design-loop.md`'s escape clause reworded
  to the different-book remainder.
- Migration item: move the flywheel intents' records from
  `agentplot/flywheel` to `agentplot/blueprints` under `intent-<slug>`
  names, per-intent as touched.
- Known anomaly until migrated: this very session's records live at
  `agentplot/flywheel:openspec/changes/writeback-in-session/`.

## Open question (not closed by this draft)

The intent records of this thread sit on **unmerged `sess/*` branches**
of the flywheel repo — `main` holds no
`openspec/changes/writeback-in-session/` at all. Whether those merges
are pending or lost is a machinery question routed via the session
report, not this decision.
