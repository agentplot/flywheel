---
name: prototype
description: Run the throwaway a flywheel prototype-type design session builds — delegate the code to a spike-repo worktree, bring back a finding note, and let the worktree die. Use whenever a design session's work order names the prototype type, or a batch's decision turns on a fact a throwaway can prove.
---

# Flywheel prototype — the throwaway that settles a fact

You are a design session charged with the **prototype type**. Something
in your batch turns on a fact, and a throwaway can prove it faster than
an argument can settle it.

## The code is built somewhere else, and dies there

Delegate the build to a **spike-repo worktree** via herdr — not in the
change's repo, and not in your session directory:

```bash
wt switch --create spike/<slug> --base main --no-cd   # in the spike repo
herdr tab create --cwd <worktree>                     # then herdr agent start
```

The worktree and the code die when the question is answered. Nothing is
merged, nothing is kept "in case" — a prototype that survives its
question has become untracked construction.

## What comes back is the note

One `prototypes/<slug>.md` finding note per prototype, written from your
worktree into the change's `prototypes/` in the form the schema's
prototypes instruction asks for: **Question**, **Where**, **Findings**,
**Feeds**. The loop's merge of your session branch admits it; the finding
also closes the commissioning item as its final comment.

**Negative results are findings.** A prototype showing the approach does
not work has done its whole job: name what failed and how you know, and
discard the worktree. Reporting "inconclusive" because the answer was no
throws away the thing you were sent to get.

## Close with a round-close plan

A batch with a next round to propose ends with a round-close plan — the
protocol is the shared copy at `skills/_reference/round-close.md`: the
`close/` files, the lavish page, the exclusive routing, the apply order,
the failure discipline. Nothing reaches GitHub before the operator
approves, and a session with nothing to propose settles as today.

## On the tracker

The object-graph rules are the shared copy at
`skills/_reference/tracker.md`; the invocations are in `herdr.md`
beside it. Your contract:

- **You receive**: usually one item per prototype (prototypes ride alone), `type:prototype`, flipped `state:in-progress` by the intent loop.
- **You leave**: the finding as a comment on the item and `prototypes/<slug>.md` in the change; the spike code stays in the spike repo and dies there.
- A finding that opens new work is a queued item, never an in-place expansion of your charge.
- The operator's word is the completion signal, and it is one label: told in the pane that an item is done, move that item to `stage:done` — the one call `flywheel-stage <n> --org <org> --repo <tracker> --stage stage:done`, which sweeps whatever stage the item carried, since an item carries exactly one `stage:*` — and settle. The loop reads the label and does the rest. You never close your own item — the finding is your evidence, and the loop closes on it.

## What you report

The finding, the decision it feeds, and what the next batch should work.
