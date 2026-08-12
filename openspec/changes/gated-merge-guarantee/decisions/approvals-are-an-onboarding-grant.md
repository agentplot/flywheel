# Decision: hook approvals are an operator onboarding grant, checked by the fleet

- **Closes:** #16 · **Question record:**
  `../questions/hook-approvals-never-granted.md`
- **Decided by:** the operator, 2026-08-12, annotating
  `../sessions/2026-08-12-gate-remedy/draft-approvals-granting.md` in a
  plannotator round.
- **Evidence:** measured while answering #14 and folded into the question
  record — authoritative here is the decision; the measurements are
  provisional and cited there.

## The decision

1. **Granting approvals is an operator onboarding step, checked by the
   fleet layer.** The operator runs `wt config approvals add` interactively
   in the repo, once, reading the templates before approving them.
   `flywheel up` (and `flywheel status` as a report row) checks that every
   hook template in the repo's `.config/wt.toml` has its grant in
   `~/.config/worktrunk/approvals.toml` under the repo's project identifier
   — `[projects."github.com/agentplot/flywheel"]`, keyed on verbatim
   template text — and refuses to start actors into a repo whose gate they
   cannot run, printing the exact command instead. The check is what
   removes the "silent" from the manual step: the stoppage happens loudly
   at fleet start with a remedy in hand, not mid-merge.

2. **An agent that hits the missing approval stops and reports — a work
   stoppage, not a workaround.** The failure is already closed (exit 1,
   nothing landed). The agent reports
   `Cannot prompt for approval in non-interactive environment` to its
   conductor; the conductor surfaces it to the operator; the merge waits
   for the grant. Two non-options, named because both have been reached
   for: `--yes` runs the hooks without persisting approval — a trust bypass
   the loop already forbids; and hand-running the underlying scripts on the
   landing tree is verification by assertion — exactly the asserted-green
   `wt merge` exists to eliminate, however honest the hands.

## What was declined, and why

**A converger writing the approvals TOML directly.** Zero-friction, but it
inverts the trust model the approval mechanism exists for: the machinery
would approve the machinery's own hooks, so anything that can edit
`.config/wt.toml` and reach the converger has arbitrary commands
auto-approved on the operator's machine. It would also write a user-level
live file owned by `wt`, holding unrelated projects' grants, in a format
that is `wt`'s internal detail. The file's format and keying therefore stay
facts on the question record, not a settled interface.

## Consequences

- **#33** — the grant itself for this repo: the operator approves the four
  templates the remedy leaves in `.config/wt.toml` (the three checks under
  `[pre-merge]` and the `[post-start]` `wt step copy-ignored` —
  `gate-runs-under-pre-merge.md`). Must land before or with #34; approvals
  key on verbatim template text, so grant after the config text is final.
- **#36** — the fleet-layer check at `flywheel up`/`flywheel status`, and
  the onboarding documentation telling an operator bringing a new built
  repo into the fleet to grant approvals.
- **#35** — `skills/_reference/herdr.md` gains the stop-and-report rule
  beside its existing "never bypass with `--yes`" sentence.
