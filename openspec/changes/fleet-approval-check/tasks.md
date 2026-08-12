## 1. Re-read the neighbours and re-measure the machine

The spec asserts things about files this change does not own and about a live
file that is worktrunk's internal detail. Neighbours move while batches run —
`#34` is editing `.config/wt.toml` in a sibling worktree of this same bolt —
so every claim below is re-checked on disk before anything is built on it.
Findings go in the session report; a contradiction is an andon-cord stop, not
a thing to build around.

- [ ] 1.1 Re-read `bin/flywheel` from disk. Confirm it still has three
      subcommands (`status`, `up`, `reconcile`); that `up` is the only place
      manifest rows are started; that `reconcile` calls `up` and *also* starts
      tracker-driven conductors of its own; and that actor working directories
      still come from `(manifest["root"] / a["cwd"]).resolve()` with
      conductors using the manifest's `conductors_cwd:`. Done when each is
      confirmed or the divergence is written down.
- [ ] 1.2 Re-read `skills/fleet/SKILL.md` from disk and locate the section an
      operator setting up a repo reads — headed *Setting up a new org* at this
      change's authoring. Done when the insertion point is named.
- [ ] 1.3 Re-read `.config/wt.toml` in **this** worktree and record which hook
      event tables it defines and their exact template text. Expect the
      `[pre-commit]` shape if `#34` has not merged back, `[pre-merge]` plus
      `[post-start]` if it has. Either is fine; the point is to know which
      tree you are on. Done when the tables and template strings are written
      down verbatim.
- [ ] 1.4 Re-measure the approvals store: `~/.config/worktrunk/approvals.toml`
      exists, its tables are `[projects."<identifier>"]`, and grants live in an
      `approved-commands` array of unexpanded template strings. Record whether
      a `github.com/agentplot/flywheel` table exists yet — it did not at
      authoring, and `#33` is what creates it.
- [ ] 1.5 Re-measure `wt config show --format json` in this worktree and
      confirm it still returns `project.identifier`, `project.path`,
      `project.exists` and `project.config`, and that its output carries no
      approval state. Confirm `wt hook --help` still enumerates exactly the ten
      hook events the spec names. If either has changed, stop and report —
      `design.md` decision 1 rests on both.
- [ ] 1.6 Measure the unmeasured keying claim: whether moving a template
      between hook event tables with its text unchanged preserves an existing
      grant. `questions/hook-approvals-never-granted.md` marks this
      **provisional** and unmeasured. Do it non-destructively — a scratch repo
      with its own project config, never by editing the operator's store. If it
      turns out false, the spec's scenario *A template moves between hook
      events without changing text* is wrong: stop and report rather than
      changing the spec.

## 2. The check itself

- [ ] 2.1 In `bin/flywheel`, add a read-only function that takes a working
      directory and returns a repo's gate-readiness: its resolved project
      identifier, its project-config path, the hook templates it defines, and
      the templates with no matching grant. Parse both TOML files with the
      standard-library TOML reader — no new dependency; `bin/flywheel` has
      none and its docstring says why. Done when the function exists and is
      called nowhere yet.
- [ ] 2.2 Resolve the identifier and the project-config path with one
      `wt config show --format json -C <path>` per repo, per `design.md`
      decision 1. Treat `project.exists: false` as "no hooks", not as an
      error. Done when a repo outside any project resolves to gate-ready.
- [ ] 2.3 Collect hook templates from exactly the ten hook event tables the
      spec names, and from no other table. Done when a project config carrying
      a non-hook table contributes nothing from it.
- [ ] 2.4 Compare with exact string equality on the unexpanded template text,
      against the `approved-commands` array of the `[projects."<identifier>"]`
      table. A missing store file, a missing table, and an empty array all mean
      "no grants". Done when each of the three yields every template as a gap.
- [ ] 2.5 Make every failure path fail closed and distinguishable: an
      unreadable or unparseable store, a failed or unavailable `wt`, and a
      null identifier are an **indeterminate** result, reported as "the check
      could not be made" with the reason — never as ungranted templates and
      never as gate-ready. Done when the three states are three distinct
      outputs.
- [ ] 2.6 Cache the result per pass, keyed on the project-config path's parent
      (or the resolved working directory when there is no project config), so
      a repo is evaluated and reported once however many actors resolve to it.

## 3. Wire it into the three commands

- [ ] 3.1 `flywheel up`: before starting each actor, consult the check for
      that actor's working directory; start nothing into a repo that is not
      gate-ready. Print the repo, its identifier, every ungranted template
      verbatim, and the remedy — the literal `wt config approvals add`, said to
      be run interactively with the working directory inside that repo. No
      generic failure, and no mention of any approval-skipping flag anywhere in
      the output.
- [ ] 3.2 `flywheel up`: a refused repo does not block actors in gate-ready
      repos in the same pass, and the command exits non-zero when it refused
      any start for this reason. Done when a mixed manifest starts one actor,
      refuses the other, and exits non-zero.
- [ ] 3.3 `flywheel status`: add one row per repo the manifest's actors resolve
      to, showing gate-readiness, with ungranted templates and the same remedy
      beneath a failing row. Leave the existing per-actor rows and the drift
      exit code intact. Start nothing.
- [ ] 3.4 `flywheel reconcile`: apply the same check to both start paths — the
      manifest rows it delegates to `up`, and the tracker-driven conductors it
      starts itself. A refused repo does not stop the rest of the pass: nudges
      and stops still run. **Read `design.md` decision 2 first** — this is a
      documented extension beyond the assertion's literal text, and it is the
      one requirement to delete if the conductor rules otherwise.
- [ ] 3.5 `flywheel reconcile --dry-run`: report which starts the check would
      refuse; start nothing and touch nothing.

## 4. The onboarding documentation

- [ ] 4.1 In `skills/fleet/SKILL.md`, at the insertion point found in 1.2,
      document the grant as an onboarding step for each built repo: the
      operator runs `wt config approvals add` interactively with the working
      directory inside that repo, once, reading the templates before approving
      them; and the fleet commands check this and refuse to start actors
      otherwise. Done when an operator following the setup section end to end
      is told to grant before bringing the fleet up.
- [ ] 4.2 Confirm the added text offers no bypass — no approval-skipping flag,
      and no suggestion that the machinery can write the approvals store.
      `decisions/approvals-are-an-onboarding-grant.md` declined exactly that.

## 5. Verify

- [ ] 5.1 Exercise the failing side against this repo as it actually stands:
      `flywheel status` reports it not gate-ready and names its templates;
      `flywheel up` starts no actor into it and prints the literal
      `wt config approvals add`. This is the assertion's own checkable claim.
- [ ] 5.2 Exercise the passing side without granting anything on the operator's
      machine — a scratch project config whose templates are granted in a
      scratch approvals file, or an equivalent isolation. **Never write the
      operator's `~/.config/worktrunk/approvals.toml`**; granting is `#33`, and
      a converger writing that file is the declined candidate. Done when a
      gate-ready repo starts actors exactly as before.
- [ ] 5.3 Exercise the indeterminate side: with `wt` unreachable, the check is
      reported as not made, no actor starts, and no template is called
      ungranted.
- [ ] 5.4 Confirm the check wrote nothing: `~/.config/worktrunk/approvals.toml`
      is byte-identical before and after the whole verification run, and no
      hook was executed.
- [ ] 5.5 Run the repo's three gates green on the tree that lands:
      `sh scripts/validate-manifests.sh`, `node scripts/check-paths.mjs`,
      `node scripts/check-site.mjs`.
- [ ] 5.6 `openspec validate --strict fleet-approval-check` green.

## 6. Hand back

- [ ] 6.1 Commit on the construction branch by pathspec — `git add <paths>`
      then `git commit -m "<msg>" -- <paths>`, footer `Refs: #36`, no closing
      keyword. Never `-a`, never `add -A`, never a pathspec-less commit: this
      repo is shared with sibling agents working `#34` and `#35`.
- [ ] 6.2 **Do not merge and do not push.** The bolt conductor merges.
- [ ] 6.3 Report to the conductor, and say plainly: **once this lands, the
      agentplot fleet refuses to start actors into `agentplot/flywheel` until
      `#33` is granted.** That is the assertion working as specified, and it is
      the conductor's to sequence — this session does not grant it and does not
      merge around it.
- [ ] 6.4 Comment on `#36` naming what was built and what was measured in
      task 1, including any neighbour that had moved.
