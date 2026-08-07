#!/usr/bin/env node
/* =============================================================================
   check-paths — nothing this plugin ships may name a path that exists only on
   the machine it was written on.

     node scripts/check-paths.mjs

   A plugin is installed into a cache directory whose location the author never
   sees: ~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/. Every
   in-plugin reference therefore goes through ${CLAUDE_PLUGIN_ROOT}, and an
   absolute path baked into a skill is a file that resolves on one laptop and
   nowhere else. The failure is silent — the skill reads fine, cites a
   reference, and the reference is not there.

   This is acceptance-checklist item five from the split decision record
   (`flywheel-repo-manifest.md`), installed as a standing gate rather than a
   grep run once at the end, so it cannot regress between now and then.

   Zero dependencies on purpose: a bare `node` runs it, in a hook and in CI.
   ============================================================================= */

import { readdirSync, readFileSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join, relative, resolve } from "node:path";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

/* The shipped surface. site/ and scripts/ are this repo's own and never travel
   into a plugin cache, so they are not bound by the rule. */
const SCANNED = ["skills", "agents", "schemas", "tools", "bin", "hooks", "commands"];

/* Machine-local roots. A path under any of these is wrong in shipped content
   however it got there — a hard-coded home directory, a nix store path a
   devenv shell printed, a Linux home from a container. */
const ABSOLUTE = [
  [/\/Users\/[A-Za-z0-9._-]+/g, "a macOS home directory"],
  [/\/home\/[A-Za-z0-9._-]+/g, "a Linux home directory"],
  [/\/nix\/store\/[a-z0-9]{32}-/g, "a nix store path"],
  [/\/private\/tmp\/[A-Za-z0-9._-]+/g, "a scratch directory"],
];

/* Files worth reading. Binaries and vendored bundles are not authored here. */
const TEXT = /\.(md|mjs|js|cjs|json|ya?ml|sh|txt)$/;

const findings = [];

function walk(dir) {
  let entries;
  try {
    entries = readdirSync(dir, { withFileTypes: true });
  } catch {
    return; // a scanned directory that does not exist yet is not a failure
  }
  for (const e of entries) {
    const p = join(dir, e.name);
    if (e.isDirectory()) {
      if (e.name === "node_modules" || e.name === ".git") continue;
      walk(p);
    } else if (e.isFile() && TEXT.test(e.name) && statSync(p).size < 2_000_000) {
      scan(p);
    }
  }
}

function scan(path) {
  const rel = relative(ROOT, path);
  const lines = readFileSync(path, "utf8").split("\n");
  lines.forEach((line, i) => {
    /* The rule is about paths this plugin would follow, not about prose that
       names one. A fenced example is still a path someone will copy, so no
       exemption is given for code blocks — say ${CLAUDE_PLUGIN_ROOT} there
       too. */
    for (const [re, what] of ABSOLUTE) {
      re.lastIndex = 0;
      let m;
      while ((m = re.exec(line))) {
        findings.push(`${rel}:${i + 1}  ${what}: ${m[0]}`);
      }
    }
  });
}

for (const d of SCANNED) walk(join(ROOT, d));

if (findings.length) {
  console.error(
    `check-paths: ${findings.length} absolute path${findings.length === 1 ? "" : "s"} in shipped content.\n` +
    `Reference files inside this plugin as \${CLAUDE_PLUGIN_ROOT}/<path>.\n`);
  for (const f of findings) console.error("  " + f);
  process.exit(1);
}

console.log(`check-paths: clean (${SCANNED.join(", ")}).`);
