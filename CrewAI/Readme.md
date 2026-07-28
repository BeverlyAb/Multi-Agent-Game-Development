# Undertale — Encounter Generation Crew

**This crew is built for *Undertale***, Toby Fox's 2015 RPG. The player
is a human child navigating the Underground, fighting or sparing
monsters in bullet-hell "SOUL box" encounters via a FIGHT/ACT/ITEM/MERCY
menu, and the choice to spare or fight shapes which of Undertale's
routes (Pacifist / Neutral / Genocide) the story follows.

This folder is a working, dependency-free multi-agent crew that
generates the content driving one of those encounters: a monster's
battle personality, its context-sensitive ACT menu, the room it's
fought in, the bullet pattern it throws, the battle-box dialogue for
that turn, and the actual staged turn behavior the player sees.

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
| Room Designer Agent | room *(requires `.location`)* | `room.feature`, enriched (mutates in place) |
| Encounter Orchestrator | a request kind (`act_menu`/`room`/`layout`) + payload | dispatches to the matching agent above, returns its result |
| Bullet Pattern Designer Agent ("One Wow") | monsters *(need `.traits`)* + rooms *(need `.location`)* | attack list (bullet patterns) |
| Dialogue Writer Agent | an attack + monsters *(need `.act_options`)* + rooms *(need `.location`)* | battle script (box dialogue + flavor text) |
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
cd CrewAI
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
