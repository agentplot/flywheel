## Context

See proposal.md — Why. What the tree bore out when this was written, so a
build can re-check it rather than trust it. Re-read each before building
on it; where the tree has moved, say so in the report rather than building
over it.

- `guard_charter` in `bin/_flywheel_bolt_loop.py` is guard 0.6. Its unit
  scan walks `snapshot.on(self.params.milestone)` sorted by number, skips
  anything without the `unit` label, and then does
  `slug = inbox.PlanCard(number=item.number, title=item.title).slug`
  followed by `if not slug or f"{slug}.md" in sealed: continue`. Its
  comment on that line reads "A title that parses no slug is the subject of
  a sibling change and is left alone here."
- After the scan the guard returns `None` when `wanted` is empty; then
  comes the `--dry-run` branch (one "would write" action, return `None`),
  then the `isinstance(self.tracker, FixtureTracker)` branch (return
  `None`, writing nothing), then `ledger.expect`, the writes, the
  `git add`/`git commit` by pathspec, the commit-failure reason string
  ending "the next pass retries it", `ledger.actual`, and the action.
- A unit whose body is empty is handled separately, one line below the slug
  test: `self._log(...)` and `continue`. It is not what this change is
  about.
- `PlanCard.slug` in `bin/_flywheel_inbox.py` is
  `re.match(r"^\s*(?:Unit|Plan|Bolt):\s*([a-z0-9][a-z0-9-]*)\s*$", self.title, re.IGNORECASE)`,
  returning the group or `None`. The prefix is case-insensitive; the slug
  body is not — a capital letter, an underscore, a space, or a leading
  hyphen in the name all answer `None`.
- `guards()` calls `guard_charter(snapshot, actions)` and returns
  `(actions, charter)` the moment it is not `None`. `cycle()` sets
  `result.halted = failure` and returns before the ready set is driven.
  `run()` sets `report.halted`, calls
  `self.ledger.note(f"HALTED — {result.halted}")`, finishes the
  observation and returns. `bin/flywheel-bolt-loop` renders it as
  `    HALTED · {cycle.halted}` and carries `halted` in its JSON.
- `BoltLoop.__init__` sets `self._log = log or (lambda message: None)`;
  `bin/flywheel-bolt-loop` passes a real `log`. So `_log` output is the raw
  loop log, which `books/flywheel/src/observation.md` distinguishes from
  the curated run record: "Facts originate in the record and nowhere else."
- `tests/test_derived_backlog.py` holds `CharterTest` with `FakeGit` (a git
  that answers `ls-tree` from a `head` dict and only moves staged paths
  into it on a successful `commit`), `NotTheFixtureTracker`, and the
  module-level `unit_item(number, slug, **kw)` helper, which builds
  `{"title": f"Unit: {slug}", "labels": ["unit"], ...}` — its `**kw`
  already lets a test override `title`.
- `openspec/specs/flywheel-derived-backlog/spec.md` carries the requirement
  "Each approved unit's document is its own artifact", whose scenarios are
  "the first unit", "a second unit expands", "nothing newly expanded" and
  "a torn write is repaired, not read as done".

## Goals / Non-Goals

**Goals:**

- No approved unit leaves `guard_charter` unwritten and unmentioned.
- The operator learns which card is wrong and what is wrong with it from
  the run report alone, without reading the loop's source.
- The guard keeps its dry-cycle property on every milestone whose unit
  titles parse.

**Non-Goals:**

- **A unit whose body is empty.** It is logged and skipped today. The log
  is not the run record, so the fact does not originate where
  `observation.md` says facts originate — but the case is named by neither
  this assertion nor the unit plan, and deciding whether an empty body is a
  pause or a permitted absence is a design decision nobody has made. Left
  exactly as it stands and recorded as a finding.
- **Two unit cards whose titles parse to the same slug.** The second is
  skipped by the `f"{slug}.md" in sealed` test with no word said, and its
  body never reaches the record. A second silent drop, a different case,
  and not this assertion's. Left as it stands and recorded as a finding.
- **Changing what makes a title parseable.** `PlanCard.slug` is the one
  parser and this change does not touch it. Widening the grammar, or
  sanitising a title into a slug, would be the loop guessing which unit the
  operator meant — the thing the pause exists to refuse.
- **Repairing the card.** The loop writes no tracker item and edits no
  title. It reports and waits; retitling the card is the operator's.
- **Any change to the charter, `merge_criteria()`, the landing, or the
  other guards.**

## Decisions

**The unnameable unit is a pause, not a log line.** The alternative — log
it and carry on — is what the empty-body case does, and it leaves the fact
in the raw loop log rather than the run record.
`books/flywheel/src/observation.md` puts the operator's answer in the
record ("Facts originate in the record and nowhere else"), and
`books/flywheel/src/construction-loop.md` names the loop's response to
judgment running out: "The loop pauses — never guesses ... A paused bolt
states its reason in the run record and waits." A returned reason string is
already that mechanism: `guards()` hands it to `cycle()` as
`result.halted`, `run()` notes it to the ledger, and the report prints it.
No new plumbing.

**The writes of the pass happen first, and the pause follows them.** The
guard's contract is "writes only what is missing", and a milestone with one
misnamed card among several good ones should still get the good ones'
durable prose. This also keeps the guard idempotent under repair: on the
pass after the operator retitles the card, only the newly nameable unit is
written, because the rest are already at HEAD.

**A commit failure outranks the unnameable unit as the returned reason.**
Only one string comes back. The commit failure names a record that is torn
right now and asks for a retry; the unnameable unit is a card waiting on a
hand. Both conditions are sticky — neither clears itself — so ordering them
loses nothing: the pass after the commit succeeds reports the unnameable
unit. The alternative, concatenating both into one string, makes the reason
harder to read for a case that is already rare.

**The reason is given on the dry-run and fixture paths too.** Both are
"report what would happen without writing", and a dry run whose output said
"nothing to write" over a dropped unit would reproduce the silence this
change closes — `observation.md`'s held loop is read before the pass runs,
so a dry run that hid the pause would let the operator approve a pass that
cannot proceed. Returning the reason there halts the cycle, which is
correct: the real pass would halt at the same point, and describing the
stages below it would describe a pass that will not happen.

**The reason names the title verbatim and states the grammar in prose.**
Verbatim, because the defect is usually invisible in a paraphrase — a
capital letter, an underscore, a trailing space. In prose, because a second
regex here would be a second definition of what a unit title is, and the
parse stays `PlanCard.slug`'s alone. The reason describes; it does not
re-decide.

**Every unnameable unit on the milestone is named in one reason.** The scan
already walks all of them, and reporting the first would make the operator
pay one pass per bad card.

## Risks / Trade-offs

- **A misnamed card now stops a bolt that used to run.** A bolt whose units
  were silently dropped kept driving its items. → That is the change: the
  drop was a guess, and the pause is the loop's stated response. The cost
  is bounded and self-clearing — retitling the card clears it on the next
  pass — and the reason names the card and the fix.
- **An old milestone carrying a card that never parsed now halts.** A bolt
  in flight can stop on a card nobody has looked at in weeks. → The reason
  names it, and the record it would otherwise land with is missing that
  unit's document either way. Finding it at 0.6 is strictly earlier than
  finding it after the landing.
- **The pause reason grows with the number of bad cards.** → In practice
  one, and the run report already carries multi-line reasons from the merge
  and verify stages.

## Migration Plan

None. The change alters what one guard does on a card it used to pass over.
No record is rewritten, no item is touched, and a milestone whose unit
titles all parse behaves exactly as before.
