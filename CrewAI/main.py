"""Entry point: runs the Undertale encounter crew end-to-end and writes
output/run.json.

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

from crew import UndertaleCrew
from models import BattleDials, Monster, Room


def build_encounter_seed():
    """A small encounter set pulled from Undertale's own cast and areas."""
    monsters = [
        Monster(
            name="Papyrus",
            role="aspiring Royal Guard, skeleton sentry",
            dials=BattleDials(aggression=20, playfulness=90, sympathy=80, chattiness=95),
        ),
        Monster(
            name="Undyne",
            role="Captain of the Royal Guard",
            dials=BattleDials(aggression=90, playfulness=40, sympathy=25, chattiness=60),
        ),
        Monster(
            name="Napstablook",
            role="ghost",
            dials=BattleDials(aggression=10, playfulness=15, sympathy=85, chattiness=20),
        ),
    ]
    rooms = [
        Room(name="Sentry Station", kind="puzzle room", feature="a lazily-guarded puzzle Papyrus is proud of"),
        Room(name="Spear Bridge", kind="battle arena", feature="a bridge lined with rising spear traps"),
        Room(name="Dummy Clearing", kind="quiet clearing", feature="an old dummy and a patch of echo flowers"),
    ]
    return monsters, rooms


def main() -> int:
    print("Undertale -- Encounter Generation Crew")
    print("=" * 55)

    try:
        monsters, rooms = build_encounter_seed()
        crew = UndertaleCrew(seed=7)

        monsters = crew.run_personality_pass(monsters)
        prep_result = crew.run_prep_pass(monsters, rooms)
        turn_result = crew.run_battle_turn(monsters, rooms)

        output = {
            "game": "Undertale",
            "route": crew.route,
            "prep_pass": prep_result,
            "battle_turn": UndertaleCrew.to_jsonable(turn_result),
        }

        os.makedirs("output", exist_ok=True)
        out_path = os.path.join("output", "run.json")
        with open(out_path, "w") as f:
            json.dump(output, f, indent=2)

        print("\n=== SUMMARY ===")
        print(f"Monsters processed   : {len(turn_result['monsters'])}")
        print(f"Attacks designed      : {len(turn_result['attacks'])}")
        if turn_result["battle_script"]:
            print(f"Battle script lines   : {len(turn_result['battle_script'].lines)}")
            print(f"Turn actions staged   : {len(turn_result['turn_actions'])}")
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
