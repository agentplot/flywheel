#!/bin/sh
# hook marker: records that a hook fired, and on which tree.
# Exit code comes from WTLAB_RC_<HOOK> (e.g. WTLAB_RC_PRE_MERGE=1) so failures
# can be exercised without changing the approved hook command text.
LOG="${WTLAB_LOG:-/tmp/wtlab/hooks.log}"
printf '%s cwd=%s head=%s payload=%s\n' \
  "$1" "$(basename "$PWD")" "$(git rev-parse --short HEAD 2>/dev/null)" \
  "$(cat payload.txt 2>/dev/null || echo NONE)" >> "$LOG"
var="WTLAB_RC_$(printf '%s' "$1" | tr 'a-z-' 'A-Z_')"
eval "rc=\${$var:-0}"
exit "$rc"
