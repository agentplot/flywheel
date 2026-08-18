## 1. Read the tree before changing it

- [x] 1.1 Re-read `guard_scaffold`, `CHARTER_SECTIONS`, `guards()`,
      `merge_criteria()` and `land_stage`'s charter refusal in
      `bin/_flywheel_bolt_loop.py`, and `ScaffoldCharterTest` with its
      `SettlingScaffold` runner in `tests/test_bolt_loop.py`. Done when
      you can name, from the files, which of `design.md` — Context still
      holds. Where it does not, say so in the report rather than building
      over it.
- [x] 1.2 Confirm from `schemas/bolt-default/schema.yaml` and its three
      siblings that `bolt` is the first declared artifact with
      `requires: []`, so `/opsx:continue` on a bolt-bound change missing
      `bolt.md` reaches the `bolt` artifact. Done when the invocation
      chosen in task 3 is the one the schemas bear out.

## 2. The guard's test is the charter

- [x] 2.1 `guard_scaffold` returns early only when
      `openspec/changes/<slug>/bolt.md` exists. A change directory
      present without it falls through to the drive rather than reporting
      done. Done when a bare directory no longer short-circuits the
      guard.
- [x] 2.2 The post-settle checks run on both paths: the change directory
      exists, and `merge_criteria()` reads back a body. The reason string
      naming the change directory and the four sections is one string,
      not one per path.
- [x] 2.3 The dry-run branch reports which of the two it would do —
      scaffolding the change, or writing the charter into the change
      already there — and still launches no session and writes nothing.
- [x] 2.4 A pass over a record whose `bolt.md` exists drives nothing,
      writes nothing and appends no action, whatever the charter says.

## 3. The order for a change that already exists

- [x] 3.1 The charter text the order carries — the four sections, the
      `Landing:` line, the `openspec instructions bolt --change <slug>`
      pointer, the description-or-not paragraph, and the "no unit's plan
      document" paragraph — is built once and used by both paths.
- [x] 3.2 The existing-change path's invocation is the one that adds a
      missing artifact to a change that exists, and its framing says the
      change is already there and its charter is what is owed. The
      creating path keeps `/opsx:new <slug>`.
- [x] 3.3 The existing-change order names the bolt type the change is
      bound to and asks the session to confirm that binding before
      writing. Both orders keep the commit-by-pathspec, no-branch,
      no-worktree, deliver-by-settling rules the scaffold order already
      carries.
- [x] 3.4 The session name is unchanged on both paths, so a charterless
      record found on a later pass resumes the scaffold session rather
      than starting a second one.

## 4. Tests

- [x] 4.1 Replace `test_a_present_change_directory_returns_before_the_check`
      with the behaviour this change states: a directory present without
      `bolt.md` drives a session, and the same directory with a `bolt.md`
      drives none.
- [x] 4.2 A charterless change directory: the session is driven, the
      order carries the four sections and the description, its invocation
      continues the existing change rather than creating one, and a
      charter that comes back with criteria passes and records its
      action.
- [x] 4.3 A charterless change directory whose driven session writes no
      charter, or one with no merge-criteria body, halts the cycle with
      the reason naming the change directory and the sections — the same
      reason the creating path gives.
- [x] 4.4 A `bolt.md` present but carrying no readable criteria (the
      older shape, `# Unit:` section and all) drives no session, writes
      nothing, records no action, and is left for the landing's refusal.
- [x] 4.5 `--dry-run` over a charterless change directory: one reported
      action naming the charter it would write, no session launched, no
      file written.
- [x] 4.6 The two orders carry the same charter text — asserted on both,
      not on one.
- [x] 4.7 `python3 -m unittest discover tests -v` green, and the repo's
      gates — `node scripts/check-paths.mjs`, `node scripts/check-site.mjs`,
      `bash scripts/validate-manifests.sh` — green.

## 5. Record

- [x] 5.1 `openspec validate a-charterless-change-directory-gets-one --strict`
      green, and every task above checked off against what the files bear
      out rather than what was edited.
