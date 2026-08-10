# Charge — intent `flywheel`, batch 7

- Change: `openspec/changes/flywheel/`
- Session type: **research**
- Session directory: `sessions/2026-08-14-mermaid-gate/`
- Your conductor: herdr agent `intent-flywheel`, running in pane 3

## Task lines this batch works

- [ ] 6.2 Design (research): `decisions/session-worktrees` claims a session
      worktree needs no provisioning, but a report says two of the three
      repo gates fail in a fresh worktree. Find out which gates actually
      fail, and why. The answer decides whether the decision needs a
      provisioning hook.

## Where the investigation got to

You ran all three gates from a herdr-cut worktree with no `node_modules`:

```
$ python3 books/preview.py --check      → exit 0   (8 books)
$ node context-map/bin/map-check.mjs    → exit 0   (clean)
$ node books/check-mermaid.mjs          → exit 2
  cannot find module 'jsdom' — run `npm ci` in the main checkout
```

One gate fails, not two. `map-check.mjs` imports only `node:fs`,
`node:url`, and `node:path`, so it never needed `node_modules`.

Reading `books/check-mermaid.mjs`, the cause is in `mainWorktree()`:

```js
function mainWorktree() {
  const out = execSync('git worktree list --porcelain').toString();
  return out.split('\n')[0].replace('worktree ', '');   // ← first line
}
```

In this repo's bare layout the first `worktree` line is `<repo>/.bare`, not
`<repo>/main/` where `npm ci` ran, so `loadJsdom()` looks in the wrong
place. Testing each listed worktree for a resolvable `jsdom` instead of
trusting the print order fixes it — two lines, and you have them written.

`books/check-mermaid.mjs` is owned by nobody in particular; nothing else in
the repo has been touched today.
