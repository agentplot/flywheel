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

One `prototypes/<slug>.md` finding note per prototype, written in your
`sessions/<date>-<slug>/` directory in the form the schema's prototypes
instruction asks for: **Question**, **Where**, **Findings**, **Feeds**.
Your conductor promotes it into the change's `prototypes/`; the finding
also closes the commissioning item as its final comment.

**Negative results are findings.** A prototype showing the approach does
not work has done its whole job: name what failed and how you know, and
discard the worktree. Reporting "inconclusive" because the answer was no
throws away the thing you were sent to get.

## What you report

The finding, the decision it feeds, and what the next batch should work.
