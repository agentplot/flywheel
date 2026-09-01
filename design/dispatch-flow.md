# The dispatch-round trigger flow

Every channel and event that produces a dispatch plan, and what happens
after the operator's word. This is the current-state map — when a round
doesn't appear or work doesn't move, diagnose against this picture
first. Companion: `skills/_reference/dispatch-plan.md` (the protocol),
`bin/_flywheel_inbox.py` (the derivations), `bin/_flywheel_server.py`
(the pass).

```mermaid
flowchart TB
    subgraph SRC["Content producers"]
        SESS["Design session settles<br/>posts dispatch-plan payload item<br/><i>label: dispatch:standing</i>"]
        IDEA["Operator idea<br/>(Discord dictation → card,<br/>or raw item, no milestone)"]
        COMPOSE["Intent-loop compose guard<br/>sweeps orphan queued items →<br/><b>elaboration parent at Backlog</b><br/><i>_flywheel_intent.py apply_compose</i>"]
        PLANNER["Bolt planner session →<br/><b>plan cards at Backlog</b>"]
        SANDON["Session raises andon<br/>in its item comment"]
    end

    subgraph TRK["Tracker = the only bus (GitHub issues + Project board)"]
        STANDING["dispatch:standing items"]
        TRIAGE_ITEMS["unmilestoned intake items"]
        NEEDSOP["needs-operator items"]
        BACKLOG["batches + plan cards<br/>at board Status <b>Backlog</b>"]
        READY["batches at board Status <b>Ready</b>"]
    end

    subgraph SRV["flywheel server — one pass / 60s"]
        SNAP["snapshot()"]
        DINBOX["dispatch_inbox<br/>relay: needs-operator<br/>triage: unmilestoned OR standing<br/>round: Backlog batches + cards"]
        RELAY["relay() — one delivery per<br/>queue STATE (dedupe by set)"]
        SINBOX["server_inbox → Job per milestone"]
        HOLD{{"backoff hold<br/>(released when the milestone's<br/>tracker state changes)"}}
        LOOPS["intent / bolt loop processes"]
    end

    subgraph DSP["Dispatch standing agent (herdr pane)"]
        POKE["MCP proxy → herdr prompt<br/>'run the round'"]
        ROUND["flywheel-round → round_inbox<br/>standing payloads + close rows<br/>+ backlog batches + cards"]
        PLAN["plan.html + Discord<br/>containers: intent · bolt · close ·<br/>finished · <b>approvals</b> (grouped by<br/>milestone, set-all per group)"]
        APPLY["apply the word:<br/>file containers · stage:done ·<br/>Ready flips · drop → closed:declined ·<br/>milestone closes · consume payloads"]
    end

    OP(("Operator"))

    SESS --> STANDING
    IDEA --> TRIAGE_ITEMS
    COMPOSE --> BACKLOG
    PLANNER --> BACKLOG
    SANDON --> NEEDSOP
    SNAP --> DINBOX
    STANDING --> DINBOX
    TRIAGE_ITEMS --> DINBOX
    NEEDSOP --> DINBOX
    BACKLOG --> DINBOX
    DINBOX --> RELAY --> POKE --> ROUND
    OP -- "says 'dispatch'" --> ROUND
    BACKLOG --> ROUND
    ROUND --> PLAN --> OP
    OP -- "approve / annotate" --> APPLY
    APPLY -- "ready rows" --> READY
    OP -- "hand-flip on board<br/>(the fallback)" --> READY
    READY --> SINBOX --> HOLD --> LOOPS
    LOOPS -- "launch sessions" --> SESS
```

## The three trigger channels, in words

1. **The server's poke** — every 60s pass derives `dispatch_inbox` from
   the snapshot: `relay` (needs-operator items — escalations, andons),
   `triage` (unmilestoned intake + `dispatch:standing` payload
   anchors), and `round` (batches and plan cards parked at board
   Backlog on open milestones). Each non-empty queue whose membership
   changed since the last delivery is prompted into the dispatch pane
   as one imperative. An unchanged queue is delivered once, not every
   pass.
2. **The operator's word** — "dispatch" in Discord or the pane runs a
   round on the spot; no poke needed.
3. **Nothing else.** Loops never talk to dispatch; sessions never talk
   to dispatch; everything routes through tracker state the pass can
   derive.

## What the round is over

`round_inbox` is a pure function of the snapshot: standing payloads
(the label nominates the anchor, the marker comment carries the
address), close-ready bolt milestones (every work item merge-closed,
nothing ready, no open card), and the Backlog batches/cards. Derived
Backlog rows render in the **approvals** container — grouped by
milestone, one set-all per group, routes `leave | ready | drop`,
seeded `leave` — so approving the one new elaboration never requires
touching twenty parked bolt cards, and `drop` retires a card for good
(`closed:declined`) instead of resurfacing it every round.

## After the word

Ready is the only release: the server's next pass turns Ready work
into loop jobs, holds are keyed to milestone tracker state (an
operator repair — a label cleared, a status flipped — releases the
hold on the next pass), and the loops launch the sessions whose
settles feed the next round.
