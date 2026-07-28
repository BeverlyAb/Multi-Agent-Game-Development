"""Shared LLM access layer for every agent in the crew.

Every agent calls generate() with a `fallback` string it can compute
locally from structured data. If a real provider is configured and its
SDK is installed, the call goes out over the network; any failure
(missing package, bad key, timeout, rate limit) is caught and the
fallback is used instead. This is what lets `main.py` guarantee it never
crashes and always produces output, with or without API access.

Supported providers, checked in this order unless LLM_PROVIDER forces one:
  1. Anthropic (Claude)  -- ANTHROPIC_API_KEY + `pip install anthropic`
  2. OpenAI               -- OPENAI_API_KEY + `pip install openai`
  3. mock (local fallback) -- always available, zero setup

Set LLM_PROVIDER=anthropic|openai|mock to force a specific one (e.g. to
run on Claude even if an OPENAI_API_KEY also happens to be set). Model
names are configurable via ANTHROPIC_MODEL / OPENAI_MODEL.
"""
from __future__ import annotations

import os
import random
from typing import Optional

DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-5"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


class LLMClient:
    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self.anthropic_model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
        self.openai_model = os.environ.get("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
        self.provider = self._detect_provider()

    def _has_anthropic(self) -> bool:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return False
        try:
            import anthropic  # noqa: F401

            return True
        except ImportError:
            print("    [llm_client] ANTHROPIC_API_KEY is set but `anthropic` isn't installed "
                  "(pip install anthropic); skipping.")
            return False

    def _has_openai(self) -> bool:
        if not os.environ.get("OPENAI_API_KEY"):
            return False
        try:
            import openai  # noqa: F401

            return True
        except ImportError:
            print("    [llm_client] OPENAI_API_KEY is set but `openai` isn't installed "
                  "(pip install openai); skipping.")
            return False

    def _detect_provider(self) -> str:
        forced = os.environ.get("LLM_PROVIDER", "").strip().lower()
        if forced == "anthropic":
            return "anthropic" if self._has_anthropic() else "mock"
        if forced == "openai":
            return "openai" if self._has_openai() else "mock"
        if forced == "mock":
            return "mock"
        if forced:
            print(f"    [llm_client] Unknown LLM_PROVIDER={forced!r}; ignoring and auto-detecting.")

        if self._has_anthropic():
            return "anthropic"
        if self._has_openai():
            return "openai"
        return "mock"

    def generate(self, system: str, prompt: str, *, fallback: str) -> str:
        try:
            if self.provider == "anthropic":
                return self._call_anthropic(system, prompt)
            if self.provider == "openai":
                return self._call_openai(system, prompt)
        except Exception as exc:  # network issues, bad key, rate limit, etc.
            print(f"    [llm_client] {self.provider} call failed ({exc}); using local fallback")
        return fallback

    def _call_anthropic(self, system: str, prompt: str) -> str:
        import anthropic

        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=self.anthropic_model,
            max_tokens=400,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in msg.content if block.type == "text").strip()

    def _call_openai(self, system: str, prompt: str) -> str:
        import openai

        client = openai.OpenAI()
        resp = client.chat.completions.create(
            model=self.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message.content.strip()

    def choice(self, options):
        return self._rng.choice(options)

    def sample(self, options, k):
        return self._rng.sample(options, min(k, len(options)))
