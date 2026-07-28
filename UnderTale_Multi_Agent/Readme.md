# Undertale — Encounter Generation Crew

**This crew is a working prototype of my capstone game's own AI
Architecture.** My capstone is *Gachō Badi (Goose Buddy)* (GDD at
`../gdd-review-kit/gdd.txt`), and its GDD already specifies an 8-agent
AI Architecture: a Character Personality Agent, a Task Creator Agent, a
Writer Agent, a Director Agent, and a Scene Orchestrator that spins up a
Character Appearance Agent, Building Designer Agent, and Island Layout
Agent. This folder implements that exact architecture — same 8 roles,
same hard-dependency pipeline — but exercises it against *Undertale*
(Toby Fox's 2015 RPG) instead of Gachō Badi's own content, because
Undertale's systems (personality-driven monsters, bullet-hell combat,
route-based reactions) are public and well-documented enough to pressure-
test the architecture end-to-end before writing Gachō Badi-specific
prompts. Every agent here has a direct, named counterpart in Gachō
Badi's GDD — see the mapping below.

## How this maps onto Gachō Badi (Goose Buddy)

| This crew (Undertale) | Gachō Badi's GDD equivalent | Shared generative pattern |
|---|---|---|
| Monster Personality Agent | Character Personality Agent | **Personality creation**: both take four numeric dials (here: aggression/playfulness/sympathy/chattiness; in the GDD: movement/speech/energy/intelligence) and turn them into named personality traits — the same bucket-then-summarize architecture, just re-labeled per game |
| Bullet Pattern Designer Agent ("One Wow") | Task Creator Agent ("One Wow") | Batch-generates the central "thing to do" (an attack pattern / a task) from the roles and environment currently available — the GDD calls this and its Writer/Director counterpart the two agents load-bearing enough that a bad generation is visible to the player |
| Dialogue Writer Agent | Writer Agent | Given personality-tagged actors and a prompt (an attack / a task), writes screenplay-style dialogue and directional cues |
| Battle Director Agent ("One Wow") | Director Agent ("One Wow") | **Maneuverability**: takes the Writer's screenplay and turns it into the actual player-visible movement — here, "SOUL: dodge inside the bullet-hell box"; in Gachō Badi, the goose's directional movement (honk/duck/dash) reacting to the same screenplay. Both are the one agent that converts a script into physical, player-controlled motion |
| Encounter Orchestrator | Scene Orchestrator | Dispatches a designer/programmer's content request to the right sub-agent instead of generating content itself |
| ACT Menu Designer Agent | (feeds Task Creator's task design) | Personality determines the concrete interaction verbs available for a given actor — Undertale surfaces this as a literal ACT menu; the GDD achieves the same effect implicitly ("task availability is dependent on residents... their roles, personalities, relationships") |
| Room Designer Agent | Building Designer Agent | Enriches a raw environment hint into a full design spec centered on one interactive/environmental feature |
| Area Layout Agent | Island Layout Agent | Assigns each environment piece a location along a fixed set of named zones |

So "personality creation" and "maneuverability" — the two mechanics
named when this mapping was requested — aren't just similar in spirit:
`MonsterPersonalityAgent._bucket()` and `BattleDirectorAgent.run()` in
this repo are architecturally identical to what Gachō Badi's Character
Personality Agent and Director Agent need to do, just fed Undertale
dials and an Undertale screenplay instead of Gachō Badi's sliders and
goose antics. Swapping the seed data in `main.py` and the flavor text in
`agents.py` for Gachō Badi's residents/buildings/tasks — without
touching the pipeline's structure or its validation — is the intended
next step once this architecture is confirmed against a known-good
reference game.

## What this crew produces

Given a small encounter seed (a few monsters with battle dials, a few
rooms), one run of the crew produces:

- **Encounter Prep content** (dispatched by the `Encounter Orchestrator`):
  - a **battle-style profile** per monster, derived from
    aggression/playfulness/sympathy/chattiness dials
  - a monster-specific **ACT menu** (e.g. Check/Compliment/Wait for a
    gentle monster, Check/Threaten/Insult for a hostile one) built from
    that battle style
  - a **room design spec** per room, calling out its environmental
    feature (a puzzle, a spear trap, an echo-flower clearing, ...)
  - an **area layout** placing each room somewhere along the Underground
    (Ruins → Snowdin → Waterfall → Hotland → CORE → New Home)
- **Battle Turn output**, using that prepped state:
  - a **bullet-hell attack pattern** per monster (the Bullet Pattern
    Designer Agent, one of this crew's two "One Wow" agents) — each
    pattern is written to reflect the monster's own personality, the
    way Undyne's spear wall or Papyrus's walkable bones do in the real
    game
  - the **battle-box dialogue** (FIGHT/ACT/ITEM/MERCY flavor text) for
    the active attack, from the Dialogue Writer Agent, aware of the
    current route
  - the **staged turn actions** — what the monster and the SOUL actually
    do in the box — from the Battle Director Agent, this crew's other
    "One Wow" agent

Everything is printed to the terminal as it's produced and written as
structured JSON to `output/run.json` so a game engine (or a grader) can
inspect exactly what each agent handed the next one.

See [`DIAGRAM.md`](DIAGRAM.md) for the full agent map and data flow.

## The eight agents — role, input, output

Each agent has exactly one job, and each one's output is a field another
agent requires — remove any single agent and the pipeline raises a clear
error instead of degrading silently. See "Why every agent is
load-bearing" in [`DIAGRAM.md`](DIAGRAM.md) for the proof (including how
to reproduce the break yourself).

| Agent | Input | Output |
|---|---|---|
| Monster Personality Agent | battle dials (aggression/playfulness/sympathy/chattiness) | `monster.traits` + battle-style summary |
| Area Layout Agent | list of rooms | `room.location` (mutates in place) |
| ACT Menu Designer Agent | monster *(requires `.traits`)* | `monster.act_options` (mutates in place) |
| Room Designer Agent | room *(requires `.location`)* | `room.feature`, enriched, + `room.designed = True` (mutates in place) |
| Encounter Orchestrator | a request kind (`act_menu`/`room`/`layout`) + payload | dispatches to the matching agent above, returns its result |
| Bullet Pattern Designer Agent ("One Wow") | monsters *(need `.traits`)* + rooms *(need `.location` + `.designed`)* | attack list (bullet patterns) |
| Dialogue Writer Agent | an attack + monsters *(need `.act_options`)* + rooms *(need `.location` + `.designed`)* | battle script (box dialogue + flavor text) |
| Battle Director Agent ("One Wow") | battle script + attack + rooms *(need `.location`)* | staged turn actions — the actual gameplay |

Implementation: [`agents.py`](agents.py) (agent definitions, with each
agent's required input validated at the top of its `run()`),
[`models.py`](models.py) (shared data passed between agents),
[`crew.py`](crew.py) (orchestration, in the order the dependencies above
require), [`main.py`](main.py) (entry point).

## Why raw orchestration instead of the `crewai` package

The crew is plain Python with no third-party dependencies, structured the
way CrewAI structures a crew (each agent has a `role`/`goal`/`backstory`
and a single `run()` task; a `Crew` class sequences them and passes
output forward as input). This was a deliberate choice over installing
`crewai`: it guarantees the assignment requirement — "3+ agents
coordinate and produce output without crashing" — holds on any machine
with Python 3.9+, with no package install and no API key.

Each agent calls out through [`llm_client.py`](llm_client.py), which
supports three providers:

1. **Anthropic (Claude)** — used if `ANTHROPIC_API_KEY` is set and
   `anthropic` is installed. Checked first.
2. **OpenAI** — used if `OPENAI_API_KEY` is set and `openai` is installed
   (and Anthropic wasn't selected).
3. **mock** — a deterministic local generator built from the same
   structured inputs (monster traits, room features, attack
   description). Used whenever no provider is configured, *or* if a real
   call fails for any reason (no network, bad key, rate limit) — the
   failure is caught per-call and that one call falls back, the run
   continues.

So the same code path demonstrates real multi-agent LLM coordination on
whichever provider you have credentials for, and still runs to
completion and produces correct, inspectable output when you don't.

## Running it

```bash
cd UnderTale_Multi_Agent
python3 main.py
```

No setup required — this uses the local mock provider.

### Running on Claude

```bash
pip install anthropic
export ANTHROPIC_API_KEY=...
python3 main.py
```

### Running on OpenAI

```bash
pip install openai
export OPENAI_API_KEY=...
python3 main.py
```

### Forcing a provider / model

If both keys happen to be set, Anthropic wins by default. Override with:

```bash
export LLM_PROVIDER=anthropic   # or: openai | mock
export ANTHROPIC_MODEL=claude-sonnet-5   # optional, this is the default
export OPENAI_MODEL=gpt-4o-mini          # optional, this is the default
```

`main.py`'s summary line reports which provider actually ran
(`LLM provider in use : anthropic (live API calls)`, etc.), so you can
confirm which one was used without reading the source.

Output lands in `output/run.json` and is also logged to the terminal as
each agent runs, so you can see the hand-off between agents in real time
(e.g. `[Bullet Pattern Designer Agent] designed 3 attack(s)` immediately
followed by `[Dialogue Writer Agent] wrote battle script for attack #1`).
