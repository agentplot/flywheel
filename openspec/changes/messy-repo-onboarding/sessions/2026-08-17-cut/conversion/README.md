# Conversion 001 — one settled artifact, end to end

This directory is the **worked conversion** #270 asks for: one settled
artifact taken from the corpus all the way to flywheel-native form, so
clause 2 of the promise (`../../../decisions/onboarding-promise.md`) is
measured rather than assumed.

## Why it is staged here and not landed

The corpus is `WilldanGroup/knowledgebase-spike` and its destination
books are `WilldanGroup/willdan-blueprints`. **Cross-org landing is
#267, still open.** The promise's own boundary applies — "until it's
settled, an import of a foreign-org corpus stops at the report tier"
— so this conversion is produced in full and **staged**, never written
into the client's tree. Every file below names the exact path it would
land at. Nothing in `~/Code/clients/github_willdan/` was written by
this session.

That is the point of running the measurement on a foreign corpus: the
conversion is exercised, the landing is not, and the seam between them
is now a file you can look at rather than a claim.

## The artifact

`SPIKE.md` L1585–L1644 — `# Design — the Atlas/GEOIQ seam: sidecar
contract vs KB lifecycle (settled)`. Chosen because it is the hardest
useful case, not the easiest: it is explicitly marked settled, it is
self-contained, **and** its substance turns out to be already present
in the destination books — which is the case an importer is most
likely to get wrong by silently duplicating it.

## The three outputs, and where each lands

| output | file here | would land at |
| --- | --- | --- |
| session-under-intent record | `session-record.md` | `willdan-blueprints/openspec/changes/kb-spike-import/sessions/2026-07-23-atlas-geoiq-seam/README.md` |
| decision record | `decision-atlas-geoiq-seam.md` | `willdan-blueprints/openspec/changes/kb-spike-import/decisions/atlas-geoiq-seam.md` |
| books-verdict | `books-verdict.md` | inside the session record above (verdicts are per-artifact, they do not get their own tree) |
| processed-ledger entry | `ledger-entry.jsonl` | `$FLYWHEEL_STATE_HOME/willdan/imports/knowledgebase-spike/processed.jsonl` |

## What the conversion measured

Three things this artifact settled that a design without a real corpus
would not have found — all written up in `../findings.md`:

1. The books-verdict came back **no-change-needed**, with the chapter
   that already carries the rule cited line by line. A verdict that
   says "already written, here is where" is a first-class outcome and
   the ledger has to be able to record it.
2. A section marked `(settled)` still carried a forward tail — its
   `## Writeback hook` paragraph is live work. Section granularity was
   not fine enough; the cut had to go to the paragraph.
3. The verdict is unreachable from the corpus alone. It required
   reading the destination books. An importer that reads only what it
   was handed cannot produce it.
