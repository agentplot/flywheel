# tools/

Implementations of the commands this plugin puts on your `PATH`. Each one is
zero-dependency Node so a bare `node` runs it, and each has a thin entry point
in `../bin/`.

Empty on purpose today. `context-map` lands here — the bounded-context map
viewer, its schema, and the checker that proves every node on the map cites a
chapter that exists.
