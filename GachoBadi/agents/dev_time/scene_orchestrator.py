from __future__ import annotations

from agents.base import BaseAgent
from agents.dev_time.building_designer_agent import BuildingDesignerAgent
from agents.dev_time.character_appearance_agent import CharacterAppearanceAgent
from agents.dev_time.island_layout_agent import IslandLayoutAgent
from api.llm_client import LLMClient


class SceneOrchestratorAgent(BaseAgent):
    role = "Scene Orchestrator"
    goal = "Spin up the right dev-time agent for a programmer's scene request and return its output."
    backstory = "Prompted by the programmer with the scene they expect; dispatches to a sub-agent and reports back."

    def __init__(self, llm: LLMClient):
        super().__init__(llm)
        self.appearance_agent = CharacterAppearanceAgent(llm)
        self.building_agent = BuildingDesignerAgent(llm)
        self.layout_agent = IslandLayoutAgent(llm)

    def run(self, request_kind: str, payload) -> str:
        self._log(f"dispatching '{request_kind}' request")
        if request_kind == "appearance":
            return self.appearance_agent.run(payload)
        if request_kind == "building":
            return self.building_agent.run(payload)
        if request_kind == "layout":
            return self.layout_agent.run(payload)
        raise ValueError(f"Unknown scene request kind: {request_kind}")
