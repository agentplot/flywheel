#!/usr/bin/env node
/* =============================================================================
   check-site — the landing page's two silent failure modes, caught before
   they ship.

     node scripts/check-site.mjs

   1. MERMAID. A mermaid block is never parsed at build time. The page hands
      the source to the browser, and a syntax error renders as a blank box
      rather than an error — so a broken diagram reaches production looking
      like a layout bug. This runs the parser the reader's browser runs: the
      very bundle in site/vendor/, loaded under jsdom, so the check cannot
      drift from the render.

   2. LINKS AND ASSETS. Every relative href and src in the site must resolve
      to a file on disk. GitHub Pages serves a 404 for the ones that do not,
      and nothing in the build says so.

   Zero configuration: it walks site/, finds the bundle, and reports.
   ============================================================================= */

import { createRequire } from "node:module";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join, relative, resolve } from "node:path";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const SITE = join(ROOT, "site");
const BUNDLE = join(SITE, "vendor", "mermaid.min.js");

const failures = [];
const fail = (where, msg) => failures.push(`${where}  ${msg}`);
const rel = (p) => relative(ROOT, p);

/* ------------------------------------------------------------- the pages -- */
function htmlFiles(dir) {
  const found = [];
  for (const e of readdirSync(dir, { withFileTypes: true })) {
    if (e.name === "vendor" || e.name.startsWith(".")) continue;
    const p = join(dir, e.name);
    if (e.isDirectory()) found.push(...htmlFiles(p));
    else if (e.name.endsWith(".html")) found.push(p);
  }
  return found.sort();
}

if (!existsSync(SITE)) {
  console.error("check-site: no site/ directory");
  process.exit(2);
}
const pages = htmlFiles(SITE);
if (!pages.length) {
  console.error("check-site: site/ carries no .html");
  process.exit(2);
}

/* ------------------------------------------------------------- 1. mermaid -- */
/* Load the bundle as a real <script>, not eval: it is an esbuild IIFE whose
   last line reads its result back off globalThis, and a top-level `var` only
   lands there when the code runs as a script. */
function loadMermaid() {
  if (!existsSync(BUNDLE)) {
    console.error(`check-site: ${rel(BUNDLE)} is missing — run \`npm run vendor-mermaid\``);
    process.exit(2);
  }
  const require_ = createRequire(join(ROOT, "package.json"));
  let JSDOM;
  try {
    ({ JSDOM } = require_("jsdom"));
  } catch {
    console.error("check-site: jsdom not installed — run `npm ci`");
    process.exit(2);
  }
  const dom = new JSDOM("<!doctype html><body></body>", {
    runScripts: "dangerously",
    pretendToBeVisual: true,
  });
  const el = dom.window.document.createElement("script");
  el.textContent = readFileSync(BUNDLE, "utf8");
  dom.window.document.body.appendChild(el);
  if (!dom.window.mermaid?.parse) {
    console.error(`check-site: ${rel(BUNDLE)} did not expose a parser`);
    process.exit(2);
  }
  dom.window.mermaid.initialize({ startOnLoad: false });
  return dom.window.mermaid;
}

/* Scanner rather than a DOM walk: it has to agree with mermaid's own
   client-side selector, which matches `pre.mermaid` textually the same way. */
function mermaidBlocks(html) {
  const found = [];
  const re = /<pre\b[^>]*class="[^"]*\bmermaid\b[^"]*"[^>]*>([\s\S]*?)<\/pre>/g;
  let m;
  while ((m = re.exec(html))) {
    found.push({
      line: html.slice(0, m.index).split("\n").length,
      text: m[1]
        .replace(/&lt;/g, "<").replace(/&gt;/g, ">")
        .replace(/&quot;/g, '"').replace(/&#3[49];/g, "'")
        .replace(/&amp;/g, "&"),
    });
  }
  return found;
}

const mermaid = loadMermaid();
let diagrams = 0;

for (const page of pages) {
  const html = readFileSync(page, "utf8");
  for (const block of mermaidBlocks(html)) {
    diagrams++;
    try {
      const parsed = mermaid.parse(block.text);
      if (parsed?.then) await parsed;
    } catch (error) {
      const detail = String(error?.message ?? error)
        .split("\n").map((l) => l.trim()).filter(Boolean).slice(0, 3).join(" / ");
      fail(`${rel(page)}:${block.line}`, `mermaid: ${detail}`);
    }
  }

  /* Coverage rule, all-or-nothing: an unclassed node beside a classed one
     falls through to mermaid's default theme and renders unreadably against a
     dark background. Mermaid parses it happily, so only this catches it. */
  for (const block of mermaidBlocks(html)) {
    const body = block.text.trim();
    if (!/^\s*flowchart\b/m.test(body.split("\n")[0] ?? "")) continue;
    const classed = new Set();
    for (const m of body.matchAll(/^\s*class\s+([A-Za-z0-9_,\s-]+?)\s+\w[\w-]*\s*$/gm))
      for (const id of m[1].split(",")) classed.add(id.trim());
    /* `subgraph X ["title"]` looks exactly like a node declaration and is not
       one — a cluster takes its styling from .cluster, never from a class. */
    const declarations = body.split("\n").filter((l) => !/^\s*subgraph\b/.test(l)).join("\n");
    const declared = new Set();
    for (const m of declarations.matchAll(/(?:^|\s|-->|---|-\.->|==>)\s*([A-Za-z][A-Za-z0-9_-]*)\s*[[({]/g))
      declared.add(m[1]);
    const unclassed = [...declared].filter((id) => !classed.has(id));
    if (classed.size && unclassed.length)
      fail(`${rel(page)}:${block.line}`,
        `mermaid classDef coverage is all-or-nothing — unclassed: ${unclassed.join(", ")}`);
  }

  /* --------------------------------------------------- 2. links and assets -- */
  const refs = new Set();
  for (const m of html.matchAll(/\b(?:href|src)="([^"]+)"/g)) refs.add(m[1]);
  for (const r of refs) {
    if (/^(https?:|mailto:|data:|#|\/\/)/.test(r)) continue;
    const [path_] = r.split("#");
    if (!path_) continue;
    const target = path_.startsWith("/")
      ? join(SITE, path_.slice(1))
      : resolve(dirname(page), path_);
    const ok = existsSync(target) &&
      (statSync(target).isFile() || existsSync(join(target, "index.html")));
    if (!ok) fail(rel(page), `dead reference: ${r}`);
  }
}

if (failures.length) {
  for (const f of failures) console.error("check-site: FAIL " + f);
  console.error(`check-site: ${failures.length} problem${failures.length === 1 ? "" : "s"}`);
  process.exit(1);
}
console.log(`check-site: ok — ${pages.length} page${pages.length === 1 ? "" : "s"}, ${diagrams} diagrams parse, every reference resolves.`);
