"""Shared base class for every agent in this package -- the runtime and
dev_time agents alike. One class, reused everywhere, so "agent" means the
same shape (role/goal/backstory/run) no matter which subpackage it lives
in.

Each class mirrors the CrewAI Agent shape (role/goal/backstory/run)
without depending on the crewai package, so this runs anywhere Python 3
runs. Every agent calls self.llm.generate(..., fallback=...) -- when no
API key is configured (the default), the deterministic fallback is what
executes, so the crew always produces output.
"""
from __future__ import annotations

from llm_client import LLMClient


class BaseAgent:
    role: str = "Agent"
    goal: str = ""
    backstory: str = ""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def _log(self, message: str) -> None:
        print(f"  [{self.role}] {message}")
