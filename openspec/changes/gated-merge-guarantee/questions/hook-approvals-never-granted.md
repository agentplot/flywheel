# Question: how do a repo's `wt` hook approvals get granted before an agent needs them?

- **Item:** #16
- **Raised by:** the `bolt-site-refresh` conductor, landing #12 (the
  second gap named in item #14)

## The question

Worktrunk gates hook execution on an approval keyed to the hook's
template text, granted once by the operator with
`wt config approvals add`. On this machine that has never been run for
this repo, so a non-interactive agent asked to run the gate cannot.
Undecided: where granting approvals belongs. Named candidates, none
ruled out — an operator onboarding step the loop documents and the
fleet skill checks; a converger, the way
`<plugin-root>/bin/flywheel-setup` converges labels, the project and its
fields idempotently; a fleet-layer precondition checked at `flywheel up`
so the fleet refuses to start actors into a repo whose gate they cannot
run. An answer says which, and what an agent that hits the missing
approval does in the meantime.

## What turns on it

Whether an agent that notices an ungated merge can do anything about it.
Today the two gaps compound: the gate does not run on a fast-forward,
and the agent that notices cannot run it either, so the only paths open
are the `--yes` bypass the loop forbids or hand-running the underlying
scripts — which is what actually happened on #12 and is precisely the
asserted-green `wt merge` exists to eliminate. It also decides whether
onboarding a new built repo into the fleet has a manual step that
silently must happen before the first merge, or a converger that makes
it not a step at all.

## What is already known

- `~/.local/share/worktrunk/approvals.toml` does not exist. The
  approvals store is empty for every template, not just this repo's.
- Approvals key on the template text, per the comment at the head of
  `.config/wt.toml`, so one grant covers every branch's expansion of a
  given hook — three grants, not three per branch.
- `skills/_reference/herdr.md` under "Merging through the gate" already
  states the rule this question works within: hook approval is the
  operator's one-time `wt config approvals add`, and agents never bypass
  with `--yes`.
- Coupled to #14, not blocked by it: if #14 lands on an explicit gate
  step the conductor runs, approvals become load-bearing rather than a
  convenience, which narrows the candidates here.
