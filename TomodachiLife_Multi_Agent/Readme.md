# Tomodachi Life — Island Event Generation Crew

**This crew is built for *Tomodachi Life***, Nintendo's 2013 life-sim.
Miis live in apartments on an island, and the game's whole appeal is
watching their personalities collide: friendships, crushes, rivalries,
and petty dramas that erupt as random skits, with a nightly news
broadcast recapping whatever happened.

This crew doubles as one of the two reference implementations behind my
capstone game, *Gachō Badi (Goose Buddy)* (GDD at
`../gdd-review-kit/gdd.txt`), which is explicitly Tomodachi Life crossed
with Untitled Goose Game. But it is **not** a re-skin of Gachō Badi's
8-agent GDD template — Tomodachi Life has systems of its own (a
relationship web between residents, per-Mii synthesized voices, a news
ticker) that don't exist in that template, so this crew has its own
agents for them instead of forcing the content into someone else's
shape. See "Eleven agents, not eight" in [`DIAGRAM.md`](DIAGRAM.md) for
exactly what's different and why.

## What this crew produces

Given a small island snapshot (a few Miis with creation-quiz dials, a
few facilities), one run of the crew produces:

- **Personality + Relationship content**:
  - a **personality profile** per Mii, derived from
    expressiveness/diligence/confidence/mischief dials
  - a **relationship map** between every pair of Miis (e.g. "close
    friends," "friendly rivals," "partners in crime") that later gates
    which events are possible
- **Island Prep content** (dispatched by the `Island Orchestrator`):
  - a **voice pattern** per Mii (pitch, pacing, catchphrase)
  - an **appearance spec** per Mii (face, hairstyle, outfit)
  - a **facility design spec** per apartment, calling out its
    interactive feature (a gossiping mirror, a mood-reactive photo
    backdrop, ...)
  - an **island layout** placing each facility on a named street
- **Event Tick output**, using that prepped state:
  - an **open-ended event list** (the Event Creator Agent, one of this
    crew's two "One Wow" agents) — each event is written to reflect both
    a Mii's personality *and* their relationship to another Mii, the way
    the real game's dramas do
  - a **skit** (thought-bubble dialogue + stage directions) for the
    active event, voiced in that Mii's own synthesized pattern
  - the **staged moments** — what the Miis and the camera actually do —
    from the Director Agent, this crew's other "One Wow" agent
  - a **news bulletin** headline recapping the event, from the
    Newscaster Agent

Everything is printed to the terminal as it's produced and written as
structured JSON to `output/run.json` so a game engine (or a grader) can
inspect exactly what each agent handed the next one.

See [`DIAGRAM.md`](DIAGRAM.md) for the full agent map and data flow.

## The eleven agents — role, input, output

Each agent has exactly one job, and each one's output is a field another
agent requires — remove any single agent and the pipeline raises a clear
error instead of degrading silently. See "Why every agent is
load-bearing" in [`DIAGRAM.md`](DIAGRAM.md) for the proof (including how
to reproduce the break yourself).

| Agent | Input | Output |
|---|---|---|
| Mii Personality Agent | creation dials (expressiveness/diligence/confidence/mischief) | `mii.traits` + personality summary |
| Relationship Agent | Miis *(need `.traits`)* | `mii.relationships` (mutates in place) |
| Island Layout Agent | list of apartments | `apartment.location` (mutates in place) |
| Mii Voice Agent | Mii *(requires `.traits`)* | `mii.voice_pattern` (mutates in place) |
| Mii Appearance Agent | Mii *(requires `.traits`)* | `mii.appearance` (mutates in place) |
| Apartment Designer Agent | apartment *(requires `.location`)* | `apartment.feature`, enriched, + `apartment.designed = True` (mutates in place) |
| Island Orchestrator | a request kind (`voice`/`appearance`/`apartment`/`layout`) + payload | dispatches to the matching agent above, returns its result |
| Event Creator Agent ("One Wow") | Miis *(need `.traits` + `.relationships`)* + apartments *(need `.location` + `.designed`)* | event list |
| Skit Writer Agent | an event + Miis *(need `.voice_pattern` + `.appearance`)* + apartments *(need `.location` + `.designed`)* | skit (thought-bubble dialogue + stage directions) |
| Director Agent ("One Wow") | skit + event + apartments *(need `.location`)* | staged moments — the actual gameplay |
| Newscaster Agent | staged moments + event | news bulletin (headline) |

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
   structured inputs (Mii traits, relationships, facility features).
   Used whenever no provider is configured, *or* if a real call fails for
   any reason (no network, bad key, rate limit) — the failure is caught
   per-call and that one call falls back, the run continues.

So the same code path demonstrates real multi-agent LLM coordination on
whichever provider you have credentials for, and still runs to
completion and produces correct, inspectable output when you don't.

## Running it

```bash
cd TomodachiLife_Multi_Agent
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
(e.g. `[Event Creator Agent] generated 3 event(s)` immediately followed
by `[Skit Writer Agent] wrote skit for event #1`).
