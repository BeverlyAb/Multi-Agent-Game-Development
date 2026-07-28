"""Entry point: runs the Untitled-Goose-Game-style village crew end-to-end
and writes output/run.json.

Usage:
    python3 main.py

No API key or third-party package is required -- set ANTHROPIC_API_KEY or
OPENAI_API_KEY (and install the matching SDK) to have agents call a real
model instead of the deterministic local fallback. Either way this script
is guaranteed to finish and produce output; see the try/except in main().
"""
from __future__ import annotations

import json
import os
import sys

from crew import UntitledGooseGameCrew
from models import Prop, RoutineDials, Villager


def build_village_seed():
    """A small village snapshot in Untitled Goose Game's own spirit: no proper names, just roles."""
    villagers = [
        Villager(
            name="The Gardener",
            role="gardener",
            dials=RoutineDials(territorialness=90, obliviousness=20, fussiness=70, patience=30),
        ),
        Villager(
            name="The Shopkeeper",
            role="shopkeeper",
            dials=RoutineDials(territorialness=60, obliviousness=35, fussiness=85, patience=65),
        ),
        Villager(
            name="The Boy",
            role="boy",
            dials=RoutineDials(territorialness=40, obliviousness=80, fussiness=55, patience=15),
        ),
    ]
    props = [
        Prop(name="Garden Rake", kind="garden tool", affordance="flings mud when stepped on"),
        Prop(name="Sun Hat", kind="clothing item", affordance="blows off in even a light breeze"),
        Prop(name="Toy Plane", kind="toy", affordance="squeaks loudly when squeezed"),
    ]
    return villagers, props


def main() -> int:
    print("Untitled Goose Game -- Village Mischief Generation Crew")
    print("=" * 55)

    try:
        villagers, props = build_village_seed()
        crew = UntitledGooseGameCrew(seed=7)

        villagers = crew.run_routine_pass(villagers)
        prep_result = crew.run_prep_pass(villagers, props)
        tick_result = crew.run_mischief_tick(villagers, props)

        output = {
            "game": "Untitled Goose Game",
            "prep_pass": prep_result,
            "mischief_tick": UntitledGooseGameCrew.to_jsonable(tick_result),
        }

        os.makedirs("output", exist_ok=True)
        out_path = os.path.join("output", "run.json")
        with open(out_path, "w") as f:
            json.dump(output, f, indent=2)

        print("\n=== SUMMARY ===")
        print(f"Villagers processed   : {len(tick_result['villagers'])}")
        print(f"Checklist items       : {len(tick_result['checklist'])}")
        if tick_result["verb_plan"]:
            print(f"Verb plan lines       : {len(tick_result['verb_plan'].lines)}")
            print(f"Staged gags           : {len(tick_result['staged_gags'])}")
        print(f"LLM provider in use   : {crew.llm.provider} "
              f"({'live API calls' if crew.llm.provider != 'mock' else 'local deterministic fallback'})")
        print(f"Full run written to   : {os.path.abspath(out_path)}")
        return 0
    except Exception as exc:  # last-resort guard: never let the crew crash silently
        print(f"\n[FATAL] Crew run failed unexpectedly: {exc!r}", file=sys.stderr)
        print("This should not happen -- please file a bug with the traceback above.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
