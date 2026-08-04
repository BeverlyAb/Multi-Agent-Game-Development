# Agent Diagram — Untitled Goose Game Village Mischief Crew

Three stages, run in order every time the crew executes: a **Routine
Pass** (one villager-behavior agent), a **Prep Pass** (dispatched by the
Area Orchestrator, once per villager/prop), and a **Mischief Tick**
(checklist → verb plan → staged gag, run every time the goose starts a
new objective). Every arrow below is a real field being read/written in
[`agents.py`](agents.py) / [`crew.py`](crew.py) — none are decorative.

```mermaid
flowchart TB
    subgraph ROUTINE["Routine Pass"]
        VRA["Villager Routine Agent<br/>in: name/role + routine dials<br/>out: villager.traits + routine_summary"]
    end

    subgraph PREP["Prep Pass — dispatched by Area Orchestrator"]
        AO["Area Orchestrator"]
        ALA["Area Layout Agent<br/>in: props<br/>out: prop.location"]
        PDA["Prop Designer Agent<br/>in: prop.affordance (raw)<br/>out: prop.affordance (designed) + prop.designed"]
        VDA["Villager Designer Agent<br/>in: villager.traits<br/>out: villager.appearance"]

        AO -->|"'layout' request"| ALA
        AO -->|"'prop' request"| PDA
        AO -->|"'villager' request"| VDA
    end

    subgraph TICK["Mischief Tick"]
        CCA["Checklist Creator Agent ('One Wow')<br/>requires: villager.traits + prop.location + prop.designed"]
        GVP["Goose Verb Planner Agent ('One Wow' / Goose Solution Planner)<br/>requires: villager.appearance + prop.location + prop.designed"]
        RDA2["Reaction Director Agent<br/>requires: VerbPlan + prop.location"]
        GAME[("Phaser web client —<br/>player-controlled goose")]
    end

    VRA -->|"villager.traits"| VDA
    VRA -->|"villager.traits"| CCA
    ALA -->|"prop.location"| PDA
    ALA -->|"prop.location"| CCA
    ALA -->|"prop.location"| GVP
    PDA -->|"prop.designed"| CCA
    PDA -->|"prop.designed"| GVP
    VDA -->|"villager.appearance"| GVP

    CCA -->|"ChecklistItem[] (objective_kind, target_villager, involves_prop)"| GVP
    GVP -->|"VerbPlan + CompletionCondition"| RDA2
    GVP -.->|"no reachable solution -> item.retire_reason, item skipped"| CCA
    RDA2 -->|"StagedGag[] (goose action + villager reaction)"| GAME
    GAME -.->|"complete_item() feedback hook, not yet wired to a live server"| GVP

    classDef routine fill:#2b2f38,stroke:#5a6270,color:#e8e6e1;
    classDef prep fill:#242832,stroke:#5a6270,color:#e8e6e1;
    classDef tick fill:#1f232b,stroke:#8a8f98,color:#e8e6e1;
    classDef data fill:#16181d,stroke:#8a8f98,color:#e8e6e1,stroke-dasharray: 3 3;
    class VRA routine;
    class AO,ALA,PDA,VDA prep;
    class CCA,GVP,RDA2 tick;
    class GAME data;
```

## Why every agent is load-bearing

Each arrow is enforced in code, not just implied — remove the upstream
agent and the downstream one raises a `ValueError` instead of silently
producing worse output:

- **Villager Routine Agent** writes `villager.traits`. Both **Villager
  Designer Agent** and **Checklist Creator Agent** check for it and
  refuse to run without it.
- **Area Layout Agent** writes `prop.location`. **Checklist Creator**,
  **Goose Verb Planner**, and **Reaction Director** all check for it
  directly and refuse to run (or have nothing to stage) without it.
- **Prop Designer Agent** sets `prop.designed = True`. **Checklist
  Creator** and **Goose Verb Planner** both check it, so a skipped Prop
  Designer can't let the raw seed affordance text slip through as if it
  were finished content.
- **Villager Designer Agent** writes `villager.appearance`. **Goose Verb
  Planner** checks for it and refuses to run without it (it's quoted
  directly into the plan's stage direction).
- **Checklist Creator Agent** is one of this crew's two "One Wow" agents:
  no checklist, no verb plan, no staged gag — the mischief tick returns
  empty immediately.
- **Goose Verb Planner Agent** is the other "One Wow" agent, and doubles
  as the crew's Goose Solution Planner: it re-validates that the
  checklist item's villager/prop still exist and that the resolved
  prop's kind still matches the objective before staging anything, and
  **Reaction Director Agent** raises if it's ever handed a plan with no
  lines.
- **Area Orchestrator** is the single entry point the designer calls for
  new prep-time content — remove it and there's no dispatcher routing
  layout/prop/villager requests to the right sub-agent.

You can reproduce this: comment out the routine pass or the prep pass in
`main.py` and re-run — the crew stops with a clear `ValueError` naming
exactly which upstream agent was skipped, rather than continuing with
silently degraded output.

## Reading the diagram

- **Solid arrows** are direct hand-offs where one agent's output is a
  required input to the next.
- **Dotted arrows** are the two feedback paths: an unreachable checklist
  item retiring back onto the same checklist instead of reaching the
  player, and `UntitledGooseGameCrew.complete_item()` — a hook meant for
  a live game loop to call once a goal condition is actually confirmed
  satisfied, so the next mischief tick advances past a finished item.
  The current `web/` client only renders one static `output/run.json`
  snapshot, so that second feedback path is a designed hook, not yet a
  live one.
- **Phaser web client** is the player-visible terminus, not an agent —
  it reads the crew's JSON output (`output/run.json`) and renders the
  village, props, and the active checklist item's goose-verb plan.
