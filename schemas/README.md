# schemas/

Empty on purpose. The two OpenSpec workflow schemas land here when the split
runs: `flywheel-intent` (one intent, its decisions, its design sessions, its
typed tasks) and `flywheel-bolt` (one construction iteration and its proposals
registry).

They are distributed as **user schemas**, installed under
`~/.local/share/openspec/schemas/` and resolved by name. `openspec schema which
--all` reports three sources — `project`, `user`, `package` — and a project copy
shadows a user copy, so a repo that wants a working copy can still fork one
without losing the published binding.
