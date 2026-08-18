# Session 2026-08-17 — the cut

Research session on `intent/messy-repo-onboarding`, item #270: run the
three-way cut and a first end-to-end conversion over a real corpus —
the measurement that tests clauses 2 and 3 of the promise
(`../../decisions/onboarding-promise.md`, #264) before the carrier
skill hardens.

## Charge

- Change: `messy-repo-onboarding`
- Type: research (reads; builds nothing — but this item's deliverable
  is a durable committed report, so the session wrote files; see
  `findings.md` F11)
- Directory: `sessions/2026-08-17-cut/`
- Items: #270
- Corpus: `WilldanGroup/knowledgebase-spike` @ `ba4b385a`
- Destination books: `WilldanGroup/willdan-blueprints` @ `2a7c8327`

## Contents

- `method.md` — inputs, scope, granularity, lane definitions, the
  evidence rule. Read this to dispute a row on method.
- `cut.md` — **the cut**: every file and section of the corpus
  assigned to discard / settled-history / live-work, with a one-line
  reason and a checkable pointer each, plus the rows the session could
  not settle and turned into questions.
- `findings.md` — what the measurement taught that the survey could
  not: thirteen findings, each bearing on a named clause or successor
  item.
- `conversion/` — one settled artifact taken end to end: session
  record, decision record, books-verdict, processed-ledger entry.
  Staged, not landed — see the note there.

## Outcome

Reported on #270. Nothing was written to
`~/Code/clients/github_willdan/` — cross-org landing (#267) is open,
so a foreign-org corpus stops at the report tier by the promise's own
boundary.

## The short version

The promise survives the measurement; the cut's **shape** does not.
Three lanes are not enough columns. `settled-history` splits by
whether the destination books already carry it (F3), again by whether
what was settled is still true (F8), and again by whether anything
else holds a copy at all (F12). `discard` splits by whether the
material may be quoted forward (F11). And the corpus already contains
a run design for the carrier we are about to write, with its own
ledger naming the exact unconverted delta (F9, F10).

**The finding that cost the most to reach** is F12, because this
session got it wrong first. Four artifacts across three directories —
4,888 lines, 42% of the corpus — were laned on inferences that sounded
careful: a summary exists, so the body is detail; the siblings are
renderings, so this is too. Every one was false, none would have been
caught by more care in the inference, and one `grep` caught all four.
The lane that loses material is never `discard` — it is the
disposition that sounds safe.
