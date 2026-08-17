# Decision draft: how a repo's `wt` hook approvals get granted (#16)

- **Item:** #16 · **Type:** planning · **Question record:**
  `../../questions/hook-approvals-never-granted.md`
- **Evidence:** measured while answering #14, folded into the question
  record. The facts that frame the choice: the store is
  `~/.config/worktrunk/approvals.toml`, a live file holding six unrelated
  `WilldanGroup` project tables and no entry for
  `github.com/agentplot/flywheel`; `wt config approvals add` cannot grant
  non-interactively by any invocation, `--yes` included — the only
  non-interactive path is writing that TOML directly; unapproved hooks fail
  closed (exit 1, nothing landed); approvals key on the verbatim template
  text, so one grant covers every branch and a table move re-keys nothing.

#14's remedy makes this load-bearing: `[pre-merge]` is the first
configuration that would ever demand an approval here, so the grant must
exist before that config change lands or every merge in the fleet aborts.

Two choices below. Each has a marked recommendation; your annotation is the
word that closes it.

## Choice 1 — where granting lives

**Option A — an operator onboarding step, checked by the fleet
(recommended).** The operator runs `wt config approvals add` interactively in
the repo, once, reading the templates before approving them. The loop
documents it as onboarding; `flywheel up` (or `flywheel status`) checks that
every hook template in the repo's `.config/wt.toml` has its approval in the
store, and refuses to start actors into a repo whose gate they cannot run —
printing the exact command instead. The check is what removes the "silent"
from the manual step: the stoppage happens loudly at fleet start with a
remedy in hand, not mid-merge.

- Preserves the trust boundary `wt`'s design intends: a human reads hook
  text before anything executes it.
- Cost: one genuinely manual step per repo, and a checker that must parse
  two TOML files and compare template text. The keying is known
  (`[projects."github.com/agentplot/flywheel"]`, verbatim template text), so
  the check is a read-and-compare, not a reimplementation of `wt`.

**Option B — a converger writes the approvals TOML directly**, the way
`flywheel-setup` converges labels and the project. Zero-friction and
idempotent, but it inverts the trust model the approval mechanism exists
for: the machinery approves the machinery's own hooks, so anything that can
edit `.config/wt.toml` and reach the converger has arbitrary commands
auto-approved on the operator's machine. The operator's consent collapses to
"the repo is in `fleet.yaml`". It also writes a user-level live file owned
by `wt`, holding six unrelated projects' grants, in a format that is `wt`'s
internal detail — a converger bug or a `wt` format change puts unrelated
repos' approvals at risk. If B wins despite this, the file's format and
keying move from the question record into the decision record as settled
interface.

**Option C — a fleet-layer check alone.** Detects, never grants; only
meaningful combined with A (it is A's second half) or as B's guard.

## Choice 2 — what an agent that hits the missing approval does meanwhile

**Recommended: stop and report — a work stoppage, not a workaround.** The
failure is closed (exit 1, nothing landed), so the safe state is already the
default. The agent reports `Cannot prompt for approval in non-interactive
environment` to its conductor, the conductor surfaces it to the operator,
and the merge waits for the grant. Two non-options, named because both have
been reached for: `--yes` runs the hooks without persisting approval — a
trust bypass the loop already forbids; and hand-running the underlying
scripts on the landing tree is verification by assertion — exactly the
asserted-green `wt merge` exists to eliminate, however honest the hands.

## Consequences, whichever way the choices go

Queued as items on the decision, not edited by this session:

1. **The grant itself, for this repo** — the operator approves the current
   templates (plus the `post-start` template if #14's Choice 3 adds one).
   Must land before or with #14's config change; see that record's ordering
   consequence.
2. **The fleet-layer check** in `flywheel up`/`flywheel status`, per
   Choice 1.
3. **The onboarding documentation** — where the loop tells an operator
   bringing a new built repo into the fleet to grant approvals, and
   `skills/_reference/herdr.md` gains the meanwhile rule from Choice 2
   beside its existing "never bypass with `--yes`" sentence. Rides with
   the herdr.md correction item #14 queues, or stands alone.
