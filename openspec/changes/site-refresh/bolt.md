# Bolt: site-refresh

## Scope

Rebuild `site/` — the GitHub Pages landing page at
https://agentplot.github.io/flywheel/ — around the settled hero design, and
register that URL as the repository homepage. The page today is a single
503-line `site/index.html` plus a vendored mermaid bundle, served as plain
static files with no build step; the rebuild keeps that shape and replaces
the content: the hero from the operator's settled study, a nav/tab
walkthrough structure over it, and required links back to the GitHub
repository and the docs. The homepage registration is part of this bolt's
done, not a follow-up.

## Sources

No intent. Dispatch triaged this as a quick bolt (route 4) on 2026-08-12 —
small and fully defined, so its one assertion was born `state:ready` on the
operator's word at triage and carries no assertion record file. The item
body IS the assertion: agentplot/flywheel#12.

The operator's word, recorded on that item:

- **No spec.** The no-spec path applies: the build session opens in plan
  mode, its plan is checked against the item's claim, and the conductor
  approves it before any edit. No `/opsx:ff` spec-driven change in the
  built repo.
- The hero design in `/Users/chuck/Downloads/flywheel-hero_1.html` is
  settled and not up for redesign.
- Nav/tabs are the walkthrough structure; links back to GitHub and the docs
  are required content.

## Repos

- agentplot/flywheel · bolt branch `bolt/site-refresh` · worktree
  `~/.herdr/worktrees/.bare/bolt-site-refresh`

This repo is a bare checkout at `flywheel/.bare` with `main` as a linked
worktree, so the bolt worktree is cut from the bare path and herdr names the
repo `.bare` in the worktree layout. It is the same repository — this bolt's
built repo and the org's tracker are one and the same.

## Merge criteria

`bolt-quick` schedules no review step. What must hold before the bolt branch
lands on main:

- **The three gates green on the tree that lands.** `.config/wt.toml`
  configures `sh scripts/validate-manifests.sh`, `node
  scripts/check-paths.mjs`, and `node scripts/check-site.mjs` as pre-commit
  hooks; `wt merge` runs them on the exact rebased tree, so the green is
  produced by the tool. `check-site.mjs` is the load-bearing one here:
  mermaid never parses at build time, so a broken diagram renders as a blank
  box rather than an error, and this gate is the only thing between a syntax
  error and production.
- **Nothing loads from a CDN.** What ships is what is in the repository —
  the page already vendors its own mermaid bundle for this reason. The
  settled hero study links two Google Fonts stylesheets; the fonts must be
  vendored into `site/` (both faces are openly licensed) or replaced by a
  system stack that preserves the design. This is not currently enforced by
  a gate, so it is checked by reading the shipped HTML for external hosts.
- **The plan was approved against the item's claim** before any edit —
  the no-spec path's substitute for a spec.
- **The full release gate at the landing.** `wt merge` with full hooks,
  never weakened, one writer to main at a time.

After landing, and only then:

- **The Pages deploy is green and the new content is served.**
  `.github/workflows/pages.yml` publishes on a push to `main` touching
  `site/**`; it re-runs `check-site.mjs` before deploying. The claim "the
  site is live" means that run succeeded and
  `curl -o /dev/null -w '%{http_code}' https://agentplot.github.io/flywheel/`
  returns 200 on the new content.
- **The homepage is registered.** Measured on `main` at f0e571a and
  re-measured on 8b8a1a3: `PATCH /repos/agentplot/flywheel` with `homepage`
  requires repo administration:write; the flywheel app installation reports
  `permissions.admin = false` on this repo, and the operator's own `gh` auth
  (`afterthought`) reports `permissions.admin = true`. So this one write runs
  on the operator's auth, not on `GH_TOKEN=$(flywheel-token …)`:

      gh api -X PATCH /repos/agentplot/flywheel \
        -f homepage=https://agentplot.github.io/flywheel/

  `repos/agentplot/flywheel` currently reports `homepage: null` and
  `has_pages: true`, with Pages sourced from the workflow.
