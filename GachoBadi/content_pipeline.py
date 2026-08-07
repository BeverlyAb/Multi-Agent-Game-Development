"""Assignment #4 -- Dynamic Content Pipeline.

Reads the GDD (gdd.txt) as the knowledge base, retrieves grounding
context per content request, generates content with agents adapted from
UntitledGooseGame_Multi_Agent (see agents/dynamic_content/), and runs every
output through a Consistency Critic Agent before it's accepted. See
Readme.md for what this generates, whether it sounds like the game, and
what the critic actually caught.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import List

from agents.dynamic_content.consistency_critic_agent import ConsistencyCriticAgent
from agents.dynamic_content.item_affordance_content_agent import ItemAffordanceContentAgent
from agents.dynamic_content.relationship_backstory_content_agent import RelationshipBackstoryContentAgent
from agents.dynamic_content.task_premise_content_agent import TaskPremiseContentAgent
from llm_client import LLMClient
from rag import GDDKnowledgeBase, RetrievedChunk


@dataclass
class GenerationRecord:
    content_type: str
    query: str
    retrieved: List[dict]
    raw_output: str
    passed_critic: bool
    critic_violations: List[str]
    critic_commentary: str
    final_output: str
    # Structured fields (item name/kind, resident names, building, connection
    # kind) so a client -- the Phaser web client in web/, in particular --
    # can drive a scene without re-parsing prose out of final_output.
    meta: dict = field(default_factory=dict)


class ContentPipeline:
    def __init__(self, gdd_path: str = "gdd.txt", seed: int = 7):
        self.kb = GDDKnowledgeBase(gdd_path)
        self.llm = LLMClient(seed=seed)
        self.item_agent = ItemAffordanceContentAgent(self.llm)
        self.backstory_agent = RelationshipBackstoryContentAgent(self.llm)
        self.task_agent = TaskPremiseContentAgent(self.llm)
        self.critic = ConsistencyCriticAgent(self.llm)

    def _retrieve(self, query: str, k: int = 2) -> List[RetrievedChunk]:
        hits = self.kb.retrieve(query, k=k)
        print(f"\n  [RAG] query: {query!r}")
        for h in hits:
            snippet = h.chunk.text if len(h.chunk.text) <= 110 else h.chunk.text[:110] + "..."
            print(f"    -> chunk #{h.chunk.chunk_id} (score {h.score}) [{h.chunk.heading}]: {snippet}")
        return hits

    def _run_through_critic(
        self, content_type: str, query: str, hits: List[RetrievedChunk], raw_output: str, meta: dict
    ) -> GenerationRecord:
        report = self.critic.run(raw_output, [h.chunk for h in hits])
        if report.violations:
            print(f"  [Consistency Critic Agent] caught {len(report.violations)} issue(s) in {content_type}:")
            for v in report.violations:
                print(f"    - {v}")
            print(f"    corrected -> {report.corrected_text}")
        else:
            print(f"  [Consistency Critic Agent] {content_type}: no lore breaks or tone drift found")
        return GenerationRecord(
            content_type=content_type,
            query=query,
            retrieved=[
                {"chunk_id": h.chunk.chunk_id, "heading": h.chunk.heading, "text": h.chunk.text, "score": h.score}
                for h in hits
            ],
            raw_output=raw_output,
            passed_critic=not report.violations,
            critic_violations=report.violations,
            critic_commentary=report.commentary,
            final_output=report.corrected_text,
            meta=meta,
        )

    def generate_item_affordance(self, item_name: str, item_kind: str) -> GenerationRecord:
        query = f"item interaction affordance {item_kind} goose actions reset rule no permanent loss"
        hits = self._retrieve(query)
        context = "\n".join(h.chunk.text for h in hits)
        raw = self.item_agent.run(item_name, item_kind, context)
        meta = {"item_name": item_name, "item_kind": item_kind}
        return self._run_through_critic("item_affordance", query, hits, raw, meta)

    def generate_relationship_backstory(
        self, resident_a: str, resident_b: str, relationship_label: str
    ) -> GenerationRecord:
        query = f"relationship agent authored backstory {relationship_label} why not just a label flip"
        hits = self._retrieve(query)
        context = "\n".join(h.chunk.text for h in hits)
        raw = self.backstory_agent.run(resident_a, resident_b, relationship_label, context)
        meta = {"resident_a": resident_a, "resident_b": resident_b, "relationship_label": relationship_label}
        return self._run_through_critic("relationship_backstory", query, hits, raw, meta)

    def generate_task_premise(
        self,
        resident: str,
        other: str,
        relationship_label: str,
        building: str,
        connection_kind: str,
        item_name: str = "a small kept memento",
    ) -> GenerationRecord:
        # Tuned from an earlier version of this query ("task creator connection
        # goose verbs honk grab pick up duck dash no dialogue"), which pulled
        # in the roster/scoping and tutorial-opening paragraphs instead of the
        # GDD's actual task-definition paragraph -- see Readme.md.
        query = "tasks are actions goose must perform on residents or buildings open-ended indirect interaction"
        hits = self._retrieve(query)
        context = "\n".join(h.chunk.text for h in hits)
        # item_name is expected to come from a prior generate_item_affordance()
        # call's meta -- the Task Premise Content Agent draws on that agent's
        # own output for a concrete step target instead of naming the
        # building three times with only the verb changed (see the
        # Consistency Critic Agent's redundant-step check).
        raw = self.task_agent.run(resident, other, relationship_label, building, connection_kind, context, item_name)
        meta = {
            "resident": resident,
            "other": other,
            "relationship_label": relationship_label,
            "building": building,
            "connection_kind": connection_kind,
            "item_name": item_name,
        }
        return self._run_through_critic("task_premise", query, hits, raw, meta)

    def check_catalog(self, task_records: List[GenerationRecord]) -> List[str]:
        """Batch check across multiple already-generated task premises --
        see ConsistencyCriticAgent.check_catalog_redundancy for why this
        can't be folded into the per-task critic pass above."""
        payload = [
            {
                "label": r.meta.get("connection_kind", r.content_type),
                "item_name": r.meta.get("item_name"),
                "text": r.final_output,
            }
            for r in task_records
        ]
        violations = self.critic.check_catalog_redundancy(payload)
        if violations:
            print(f"  [Consistency Critic Agent] caught {len(violations)} catalog-level issue(s):")
            for v in violations:
                print(f"    - {v}")
        else:
            print(f"  [Consistency Critic Agent] catalog check: no redundancy across {len(task_records)} task(s)")
        return violations

    @staticmethod
    def to_jsonable(records: List[GenerationRecord]) -> list:
        return [asdict(r) for r in records]
