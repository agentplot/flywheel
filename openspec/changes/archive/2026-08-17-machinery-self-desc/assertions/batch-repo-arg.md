# Assertion: flywheel-batch says which `--repo` shape it wants

- **Repo:** agentplot/flywheel
- **Item:** #40
- **Raised by:** `intent-work-object-vocabulary`, composing unit #38.

## The claim

`flywheel-batch` prepends `--org` to `--repo` itself, so `--repo` wants
the bare repository name. When this is built, passing the qualified form
does not produce a 404 naming a nonsense path: the tool either accepts
both shapes — stripping a leading `<org>/` that matches `--org` — or
refuses before any API call with a message that names the shape it wants
and the value it got.

The same correction lands on the reference that taught the wrong form.
`skills/_reference/herdr.md` writes every `gh` invocation as
`--repo <org>/<tracker>` and then, on the same page, gives the
`flywheel-batch` line, which wants the other shape. When this is built
the `flywheel-batch` example shows the bare name and says on the line
that it differs from the `gh` invocations above it.

The abort-before-creating behaviour is not a defect and is preserved:
the failing run created nothing, verified by listing the milestone
afterwards.

## Why

The defect is one reader moving down one page and carrying the argument
shape across, which is exactly what happened to
`intent-work-object-vocabulary`. The observed failure is in the item
body: `gh api /repos/agentplot/agentplot/flywheel/issues/37 failed: gh:
Not Found (HTTP 404)`.

## Boundaries

The other `bin/` commands that take `--org` and `--repo` —
`flywheel-board`, `flywheel-setup`, `flywheel-migrate`, `flywheel-token`
— are covered only to the extent that they share the argument handling
being fixed; auditing each one's flag surface is not claimed here. The
tool's argument refusal for a conductor name that is too long is #44.
