# bin/

**Reserved. Public commands only.**

Claude Code puts an installed plugin's `bin/` directory on the user's `PATH`
for the length of a session. Anything dropped here becomes a command in the
shell of every person who installs the flywheel, so it holds commands meant to
be called by name and nothing else.

This repository's own gate scripts live in `../scripts/`, precisely because
they are not that.

The `_`-prefixed `.py` files here are the exception the rule needs: shared
modules the commands beside them import, and that no user ever calls. They
carry the underscore and the extension precisely so they read as
not-a-command — `_flywheel_gh.py` (tracker plumbing), `_flywheel_sessions.py`
(session launch and supervision), `_flywheel_inbox.py` (the tracker's four
inbox filters), `_flywheel_bolt_loop.py` (the construction loop itself, which
`flywheel-bolt-loop` runs), `_flywheel_intent.py` (the design loop's cycle,
guards and dispatch) and `_flywheel_server.py` (the reconcile pass and the
daemon that repeats it). A loop program's logic lives in a module rather than in
the command because the command is extensionless and so not importable, and
the unit suite in `../tests/` has to reach it. A sibling imports one by
putting its own directory on the path, since the commands beside them are
extensionless:

```python
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _flywheel_gh import resolve_token, gh
```

The shared modules live here by decision
(`openspec/changes/loops-run-unattended/decisions/shared-module-home.md`):
a command must be reachable by name; its logic lives in an importable
sibling module when tests need it or commands share it; `../tools/` is for
a large command's whole implementation behind a thin entry point here,
never for shared libraries.

The commands here are zero-dependency stdlib scripts, which is the bar for
skipping the `../tools/` split:

- `flywheel` — drive an org fleet from its `fleet.yaml`. `server` is the
  daemon: every 60s it starts one loop process per milestone with a job,
  stops those without, and runs a one-shot archive for a closed
  milestone whose change is still on disk. `up` starts dispatch and then
  the server, detached; `status` reports both against the tracker. The
  `flywheel:fleet` skill wraps it.
- `flywheel-bolt-loop` — run one bolt's construction loop: query+guards,
  spec by the type's strategy, apply, verify, merge through the gate,
  landing per `bolt.md`, STOP. `--dry-run` reads and decides without
  writing; `--fixture` points it at a tracker file instead of GitHub.
- `flywheel-intent-loop` — run the design loop for one `intent/<slug>`
  milestone: guards, typed design sessions, `sess/*` merges, STOP.
  `--dry-run` plans every write and applies none.
- `flywheel-stage` — move one item to one `stage:*` label, removing any
  other. The one implementation of the one-stage rule, reachable from a
  pane: a design session told by the operator that an item is done runs
  this rather than a hand-built two-label edit, because which stage
  precedes the flip depends on where the item was picked up.
- `install-schemas` — publish the plugin's OpenSpec schemas as user
  schemas, moving any existing copy aside as `<name>.replaced`.

`context-map` lands here later, with its implementation in `../tools/`.
