# Assertion: The teardown instruction is split by how the worktree was cut

- **Repo:** agentplot/flywheel
- **Item:** #39
- **Raised by:** `intent-work-object-vocabulary`, tearing down a design
  session and finding the reference's teardown command aimed at the
  shared workspace.

## The claim

`skills/_reference/herdr.md` gives teardown as
`herdr worktree remove --workspace <workspace-id>`, which is correct
only for a worktree cut with `herdr worktree create` — that command
makes a worktree and its own workspace together. The reference's own
"Spawning a design session" sequence cuts the worktree with
`wt switch --create` and opens a tab with `herdr tab create --cwd`, and
a tab created that way joins the **caller's existing workspace**. The
session agent's reported `workspace_id` is therefore the fleet's shared
workspace, and it looks exactly like the id the teardown instruction
asks for.

When this is built, the reference's teardown section is split by
provenance. It gives one path for a `herdr worktree create` worktree and
another for a `wt switch --create` worktree, and it states plainly that
a session's reported `workspace_id` is not safe to pass to
`herdr worktree remove` unless `herdr worktree create` produced it. The
`wt switch` path is the pair that worked:

    herdr tab close <tab-id>          # just this session's tab
    wt remove <branch> --foreground   # worktree + branch, once merged

The "Spawning a design session" sequence and the teardown section name
each other, so a reader who followed the first cannot arrive at the
wrong half of the second.

## Why

Followed literally, the instruction runs `herdr worktree remove
--workspace w3` and takes down every pane in the fleet's shared
workspace — dispatch, both intent conductors and every running session.
Nothing in the reported state signals the difference. The item body
carries the observed `workspace_id` and the working alternative.

## Boundaries

herdr's tab-workspace inheritance is not being changed; this makes the
reference true of it. Reclaiming what a skipped `post-remove` hook would
have handled — processes, ports — is already covered by the reference's
existing teardown text and is not restated here. The conductor's
obligation to tear down at all is loop practice, not this assertion.
