# Assertion: the fleet refuses to start actors into a repo whose gate they cannot run

- **Repo:** agentplot/flywheel
- **Item:** #36
- **Raised by:** `sessions/2026-08-12-gate-remedy/` — the operator's round
  closing #16, carved by the conductor's fold.

## The claim

`flywheel up` checks, before starting any actor into a repo, that every
hook template defined in that repo's `.config/wt.toml` has a matching grant
in `~/.config/worktrunk/approvals.toml` under the repo's project identifier
(`[projects."github.com/<org>/<repo>"]`), matched on verbatim template
text. Where a template is unmatched it starts nothing for that repo and
prints what is missing together with the exact remedy — `wt config
approvals add`, run interactively in the repo — rather than a generic
failure. `flywheel status` reports the same check as a row, without
starting anything.

Checkable against the tree: with this repo's templates ungranted,
`flywheel up` names the ungranted templates and starts no actor into it;
with them granted, it behaves as it does today.

The check reads and compares two TOML files. It does not invoke `wt` to
determine approval state and does not write to the approvals store.

## Why

`decisions/approvals-are-an-onboarding-grant.md` settles granting as an
operator onboarding step and puts the check at the fleet layer, on the
reasoning that a check is what removes the *silent* from a manual step —
the stoppage lands loudly at fleet start with a remedy in hand, rather than
mid-merge. It also records why the converger alternative was declined, which
is why this assertion reads rather than writes the store. The keying and
store facts are on `questions/hook-approvals-never-granted.md`, measured
and provisional; re-check them against the machine that builds this.

## Boundaries

Reads the approvals store; never writes it. Does not grant this repo's
approvals — that is #33, the operator's own interactive step, and this
check's first useful act is to fail until #33 happens. Independent of #34
and #35: it can land before or after them, since it changes no gate
behaviour and only reports on state. The same pass documents the grant as
an onboarding step for bringing a new built repo into the fleet, in the
fleet skill's setup section; it does not add the stop-and-report rule for
individual agents, which is #35's
(`assertions/gate-prose-correction.md`).
