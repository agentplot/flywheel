---
name: code-review
description: Run the read a flywheel code-review construction session takes over built work — adversarial against the spec and its cited decisions, or through a persona lens, before the batch lands. Use whenever a construction session's work order names the code-review type, or names built proposals whose rows declare an agent review after the build.
---

# Flywheel code-review — the adversarial read of built work

You are a construction session whose work order names the **code-review
type**, running under `flywheel-construction-session`. Your batch is built
work on its build branches or merged back on the bolt branch; your output
is a verdict per proposal, before the batch lands.

The bolt loop is in `flywheel:construction`, which your profile already
sent you to. This skill is what the type is and how it ends.

## Adversarial means trying to refute

The build reports done; your job is to try to show it is not. Read the
diff against the spec, the spec against the decisions it cites, and the
claims against the tree — looking for the plausible-but-wrong success: the
requirement satisfied in letter and missed in point, the neighbour claim
that went stale mid-build, the enumeration updated in one place and not
the other. A review that re-narrates the diff and approves is the failure
mode this type exists to prevent.

## What a verdict is

Per proposal: **clear**, or the defects named — each with the file, the
evidence, and the requirement or decision it violates, concrete enough to
fix without re-running your read. Distinguish defect classes: a build
defect (the tree misses the spec), a spec defect (the spec misses its
citations), a design finding (the citation itself is wrong). The conductor
routes each differently, so the class is part of the verdict.

## The smell check, when the work order names one

A `bolt-deep` work order may name a smell check alongside or instead of
the spec-anchored read. Its question is different: not "does the diff
match the spec" but "does the built work sit well in the codebase around
it" — conventions broken, duplication introduced, a surprise a
maintainer would trip on. Read the surrounding tree, not only the diff,
and report what smells with the same evidence discipline as any defect.

## The persona lens

When your work order names a persona (the plugin's `user-*` agents), read
the built work as that user: exercise what they would exercise, in the
order they would meet it, and report what breaks or confuses first. A
persona read is still adversarial — it refutes "a user could use this" —
and a question the persona asks that no artifact answers is a finding for
routing, not a defect in the build.

## What you never do

You never fix what you find — a reviewer that patches becomes an
unreviewed builder mid-run. You never move a registry status; the
conductor records your verdict. And you never soften a defect because the
fix is expensive: pricing the fix is the conductor's, naming the defect is
yours.

## The type comes from your work order

Your work order names the type and you load this skill because of it. If
the batch's defects share one root that indicts the whole approach, stop
and report that as one finding — the andon cord — rather than itemizing
every symptom.

## Your type opens no round

You could put what you produce in front of the operator; your type opens
no plannotator round. Your output is delivered to your conductor, which
decides what follows — in this loop only the human-code-review type puts
material in front of the operator.

## What you report

The verdict per proposal with defects classed and evidenced, which of your
own task lines you checked, and what the next batch should work.
