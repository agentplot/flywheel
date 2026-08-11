---
name: human-code-review
description: Run the operator's review round a flywheel human-code-review construction session prepares — built diffs put in front of the operator through plannotator, the annotations folded and reported. Use whenever a construction session's work order names the human-code-review type.
---

# Flywheel human-code-review — the operator's round over built diffs

You are a construction session charged with the **human-code-review
type**. Your batch is built work an agent asked the operator's eyes for;
your output is the operator's verdict, folded and reported.

## What goes in front of the operator

A review document you compose in your worktree — the diff per assertion
with what it implements, the decisions it cites, and what you would
have them look hardest at: the judgement calls, the deviations from the
spec and their reasons, the claims you could not verify. One round per
batch, never one per assertion, ordered by where their eyes matter
most. Composing it honestly matters more than composing it favourably:
a round that hides the doubtful diff produces an approval that means
nothing.

```bash
plannotator annotate <your-review-document>.md
```

The result comes back to you.

## What comes back, and where it goes

Fold the annotations into your report, sorted the way the conductor
will route them: a correction to apply, a defect that holds the item,
an approval, a design-level objection queued for the intent. Raw
annotations are never relayed to another actor. You never apply the
corrections yourself — the round makes you a reviewer, and a reviewer
that patches becomes an unreviewed builder mid-run.

If `plannotator` does not resolve on `PATH`, report the shortfall and
stop — the item asked for the operator's eyes, and a round the operator
never saw produces annotations nobody made. An annotation set that
rejects the batch's whole approach is one finding and the andon cord.

## What you report

The document as annotated, the fold sorted for routing, and what the
next batch should work.
