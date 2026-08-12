# Decision draft: which remedy makes a `wt merge` ✓ mean the gate ran (#14)

- **Item:** #14 · **Type:** planning · **Question record:**
  `../../questions/fast-forward-gate-hole.md`
- **Evidence:** `../2026-08-12-ff-gate-facts/finding.md` — the option set is
  closed and costed by lab; nothing below re-litigates it. `ff = false`, an
  upstream fix, and `verify` as a selector are dead on that evidence.

Three choices below. Each has a marked recommendation; your annotation is the
word that closes it.

## Choice 1 — which hook table carries the gate

`[pre-merge]` hooks run on every shape of `wt merge` — the clean fast-forward
included — after the rebase, in the source worktree, with `HEAD` equal to the
sha that lands, and a failure aborts with nothing landed. `[pre-commit]` fires
only where `wt` itself writes a commit (a dirty tree, or `squash = true`).
Both survivors configure `[pre-merge]`; the choice is whether `[pre-commit]`
keeps a copy.

**Option A — `[pre-merge]` alone (recommended).** Move the three checks.

- The guarantee the loop leans on is about the tree that lands, and
  `[pre-merge]` is where that is true. Checks run exactly once per merge, on
  every shape.
- One table means one copy of each command. Approvals key on template text,
  so a single grant covers it, and there is no second copy to drift.
- What A gives up: on the shapes where `wt` writes a commit, the bad commit
  gets written before the merge aborts — gated after creation instead of
  refused at creation. Nothing ungated lands either way; the branch keeps a
  commit the agent must fix. With `squash = false` and conductors merging
  already-committed trees, these shapes are rare in this loop.

**Option B — both tables.** The same three commands under `[pre-commit]` and
`[pre-merge]`.

- Buys the earlier failure on the rare shapes, at ~1.2 s of double-run there.
- Costs a second copy of every command: edits must touch both tables or they
  drift, and a drifted copy re-keys its approval while the other keeps the
  old grant — a quiet way to reintroduce a merge that aborts unexpectedly.

## Choice 2 — whether the conductor runs an explicit gate step

**Recommended: no standing explicit step.** The explicit step was a remedy
for the hole; with `[pre-merge]` configured the hole is closed and `wt merge`
aborting on failure *is* the gate. A routine `wt hook pre-merge` before every
merge would run the checks twice on every shape and reintroduce a
conductor-asserted green beside the tool-produced one.

The one place the explicit step earns its keep is the retry path the
reference already prescribes: after a gate failure, the worktree's agent
fixes and re-runs `wt hook pre-merge`, then the conductor merges again. That
instruction — a silent pass today — becomes genuinely functional the moment
`[pre-merge]` exists, and stays.

## Choice 3 — the `node_modules` precondition

`[pre-merge]` runs in the source worktree, and `scripts/check-site.mjs` exits
2 there without `jsdom`. No lifecycle hook installs it, so the first gated
merge from a fresh worktree aborts on a missing install, not a real defect.
Latent today only because nothing runs the checks at merge time; the remedy
makes it bite.

**Option A — a `[post-start]` hook warming the worktree (recommended; taken
as `wt step copy-ignored`).** The hook copies gitignored files —
`node_modules`, caches — from an existing worktree instead of paying a fresh
install: worktrunk's "eliminate cold starts" pattern
(worktrunk.dev/tips-patterns/#eliminate-cold-starts). Worktrees cut with
`wt switch --create` get it automatically; herdr-created worktrees fire no
`wt` lifecycle hooks, and the reference already instructs
`wt -C <path> hook post-start` right after creating one, so the same hook
covers both paths. Cost: a fourth template needing approval — it joins the
same grant #16 settles. Residual: the copy carries what the source worktree
has, so a machine whose primary checkout lacks `node_modules` still surfaces
`check-site`'s exit 2 — fail closed, remedied by one `npm ci` there.

**Option B — a documented manual step** ("run `npm ci` before merging").
Cheaper to land, but it is exactly the silent must-happen-first step this
intent exists to remove, enforced only by an abort at merge time.

Scope note: the intent excludes "adding, removing or retuning checks"; a
`post-start` install is a precondition of running the checks, not a check,
so this draft treats it as in scope. Annotate if you read the boundary
differently and it becomes its own queued item instead.

## Consequences, whichever way the choices go

Queued as items on the decision, not edited by this session:

1. **Configure the chosen table(s) in `.config/wt.toml`** and rewrite its
   comment block — the head comment says the hooks run "before the commit,
   on the exact tree that lands" and calls "all four" independent while
   defining three; both sentences move with the remedy.
2. **Correct `skills/_reference/herdr.md` in the same pass** — under
   "Merging through the gate", the claim that `wt merge` "runs the repo's
   `.config/wt.toml` checks on the exact rebased tree that lands" becomes
   true only when the config change lands, and should name the mechanism
   (`[pre-merge]`, after the rebase, every shape); the "fix and re-run
   `wt hook pre-merge`" retry instruction becomes functional and stays.
3. **Ordering:** the config change must not land before this repo's
   approvals exist (#16). The moment `[pre-merge]` is configured, every
   merge aborts until the templates are approved — fail-closed, but a fleet
   stoppage if landed out of order.
