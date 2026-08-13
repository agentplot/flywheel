#!/bin/sh
# Run the unit suite.
#
#   sh scripts/test.sh
#   npm test
#   devenv shell -- tests
#
# Three callers, one definition, the way the three gates already work.
#
# STDLIB unittest, no pytest, no requirements file. Everything in bin/ is a
# zero-dependency stdlib script — that is the repo's stated bar — and a test
# runner that needs a package install would be the first thing here that does
# not clear it. `pkgs.python3` is already in devenv.nix.
#
# NOT A MERGE GATE. This is deliberately not registered in .config/wt.toml's
# [pre-merge] hooks: those three are approval-gated in
# ~/.config/worktrunk/approvals.toml, and adding a fourth would make every
# merge fail with "Cannot prompt for approval in non-interactive environment"
# until the operator grants it by hand. Wiring it into the gate and into CI is
# a separate item, with the approval taken first.
set -eu

cd "$(dirname "$0")/.."

# -t tests, not -t .  — tests/ is the top-level directory for discovery, which
# puts it on sys.path so `from context import ...` resolves. With `-t .` the
# tests/ directory would have to be an importable package, and it is a
# directory of scripts, not a package.
exec python3 -m unittest discover -s tests -t tests "$@"
