# flywheel

**Two loops that turn intent into built code.** A design loop burns fog into
decisions. A construction loop drives proposals to merged. They are coupled at
exactly one point, and that point is you.

A Claude Code plugin, and its own marketplace.
[The landing page](https://agentplot.github.io/flywheel/) has the diagrams.

---

## Why two loops

Most agent workflows collapse design and construction into one conversation.
That works until the conversation has to do both at once — and then it does
neither, because the two answer to different things.

Design is slow and converging. It is full of open questions, it produces
records rather than commits, and its output is a destination somebody could
build toward. Construction is fast and parallel. It wants a settled target, it
produces commits, and its output is merged code.

Fused, you get one of two failures: designing under build pressure, where the
first plausible answer wins because something has to compile; or building
against a design still moving, where half the work is redone every time a
question closes.

So there are two loops, each with its own record and its own actors, and one
place where work crosses from the first into the second.

## The design loop — an intent

One **intent** is one tracked change. Its task list is the frontier, and the
loop's whole job is burning fog into decisions, writing the destination into
the design books and the context map, and handing settled slices on.

```
a raw idea
  → dispatch routes it, and files the intent
  → a design session works a batch of its tasks
  → a decision record, plus the books and the map
  → a handoff — batched, named, drafted to the point of one question
```

A task is filed under the session type that will run it, so the line says
both what the work is and who does it. The six design types, chosen by
what you will actually do with the material:

| type | the session it spawns |
|---|---|
| **design** | builds a page you work — options, trade-offs, coupled choices side by side |
| **planning** | puts drafts the session wrote through plannotator for your annotations |
| **research** | answers a factual question by reading code, docs, and behaviour |
| **prototype** | settles a fact a throwaway can prove faster than an argument can |
| **writeback** | rewrites chapters and moves the map — no approval sought, because the books are the loop's own scope |
| **handoff** | composes the release request and carries the receipt — the one type behind your approval |

Open questions live as records with state, not as a task type: a question
closes into a decision, and the decision's consequences become tasks.

## The construction loop — a bolt

One **bolt** is one construction iteration, tracking a registry of proposals
across however many repositories the work touches. A bolt exists only past the
gate, which is why it can run without you: the approval that released it is
the approval for everything inside it.

Each row of the registry moves through one sequence:

```
to-spec → specced → in-review → approved → building → built → verified → merged
```

A bounced review returns the row to `to-spec` — **once**. After that the row
takes one binary call on the evidence in hand (approve, or re-spec from the
decision record that settled it) and then builds. Further rounds converge on
wording rather than on whether the thing can actually be built.

What is bounded is *reading*. The commit stage, the merge gate, the batched
acceptance run and the full release gate never relax. Adversarial agent review
plus automated testing is what earns the loop its automated delivery, and
weakening either of them is a design decision, not a call the loop makes for
itself.

## The gate between them

Nothing crosses from design into construction without your word.

It is **one inline approval covering a whole batch** — the proposals already
named, the bolt already drafted, the repositories and merge criteria already
written, so you answer rather than design. It is taken on the cheapest channel
that can carry it. It is not a meeting, not a status report, and not one
question per proposal.

Two moments in a bolt's life belong to you: the gate that created it, and the
closure you agree to. Nothing between them is a standing human stage.

## One rule does most of the work

> Every file edit that is not a design record is construction, and leaves
> through the gate. Including edits to the repository the loop itself runs in.

Without it, the design loop quietly grows a habit of making small fixes, and
the record of why the code looks the way it does starts going missing. With it
there is exactly one path out of design — and a handoff carrying a single
proposal is a **one-proposal bolt**: the same path at its smallest size, not a
shortcut around it.

## The actors

Nine profiles: six actors and three persona lenses. Each actor owns a
write scope, and the scopes do not overlap.

| actor | lives as long as | writes |
|---|---|---|
| `flywheel-dispatch` | always — one per fleet | new intent changes, at the moment of triage; inbox files; nothing else |
| `flywheel-intent-conductor` | its intent | that intent's records on main; the books; the context map |
| `flywheel-bolt-conductor` | its bolt | the bolt's proposal registry and its tasks, on main |
| `flywheel-design-session` | one task batch | its session directory, its own task lines, its charged closures, the books and map — in its worktree |
| `flywheel-interactive-session` | one task batch | the same, and it builds a page you work |
| `flywheel-construction-session` | one task batch | the built repo and its own task lines — in its worktree |

The `user-*` profiles — data scientist, DevOps engineer, app developer —
are personas: lenses a review session reads built work through, never
actors, never owners.

Two consequences worth stating outright, because both are load-bearing:

- **A session closes what it was charged with; the conductor opens what
  it discovered.** In its own worktree a session checks off exactly its
  assigned task lines and writes the decision records for questions it
  closed firsthand; the conductor is sole writer on main, and its merge
  is what admits a session's work. A conductor, symmetrically, never
  edits inside a session's directory.
- **Dispatch is the only actor bridged to a human.** A question a bolt
  conductor cannot answer travels out through dispatch — resolved change
  → owner → DM — and the answer comes back to the conductor that raised
  it, never to a different actor, and never as an edit to that
  conductor's change.

## Install

The repository is its own marketplace, so it is two commands:

```
/plugin marketplace add agentplot/flywheel
/plugin install flywheel@flywheel
```

## Working on the flywheel itself

Both commands above are bypassed while you are editing the plugin. Point
Claude Code at a checkout and reload in place — no publish, no reinstall, no
version bump between an edit and trying it:

```bash
claude --plugin-dir /path/to/flywheel/main
```

then `/reload-plugins` in the session.

### Gates

Three checks, defined once and run by three callers — `.config/wt.toml` before
a merge, `devenv.nix` by hand, and `.github/workflows/gates.yml` on every push
— so a green claim means the same thing everywhere:

```bash
devenv shell -- gates
```

- **`scripts/validate-manifests.sh`** — `claude plugin validate --strict` on
  both manifests. Twice, because passing a directory resolves to the
  marketplace manifest and the plugin manifest is then never read.
- **`scripts/check-paths.mjs`** — no absolute path survives in shipped
  content. A plugin is installed into a cache directory the author never sees,
  so a hard-coded home directory resolves on one laptop and nowhere else, and
  it fails silently: the skill reads fine and its reference is simply not
  there.
- **`scripts/check-site.mjs`** — every mermaid block on the landing page
  parses under the very bundle the page ships, and every relative reference
  resolves. Mermaid never parses at build time; a syntax error renders as a
  blank box rather than an error, so a broken diagram would otherwise reach
  production looking like a layout bug.

`devenv shell -- site-up` serves the page at <http://127.0.0.1:8451>.

## Layout

```
.claude-plugin/   plugin.json and marketplace.json — this repo is both
skills/           the loop skills and the session-type skills
agents/           the nine agent profiles — six actors, three personas
schemas/          the OpenSpec workflow schemas, published as user schemas
bin/              commands. An installed plugin's bin/ goes on your PATH
tools/            the implementations behind bin/, zero-dependency
scripts/          this repo's own gates. Never shipped, never on PATH
site/             the landing page. Plain static files, no build step
openspec/         this repo's own tracked changes
```

**Skills drop the `flywheel-` prefix; agent profiles keep it.** A skill invokes
as `/<plugin>:<skill>`, so the plugin name supplies the prefix and the
directory sheds it — `skills/inception/` is `/flywheel:inception`. An agent is
resolved by `claude --agent` under its **bare** name as well as its namespaced
one, so the bare name has to stay globally unique and `flywheel-dispatch` keeps
its prefix.

## Status

The machinery is landed: fifteen loop and session-type skills, the fleet
skill and command, nine profiles, four schemas, and the OpenSpec record
that built them. Nine skills have no eval suites yet (the seven
construction types, `handoff`, and `fleet`), the seven travelled suites
await conversion to the format `claude plugin eval` reads, and the
context-map tool arrives in a later change.

MIT licensed.
