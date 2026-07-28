# Gachō Badi (Goose Buddy) — AI Architecture Crew

**This is the AI crew for my capstone game, *Gachō Badi (Goose Buddy)***
(GDD at `../gdd-review-kit/gdd.txt`). It's Tomodachi Life meets Untitled
Goose Game: the player controls a goose that pulls off indirect,
open-ended antics on custom residents and buildings, earning credits
that unlock more residents/buildings, which unlock more tasks, until the
island's task list is exhausted.

This folder is a working, dependency-free implementation of the eight
agents described in that GDD's **AI Architecture** section, wired
together as a coordinating crew rather than left as a spec. It exists to
generate the content that actually drives Gachō Badi's gameplay loop —
resident personalities and looks, building designs, island layout, the
task list that gates progression, and the screenplay + staged behavior
for whichever task is currently active.

## What this crew produces

Given a small island snapshot (a few residents with personality sliders,
a few interactive buildings), one run of the crew produces:

- **Island Prep content** (dispatched by the `Scene Orchestrator`):
  - a **personality profile** per resident, derived from their
    movement/speech/energy/intelligence sliders
  - a plain-language **appearance spec** per resident, built from that
    personality
  - a **building design spec** per building, calling out its interactive
    feature (a hose that spouts water, a gate that opens/closes, ...)
  - an **island layout** assigning each building a physical location
- **Runtime Tick output**, using that prepped state:
  - an **open-ended task list** (the Task Creator Agent, one of the
    GDD's two "One Wow" agents)
  - a **screenplay** (dialogue + directional cues) for the active task,
    from the Writer Agent
  - **staged actions** — what the goose and resident actually do in
    engine, at a real island location — from the Director Agent, the
    GDD's other "One Wow" agent

Everything is printed to the terminal as it's produced and written as
structured JSON to `output/run.json` so a game engine (or a grader) can
inspect exactly what each agent handed the next one.

See [`DIAGRAM.md`](DIAGRAM.md) for the full agent map and data flow.

## The eight agents — role, input, output

Each agent has exactly one job, and each one's output is a field another
agent requires — remove any single agent and the pipeline raises a clear
error instead of degrading silently. See "Why every agent is load-bearing"
in [`DIAGRAM.md`](DIAGRAM.md) for the proof (including how to reproduce
the break yourself).

| Agent | Input | Output |
|---|---|---|
| Character Personality Agent | slider values (movement/speech/energy/intelligence) | `resident.traits` + summary |
| Island Layout Agent | list of buildings | `building.location` (mutates in place) |
| Character Appearance Agent | resident *(requires `.traits`)* | `resident.appearance` (mutates in place) |
| Building Designer Agent | building *(requires `.location`)* | `building.interactive_feature`, enriched, + `building.designed = True` (mutates in place) |
| Scene Orchestrator | a request kind (`appearance`/`building`/`layout`) + payload | dispatches to the matching agent above, returns its result |
| Task Creator Agent ("One Wow") | residents *(need `.traits`)* + buildings *(need `.location` + `.designed`)* | task list |
| Writer Agent | a task + residents *(need `.appearance`)* + buildings *(need `.location` + `.designed`)* | screenplay (dialogue + directional cues) |
| Director Agent ("One Wow") | screenplay + task + buildings *(need `.location`)* | staged actions — the actual gameplay |

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

Each agent calls out through [`llm_client.py`](llm_client.py), which supports
three providers:

1. **Anthropic (Claude)** — used if `ANTHROPIC_API_KEY` is set and
   `anthropic` is installed. Checked first.
2. **OpenAI** — used if `OPENAI_API_KEY` is set and `openai` is installed
   (and Anthropic wasn't selected).
3. **mock** — a deterministic local generator built from the same
   structured inputs (resident traits, building features, task
   description). Used whenever no provider is configured, *or* if a real
   call fails for any reason (no network, bad key, rate limit) — the
   failure is caught per-call and that one call falls back, the run
   continues.

So the same code path demonstrates real multi-agent LLM coordination on
whichever provider you have credentials for, and still runs to
completion and produces correct, inspectable output when you don't.

## Running it

```bash
cd Pipeline
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
each agent runs, so you can see the hand-off between agents in real
time (e.g. `[Task Creator Agent] generated 3 task(s)` immediately
followed by `[Writer Agent] wrote screenplay for task #1`).
