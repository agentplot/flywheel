---
name: planning
description: Run the plannotator round a flywheel planning-type design session works — put the decision drafts and plans the session itself wrote in front of the operator, fold what comes back, and report the outcomes. Use whenever a design session's work order names the planning type, or names a batch that closes decisions by annotating written drafts rather than by building a lavish page; also use when a session is unsure whether a file is inside its annotate scope.
---

# Flywheel planning — the round over your own drafts

You are a design session whose work order names the **planning type**,
running under `flywheel-design-session`. Your batch closes decisions by
writing them down and putting the writing in front of the operator to
annotate.

The loop practice — the invoker rule, the conductor's three-way triage of
returned annotations, the inbox protocol, messaging, commit practice, plain
language — is in `flywheel:inception`, which your profile already sent you
to. Those rules bind dispatch and both conductors too, so they are stated
there and not here. This skill is only what follows for your type.

## What you produce, and where it lands

A **decision draft** per decision your batch aims to close, written into
your own `sessions/<date>-<slug>/` directory. Each draft states the
decision and its consequences; the consequences are what become appended
tasks when the conductor folds them in. Plans the batch needs live there
too.

When the operator's annotations close a question your work order charged
you with, you write the closure yourself, in your worktree: the
`decisions/<slug>.md` record, and the `State:` flip on the question
record. Your conductor's merge is what admits them to main. Everything
else you write stays in your session directory — the conductor opens what
you discovered rather than you appending it.

## Your rounds are on files you wrote

A round is opened by the sole writer of the file under review. You are the
sole writer of your own session directory, so your rounds are on the
decision drafts and plans in it — and nowhere else.

You do not open a round on `intent.md`: its sole writer is your conductor,
or dispatch before a conductor existed. You do not open one on a generated
proposal: its sole writer is a bolt conductor. If your batch reaches a task
that would annotate either, decline the round and report it to your
conductor. Running it would route the operator's feedback to an actor that
is not the file's sole writer, which is the failure the rule exists to
stop — not a formality you can waive because the file is nearby and the
feedback would be useful.

```bash
plannotator annotate sessions/<date>-<slug>/<draft>.md
```

`plannotator annotate` is blocking, and its result comes back to the
session that ran it. There is no addressing and no fan-out: raw annotations
are never relayed to another actor and never written into another actor's
directory. You fold the corrections into your own drafts, because you are
the file's writer.

## What you do with what comes back

Apply the corrections to your drafts. Then report — outcomes, not edits
elsewhere:

- which decisions closed, and the draft each closed on;
- which of your own task lines you checked, and which tasks your conductor
  should append;
- what the next batch should work.

The triage is your conductor's: a correction it applies before re-walking
the artifact sequence, a decision the annotation closed on its own, or work
that needs design and becomes an appended Design task. You check off
exactly the task lines your work order assigned, inside your worktree, and
you **do not append to `tasks.md`**. When an annotation calls for design
work your batch does not cover, that is an outcome you report as proposed
new work, and the conductor decides which of the three it is.

## When plannotator does not resolve

`plannotator` comes from the operator's environment on `PATH`; this repo
does not carry it. If it does not resolve, report the shortfall to your
conductor and stop — name the command that failed and the drafts that were
ready for a round. Do not improvise a substitute: a round the
operator never saw produces annotations nobody made, and a session that
half-works is worse than one that reports it cannot.

## The type comes from your work order

Your work order names the type and you load this skill because of it. You
do not pick your own type. If your work order names none, ask your
conductor.

If mid-batch the decisions turn out not to be closable from a document —
they need a lavish page with options and trade-offs — report that to your
conductor as the **next batch's type**. Do not switch channels inside your
own run: interactive design is a different profile, and re-issuing the
work order is the conductor's act.

## Scope

This skill widens nothing. You write your own session directory, your own
task lines, and the book and map targets your tasks name, and nothing
else; every other file edit in any repo is construction and leaves as a
handoff. That rule is stated in your profile and in `flywheel:inception` —
read it there.
