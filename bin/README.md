# bin/

**Reserved. Public commands only.**

Claude Code puts an installed plugin's `bin/` directory on the user's `PATH`
for the length of a session. Anything dropped here becomes a command in the
shell of every person who installs the flywheel, so it holds commands meant to
be called by name and nothing else.

This repository's own gate scripts live in `../scripts/`, precisely because
they are not that.

Two commands live here now, whole — each is a self-contained,
zero-dependency script, which is the bar for skipping the `../tools/`
split:

- `flywheel` — drive an org fleet from its `fleet.yaml` (`up` /
  `status`); the `flywheel:fleet` skill wraps it.
- `install-schemas` — publish the plugin's OpenSpec schemas as user
  schemas, moving any existing copy aside as `<name>.replaced`.

`context-map` lands here later, with its implementation in `../tools/`.
