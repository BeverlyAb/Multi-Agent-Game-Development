"""The agent-AGNOSTIC half of the workflow -- everything here works the
same way regardless of which agent it's guarding: guardrails.py
(generic checks), changelog.py (audit log), and the two entry points,
guarded_llm_client.py and guarded_output.py. The shared vocabulary these
all speak (Finding, GuardrailViolation, CallRecord, ReviewResult) lives
one level up in ../definitions/models_verification.py, not in this
package -- it's shared with ../constraints/ too, so it belongs to
neither side alone.

The agent-SPECIFIC half (token budgets, gap-detection logic, priority
weights) lives one level up in ../constraints/ -- see ../README.md for
the full design.
"""
