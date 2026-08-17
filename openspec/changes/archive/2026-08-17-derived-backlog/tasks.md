# Tasks

## 1. Inbox

- [x] 1.1 Plan-card model: parse slug, system, input commits, Team,
  Status, blocked-by, stale marker from a `plan`-labeled item
- [x] 1.2 Snapshot carries plan cards; server inbox yields a bolt job
  for a Ready card awaiting expansion
- [x] 1.3 Task-table parser for the plan document body
- [x] 1.4 Tracker writes: create milestone, set milestone, attach
  sub-issue, clear board Status

## 2. Server

- [x] 2.1 `books:` bindings on ServerConfig, parsed from fleet.yaml
- [x] 2.2 Staleness marking against current book/spec heads
- [x] 2.3 Planning-run charge on missing-or-stale + settled book, with
  backoff; run-record entries
- [x] 2.4 Wire the planner charge in bin/flywheel (herdr session,
  flywheel-bolt-planner profile)

## 3. Expansion

- [x] 3.1 Bolt loop expansion guard: milestone, card→unit, items from
  tasks, Ready consumed, charter written
- [x] 3.2 Team-missing pause; builds-on defer via blocked-by
- [x] 3.3 flywheel-bolt-planner profile; skill board-mode conventions
  (card title, System line, Team at filing)

## 4. Tests

- [x] 4.1 Fixture support: plan cards, board rows, new writes recorded
- [x] 4.2 Trigger tests: quiet/moving book, missing/stale/fresh cards
- [x] 4.3 Expansion tests: full path, Team refusal, defer
- [x] 4.4 Full suite green
