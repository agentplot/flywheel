## 1. Re-read the neighbours from disk before trusting a claim

Siblings on this bolt are live, `main` has already moved under this branch
once, and line numbers in these files have drifted three times inside this
bolt. Locate every site by heading or quoted phrase.

- [x] 1.1 Re-read `.config/wt.toml` and confirm it still holds the three
      checks under `[pre-commit]` alone, with both false comment sentences
      present. If it does not, stop — someone else has moved it.
- [x] 1.2 Re-read `openspec/changes/merge-gate-remedy/bolt.md` for the
      ordering, the scoped zero-hook reading this change cites rather than
      reproduces, and the approvals measurements. It is the conductor's
      file and may be ahead of this branch — read `main`'s copy if so.
- [x] 1.3 Confirm the co-landing sibling `openspec/changes/gate-prose-correction/`
      is present on this branch. Neither change is landable alone.

## 2. `.config/wt.toml` — make the gate real

- [x] 2.1 Move `manifests`, `paths` and `site` to a `[pre-merge]` table and
      delete `[pre-commit]` entirely, leaving no copy of any of the three
      commands anywhere else in the file.
- [x] 2.2 Add a `[post-start]` entry running `wt step copy-ignored`.
- [x] 2.3 Rewrite the head comment block to describe the mechanism the file
      then configures: after the rebase, before the merge to target, every
      shape of `wt merge` including the clean fast-forward, `HEAD` equal to
      the sha that lands, cwd the source worktree, failure aborts with
      nothing landed. Keep the per-check rationale paragraphs.
- [x] 2.4 Verify neither "during `wt merge` before the commit, on the exact
      tree that lands" nor "All four are independent" survives in any form,
      and that the block asserts neither sequential nor concurrent
      execution.
- [x] 2.5 Verify the block names the config-locus question as open, carries
      no standing instruction about a zero-hook merge, and does not state
      "`wt merge` runs these" flatly — which reads as source-config-governs
      asserted as fact.
- [x] 2.6 `grep` each of the three command strings and confirm exactly one
      occurrence each, all inside `[pre-merge]`.
- [x] 2.7 **Produce the four-template measurement on the tree that lands.**
      Run `wt hook show` in this worktree against the committed
      `.config/wt.toml` and record what it lists, with the branch, the
      commit sha and the `wt` version. Four project templates are
      *expected*, one of them `wt step copy-ignored`, each reading
      `(requires approval)` — the grant is #33 and is not yet taken. This is
      the first tree on which this can be measured, so report what it
      actually says rather than confirming what was expected. Anything
      other than four is a stop-and-report, not an adjustment.

## 3. Verify on the committed tree

- [x] 3.1 Run the three checks directly and confirm green:
      `sh scripts/validate-manifests.sh`, `node scripts/check-paths.mjs`,
      `node scripts/check-site.mjs`. If `check-site.mjs` exits 2 on missing
      `jsdom`, warm the worktree with `wt step copy-ignored` — that is the
      `[post-start]` payload being exercised, and worth reporting.
- [x] 3.2 `openspec validate --strict` green.
- [x] 3.3 Record what could **not** be verified and why: `wt hook pre-merge`
      and `wt merge` actually executing the three checks both require #33's
      grant, and a non-interactive attempt is the stop-and-report case
      `gate-prose-correction` documents. `--yes` is forbidden. That evidence
      belongs to the merge-back and the acceptance run.

## 4. Commit, then freeze

- [x] 4.1 Commit by pathspec (`git add -- <paths>`, then
      `git commit -F <file> -- <paths>`) with `Refs: #34`. Never `-a`, never
      `add -A`, never a closing keyword. Note that `--` must follow the
      options, not precede them.
- [x] 4.2 Report the four hook template strings **verbatim**, with the
      worktree path and the commit sha, for the conductor to take to #33.
- [x] 4.3 **From that report onward, nothing touches `.config/wt.toml`** —
      not a typo fix, not a rebase fixup — until the operator confirms the
      grant. Text edited after a grant silently un-grants it. If the
      code-review names a defect in that file, the template text changes and
      the grant must be re-taken; that is the conductor's call, not a fix to
      slip in.
- [x] 4.4 Do not merge. Do not push. The merge-back is the conductor's, it
      carries both changes together, and it waits on the grant.

## 5. Comment corrections after the code-review (comments only — the freeze holds)

**The freeze protects template strings, not the file.** Approvals key on the
command text, measured twice in this bolt: a template moved between hook
tables with unchanged text kept its grant, and the negative control was a
trailing space *inside the command*. Both edits below are in comments, which
are part of no template. If any fix here would require touching a command
string, **stop and report** — that re-takes the operator's grant and is the
conductor's call.

- [ ] 5.1 Capture the baseline first: run `wt hook show` and save its exact
      output before editing anything.
- [ ] 5.2 The `[post-start]` comment: remove "the cheaper path to the same
      state". Neither half is measured — `npm ci` is timed in `finding.md`
      but `wt step copy-ignored` is timed nowhere, and "the same state" is
      contradicted by this bolt's own residual, since the copy delivers
      `jsdom` only if the source worktree has it. Say instead that
      `decisions/gate-runs-under-pre-merge.md` chose the copy over a fresh
      `npm ci`, and that worktrunk offers it as its eliminate-cold-starts
      step.
- [ ] 5.3 The head comment: qualify the shapes claim to **"on every shape of
      `wt merge` that does not suppress them"**, the clean fast-forward
      included, naming `--no-hooks` and `--no-verify` as the suppressing
      shapes. The bare universal is refuted by the `nohooks` and `noverify`
      rows of the very finding cited for it. Take the corrected wording from
      `openspec/changes/merge-gate-remedy/bolt.md` at `28fb534`.
- [ ] 5.4 Reflect the bolt record's other correction: it no longer says a
      zero-hook merge-back is the config-locus question answering itself.
      Four causes produce zero hooks, and this bolt's merge-backs now run
      from inside the worktree with no `-C`. **Cite the record; do not
      reproduce its scoped reasoning as standing prose** — that reasoning
      has already moved once.
- [ ] 5.5 **Prove the grant is untouched**: run `wt hook show` again and
      confirm it lists the same four templates **byte-identical** to the
      5.1 baseline. A diff of one character means a template changed —
      stop and report rather than adjusting.
