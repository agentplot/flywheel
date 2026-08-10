---
name: handoff
description: Work the transfer a flywheel handoff-type design session runs — compose the release request from the released assertions, deliver it to the bolt conductor, wait for the receipt, and report it. Use whenever a design session's work order names the handoff type, or names a batch of released Handoff task lines; also use when a session needs to know what a release request must contain or when a Handoff line may be checked off.
---

# Flywheel handoff — the transfer to construction

You are a design session whose work order names the **handoff type**,
running under `flywheel-design-session`. The operator has approved a
release; your batch turns that approval into a bolt: you compose the
release request, deliver it to the bolt conductor, and bring back the
receipt.

The loop practice is in `flywheel:inception`, which your profile already
sent you to. This skill is what the type is and how it ends.

## Why this is a session at all

Worktree management, not the wait. A session owns exactly one worktree and
merges it once; a conductor doing the transfer itself would write in its
own base tree or juggle a nested one. The wait on the bolt conductor is
incidental — the worktree discipline is the reason.

## What the release request carries

One request per released batch, composed from the released assertions'
own files — never re-derived from memory:

- the assertions being released, by change-relative path, each still
  `State: open`;
- the built repos they land in;
- the bolt member the work warrants (`bolt-default`, `bolt-quick`,
  `bolt-deep` — or `bolt-no-spec` when the handoff arrived already
  specified), because the member picked at creation IS the review depth;
- the bolt's owner — the developer whose word settles its decisions;
- any architecture decision record a Handoff line names: repo, decision to
  record, sources. It generates no proposal; the bolt conductor writes it
  directly.

## How it travels

To the bolt conductor by the two transports, one block: `herdr agent
prompt bolt-<slug>` when it runs, a file in the bolt change's `inbox/`
when it does not. If no bolt exists yet, report that to your conductor —
creating the bolt change and starting its conductor is the release path's
work, not a session's.


The prompt and inbox invocations are in
the flywheel plugin's `skills/_reference/herdr.md`, the one shared copy — read it
before sending.

## The receipt is custody, not completion

The bolt conductor's receipt says the proposals now exist in its registry
— custody has transferred. It does not say the work is done. A Handoff
task line is checked off when the proposals exist in the bolt, not when
the request is sent; your conductor closes the line on the receipt, and
the assertion's `State` moves to built only when evidence lands on main.

You deliver the receipt in your report: which bolt took custody, the
proposal rows it opened, and anything it declined or deferred. A declined
piece goes back to your conductor as an open item, never quietly dropped.

## The type comes from your work order

Your work order names the type and you load this skill because of it. You
do not pick your own type. If your work order names none, ask your
conductor. If the batch turns out to need composing that is really
design — the assertions contradict each other, the batch has no coherent
scope — stop and report; a handoff session transfers settled work and
settles nothing itself.

## Your type opens no round

You could put the release request in front of the operator; your type
opens no plannotator round. The request goes to the bolt conductor and
the receipt to your own conductor — in the design loop only the planning
type puts material in front of the operator.

## What you report

The request as sent, the receipt as received, which of your own task lines
you checked, any declined or deferred pieces, and what the next batch
should work.

## Scope

This skill widens nothing. You write your own session directory, your own
task lines, and nothing else — the request itself is a message, not a
file edit in another change. Writing into the bolt change's artifacts is
its conductor's act alone; your inbox drop is the one file you may leave,
and only when its conductor is not running.
