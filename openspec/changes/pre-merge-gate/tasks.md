## 1. Re-read every neighbour from disk before trusting a claim

Siblings on this bolt are live and line numbers in these exact files have
already drifted once. Locate every site by heading or quoted phrase.

- [ ] 1.1 Re-read `.config/wt.toml` and confirm it still holds the three
      checks under `[pre-commit]` alone, with the two false comment
      sentences present. If it does not, stop — someone else has moved it.
- [ ] 1.2 Re-read `skills/_reference/herdr.md` and locate, by phrase: the
      "Merging through the gate" heading; "The gate runs the repo's
      `.config/wt.toml` checks on the exact rebased tree that lands"; the
      retry paragraph naming `wt hook pre-merge`; "Hook approval is the
      operator's one-time `wt config approvals add`"; the `--no-hooks`
      paragraph beginning "No `--no-hooks`."; and the trailing-`-C` warning.
- [ ] 1.3 Re-read `skills/construction/SKILL.md` and locate, by phrase, the
      Build stage's "The repo's commit checks run on every push" and "the
      merge gate runs on the rebased tree at merge-back", and the Merge
      stage's "full hooks, never weakened" (which is not edited).
- [ ] 1.4 Re-read `devenv.nix` and confirm **both** miscounts are present:
      the packages comment's "Two gates … node runs both checks" and the
      `gates` script comment's "the same two commands". Confirm the `gates`
      script defines exactly three check commands and which runtime runs
      each.
- [ ] 1.5 Re-read `.github/workflows/gates.yml`'s head comment and confirm
      "The same four checks".
- [ ] 1.6 Re-read `openspec/changes/merge-gate-remedy/bolt.md` from `main`
      (it is the conductor's file and is ahead of this branch) for the
      ordering and the scoped zero-hook reading this change cites rather
      than reproduces.
- [ ] 1.7 Confirm the three no-edit sites still read as design.md records
      them — `AGENTS.md` "before a merge", `README.md`'s Gates section,
      `openspec/specs/flywheel-construction-skill/spec.md` "the tree that
      lands". If any is false rather than merely not-yet-true, stop and
      report instead of editing.

## 2. `.config/wt.toml` — make the gate real

- [ ] 2.1 Move `manifests`, `paths` and `site` to a `[pre-merge]` table and
      delete `[pre-commit]` entirely, leaving no copy of any of the three
      commands anywhere else in the file.
- [ ] 2.2 Add a `[post-start]` entry running `wt step copy-ignored`.
- [ ] 2.3 Rewrite the head comment block to describe the mechanism the file
      then configures: after the rebase, before the merge to target, every
      shape of `wt merge` including the clean fast-forward, `HEAD` equal to
      the sha that lands, cwd the source worktree, failure aborts with
      nothing landed. Keep the per-check rationale paragraphs.
- [ ] 2.4 Verify neither "during `wt merge` before the commit, on the exact
      tree that lands" nor "All four are independent" survives in any form,
      and that the block asserts neither sequential nor concurrent
      execution.
- [ ] 2.5 Verify the block names the config-locus question as open and does
      not state "`wt merge` runs these" flatly, which reads as
      source-config-governs asserted as fact.
- [ ] 2.6 `grep` each of the three command strings and confirm exactly one
      occurrence each, all inside `[pre-merge]`.
- [ ] 2.7 Run `wt hook show` in the worktree and confirm it parses the file
      and lists exactly four project templates. Expect every one to read
      `(requires approval)` — the grant is #33 and is not yet taken.

## 3. `skills/_reference/herdr.md` — describe the gate that then exists

- [ ] 3.1 Under "Merging through the gate", replace the bare-guarantee
      sentence with the `[pre-merge]` mechanism at measured strength.
- [ ] 3.2 Name the config-locus question as open, at the same strength the
      `.config/wt.toml` head comment uses. Cite
      `openspec/changes/merge-gate-remedy/bolt.md` for this bolt's scoped
      reading rather than reproducing it, and write **no** standing
      instruction about how to read a merge that runs zero hooks.
- [ ] 3.3 Keep the retry paragraph — fix, re-run `wt hook pre-merge`, merge
      again — present and unchanged in substance.
- [ ] 3.4 Beside the existing "Never bypass with `--yes`" sentence, add the
      stop-and-report rule for
      `Cannot prompt for approval in non-interactive environment`, naming
      both non-options (`--yes`; hand-running the check scripts) and framing
      the stoppage as closed-failure rather than hazard.
- [ ] 3.5 Verify no sentence claims or implies that one
      `wt config approvals add` enumerates or covers all four templates.
      What is measured is `wt hook show`'s four `(requires approval)` rows.
- [ ] 3.6 Rewrite the `--no-hooks` paragraph: drop "This repo configures no
      `wt` lifecycle hooks today", and give the gate — not the warm-up — as
      the reason the flag is never passed. State any cold-worktree
      consequence only at measured strength.
- [ ] 3.7 Leave the squash sentence alone. It is false and it is filed as
      its own item; it is not this change's.
- [ ] 3.8 Do not go looking for a second `herdr.md`. There is one tracked
      file; the copy under `~/.claude/plugins/cache/flywheel/` is a release
      artifact that updates by releasing.

## 4. `skills/construction/SKILL.md` — the Build stage

- [ ] 4.1 Rewrite the Build stage sentence to state the `[pre-merge]`
      mechanism in place of "the merge gate runs on the rebased tree at
      merge-back".
- [ ] 4.2 Make the "commit checks run on every push" clause deliberate and
      true — `[pre-commit]` is empty after task 2, and what runs on push is
      `.github/workflows/gates.yml` — or drop it. Do not leave it as an
      incidental survivor.
- [ ] 4.3 Leave the Merge stage's "full hooks, never weakened" untouched.

## 5. The count claims

- [ ] 5.1 `devenv.nix` packages comment: correct "Two gates" to three, and
      fix "node runs both checks" so the runtime claim is true of the
      `gates` script (`sh` runs `validate-manifests.sh`; `node` runs the
      other two).
- [ ] 5.2 `devenv.nix` `gates` script comment: "the same two commands" →
      three.
- [ ] 5.3 `.github/workflows/gates.yml` head comment: "The same four
      checks" → three.
- [ ] 5.4 Confirm all four count claims — the two in `devenv.nix`, the one
      in `gates.yml`, and `.config/wt.toml`'s rewritten block — agree with
      each other and with the `gates` script.

## 6. Verify on the committed tree

- [ ] 6.1 Run the three checks directly and confirm green:
      `sh scripts/validate-manifests.sh`, `node scripts/check-paths.mjs`,
      `node scripts/check-site.mjs`. If `check-site.mjs` exits 2 on missing
      `jsdom`, warm the worktree with `wt step copy-ignored` — that is the
      `[post-start]` payload being exercised, and worth reporting.
- [ ] 6.2 `openspec validate --strict` green.
- [ ] 6.3 Confirm no stale gate phrasing survives outside `openspec/`
      records that quote it deliberately.
- [ ] 6.4 Record what could **not** be verified and why: `wt hook pre-merge`
      and `wt merge` actually executing the three checks both require #33's
      grant, and a non-interactive attempt is the stop-and-report case this
      change documents. `--yes` is forbidden. That evidence belongs to the
      merge-back and the acceptance run.

## 7. Commit, then freeze

- [ ] 7.1 Commit by pathspec (`git add -- <paths>`, `git commit -- <paths>`)
      with `Refs: #34` and `Refs: #35`. Never `-a`, never `add -A`, never a
      closing keyword.
- [ ] 7.2 Report the four hook template strings **verbatim**, with the
      worktree path, for the conductor to take to #33.
- [ ] 7.3 **From that report onward, nothing touches `.config/wt.toml`** —
      not a typo fix, not a rebase fixup — until the operator confirms the
      grant. Text edited after a grant silently un-grants it. If the
      code-review names a defect in that file, the template text changes and
      the grant must be re-taken; that is the conductor's call, not a fix to
      slip in.
- [ ] 7.4 Do not merge. Do not push. The merge-back is the conductor's, and
      it waits on the grant.
