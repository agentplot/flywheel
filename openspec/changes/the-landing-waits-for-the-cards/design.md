## Context

See `proposal.md` — Why. The state the build works against, read from
disk on `build/the-landing-waits-for-the-cards` at writing:

- `Bolt.run`'s tail in `bin/_flywheel_bolt_loop.py` computes
  `planned` from the snapshot's plan cards whose `bolt` is this
  milestone, and when that set is non-empty *and* the landing was
  otherwise wanted, logs "landing held — unit card(s) still open",
  writes the same note to the ledger, finishes the observation and
  returns the report untouched.
- `RunReport.landing` defaults to `"not attempted"`;
  `bin/flywheel-bolt-loop` prints `landing: {report.landing}` and puts
  the same string under `"landing"` in its JSON.
- `Tracker.snapshot` in `bin/_flywheel_inbox.py` builds `plan_cards`
  from open issues carrying the `plan` label, over **all** the raws it
  read rather than the milestone-filtered ones, so cards from other
  milestones are in the set and the `c.bolt == milestone` filter is what
  makes it this bolt's. `PlanCard.bolt` answers the card's own `bolt/*`
  milestone or `None`.
- `close_unit_parents` closes every `unit` batch on this milestone plus
  any landed assertion's `parent_batch`, skipping elaborations and
  already-closed issues, with `closed:done` and the landing SHA. Its
  behaviour already covers several units; its docstring says "Close the
  release's unit parent at the landing".

## Goals / Non-Goals

Goals: put the two live writes into the record, and make a held landing
legible in the one line that reports landings.

Non-Goals:

- Changing what the landing does once it runs.
- The operator's milestone close as the landing's release gesture. All
  three cited chapters name it; the assertion this change derives from
  does not, and nothing in the tree gates on the milestone's state
  today. This change neither adds it nor removes anything standing in
  for it.
- Any change to expansion, to the defer predicate, or to the server's
  job filter — the three sibling tasks of this unit, each merged.

## Decisions

**The hold reads the `plan` label, not the board.** "No unit card still
open" is satisfiable only if an expanded unit stops counting as a card,
since a unit stays open until the landing closes it. The label is the
line the tree already draws — expansion swaps `plan` for `unit`, and
`plan_cards` is open `plan`-labelled issues — so the hold needs no new
state and no new field. The alternative, reading board Status, would
have counted a card the loop had already consumed the Ready status of.

**The hold sits ahead of the expectation gate, not inside
`landing_wanted`.** Two reasons. `landing_wanted` answers "is there a
landing to reach for", and its answer is what distinguishes the held run
from the quiet one in the report — folding the card test into it would
collapse both into `False` and leave the report unable to say which.
And the gate writes a pending approval keyed to the landing plan; a bolt
that cannot land should not be asking the operator to approve a landing.

**A dry run reports the hold like any other run.** Because the hold is
asked before the landing question at all, and `holding_cards` reads
nothing but the snapshot's cards, `--dry-run` says "held, card #231" on a
bolt whose card is open — which is the answer an operator asking what
this pass would do is after. It stays within what a dry run may do: the
tracker is wrapped in `ReadOnlyTracker` under `--dry-run`, so any tracker
write would raise, and the held path makes none. Its only writes are the
local ledger note and the observation report, which a dry run writes on
every pass already.

**The hold outranks `land="force"`.** `force` exists for the operator or
the server resuming a run that died between the last merge and the
landing — a question about *this process's* knowledge, not about the
operator's ruling. An open card is the operator's own unfinished
gesture, and the way past it is to rule the card. A forced run therefore
reports the hold rather than landing over it.

**The report line, not a new field.** `RunReport` already has exactly one
landing line, and both readers of a run — the printed report and the
JSON — read it. A held landing writes that line; nothing new is added to
the report shape, and the ledger note stays as it is.

## Risks / Trade-offs

- **A forgotten card wedges the bolt.** A stale Backlog card nobody ever
  rules holds the landing indefinitely → the run says so on every pass,
  by number, and `flywheel status` already reports an unapproved card
  under what waits on the operator.

## Open Questions

None.
