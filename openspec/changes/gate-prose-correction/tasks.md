## 1. Re-read every neighbour from disk before trusting a claim

Siblings on this bolt are live, `main` has already moved under this branch
once, and line numbers in these files have drifted three times inside this
bolt. Locate every site by heading or quoted phrase — and note that the
`skills/construction/SKILL.md` phrases are **line-wrapped in the source**,
so a literal single-line `grep` returns nothing and must not be read as "the
phrase is gone".

- [ ] 1.1 Re-read `skills/_reference/herdr.md` and locate, by phrase: the
      "Merging through the gate" heading; "The gate runs the repo's
      `.config/wt.toml` checks on the exact rebased tree that lands"; the
      retry paragraph naming `wt hook pre-merge`; "Hook approval is the
      operator's one-time `wt config approvals add`"; the `--no-hooks`
      paragraph beginning "No `--no-hooks`."; the trailing-`-C` warning; and
      the squash sentence, which is **not edited**.
- [ ] 1.2 Re-read `skills/construction/SKILL.md` and locate, by a fragment
      that does not span a line break, the Build stage's "checks run on
      every push" and "rebased tree at" / "merge-back", plus the Merge
      stage's "never weakened" (not edited) and the Spec stage (not edited).
- [ ] 1.3 Re-read `devenv.nix` and confirm **both** miscounts are present:
      the packages comment's "Two gates … node runs both checks" and the
      `gates` script comment's "the same two commands". Confirm the `gates`
      script defines exactly three check commands and which runtime runs
      each.
- [ ] 1.4 Re-read `.github/workflows/gates.yml`'s head comment and confirm
      "The same four checks".
- [ ] 1.5 Re-read `openspec/changes/merge-gate-remedy/bolt.md` for the
      scoped zero-hook reading this change cites rather than reproduces, and
      for the approvals measurements it states. It is the conductor's file
      and may be ahead of this branch — read `main`'s copy if so.
- [ ] 1.6 Confirm the three no-edit sites still read as `design.md` records
      them — `AGENTS.md` "before a merge", `README.md`'s Gates section,
      `openspec/specs/flywheel-construction-skill/spec.md` "the tree that
      lands". If any is false rather than merely not-yet-true, stop and
      report instead of editing.
- [ ] 1.7 Confirm the co-landing sibling `openspec/changes/pre-merge-gate/`
      is present on this branch, and read its `.config/wt.toml` requirements
      — this change's prose must match that file's strength exactly.

## 2. `skills/_reference/herdr.md` — describe the gate that then exists

- [ ] 2.1 Under "Merging through the gate", replace the bare-guarantee
      sentence with the `[pre-merge]` mechanism at measured strength.
- [ ] 2.2 Name the config-locus question as open, at the same strength the
      `.config/wt.toml` head comment uses. Cite
      `openspec/changes/merge-gate-remedy/bolt.md` for this bolt's scoped
      reading rather than reproducing it, and write **no** standing
      instruction about how to read a merge that runs zero hooks.
- [ ] 2.3 Keep the retry paragraph — fix, re-run `wt hook pre-merge`, merge
      again — present and unchanged in substance.
- [ ] 2.4 Beside the existing "Never bypass with `--yes`" sentence, add the
      stop-and-report rule for
      `Cannot prompt for approval in non-interactive environment`, naming
      both non-options (`--yes`, which is measured to persist nothing;
      hand-running the check scripts) and framing the stoppage as
      closed-failure rather than hazard.
- [ ] 2.5 Verify no sentence presents the four-template shape of this
      repo's configuration as a reading already taken on some tree. What is
      measured is that `wt config approvals add` enumerates `[post-start]`
      templates; the four-template count is produced by `pre-merge-gate`'s
      task 2.7 on the tree that lands.
- [ ] 2.6 Rewrite the `--no-hooks` paragraph: drop "This repo configures no
      `wt` lifecycle hooks today", and give the gate — not the warm-up — as
      the reason the flag is never passed. State any cold-worktree
      consequence only at measured strength.
- [ ] 2.7 Leave the squash sentence alone. It is false and it is filed as
      its own item; it is not this change's, even though it sits directly
      against the section being edited.
- [ ] 2.8 Do not go looking for a second `herdr.md`. There is one tracked
      file; the copy under `~/.claude/plugins/cache/flywheel/` is a release
      artifact that updates by releasing.

## 3. `skills/construction/SKILL.md` — the Build stage

- [ ] 3.1 Rewrite the Build stage sentence to state the `[pre-merge]`
      mechanism in place of "the merge gate runs on the rebased tree at
      merge-back".
- [ ] 3.2 Make the "commit checks run on every push" clause deliberate and
      true — `[pre-commit]` is empty after the sibling change, and what runs
      on push is `.github/workflows/gates.yml` — or drop it. Do not leave it
      as an incidental survivor.
- [ ] 3.3 Leave the Merge stage's "full hooks, never weakened" and the Spec
      stage untouched.

## 4. The count claims

- [ ] 4.1 `devenv.nix` packages comment: correct "Two gates" to three, and
      fix "node runs both checks" so the runtime claim is true of the
      `gates` script (`sh` runs `validate-manifests.sh`; `node` runs the
      other two).
- [ ] 4.2 `devenv.nix` `gates` script comment: "the same two commands" →
      three.
- [ ] 4.3 `.github/workflows/gates.yml` head comment: "The same four
      checks" → three.
- [ ] 4.4 Confirm all four count claims — the two in `devenv.nix`, the one
      in `gates.yml`, and the sibling change's rewritten `.config/wt.toml`
      block — agree with each other and with the `gates` script.

## 5. Verify on the committed tree

- [ ] 5.1 Run the three checks directly and confirm green:
      `sh scripts/validate-manifests.sh`, `node scripts/check-paths.mjs`,
      `node scripts/check-site.mjs`.
- [ ] 5.2 `openspec validate --strict` green.
- [ ] 5.3 Confirm no stale gate phrasing survives outside `openspec/`
      records that quote it deliberately, and that the tracked `herdr.md`
      now differs from the installed copy under
      `~/.claude/plugins/cache/flywheel/` — expected, since that copy
      updates by releasing.
- [ ] 5.4 Read the edited `herdr.md` gate section and the sibling's edited
      `.config/wt.toml` head comment **side by side** and confirm they carry
      the config-locus question at the same strength. This is the joint
      requirement neither change can check alone.

## 6. Commit, do not merge

- [ ] 6.1 Commit by pathspec (`git add -- <paths>`, then
      `git commit -F <file> -- <paths>`) with `Refs: #35`. Never `-a`, never
      `add -A`, never a closing keyword. Note that `--` must follow the
      options, not precede them.
- [ ] 6.2 Do not merge. Do not push. The merge-back is the conductor's, it
      carries both changes together, and it waits on the operator's grant
      (#33).
