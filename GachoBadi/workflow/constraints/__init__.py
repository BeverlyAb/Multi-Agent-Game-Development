"""One constraint spec per agent -- <agent>_constraints.py +
<agent>_constraints.yaml -- the agent-SPECIFIC half of the workflow (see
base.py for the shared shape every spec implements, and
../guardrails.py for the agent-AGNOSTIC half).

Every file here (and its matching .yaml) is named ending in
"_constraints" specifically so it can never be mistaken for the actual
agent module it constrains, e.g. goose_solution_planner_constraints.py
vs. agents/runtime/goose_solution_planner_agent.py.

Split within each pair: the .yaml holds declarative VALUES (token
budget, priority weights, max_retries); the .py holds gap-detection
LOGIC (regex extraction, word-overlap, etc.) and loads the .yaml's
values in via config_loader.py. See ../README.md's "Why the YAML/Python
split" for the reasoning.

To add guardrailed verification for another agent in this crew:
  1. Copy goose_solution_planner_constraints.{py,yaml} (if that agent
     calls self.llm.generate() -- input side) or
     chain_reaction_constraints.{py,yaml} (if it doesn't -- output side,
     via ../guarded_output.py) as a template.
  2. In the .yaml: set token_budget from gdd.txt's Technical Strategy
     table, and any priority_weights that need to outrank the default.
  3. In the .py: write gap_detectors -- functions of (output_text,
     context) -> List[Finding] that check things ONLY true for that
     agent's domain. Don't override priority_score() in Python unless a
     rule needs ranking logic a flat weight table can't express.
  4. Wrap that agent's LLMClient with GuardedLLMClient(base,
     constraints=...), or call verify_output() on its return value --
     either way, no change to the agent's own file.
"""
