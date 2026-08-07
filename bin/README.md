# bin/

**Reserved. Public commands only.**

Claude Code puts an installed plugin's `bin/` directory on the user's `PATH`
for the length of a session. Anything dropped here becomes a command in the
shell of every person who installs the flywheel, so it holds commands meant to
be called by name and nothing else.

This repository's own gate scripts live in `../scripts/`, precisely because
they are not that.

Empty on purpose today. `context-map` lands here.
