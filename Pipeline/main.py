"""Entry point: runs the Gacho Badi crew end-to-end and writes output/run.json.

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

from crew import GachoBadiCrew
from models import Building, Resident, Sliders


def build_island_seed():
    """A small island snapshot pulled straight from the GDD's examples."""
    residents = [
        Resident(name="Hazel", role="baker", sliders=Sliders(movement=30, speech=70, energy=60, intelligence=55)),
        Resident(name="Otto", role="teacher", sliders=Sliders(movement=20, speech=40, energy=35, intelligence=90)),
        Resident(name="Vic", role="gym instructor", sliders=Sliders(movement=90, speech=80, energy=95, intelligence=45)),
    ]
    buildings = [
        Building(name="Hazel's Bakery", kind="shop", interactive_feature="oven that can overheat and puff flour"),
        Building(name="Front Gate", kind="structure", interactive_feature="gate that can open and close"),
        Building(name="Garden Hose Stand", kind="prop", interactive_feature="hose that can spout water"),
    ]
    return residents, buildings


def main() -> int:
    print("Gacho Badi (Goose Buddy) -- AI Architecture Crew")
    print("=" * 55)

    try:
        residents, buildings = build_island_seed()
        crew = GachoBadiCrew(seed=7)

        residents = crew.run_personality_pass(residents)
        dev_time_result = crew.run_dev_time_pass(residents, buildings)
        tick_result = crew.run_game_tick(residents, buildings)

        output = {
            "game": "Gacho Badi (Goose Buddy)",
            "dev_time_pass": dev_time_result,
            "game_tick": GachoBadiCrew.to_jsonable(tick_result),
        }

        os.makedirs("output", exist_ok=True)
        out_path = os.path.join("output", "run.json")
        with open(out_path, "w") as f:
            json.dump(output, f, indent=2)

        print("\n=== SUMMARY ===")
        print(f"Residents processed : {len(tick_result['personalities'])}")
        print(f"Tasks generated      : {len(tick_result['tasks'])}")
        if tick_result["screenplay"]:
            print(f"Screenplay lines     : {len(tick_result['screenplay'].lines)}")
            print(f"Staged actions       : {len(tick_result['staged_actions'])}")
        print(f"LLM provider in use  : {crew.llm.provider} "
              f"({'live API calls' if crew.llm.provider != 'mock' else 'local deterministic fallback'})")
        print(f"Full run written to  : {os.path.abspath(out_path)}")
        return 0
    except Exception as exc:  # last-resort guard: never let the crew crash silently
        print(f"\n[FATAL] Crew run failed unexpectedly: {exc!r}", file=sys.stderr)
        print("This should not happen -- please file a bug with the traceback above.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
