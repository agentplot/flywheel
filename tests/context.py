"""Make `bin/`'s private modules importable from a test.

`python3 -m unittest discover -s tests -t .` puts the repo root on `sys.path`,
not `bin/`, and the scripts beside these modules are extensionless on purpose
(they are commands, and `bin/` is on every installed user's PATH). So the one
path insert lives here rather than at the top of every test file.

    from context import ROOT, sessions, inbox
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin"
FIXTURES = ROOT / "workflows" / "fixtures"

if str(BIN) not in sys.path:
    sys.path.insert(0, str(BIN))

import _flywheel_herdr as herdr            # noqa: E402
import _flywheel_inbox as inbox            # noqa: E402
import _flywheel_intent as intent          # noqa: E402
import _flywheel_ledger as ledger          # noqa: E402
import _flywheel_manifest as manifest_mod  # noqa: E402
import _flywheel_sessions as sessions      # noqa: E402

__all__ = ["ROOT", "BIN", "FIXTURES", "herdr", "inbox", "intent", "ledger",
           "manifest_mod", "sessions"]
