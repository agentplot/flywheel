## Context

See proposal.md — Why. What the tree bore out when this was written, so a
build can re-check it rather than trust it:

- `guard_scaffold` in `bin/_flywheel_bolt_loop.py` opens
  `if self.params.change_dir.exists(): return None`, with a docstring
  stating "Idempotent: the directory existing is the whole test". Below
  that come the `--dry-run` branch, the order built on
  `f"/opsx:new {self.params.slug}"`, the drive, the
  `change_dir.exists()` post-check, and the `merge_criteria()` post-check
  with the reason naming `openspec/changes/<slug>/bolt.md` and the
  four sections.
- `CHARTER_SECTIONS` on the same class holds the four headings, and the
  order's charter text is built inline in `guard_scaffold` from it and
  from `self.params.description`.
- `guards()` runs scaffold at 0 — before `guard_topology` at 0.5 and
  `guard_charter` at 0.6 — and any guard's returned string halts the
  cycle in `cycle()` as `result.halted`.
- `merge_criteria()` returns `""` for a missing `bolt.md`, a missing
  section and an empty body alike; `land_stage` refuses on it with a
  comment saying so in as many words.
- `tests/test_bolt_loop.py` holds `ScaffoldCharterTest` with the
  `SettlingScaffold` runner (a scaffold session that writes `CHARTER`, or
  `charter=None` for one that writes none) and
  `test_a_present_change_directory_returns_before_the_check`, which makes
  a bare directory and asserts the guard passes and launches nothing.
- The `/opsx:new` command file shipped with this plugin
  (`.claude/commands/opsx/new.md`) carries the guardrail "If a change with
  that name already exists, suggest using `/opsx:continue` instead";
  `.claude/commands/opsx/continue.md` picks the FIRST artifact whose
  status is `ready` and creates exactly that one.
- In all four `schemas/bolt-*/schema.yaml`, `bolt` is the first declared
  artifact with `requires: []`, so on a bolt-bound change carrying no
  `bolt.md` the first ready artifact is `bolt`.

Re-read each of these before building on it — they are what the tree bore
out at spec time, not a promise about the tree the build finds.

## Goals / Non-Goals

**Goals:**

- One guard owns the question "does this bolt have a charter", and answers
  it from the charter file.
- The two paths — no directory, directory without a charter — ask for the
  same charter and are checked by the same reader.

**Non-Goals:**

- Repairing a charter that exists. That is the landing's refusal, and a
  guard that rewrote it would be a second writer over committed prose.
- Reading, moving or rewriting an older-shape `bolt.md` carrying a
  `# Unit:` section. `charter_region()` already bounds the reader; this
  change adds nothing there.
- Any change to `guard_charter`, `merge_criteria()`, `landing_mode()` or
  `land_stage`.

## Decisions

**The early return tests `bolt.md`, and the two cases are one guard.**
The alternative — a separate 0.4 guard for the charterless case — would
put two writers on `bolt.md` and two copies of the post-settle check, and
the failure this change exists to close is precisely two answers to one
question. One guard with two invocations keeps one check, one reason
string, and one place where the charter's content is stated.

**The order's charter text is shared, and only the framing differs.**
The four sections, the `Landing:` line, the description-or-not paragraph
and the "no unit's plan document" paragraph are one text used by both
paths; what differs is the invocation and the sentence that says whether
the change is being created or completed. Building the shared text once
is what makes the spec's "the same on both paths" checkable by reading
the program rather than by diffing two strings.

**`/opsx:continue` is the invocation for an existing change.** It creates
the first `ready` artifact, which on a bolt-bound change missing `bolt.md`
is `bolt`. `/opsx:ff` would drive every artifact including the `unit`
files the loop writes itself, and `/opsx:new` cannot be obeyed on a change
that exists. Because the artifact the schema hands the session is `bolt`,
the order still points at `openspec instructions bolt --change <slug>` for
the sections' content, exactly as the creating path does.

**The session name stays `scaffold-<slug>`.** The session id derives from
the name and cwd, so a charterless record found on a later pass resumes
the warm scaffold conversation instead of starting a cold second one —
which is the case this most often arises from: the same session that
settled without writing the charter is the one asked to finish it.

**The dry-run branch moves below the charter test** so it can report which
of the two it would do. It still launches nothing and writes nothing.

## Risks / Trade-offs

- **A session that cannot write the charter loops the guard.** Every pass
  finds no `bolt.md`, drives a session, fails the check and halts the
  cycle with the reason. → This is the loop's stated pause behaviour, not
  a regression: `construction-loop.md` has the loop stop and state its
  reason rather than guess, and the reason already names the change
  directory and what is missing. The cost is one session per pass, which
  the run report makes visible.
- **A change directory bound to the wrong schema, or to none, cannot
  produce a `bolt` artifact.** `/opsx:continue` would offer whatever the
  bound schema's first ready artifact is. → The order names the bolt type
  the change belongs to and asks the session to confirm the binding before
  writing, and the post-settle check catches anything else: a charter that
  is not there still reads as absent.
- **Two orders drift apart over time.** → The shared text is one
  expression in the program and the tests assert both orders carry the
  four sections and the description.

## Migration Plan

None. The change alters what one guard does on a record it used to pass
over; records that already carry a charter are untouched, and a record
that carries none gets one on the next pass.
