# AGENTS.md

This repo is a Claude Code plugin and its own marketplace. `README.md` says
what the flywheel is; this file says how to work on it.

Named `AGENTS.md` rather than `CLAUDE.md` for one concrete reason: Claude Code
hardcodes discovery of both, so contributors get this context either way — but
a `CLAUDE.md` at a *plugin* root is not loaded for anyone who installs the
plugin, and `claude plugin validate --strict` warns about exactly that. The
warning is right, the file is for contributors, and the rename settles both.

## The one rule that catches most mistakes

**Reference files inside this plugin as `${CLAUDE_PLUGIN_ROOT}/<path>`.**

A plugin is installed into a cache directory the author never sees —
`~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`. An absolute path
baked into a skill resolves on the machine it was written on and nowhere else,
and the failure is silent: the skill reads fine, cites a reference, and the
reference is not there. `node scripts/check-paths.mjs` is the gate, and it
covers `skills/`, `agents/`, `schemas/`, `tools/`, `bin/`, `hooks/`,
`commands/`.

## What goes where, and why the naming is asymmetric

| directory | holds | shipped? |
|---|---|---|
| `skills/<name>/` | a skill, invoked `/flywheel:<name>` | yes |
| `agents/<name>.md` | an agent profile | yes |
| `schemas/<name>/` | an OpenSpec workflow schema | yes |
| `bin/` | commands — **an installed plugin's `bin/` goes on the user's PATH** | yes |
| `tools/<name>/` | the implementation behind a `bin/` entry point | yes |
| `scripts/` | this repo's own gates | **no** |
| `site/` | the landing page, plain static files | **no** |

**Skills drop the `flywheel-` prefix. Agent profiles keep it.** A skill invokes
as `/<plugin>:<skill>`, so the plugin name already supplies the prefix and a
directory named `flywheel-inception` would produce `/flywheel:flywheel-inception`.
An agent is resolved by `claude --agent` under its **bare** name as well as its
namespaced one, so that name has to stay globally unique — hence
`flywheel-dispatch`, not `dispatch`.

**Nothing goes in `bin/` that is not meant to be a command in a stranger's
shell.** That is the whole reason this repo's gate scripts live in `scripts/`.

## Gates

```bash
devenv shell -- gates
```

Four checks. The same four run in `.config/wt.toml` before a merge and in
`.github/workflows/gates.yml` on every push, so a green claim means the same
thing in all three places. Add a gate to all three or to none.

- `claude plugin validate ./.claude-plugin/plugin.json --strict`
- `claude plugin validate ./.claude-plugin/marketplace.json --strict` —
  **both**, because passing a *directory* validates only the marketplace
  manifest and the plugin manifest is then never read
- `node scripts/check-paths.mjs`
- `node scripts/check-site.mjs`

Once `skills/` carries evals, `claude plugin eval .` joins them; the CI step is
already written and no-ops until then.

Two things `--strict` has already caught here, worth knowing before you
reintroduce either: a plain `README.md` under `agents/` is loaded as an **agent
profile** and fails for having no frontmatter (the placeholder is
`agents/.gitkeep` for that reason — `skills/` is safe, because a skill is
discovered as `skills/<name>/SKILL.md` and a loose file is ignored); and a
`CLAUDE.md` at the plugin root warns, which is why this file is `AGENTS.md`.

## Diagrams

Every mermaid block on the site must parse under `site/vendor/mermaid.min.js`
— the exact bundle the page ships. Mermaid never parses at build time: it
hands the source to the browser, and a syntax error renders as a **blank box**
rather than an error, so a broken diagram reaches production looking like a
layout bug.

Two rules the checker enforces, both learned the hard way:

- **`classDef` coverage in a flowchart is all-or-nothing.** If any node carries
  a class, every node must. An unclassed node beside a classed one falls
  through to mermaid's default theme and renders unreadably.
- **`classDef` carries no colours here.** Mermaid writes them as an inline
  `style="…!important"` on the shape, which no stylesheet can override — so a
  literal colour there cannot follow the page's light/dark theme. Declare the
  class with something inert (`stroke-width`) and put the colours in the
  page's own CSS, keyed to the class name, where the custom properties already
  know which theme is on.

Subgraph ids look exactly like node declarations and are not nodes; the
coverage check skips lines opening with `subgraph`.

`site/` has no build step and must keep having none. It is uploaded to Pages
as-is, so anything that needs compiling would ship uncompiled.

## Commits

Stage and commit only the paths you wrote: `git add <paths>` then
`git commit -- <paths>`. Never `-a`, never `add -A` or `add .`, never a
pathspec-less commit — a sibling agent may share this working tree and
therefore this index. Anything tree-wide (`git stash`, `git reset --hard`,
`git checkout .`) reaches their uncommitted work the same way.

## OpenSpec

This repo tracks its own changes under the `spec-driven` schema
(`openspec/config.yaml`). The two flywheel schemas it *publishes* are for
consuming repos to bind their intents and bolts to — they are not this repo's
own workflow, and no project copy of them belongs here.

## Layout on disk

The checkout uses the bare layout: `.bare/` holds git, the working tree is
`main/`, further worktrees sit beside it.
