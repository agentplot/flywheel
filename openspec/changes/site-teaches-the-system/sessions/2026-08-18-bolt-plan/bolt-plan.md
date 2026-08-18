# Bolt plan — site-teaches-the-system handoff, 2026-08-18

Drafted by the handoff session on item #302, from the closed decision
`../../decisions/page-teaching-order.md` and the operator's round recorded
in `../2026-08-18-beats-and-tour/README.md` (items #284/#285). One bolt: all
five pages are one restructure in one repo, sharing one shell.

## bolt/site-five-beats

- **type**: `bolt-adversarial` — the work has users who are not the author,
  and that is the whole point of it: five pages whose job is teaching a
  stranger who has installed nothing. The type's persona read before the
  build and personas exercising the result put that stranger in the loop,
  which is the only check that can catch the defect this intent exists to
  fix. The repo's merge gate (`scripts/check-site.mjs`) proves mermaid parses
  and every relative reference resolves — it says nothing about whether the
  page teaches — so `bolt-direct`'s "the gate settles correctness" does not
  hold here, and `bolt-default`'s adversarial code-review reads the code
  rather than the page.
- **landing**: merge — straight to main once the bolt's stages are green.
  `.github/workflows/pages.yml` publishes on any push to main touching
  `site/**`, so landing IS publishing; the human review inside
  `bolt-adversarial` comes before that, which is why this is a merge and not
  a PR.
- **owner**: @afterthought — the items carry no assignee, so the owner is
  the operator, whose word settled the decision and the round behind every
  assertion here.
- **repos**: agentplot/flywheel (`site/`)
- **assertions**:
  - #305 — `assertions/home-page-five-beats.md` — `site/index.html` teaches
    the five beats in order and opens on the variant-A split hero, with the
    operator reference gone from it.
  - #306 — `assertions/overview-page.md` — `site/overview.html` carries the
    actors, write scopes, bolt state machine and plugin-dev material,
    rendered, linked from every page's topbar.
  - #307 — `assertions/concept-tour-pages.md` — three scrollytelling tour
    pages walk the same seven steps for three different ideas, linked from
    beat 3.
- **sequencing** — to wire at the custody move, as native blocked-by
  relations on the three items:
  - **#305, #306 and #307 all blocked by #301** — the stranger-facing word
    for the coupling ("approval" vs "gate", and the ban on "release"). Its
    answer changes copy on all five pages; building before it closes means
    rewriting copy in the same bolt that wrote it. **Nothing here may be
    released while #301 is open.**
  - **#306 and #307 blocked by #305** — `index.html` establishes the shell
    every other page inherits (topbar with the Overview link, tokens,
    vendored fonts, plate geometry) and names where each moved section went.
    Overview and the tours then run in parallel behind it, on disjoint files.
- **ADRs**: none. The repo carries no log4brains layout, and nothing here
  is an architecture decision — the design decisions are already recorded as
  this change's decision record and round outcomes.

## Where custody stands

The three assertions are **queued on `intent/site-teaches-the-system`,
unparented and unblocked**, which is the state the intent loop's handoff
guard reads: it births the unit at Backlog holding them and a handoff item
to execute this plan. That handoff session is the one that wires the
sequencing above and makes the custody move
(`--milestone bolt/site-five-beats`, `state:ready`).

They are left unblocked deliberately, and the consequence needs saying: **the
#301 dependency lives in this plan and in the items' comments, not yet in
the tracker's dependency field.** Do not flip the unit to Ready before #301
has closed, and wire the blockers before releasing.

## Open — the annotation round returned dismissed

`plannotator annotate --gate` was opened on this plan and came back
`{"decision":"dismissed"}`: no annotations, no approval. These three
questions are therefore still the operator's, and ride on #302 with
`needs-operator`:

1. **Type** — `bolt-adversarial` as argued, or `bolt-default` (proposal
   review + adversarial code-review + batched acceptance, no persona work)?
   Adversarial costs more agent time on a five-page site; it is the only
   type that reads the pages as a stranger.
2. **Landing** — merge, given that landing publishes to Pages immediately?
   Or a PR, so the whole restructure is seen as one diff and the publish
   waits on a human merge?
3. **The split** — three assertions as above, or does `overview.html` ride
   inside the home-page assertion (it is that page's content, moved),
   leaving two?

Answering 1 or 2 amends this plan and nothing else; answering 3 amends the
item set, and #306 would close `closed:superseded` with its record folded
into `home-page-five-beats.md`.
