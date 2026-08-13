## 1. Re-read the neighbours and re-measure the machine

The spec asserts things about files this change does not own and about a live
file that is worktrunk's internal detail. Neighbours move while batches run —
`#34` is editing `.config/wt.toml` in a sibling worktree of this same bolt —
so every claim below is re-checked on disk before anything is built on it.
Findings go in the session report; a contradiction is an andon-cord stop, not
a thing to build around.

- [x] 1.1 Re-read `bin/flywheel` from disk. Confirm it still has three
      subcommands (`status`, `up`, `reconcile`); that `up` is the only place
      manifest rows are started; that `reconcile` calls `up` and *also* starts
      tracker-driven conductors of its own; and that actor working directories
      still come from `(manifest["root"] / a["cwd"]).resolve()` with
      conductors using the manifest's `conductors_cwd:`. Done when each is
      confirmed or the divergence is written down.
- [x] 1.2 Re-read `skills/fleet/SKILL.md` from disk and locate the section an
      operator setting up a repo reads — headed *Setting up a new org* at this
      change's authoring. Done when the insertion point is named.
- [x] 1.3 Re-read `.config/wt.toml` in **this** worktree and record which hook
      event tables it defines and their exact template text. Expect the
      `[pre-commit]` shape if `#34` has not merged back, `[pre-merge]` plus
      `[post-start]` if it has. Either is fine; the point is to know which
      tree you are on. Done when the tables and template strings are written
      down verbatim.
- [x] 1.4 Re-measure the approvals store: `~/.config/worktrunk/approvals.toml`
      exists, its tables are `[projects."<identifier>"]`, and grants live in an
      `approved-commands` array of unexpanded template strings. Record whether
      a `github.com/agentplot/flywheel` table exists yet — it did not at
      authoring, and `#33` is what creates it.
- [x] 1.5 Re-measure `wt config show --format json` in this worktree and
      confirm it still returns `project.identifier`, `project.path`,
      `project.exists` and `project.config`, and that its output carries no
      approval state. Confirm `wt hook --help` still enumerates exactly the ten
      hook events the spec names. If either has changed, stop and report —
      `design.md` decision 1 rests on both.
- [x] 1.6 Measure the unmeasured keying claim: whether moving a template
      between hook event tables with its text unchanged preserves an existing
      grant. `questions/hook-approvals-never-granted.md` marks this
      **provisional** and unmeasured. Do it non-destructively — a scratch repo
      with its own project config, never by editing the operator's store. If it
      turns out false, the spec's scenario *A template moves between hook
      events without changing text* is wrong: stop and report rather than
      changing the spec.

## 2. The check itself

- [x] 2.1 In `bin/flywheel`, add a read-only function that takes a working
      directory and returns a repo's gate-readiness: its resolved project
      identifier, its project-config path, the hook templates it defines, and
      the templates with no matching grant. Parse both TOML files with the
      standard-library TOML reader — no new dependency; `bin/flywheel` has
      none and its docstring says why. Done when the function exists and is
      called nowhere yet.
- [x] 2.2 Resolve the identifier and the project-config path with one
      `wt config show --format json -C <path>` per repo, per `design.md`
      decision 1. Treat `project.exists: false` as "no hooks", not as an
      error. Done when a repo outside any project resolves to gate-ready.
- [x] 2.3 Collect hook templates from worktrunk's own enumeration of the repo's
      configured hooks — `wt hook show --format json -C <path>`, taking
      `template` from every record whose `source` is `"project"`. Do NOT parse
      the hook grammar by hand: it accepts five shapes (`design.md`, *The
      hook-template grammar*), and a parser covering only the named-table form
      reports a repo gate-ready whose hooks are entirely ungranted. Ignore
      `needs_approval` — that field is approval state, and the store is the
      authority on grants. Done when a fixture in each of the five shapes
      yields every one of its commands, and a user-level hook yields none.
- [x] 2.4 Compare with exact string equality on the unexpanded template text,
      against the `approved-commands` array of the `[projects."<identifier>"]`
      table. A missing store file, a missing table, and an empty array all mean
      "no grants". Done when each of the three yields every template as a gap.
- [x] 2.5 Make every failure path fail closed and distinguishable: an
      unreadable or unparseable store, a failed or unavailable `wt`, and a
      null identifier are an **indeterminate** result, reported as "the check
      could not be made" with the reason — never as ungranted templates and
      never as gate-ready. Done when the three states are three distinct
      outputs.
- [x] 2.6 Cache the result per pass, keyed on the project-config path's parent
      (or the resolved working directory when there is no project config), so
      a repo is evaluated and reported once however many actors resolve to it.
- [x] 2.7 Treat a non-zero exit from the hook enumeration as **indeterminate**,
      never as an empty template set. Measured: with a project config worktrunk
      cannot load, `wt hook show --format json` exits 1 with empty stdout — so
      "no records" and "config unreadable" are indistinguishable without the
      exit code, and reading the first as gate-ready is a false green on a repo
      whose gate is definitionally unrunnable. Done when a malformed project
      config yields indeterminate and a repo with genuinely no project hooks
      yields gate-ready.
- [x] 2.8 Contain every failure to the repo it concerns: a store that is
      unreadable or not shaped as expected, and a failed worktrunk query, make
      that one repo indeterminate and let the pass finish reporting the others.
      No unhandled exception may escape the check into `up`, `status` or
      `reconcile`. Summarise a worktrunk failure rather than relaying its raw
      error stream. Done when a reshaped store leaves all three commands
      running and reporting.

## 3. Wire it into the three commands

- [x] 3.1 `flywheel up`: before starting each actor, consult the check for
      that actor's working directory; start nothing into a repo that is not
      gate-ready. Print the repo, its identifier, every ungranted template
      verbatim, and the remedy — the literal `wt config approvals add`, said to
      be run interactively with the working directory inside that repo. No
      generic failure, and no mention of any approval-skipping flag anywhere in
      the output.
- [x] 3.2 `flywheel up`: a refused repo does not block actors in gate-ready
      repos in the same pass, and the command exits non-zero when it refused
      any start for this reason. Done when a mixed manifest starts one actor,
      refuses the other, and exits non-zero.
- [x] 3.3 `flywheel status`: add one row per repo **it can inspect from here** —
      this host's actors whose working directories resolve on this machine —
      showing gate-readiness, with ungranted templates and the same remedy
      beneath a failing row. Claim nothing about a repo on another host or a
      directory that is absent. Leave the existing per-actor rows and the drift
      exit code intact. Start nothing.
- [x] 3.3a `flywheel status`: name every actor whose repo was skipped from the
      gate rows and why — on another host, or its directory not present here.
      Done when a reader can tell from the output alone which repos were
      checked and which were not; silently omitting them is the defect.
- [x] 3.4 `flywheel reconcile`: apply the same check to both start paths — the
      manifest rows it delegates to `up`, and the tracker-driven conductors it
      starts itself. A refused repo does not stop the rest of the pass: nudges
      and stops still run. **Read `design.md` decision 2 first** — this is a
      documented extension beyond the assertion's literal text, and it is the
      one requirement to delete if the conductor rules otherwise.
- [x] 3.5 `flywheel reconcile --dry-run`: report which starts the check would
      refuse; start nothing and touch nothing.

## 4. The onboarding documentation

- [x] 4.1 In `skills/fleet/SKILL.md`, at the insertion point found in 1.2,
      document the grant as an onboarding step for each built repo: the
      operator runs `wt config approvals add` interactively with the working
      directory inside that repo, once, reading the templates before approving
      them; and the fleet commands check this and refuse to start actors
      otherwise. Done when an operator following the setup section end to end
      is told to grant before bringing the fleet up.
- [x] 4.2 Confirm the added text offers no bypass — no approval-skipping flag,
      and no suggestion that the machinery can write the approvals store.
      `decisions/approvals-are-an-onboarding-grant.md` declined exactly that.

## 5. Verify

- [x] 5.1 Exercise the failing side against this repo as it actually stands:
      `flywheel status` reports it not gate-ready and names its templates;
      `flywheel up` starts no actor into it and prints the literal
      `wt config approvals add`. This is the assertion's own checkable claim.
- [x] 5.2 Exercise the passing side without granting anything on the operator's
      machine — a scratch project config whose templates are granted in a
      scratch approvals file, or an equivalent isolation. **Never write the
      operator's `~/.config/worktrunk/approvals.toml`**; granting is `#33`, and
      a converger writing that file is the declined candidate. Done when a
      gate-ready repo starts actors exactly as before.
- [x] 5.3 Exercise the indeterminate side: with `wt` unreachable, the check is
      reported as not made, no actor starts, and no template is called
      ungranted.
- [x] 5.4 Confirm the check wrote nothing: `~/.config/worktrunk/approvals.toml`
      is byte-identical before and after the whole verification run, and no
      hook was executed.
- [x] 5.5 Run the repo's three gates green on the tree that lands:
      `sh scripts/validate-manifests.sh`, `node scripts/check-paths.mjs`,
      `node scripts/check-site.mjs`.
- [x] 5.6 `openspec validate --strict fleet-approval-check` green.

## 6. Hand back

- [x] 6.1 Commit on the construction branch by pathspec — `git add <paths>`
      then `git commit -m "<msg>" -- <paths>`, footer `Refs: #36`, no closing
      keyword. Never `-a`, never `add -A`, never a pathspec-less commit: this
      repo is shared with sibling agents working `#34` and `#35`.
- [x] 6.2 **Do not merge and do not push.** The bolt conductor merges.
- [x] 6.3 Report to the conductor, and say plainly: **once this lands, the
      agentplot fleet refuses to start actors into `agentplot/flywheel` until
      `#33` is granted.** That is the assertion working as specified, and it is
      the conductor's to sequence — this session does not grant it and does not
      merge around it.
- [x] 6.4 Comment on `#36` naming what was built and what was measured in
      task 1, including any neighbour that had moved.

## 7. Re-verify after the code-review remediation

The adversarial code-review found the extraction reported gate-ready on hooks
it could not see. These tasks are what prove that class of defect is gone —
run them against the rebuilt check, not against the reasoning about it.

- [x] 7.1 Build one fixture per accepted grammar shape — bare string, named
      table, inline table, array of strings, mixed array, `[[event]]` pipeline
      blocks — each ungranted, and confirm every command in every shape is
      reported as a gap. Isolate with a relocated `HOME`; **never** write the
      operator's `~/.config/worktrunk/approvals.toml`.
- [x] 7.2 Cross-check each fixture against `wt hook show --format json`: the
      set of templates the check reports SHALL equal the set of `template`
      values whose `source` is `"project"`. A shape where the two disagree is a
      defect in the check, not in the fixture.
- [x] 7.3 Confirm a `[[event]]` block's keys are read as command names: a block
      written `name = "x"` / `command = "y"` yields two commands, `x` and `y`,
      matching worktrunk's enumeration exactly.
- [x] 7.4 Confirm a user-level hook is never reported as a gap, and that a repo
      whose only hooks are user-level is gate-ready.
- [x] 7.5 Confirm a malformed project config is indeterminate, not gate-ready,
      and that a reshaped approvals store leaves `up`, `status` and `reconcile`
      running rather than raising.
- [x] 7.6 Confirm `flywheel status` on a manifest with an off-host actor and an
      absent working directory names both as skipped, with reasons, and claims
      gate-readiness for neither.
- [x] 7.7 Re-run the whole verification group 5 against the rebuilt check, and
      re-confirm 5.4: the operator's approvals store is byte-identical before
      and after, and no hook was executed.
