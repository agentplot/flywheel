## 1. Re-read every neighbour from disk before trusting a claim

Siblings on this bolt are live, `main` has already moved under this branch
once, and line numbers in these files have drifted three times inside this
bolt. Locate every site by heading or quoted phrase — and note that the
`skills/construction/SKILL.md` phrases are **line-wrapped in the source**,
so a literal single-line `grep` returns nothing and must not be read as "the
phrase is gone".

- [x] 1.1 Re-read `skills/_reference/herdr.md` and locate, by phrase: the
      "Merging through the gate" heading; "The gate runs the repo's
      `.config/wt.toml` checks on the exact rebased tree that lands"; the
      retry paragraph naming `wt hook pre-merge`; "Hook approval is the
      operator's one-time `wt config approvals add`"; the `--no-hooks`
      paragraph beginning "No `--no-hooks`."; the trailing-`-C` warning; and
      the squash sentence, which is **not edited**.
- [x] 1.2 Re-read `skills/construction/SKILL.md` and locate, by a fragment
      that does not span a line break, the Build stage's "checks run on
      every push" and "rebased tree at" / "merge-back", plus the Merge
      stage's "never weakened" (not edited) and the Spec stage (not edited).
- [x] 1.3 Re-read `devenv.nix` and confirm **both** miscounts are present:
      the packages comment's "Two gates … node runs both checks" and the
      `gates` script comment's "the same two commands". Confirm the `gates`
      script defines exactly three check commands and which runtime runs
      each.
- [x] 1.4 Re-read `.github/workflows/gates.yml`'s head comment and confirm
      "The same four checks".
- [x] 1.5 Re-read `openspec/changes/merge-gate-remedy/bolt.md` for the
      scoped zero-hook reading this change cites rather than reproduces, and
      for the approvals measurements it states. It is the conductor's file
      and may be ahead of this branch — read `main`'s copy if so.
- [x] 1.6 Confirm the three no-edit sites still read as `design.md` records
      them — `AGENTS.md` "before a merge", `README.md`'s Gates section,
      `openspec/specs/flywheel-construction-skill/spec.md` "the tree that
      lands". If any is false rather than merely not-yet-true, stop and
      report instead of editing.
- [x] 1.7 Confirm the co-landing sibling `openspec/changes/pre-merge-gate/`
      is present on this branch, and read its `.config/wt.toml` requirements
      — this change's prose must match that file's strength exactly.

## 2. `skills/_reference/herdr.md` — describe the gate that then exists

- [x] 2.1 Under "Merging through the gate", replace the bare-guarantee
      sentence with the `[pre-merge]` mechanism at measured strength.
- [x] 2.2 Name the config-locus question as open, at the same strength the
      `.config/wt.toml` head comment uses. Cite
      `openspec/changes/merge-gate-remedy/bolt.md` for this bolt's scoped
      reading rather than reproducing it, and write **no** standing
      instruction about how to read a merge that runs zero hooks.
- [x] 2.3 Keep the retry paragraph — fix, re-run `wt hook pre-merge`, merge
      again — present and unchanged in substance.
- [x] 2.4 Beside the existing "Never bypass with `--yes`" sentence, add the
      stop-and-report rule for
      `Cannot prompt for approval in non-interactive environment`, naming
      both non-options and framing the stoppage as closed-failure rather
      than hazard. Keep the two `--yes` facts apart: on `wt merge` it runs
      the hooks without persisting the approval (the trust bypass); on
      `wt config approvals add` it fails and persists nothing (not a route
      to the grant). Different commands, different facts.
- [x] 2.5 Verify no sentence presents the four-template shape of this
      repo's configuration as a reading already taken on some tree. What is
      measured is that `wt config approvals add` enumerates `[post-start]`
      templates; the four-template count is produced by `pre-merge-gate`'s
      task 2.7 on the tree that lands.
- [x] 2.6 Rewrite the `--no-hooks` paragraph: drop "This repo configures no
      `wt` lifecycle hooks today", and give the gate — not the warm-up — as
      the reason the flag is never passed. State any cold-worktree
      consequence only at measured strength.
- [x] 2.7 Leave the squash sentence alone. It is false and it is filed as
      its own item; it is not this change's, even though it sits directly
      against the section being edited.
- [x] 2.8 Do not go looking for a second `herdr.md`. There is one tracked
      file; the copy under `~/.claude/plugins/cache/flywheel/` is a release
      artifact that updates by releasing.
- [x] 2.9 Leave the trailing-`-C` warning paragraph as it is, and write
      nothing new that labels it measured. Its only provenance is that
      paragraph, added in `b5d308b`; #64 is the item that will measure it.
      Keeping the warning while dropping the label is the whole fix.
- [x] 2.10 Write nothing about the order the three checks run in, in either
      direction. Worktrunk's documentation states both answers in two copies
      both labelled 1.0.0 — see `pre-merge-gate`'s `design.md` for the
      quotes — and none of it is a measurement of this tree.

## 3. `skills/construction/SKILL.md` — the Build stage

- [x] 3.1 Rewrite the Build stage sentence to state the `[pre-merge]`
      mechanism in place of "the merge gate runs on the rebased tree at
      merge-back".
- [x] 3.2 Make the "commit checks run on every push" clause deliberate and
      true — `[pre-commit]` is empty after the sibling change, and what runs
      on push is `.github/workflows/gates.yml` — or drop it. Do not leave it
      as an incidental survivor.
- [x] 3.3 Leave the Merge stage's "full hooks, never weakened" and the Spec
      stage untouched.

## 4. The count claims

- [x] 4.1 `devenv.nix` packages comment: correct "Two gates" to three, and
      fix "node runs both checks" so the runtime claim is true of the
      `gates` script (`sh` runs `validate-manifests.sh`; `node` runs the
      other two).
- [x] 4.2 `devenv.nix` `gates` script comment: "the same two commands" →
      three.
- [x] 4.3 `.github/workflows/gates.yml` head comment: "The same four
      checks" → three.
- [x] 4.4 Confirm all four count claims — the two in `devenv.nix`, the one
      in `gates.yml`, and the sibling change's rewritten `.config/wt.toml`
      block — agree with each other and with the `gates` script.

## 5. Verify on the committed tree

- [x] 5.1 Run the three checks directly and confirm green:
      `sh scripts/validate-manifests.sh`, `node scripts/check-paths.mjs`,
      `node scripts/check-site.mjs`.
- [x] 5.2 `openspec validate --strict` green.
- [x] 5.3 Confirm no stale gate phrasing survives outside `openspec/`
      records that quote it deliberately, and that the tracked `herdr.md`
      now differs from the installed copy under
      `~/.claude/plugins/cache/flywheel/` — expected, since that copy
      updates by releasing.
- [x] 5.4 Read the edited `herdr.md` gate section and the sibling's edited
      `.config/wt.toml` head comment **side by side** and confirm they carry
      the config-locus question at the same strength. This is the joint
      requirement neither change can check alone.

## 6. Commit, do not merge

- [x] 6.1 Commit by pathspec (`git add -- <paths>`, then
      `git commit -F <file> -- <paths>`) with `Refs: #35`. Never `-a`, never
      `add -A`, never a closing keyword. Note that `--` must follow the
      options, not precede them.
- [x] 6.2 Do not merge. Do not push. The merge-back is the conductor's, it
      carries both changes together, and it waits on the operator's grant
      (#33).

## 7. Prose corrections after the code-review

- [ ] 7.1 **The CI-on-push claim, in `skills/construction/SKILL.md`.** The
      Build stage now says the built repo's CI runs its checks on every
      push. Measured on the tree: `.github/workflows/gates.yml` triggers on
      `push` to `branches: [main]`, on `pull_request`, and on
      `workflow_dispatch`. This repo lands through `wt merge`, not pull
      requests, so a build session's pushes to `build/*` fire **nothing**.
      Replace it with where a construction branch's commits are actually
      checked: the `[pre-merge]` hooks at merge-back, and CI once the work
      has landed on `main`.
- [ ] 7.2 The same sentence is re-typed in `devenv.nix`'s `gates` script
      comment ("`.github/workflows/gates.yml` runs on every push").
      Correct it to what the workflow's own `on:` block says.
- [ ] 7.3 **Do not touch `AGENTS.md` or `README.md`**, which carry the same
      claim. They are queued as #67. Editing them here is a silent widening.
- [ ] 7.4 **Split the `--no-hooks` warning; do not move it.**
      `grep -n no-hooks skills/_reference/herdr.md` returns one line, under
      "Cutting a worktree", right after the `wt switch --create` block — and
      it now leads with the merge gate. `[pre-merge]` is not among the hooks
      that command runs at all, so there the warm-up is the *only* reason
      and the sentence is backwards.
- [ ] 7.5 Give each section the warning true of its own command: under
      "Cutting a worktree", `--no-hooks` skips the `[post-start]` warm-up
      and leaves the worktree cold; under "Merging through the gate", where
      the section currently carries no warning at all, `--no-hooks` skips
      the gate — zero hooks, exit 0, measured.
- [ ] 7.6 Qualify the shapes claim in the gate section to **"on every shape
      of `wt merge` that does not suppress them"**, the clean fast-forward
      included. It currently carries the bare universal that `bolt.md` was
      corrected for at `28fb534`.
- [ ] 7.7 Re-read `openspec/changes/merge-gate-remedy/bolt.md` and confirm
      the reference cites it rather than reproducing its reasoning about a
      zero-hook merge — that reasoning was withdrawn at `28fb534`, which is
      exactly why standing prose cites rather than copies.
- [ ] 7.8 `openspec validate --strict` green, and the three checks green on
      the committed tree.
