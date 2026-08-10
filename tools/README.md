# tools/

Implementations of the larger commands this plugin puts on your `PATH` —
zero-dependency, with a thin entry point in `../bin/`. A command that is
itself one self-contained script (today's `flywheel`, `install-schemas`)
lives whole in `../bin/` instead. Empty until `context-map` arrives.

Empty on purpose today. `context-map` lands here — the bounded-context map
viewer, its schema, and the checker that proves every node on the map cites a
chapter that exists.
