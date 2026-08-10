---
name: research
description: Work the investigation a flywheel research-type design session runs — read code, docs, and a tool's actual behavior to answer a factual question, and deliver the answer in the session report. Use whenever a design session's work order names the research type or files its batch as `research:`; also use when an investigating session finds a problem it could fix and needs to know whether to fix it.
---

# Flywheel research — the investigation that reads rather than builds

You are a design session charged with the **research type**, running under
`flywheel-design-session`. Your batch has a factual question, and the
answer is already on disk or in a running system: in code, in docs, in an
API's actual behavior, in what a command actually prints.

The loop practice and the criteria for choosing this type over its
neighbours are in `flywheel:inception`, which your profile already sent you
to. This skill is what the type is and how it ends.

## You read; you do not build

That is the whole boundary between this type and the prototype type. A
prototype builds a throwaway to *make* a fact exist so it can be measured.
Research goes and *finds* a fact that already exists.

So there is no spike-repo worktree, no throwaway, and no code that outlives
the session. Reading includes running things to observe them — a command,
a script that only prints, a request against an API you are characterizing.
When you catch yourself writing something that would have to be maintained
or merged to be useful, you have crossed into a prototype or into
construction, and either is a report to your conductor rather than a thing
you keep doing.

## The finding is delivered in your report

No `prototypes/<slug>.md` note is written, because nothing was built and
there is no spike-repo location to record. Your finding goes in the session
report in your own `sessions/<date>-<slug>/` directory, and it names:

- the question you were sent to answer;
- the answer, plainly, including "no" and "it depends, on this";
- the evidence — the file and line, the command and its output, the
  observed behavior — so the next reader can check it rather than trust it;
- the decision(s) the answer feeds.

An answer of "not what we assumed" is the finding, not a failed
investigation.

## Finding a fixable problem produces a handoff, not an edit

Investigations turn up broken things. That is most of what they are for.
When the bug you were looking for turns out to be two lines from fixed, the
two lines are still construction: they leave on the operator's approval as a
handoff, and a small one is a one-proposal bolt, never an untracked edit.
This holds in every repo, blueprints included — a skill, an agent profile,
a schema instruction, a `CLAUDE.md` are machinery whoever is running where.

The reason is not ceremony. A fix made from inside an investigation is
untested, unreviewed, and invisible to whoever owns the file, and the
session that made it reports a finding that is no longer true of the repo.
Write down exactly what the fix would be — that is worth a lot to the bolt
that lands it — and report it.

## Your type opens no round

You have a written report and could put it in front of the operator. Your
type opens none: the report is delivered to your conductor, which decides
what follows. If the operator should annotate what you found, the conductor
charges a review-type session for it.

## The type comes from your work order

Your work order names the type and you load this skill because of it. You do
not pick your own type. If your work order names none, ask your conductor. If
mid-batch the question turns out to need something built to answer it,
report that as the next batch's type — a prototype — rather than starting
to build inside your own run.

## What you report

The answer and its evidence, the decisions it feeds, which tasks your
conductor should check or append, any handoff the investigation turned up,
and what the next batch should work. You append nothing to `tasks.md` and
check nothing off.

## Scope

This skill widens nothing. You write your own session directory and the
book and map targets your tasks name, and nothing else. That rule is stated
in your profile and in `flywheel:inception`; read it there.
