"""LLM client wrapper (api/llm_client.py) -- the one place every agent
routes its generate() calls through, whether that hits a real provider or
the deterministic local fallback.
"""
