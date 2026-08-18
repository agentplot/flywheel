# Bolt plan — site-teaches-the-system handoff, 2026-08-18

Drafted by the handoff session on item #302, from the closed decision
`../../decisions/page-teaching-order.md` and the operator's round recorded
in `../2026-08-18-beats-and-tour/README.md` (items #284/#285). One bolt: all
five pages are one restructure in one repo, sharing one shell.

**This round is where the plan gets your eyes.** Annotate anything below;
the answers to the three open questions at the foot are what I need most.

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
  Worth knowing while you annotate: `.github/workflows/pages.yml` publishes
  on any push to main touching `site/**`, so landing IS publishing. The
  human review inside `bolt-adversarial` comes before that, which is why
  this is a merge and not a PR.
- **owner**: @afterthought — the items carry no assignee, so the owner is
  the operator, whose word settled the decision and the round behind every
  assertion here.
- **repos**: agentplot/flywheel (`site/`)
- **assertions**:
  - #TBD — `assertions/home-page-five-beats.md` — `site/index.html` teaches
    the five beats in order and opens on the variant-A split hero, with the
    operator reference gone from it.
  - #TBD — `assertions/overview-page.md` — `site/overview.html` carries the
    actors, write scopes, bolt state machine and plugin-dev material,
    rendered, linked from every page's topbar.
  - #TBD — `assertions/concept-tour-pages.md` — three scrollytelling tour
    pages walk the same seven steps for three different ideas, linked from
    beat 3.
- **sequencing**:
  - All three blocked by **#301** (the stranger-facing word for the
    coupling — "approval" vs "gate", and the ban on "release"). Its answer
    changes copy on all five pages; building before it closes means
    rewriting copy in the same bolt that wrote it.
  - The two page-adding assertions blocked by the home-page assertion:
    `index.html` establishes the shell every other page inherits — topbar
    with the Overview link, tokens, vendored fonts, plate geometry — and it
    is the page that names where each moved section went. Overview and the
    tours then run in parallel behind it, and they touch disjoint files.
- **ADRs**: none. The repo carries no log4brains layout, and nothing here
  is an architecture decision — the design decisions are already recorded
  as this change's decision record and round outcomes.

## Held back

- Nothing is dropped, but **nothing moves to `bolt/site-five-beats` in this
  session**. The custody move needs two things that do not exist yet:
  - **#301 has not closed.** It is in session right now, and every
    assertion above is blocked by it.
  - **There is no released unit.** This handoff item was born inside the
    elaboration #304 alongside #301, not inside a `unit` at Backlog holding
    the assertions — because this intent had no assertion items at all until
    this session wrote the three records above. The release approval is
    yours to give on a unit, and I do not write it for you.

  So this session ends with the three assertions **queued** on
  `intent/site-teaches-the-system`, blocked by #301, with no parent. When
  #301 closes, the intent loop's handoff guard sees three settled, unbolted
  assertions and births a unit at Backlog holding them; you flip it to
  Ready; the handoff session inside it executes this plan as written.

## Three questions for this round

1. **Type** — `bolt-adversarial` as argued, or `bolt-default` (proposal
   review + adversarial code-review + batched acceptance, no persona work)?
   Adversarial costs more agent time on a five-page site; it is the only
   type that reads the pages as a stranger.
2. **Landing** — merge, given that landing publishes to Pages immediately?
   Or a PR, so you see the whole restructure as one diff and hold the
   publish until you merge it yourself?
3. **The split** — three assertions as above, or is `overview.html` small
   enough to ride inside the home-page assertion (it is that page's content,
   moved), leaving two?
