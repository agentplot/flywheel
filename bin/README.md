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
inbox filters) and `_flywheel_bolt_loop.py` (the construction loop itself,
which `flywheel-bolt-loop` runs and the unit suite imports). A sibling
imports one by putting its own directory on the
path, since the commands beside them are extensionless:

```python
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _flywheel_gh import resolve_token, gh
```

Whether shared modules like these belong here at all or under `../tools/` is
an open question — the bar stated below is "self-contained", and a command
importing a sibling module is arguably not that. It is queued rather than
settled mid-bolt, because moving `_flywheel_gh.py` touches five commands.

The commands here are zero-dependency stdlib scripts, which is the bar for
skipping the `../tools/` split:

- `flywheel` — drive an org fleet from its `fleet.yaml` (`up` /
  `status`); the `flywheel:fleet` skill wraps it.
- `flywheel-bolt-loop` — run one bolt's construction loop: query+guards,
  spec by the type's strategy, apply, verify, merge through the gate,
  landing per `bolt.md`, STOP. `--dry-run` reads and decides without
  writing; `--fixture` points it at a tracker file instead of GitHub.
- `install-schemas` — publish the plugin's OpenSpec schemas as user
  schemas, moving any existing copy aside as `<name>.replaced`.

`context-map` lands here later, with its implementation in `../tools/`.
