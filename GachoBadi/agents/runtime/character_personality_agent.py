from __future__ import annotations

from agents.base import BaseAgent
from definitions.models import Resident, Sliders


class CharacterPersonalityAgent(BaseAgent):
    role = "Character Personality Agent"
    goal = "Turn a resident's tuned sliders into a coherent personality profile."
    backstory = "Reads player-set movement/speech/energy/intelligence sliders and names the personality that falls out of them."

    TRAIT_TABLE = {
        "movement": {"low": "sedentary", "high": "energetic"},
        "speech": {"low": "reserved", "high": "candid"},
        "energy": {"low": "flat", "high": "excitable"},
        "intelligence": {"low": "dull", "high": "astute"},
    }

    def _bucket(self, value: int) -> str:
        return "high" if value >= 50 else "low"

    def run(self, name: str, role_title: str, sliders: Sliders) -> Resident:
        traits = [
            self.TRAIT_TABLE["movement"][self._bucket(sliders.movement)],
            self.TRAIT_TABLE["speech"][self._bucket(sliders.speech)],
            self.TRAIT_TABLE["energy"][self._bucket(sliders.energy)],
            self.TRAIT_TABLE["intelligence"][self._bucket(sliders.intelligence)],
        ]
        fallback = (
            f"{name} the {role_title} comes across as {', '.join(traits)}. "
            f"({sliders.movement}/{sliders.speech}/{sliders.energy}/{sliders.intelligence} "
            f"movement/speech/energy/intelligence)"
        )
        summary = self.llm.generate(
            system="You write a one-sentence personality summary for a life-sim resident from slider values.",
            prompt=f"Name: {name}\nRole: {role_title}\nSliders: {sliders}\nTraits: {traits}",
            fallback=fallback,
        )
        self._log(f"built personality for {name} -> {traits}")
        return Resident(name=name, role=role_title, sliders=sliders, traits=traits, personality_summary=summary)
