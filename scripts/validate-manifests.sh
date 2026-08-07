#!/bin/sh
# Validate both plugin manifests with the shipped validator.
#
#   sh scripts/validate-manifests.sh
#
# TWICE, not once, and not against the directory: `claude plugin validate .`
# resolves to the marketplace manifest and stops, so the plugin manifest is
# never read. Each file is named.
#
# WHICH BINARY. Some installs wrap `claude` in a shell script that appends
# session flags — a nix-darwin wrapper on the author's machine appends
# `--dangerously-skip-permissions` unconditionally, which every `claude
# <subcommand>` then rejects as an unknown option. CLAUDE_CODE_EXECPATH points
# at the real executable and is set inside every Claude Code session, which is
# where this runs from a `wt` hook. CI has no wrapper and falls through to
# PATH.
set -eu

cd "$(dirname "$0")/.."

if [ -n "${CLAUDE_CODE_EXECPATH:-}" ] && [ -x "${CLAUDE_CODE_EXECPATH}" ]; then
  CLAUDE="${CLAUDE_CODE_EXECPATH}"
elif command -v claude >/dev/null 2>&1; then
  CLAUDE="claude"
else
  echo "validate-manifests: no claude on PATH — npm i -g @anthropic-ai/claude-code" >&2
  exit 2
fi

for manifest in ./.claude-plugin/plugin.json ./.claude-plugin/marketplace.json; do
  if ! out=$("$CLAUDE" plugin validate "$manifest" --strict 2>&1); then
    printf '%s\n' "$out" >&2
    case "$out" in
      *"unknown option"*"--dangerously-skip-permissions"*)
        echo "" >&2
        echo "validate-manifests: the \`claude\` on PATH is a wrapper that appends" >&2
        echo "session flags, which subcommands reject. Run this from inside a" >&2
        echo "Claude Code session, or point CLAUDE_CODE_EXECPATH at the real" >&2
        echo "executable." >&2
        ;;
    esac
    exit 1
  fi
  printf '%s\n' "$out" | tail -1
done
