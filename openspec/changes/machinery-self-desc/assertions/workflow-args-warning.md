# Assertion: The apply instruction warns that `args` must be a JSON value

- **Repo:** agentplot/flywheel
- **Item:** #29
- **Raised by:** `intent-work-object-vocabulary`, running its own apply
  loop twice — runs `wf_34827627-076` and `wf_78dbb11d-b87`.

## The claim

Both loop skills and all four schemas now command the conductor to
encode the apply instruction as a dynamic workflow's script. The
workflow tool's `args` input must be an actual JSON value; a
JSON-**encoded string** is accepted silently, and every `${args.foo}`
interpolation in the script's prompts then renders the literal text
`undefined`.

When this is built, that sentence appears wherever the
loop-is-the-workflow binding is stated — `skills/inception/SKILL.md`,
`skills/construction/SKILL.md`, and the `apply` instruction of each of
the four schemas — and the QUERY stage is told to assert its inputs are
defined before it does anything, so a run that lost its args halts at
stage one instead of proceeding.

## Why

In `wf_78dbb11d-b87` every stage agent received a prompt naming org
`undefined`, tracker `undefined`, milestone `undefined`. The run
survived only because the stage agents independently re-derived the org,
tracker and milestone from `fleet.yaml`, the checkout and the pane's own
herdr agent name, and said so in their notes. Neither the tool nor the
script errors, so a less resourceful conductor would have written to the
wrong repo or halted with nothing to point at.

## Boundaries

The workflow tool's own acceptance of a stringified `args` is not in
scope — this makes the flywheel side warn about it and fail early. The
apply instruction's stage structure is unchanged; the assertion adds a
precondition to QUERY, not a stage. The four schemas' artifact sets and
their instruction text otherwise stay as they are; the `proposals`
registry drift is #26.
