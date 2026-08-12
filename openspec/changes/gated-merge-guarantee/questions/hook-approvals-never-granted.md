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

A converger here cannot shell out to `wt config approvals add` — that
command cannot grant non-interactively by any invocation, `--yes`
included. Whatever converges approvals writes the approvals TOML
directly, which makes the file's format and its keying part of what an
answer settles.

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

Measured on this machine while answering #14; re-check against the
tree and machine you read this on.

- **The store is `~/.config/worktrunk/approvals.toml`**, and it is not
  empty: six `[projects."github.com/WilldanGroup/…"]` tables, and no
  entry for `github.com/agentplot/flywheel`. (An earlier reading of this
  record named `~/.local/share/worktrunk/approvals.toml` and called the
  store empty; that path does not exist here. The gap is this repo's
  missing entry, not an absent store — so a converger appends a table to
  a live file rather than creating one.)
- **`wt config approvals add` cannot grant non-interactively.** Run in
  this repo it lists the three `[pre-commit]` templates and stops at
  `Cannot prompt for approval in non-interactive environment`; `--yes`
  behaves identically, and neither form writes anything — the file still
  had no `agentplot` entry after both. The tool's own hint suggesting
  `--yes` is therefore circular, and the only non-interactive path is
  writing the TOML by hand.
- **It fails closed.** Unapproved hooks non-interactively abort with
  exit 1 and nothing landed — never an ungated green. So a missing
  approval is a work stoppage, not a silent hole.
- Approvals key on the template text, per the comment at the head of
  `.config/wt.toml`, so one grant covers every branch's expansion of a
  given hook — three grants, not three per branch. Moving a check
  between `[pre-commit]` and `[pre-merge]` re-keys nothing; editing its
  command text does.
- **Why this has never bitten anyone.** `wt` asks for approval only for
  hooks it is about to run, and on this repo's shape it has never been
  about to run any. A lab repo configured exactly like this one — three
  `[pre-commit]` hooks, no `[pre-merge]`, no approval entry — merged a
  clean rebased descendant with a green exit 0, zero hooks fired, **and
  no approval prompt**. #14 and #16 are the same silence.
- `skills/_reference/herdr.md` under "Merging through the gate" already
  states the rule this question works within: hook approval is the
  operator's one-time `wt config approvals add`, and agents never bypass
  with `--yes`.
- Coupled to #14, not blocked by it: #14's survivors both need
  `[pre-merge]` configured, which is the first thing that would ever
  demand an approval here — so approvals become load-bearing rather than
  a convenience, and this question's answer must land in the same pass.
