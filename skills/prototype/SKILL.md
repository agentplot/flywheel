---
name: prototype
description: Run the throwaway a flywheel prototype-type design session builds — delegate the code to a spike-repo worktree, bring back a `prototypes/<slug>.md` finding note, and let the worktree die. Use whenever a design session's work order names the prototype type, or names a batch whose decision turns on a fact a throwaway can prove; also use when a session is about to write or deliver a prototype finding.
---

# Flywheel prototype — the throwaway that settles a fact

You are a design session charged with the **prototype type**, running under
`flywheel-design-session`. Something in your batch turns on a fact, and a
throwaway can prove it faster than an argument can settle it.

Whether that is true of a given decision is the choosing criterion, and it
lives in `flywheel:inception` where your conductor reads it before charging
you. So does the rest of the loop practice. This skill is the mechanics.

## The code is built somewhere else, and dies there

Delegate the build to a **spike-repo worktree** via herdr — a worktree cut
in the spike repo, an agent started in its pane, the throwaway written
there. Not in blueprints, and not in your session directory.

```bash
wt switch --create spike/<slug> --base main --no-cd   # in the spike repo
herdr tab create --cwd <worktree>                     # then herdr agent start in that pane
```

The worktree and the code die when the question is answered. Nothing is
merged, nothing is promoted, nothing is kept "in case". A prototype that
survives its question has stopped being a prototype and become untracked
construction.

## What comes back is the note

One `prototypes/<slug>.md` finding note per prototype, in the form the
`flywheel-intent` schema's prototypes instruction asks for — exactly these
four things:

- **Question** — what the prototype set out to prove or disprove.
- **Where** — the spike-repo path or branch that held the throwaway code.
- **Findings** — what was proven, plainly.
- **Feeds** — the decision(s) this evidence feeds.

You write the note in your own `sessions/<date>-<slug>/` directory and
deliver it; your conductor promotes it into the change's `prototypes/` and
gives it a row in `design.md`. The code never moves with the note.

**Negative results are findings.** A prototype showing that the approach it
was testing does not work has done its whole job: write the note, name what
failed and how you know, and discard the worktree. Reporting "inconclusive"
because the answer was no throws away the thing you were sent to get.

## Your type opens no round

The note is a file you wrote, so it falls inside the annotate scope a
review session is bounded by — and your type opens no round anyway. You
deliver the finding to your conductor instead. If the operator should
annotate what the prototype proved, your conductor charges a review-type
session for it; that is a new charge, not something you can reach by
opening `plannotator` on your own note.

## The type comes from your work order

Your work order names the type and you load this skill because of it. You do
not pick your own type. If your work order names none, ask your conductor. If
mid-batch the work turns out to need a different type, report that as the
next batch's type rather than switching inside your own run.

## What you report

The finding, the decision it feeds, which tasks your conductor should check
or append, and what the next batch should work. You append nothing to
`tasks.md` and check nothing off.

## Scope

This skill widens nothing. The throwaway lives in a spike-repo worktree
that dies; you write your own session directory, and the book and map
targets your tasks name. Every other file edit in any repo — blueprints
included — is construction and leaves as a handoff. That rule is stated in
your profile and in `flywheel:inception`; read it there.
