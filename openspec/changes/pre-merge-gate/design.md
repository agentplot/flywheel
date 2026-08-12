## Context

See `proposal.md` — Why. What this section adds is the evidence ledger,
because almost every defect available in this change is a strength error:
writing a sentence more confidently than the tree has been measured for, or
writing a scoped instruction as standing prose.

`gate-prose-correction` (#35) carries the same ledger for the prose half.
The two co-land; see that change's design for the prose obligations and for
the conductor-authorized adjacent edits.

### What is measured, and where

| Fact | Strength | Source |
| --- | --- | --- |
| `[pre-merge]` hooks run on every shape of `wt merge`, including the clean fast-forward, after the rebase, with `HEAD` equal to the sha that lands and cwd the source worktree; a failure aborts with exit 1 and nothing landed | **measured**, ten shapes | `openspec/changes/gated-merge-guarantee/sessions/2026-08-12-ff-gate-facts/finding.md` |
| `[pre-commit]` fires only where `wt` itself writes a commit — never on the clean fast-forward, and not even on `--no-ff` | **measured** | same, `noff` and `ff-clean-2` rows |
| `--no-hooks` and `verify = false` each run **zero** hooks and exit 0 | **measured** | same, `nohooks` and `noverify` rows |
| Unapproved project hooks in a non-interactive environment abort with exit 1 and nothing landed — never an ungated green | **measured** | same, `lab/evidence/unapproved.txt` |
| The installed `wt 5fba0bd` **is** worktrunk 0.57.0 — the same nix store build the ten shapes were measured on | **measured** | same, its "Exercised, not read" bullet |
| Moving a granted hook template between hook event tables, with its text unchanged, **preserves the grant**; one added trailing space breaks it | **measured**, this bolt, negative control included | `openspec/changes/merge-gate-remedy/bolt.md` |
| `wt config approvals add` **does** enumerate `[post-start]` templates, `wt step copy-ignored` included | **measured**, this bolt, while reviewing #36 | `bolt.md` |
| `--yes` on `wt config approvals add` fails non-interactively and persists nothing | **measured**, same pass | `bolt.md` |
| `wt step copy-ignored --help`: `--from` "Defaults to main worktree" | **documented by the binary**, not a measurement of behaviour — `wt 5fba0bd`, read by this spec session | the binary's own help |
| Worktrunk's own documentation states **both** answers for a pre-\* hook table, in two copies both labelled version 1.0.0 | **documented, and self-contradictory** — see below | the two `hook.md` copies and `wt hook --help`, all quoted below |
| A trailing `-C` reads the wrong directory and reports no hooks | **PROSE ONLY, not measured** — its sole provenance is `skills/_reference/herdr.md`, added in `b5d308b` | filed for measurement as #64 |
| `wt hook show` listing exactly four project templates on this configuration | **EXPECTED, not measured** — see below | task 2.7 |
| Which worktree's *config* supplies the hooks when source and target differ | **NOT measured** — the lab ran symmetric config throughout | see below |
| What order the three `[pre-merge]` entries actually run in **on this tree** | **NOT measured**, and not measurable until the grant lets the hooks run | see below |

The version fact is in the table because a previous session raised an alarm
that the installed binary differs from the one the finding measured. It is
false. `finding.md` names the same nix store path. Any restatement of that
alarm in this change is a defect, not a caution.

### The four-template reading is expected, not measured — and why that matters

An earlier revision of this spec stated at measured strength that
`wt hook show` on this configuration lists four `(requires approval)`
templates, and cited `bolt.md`. `bolt.md` carries no such measurement, and
**no committed tree carries the four-template configuration** — so the tree
that would have been measured does not exist yet. A claim about the tree
that lands cannot rest on a tree that will not.

The reading itself is real, but its provenance is: `wt hook show` under
`wt 5fba0bd` on the **discarded** plan-mode branch `build/gate-remedy` at
`37118d9`, by a session that was subsequently stood down. That is
corroboration and nothing more; it is recorded here with full provenance
and is cited nowhere as evidence for the landing tree.

Task 2.7 produces the measurement on the tree that will actually land, and
the requirement is written as an expectation until it does.

### The two unmeasured facts, and why each is handled the way it is

**Config locus.** The spec forbids resolving it in either direction and
forbids a standing instruction about how to read a zero-hook merge. The
reasoning is worth keeping where a builder will read it: the scoped
reading — "for *this* bolt's merge-back, zero hooks is the asymmetric-config
question answering itself, neither a green nor a defect" — is correct as an
instruction about one merge, and it is what `bolt.md` says. Transplanted
into standing prose it becomes a general licence telling every future agent
to shrug at an ungated merge. That is the precise symptom `finding.md`
records as having "no way to tell it apart from a gated merge", and it is
why this intent exists at all. It would also be a false dichotomy: two other
causes of a zero-hook merge are measured (`nohooks`, `noverify`) and a third
is documented in `herdr.md` without ever having been measured. Cite
`bolt.md`; do not reproduce it.

**Execution order.** Dropped, and the conclusion is unchanged under every
reading. The rationale, however, has now been wrong twice in this bolt in
opposite directions, so here is what was actually read, on this machine,
with paths and verbatim quotes. All three are documentation; none is a
measurement of this tree.

- `/Users/chuck/.claude/plugins/marketplaces/worktrunk/skills/worktrunk/reference/hook.md`
  — "For pre-\* hooks, commands in a table run sequentially. For post-\*
  hooks, they run concurrently in the background." The same sentence is in
  that marketplace's `docs/content/hook.md`. This copy has no
  "table … run concurrently" sentence at all.
- `/Users/chuck/.claude/plugins/cache/worktrunk/worktrunk/1.0.0/skills/worktrunk/reference/hook.md`
  — "A table is multiple commands that run concurrently:", with no pre-\* /
  post-\* distinction anywhere.
- `wt hook --help` on `wt 5fba0bd` — "A table is multiple commands that run
  concurrently:", agreeing with the cache copy.

Both `hook.md` copies are labelled **version 1.0.0** and they contradict
each other on the exact construct at issue: a pre-\* hook table, which is
what `[pre-merge]` is here. This is not the table-versus-pipeline conflation
it was at one point taken for — the marketplace sentence says "commands in a
table" for "pre-\* hooks" in so many words. The pipeline construct is
described separately in both copies and is not involved.

So the head comment asserts nothing, for the reason that survives all of
this: **documentation is not a measurement of what happens here**, and where
the documentation disagrees with itself the point is only sharper. That is
the standard `finding.md` set when it ran ten shapes rather than quoting
`wt hook --help`. Ordering cannot be measured on this tree until the grant
lets the hooks run, so it is a named measurement for the acceptance run —
and that run now has both documented candidates on record to check against.

## Goals / Non-Goals

**Goals:**

- Make the gate real, and let the file that configures it describe it at the
  strength it is known at.
- Leave every claim re-checkable: cite by anchor or quoted phrase, never by
  line number.
- Leave a configuration the operator can grant in one interactive pass.

**Non-Goals:**

- Adding, removing, or retuning what the three checks test.
- Any prose file — that is `gate-prose-correction` (#35), co-landing.
- The operator's grant (#33), and the fleet-layer check that the grant
  exists (#36).
- Resolving either unmeasured fact above. A change that resolves one of them
  is asserting past its evidence.

## Decisions

### Two changes, one branch, one merge-back

`skills/construction/SKILL.md`'s Spec stage sets the grain: "one
spec-driven change per assertion … a session may write several changes, but
the change grain is the assertion: its record binds one change id and one
landing ref." So #34 and #35 are two change ids.

They co-land on one branch in one pass, because #35's central sentence is
false before this change lands and stale-wrong after it: there is no
ordering of the two that leaves the repo correct in between. What the design
rejects is *sequencing* them, not separating them. Co-landing satisfies both
the grain rule and the one-pass necessity.

### A capability of its own, split from the description

`openspec/specs/` was read for an existing home. No capability carries a
requirement about which hook table this repo's checks live under. This is
`flywheel-merge-gate`, new — sibling to `flywheel-fleet-approvals` (#36),
which checks that the gate's grants exist, and to
`flywheel-gate-description` (#35), which governs what the machinery says
about the gate. The split follows the assertions: one is mechanism, one is
description.

### The head comment stays with the configuration

#34's assertion owns the head comment explicitly — "its count of the checks
it defines matches the number defined" — so the block is specced here rather
than with the prose. The count claims in `devenv.nix` and
`.github/workflows/gates.yml` are **not** here: #34's own boundary says it
"does not touch `.github/workflows/gates.yml`", and those corrections are
conductor-authorized adjacent scope carried by `gate-prose-correction`.

### The config-locus requirement is stated in both changes, deliberately

It is a property of a *pair* of files, and the grain rule puts each file in
a different change. Each change states its own file's obligation and
cross-references the other, so neither is landable while satisfying its own
requirement and violating the joint one. A reviewer checking only one change
still sees the joint constraint.

## Risks / Trade-offs

**Editing `.config/wt.toml` after the operator's grant silently un-grants
the hooks.** → Approvals key on verbatim template text, measured twice over.
From the moment this change's template text is reported for #33, nothing
touches the file — not a typo fix, not a rebase fixup — until the grant is
taken. "Grant on final text" means final *after review*, not merely after
build. A build session that discovers it wants to change a template string
after the report stops and tells its conductor.

**The merge that lands this change is the first merge the new table can
govern.** → Unapproved hooks fail closed (exit 1, nothing landed), so the
failure mode is a stoppage rather than an ungated green. The sequence is the
bolt record's: author → grant (#33) → merge. It holds under either answer to
the config-locus question — if source config governs, the merge-back gates;
if target config governs, the landing on main does, and the grant was merely
taken earlier than it strictly had to be.

**A zero-hook merge-back could be read as a defect and worked around.** →
The spec forbids the standing instruction that would license shrugging at
it, and the bolt record carries the scoped reading for this one merge. The
acceptance run records what actually happened; it does not decide it in
advance.

**Line numbers drift, and phrases wrap.** → Every site is anchored by
heading or quoted phrase. `herdr.md`'s gate sentence was `:184` at
`c7697d6`, `:202` before this branch was rebased, and `:215` after — three
positions inside one bolt. Separately, quoted phrases in
`skills/construction/SKILL.md` are **line-wrapped in the source**, so a
literal single-line `grep` for them returns nothing; search on a fragment
that does not span a line break.

**Prose written to a tree that moved.** → Every neighbour this change
asserts anything about is re-read from disk at build time before the claim
is trusted. Siblings on this bolt are live, and `main` has already moved
under this branch once.

## Migration Plan

Not a deployment. The ordering that matters is the bolt's, and it is
`openspec/changes/merge-gate-remedy/bolt.md`'s to state:

1. Author and commit both changes' edits on this branch. Do not merge.
2. Report the four hook template strings verbatim, with the worktree path,
   for #33. From that moment `.config/wt.toml` is frozen.
3. The operator grants interactively, cwd inside that worktree. The listing
   must show four templates, one of them `wt step copy-ignored`. Three rows
   is `main`'s three-check shape — the wrong checkout — and the remedy is to
   re-run with cwd in the construction worktree.
4. Merge back, both changes together.

Rollback is `git revert` of the commits; nothing outside the repo changes
except the operator's approvals store, which is additive and keyed on text
that would no longer exist.

## Open Questions

None that block this change. The two unmeasured facts above are named in the
spec as things the configuration must *not* resolve, and both are named
measurements for this bolt's acceptance run.
