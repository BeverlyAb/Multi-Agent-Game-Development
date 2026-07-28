"""Eleven agents built around Tomodachi Life's own defining systems: Mii
personality, the relationship web between Miis (friendship/rivalry/crush),
each Mii's synthesized voice pattern, appearance, apartment/facility
design, island layout, event ("drama") creation, skit dialogue, staged
moments, and the island news ticker that recaps what happened.

This is deliberately NOT a re-skin of Gacho Badi's 8-agent GDD template --
Tomodachi Life has its own identity (relationship tracking, Mii voices,
a nightly news broadcast) that a faithful crew needs agents for, even
though the pipeline-with-hard-dependencies engineering pattern is shared
across every crew in this repo.

Each class mirrors the CrewAI Agent shape (role / goal / backstory / run)
without depending on the crewai package, so this runs anywhere Python 3
runs. Every agent calls self.llm.generate(..., fallback=...) -- when no
API key is configured (the default), the deterministic fallback is what
executes, so the crew always produces output.
"""
from __future__ import annotations

from typing import List

from llm_client import LLMClient
from models import Apartment, Event, Mii, NewsBulletin, PersonalityDials, Skit, StagedMoment


class BaseAgent:
    role: str = "Agent"
    goal: str = ""
    backstory: str = ""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def _log(self, message: str) -> None:
        print(f"  [{self.role}] {message}")


# ---------------------------------------------------------------------------
# Daily-loop agents (run every time the island advances to a new event)
# ---------------------------------------------------------------------------


class MiiPersonalityAgent(BaseAgent):
    role = "Mii Personality Agent"
    goal = "Turn a Mii's creation-quiz dials into a coherent personality profile."
    backstory = (
        "Reads creator-set expressiveness/diligence/confidence/mischief dials and names the "
        "personality that falls out of them -- the same dial-to-type idea Tomodachi Life uses "
        "to turn quiz answers into a Mii who acts like 'Sassy' or 'Devious' or 'Easy-going'."
    )

    DIAL_TABLE = {
        "expressiveness": {"low": "keeps to themself", "high": "wears every feeling on their sleeve"},
        "diligence": {"low": "happily laid-back", "high": "driven to a fault"},
        "confidence": {"low": "shy around new faces", "high": "struts in like they own the place"},
        "mischief": {"low": "sweet almost to a fault", "high": "can't resist a devious bit"},
    }

    def _bucket(self, value: int) -> str:
        return "high" if value >= 50 else "low"

    def run(self, name: str, role_title: str, dials: PersonalityDials) -> Mii:
        traits = [
            self.DIAL_TABLE["expressiveness"][self._bucket(dials.expressiveness)],
            self.DIAL_TABLE["diligence"][self._bucket(dials.diligence)],
            self.DIAL_TABLE["confidence"][self._bucket(dials.confidence)],
            self.DIAL_TABLE["mischief"][self._bucket(dials.mischief)],
        ]
        fallback = (
            f"{name} the {role_title} {', '.join(traits)}. "
            f"(expressiveness/diligence/confidence/mischief: "
            f"{dials.expressiveness}/{dials.diligence}/{dials.confidence}/{dials.mischief})"
        )
        summary = self.llm.generate(
            system="You write a one-sentence personality summary for a Tomodachi-Life-style Mii from dial values.",
            prompt=f"Name: {name}\nRole: {role_title}\nDials: {dials}\nTraits: {traits}",
            fallback=fallback,
        )
        self._log(f"built personality for {name} -> {traits}")
        return Mii(name=name, role=role_title, dials=dials, traits=traits, personality_summary=summary)


class RelationshipAgent(BaseAgent):
    role = "Relationship Agent"
    goal = "Work out how every pair of Miis on the island feels about each other."
    backstory = (
        "Tomodachi Life's actual engine is its relationship web -- friendships, rivalries, "
        "crushes that escalate to marriage and kids. No event system can imitate the game "
        "without a dedicated agent tracking who feels what about whom."
    )

    """
    Input:  Miis already enriched by MiiPersonalityAgent (need .traits).
    Output: mii.relationships populated in place on every Mii (other Mii
            name -> relationship label), required by EventCreatorAgent
            whenever there's more than one Mii to relate.
    """

    def _label(self, a: Mii, b: Mii) -> str:
        a_mischief = "can't resist a devious bit" in a.traits
        b_mischief = "can't resist a devious bit" in b.traits
        a_confident = "struts in like they own the place" in a.traits
        b_confident = "struts in like they own the place" in b.traits
        a_expressive = "wears every feeling on their sleeve" in a.traits
        b_expressive = "wears every feeling on their sleeve" in b.traits
        if a_mischief and b_mischief:
            return "partners in crime"
        if a_confident and b_confident:
            return "friendly rivals"
        if a_expressive != b_expressive:
            return "unlikely friendship"
        return "close friends"

    def run(self, miis: List[Mii]) -> List[Mii]:
        for mii in miis:
            if not mii.traits:
                raise ValueError(
                    f"RelationshipAgent requires '{mii.name}' to carry personality traits "
                    "-- run MiiPersonalityAgent first."
                )
        if len(miis) < 2:
            self._log("fewer than 2 Miis -> no relationships to compute")
            return miis
        for i, mii in enumerate(miis):
            other = miis[(i + 1) % len(miis)]
            fallback = self._label(mii, other)
            label = self.llm.generate(
                system="You name, in 2-4 words, the relationship between two Tomodachi-Life-style Miis based on their traits.",
                prompt=f"Mii A: {mii.name} ({mii.traits})\nMii B: {other.name} ({other.traits})",
                fallback=fallback,
            )
            mii.relationships[other.name] = label
        self._log(f"mapped relationships: {[(m.name, m.relationships) for m in miis]}")
        return miis


class MiiVoiceAgent(BaseAgent):
    role = "Mii Voice Agent"
    goal = "Give a Mii its synthesized voice pattern from its personality."
    backstory = (
        "Every Mii's chirpy, garbled synthesized voice is one of Tomodachi Life's most "
        "recognizable touches -- a Mii who sounds like everyone else isn't really themselves."
    )

    """
    Input:  a Mii already enriched by MiiPersonalityAgent (needs .traits).
    Output: a voice-pattern spec, written into mii.voice_pattern so
            SkitWriterAgent can require and use it downstream.
    """

    def run(self, mii: Mii) -> str:
        if not mii.traits:
            raise ValueError(
                f"MiiVoiceAgent requires '{mii.name}' to carry personality traits "
                "-- run MiiPersonalityAgent first."
            )
        fallback = (
            f"{mii.name} speaks in a synthesized, slightly-off pitch that leans "
            f"{'high and quick' if 'wears every feeling on their sleeve' in mii.traits else 'low and deliberate'}, "
            "with a catchphrase that pops up whenever they're excited."
        )
        spec = self.llm.generate(
            system="You describe a Tomodachi-Life-style Mii's synthesized voice pattern (pitch, pacing, catchphrase) in one sentence, based on its traits.",
            prompt=f"Mii: {mii}",
            fallback=fallback,
        )
        mii.voice_pattern = spec
        self._log(f"built voice pattern for {mii.name}")
        return spec


class EventCreatorAgent(BaseAgent):
    role = "Event Creator Agent"
    goal = "Generate the island's open-ended list of daily events (dramas, crushes, songs, mix-ups) from the Miis, their relationships, and the facilities available."
    backstory = (
        "One of this crew's two 'One Wow' agents: Tomodachi Life's whole appeal rests on random "
        "events reading as an expression of who each Mii is and how they feel about their "
        "neighbors -- a devious Mii starting drama with their 'friendly rival' at the cafe hits "
        "different than a generic pop-up. A generic event here breaks the illusion for the "
        "whole island."
    )

    """
    Input:  Miis enriched by MiiPersonalityAgent (need .traits) and, when
            there's more than one Mii, RelationshipAgent (need
            .relationships); apartments enriched by IslandLayoutAgent
            (need .location) and ApartmentDesignerAgent (need .designed).
    Output: List[Event] consumed by SkitWriterAgent.
    """

    TEMPLATES = [
        "{mii} develops a sudden crush on {other} while hanging around {location}.",
        "{mii} and {other}, {relationship}, start a petty argument over {feature} at {location}.",
        "{mii} writes an embarrassing song about {other} at {location}.",
        "{mii} gets caught doing something silly near {feature}, and {other} won't let them live it down.",
        "{mii} and {other} patch up a falling-out that only makes sense given they're {relationship}.",
    ]

    def run(self, miis: List[Mii], apartments: List[Apartment]) -> List[Event]:
        events: List[Event] = []
        if not miis or not apartments:
            self._log("no Miis/apartments yet -> no events available")
            return events
        for mii in miis:
            if not mii.traits:
                raise ValueError(
                    f"EventCreatorAgent requires '{mii.name}' to carry personality traits "
                    "-- run MiiPersonalityAgent first."
                )
        if len(miis) > 1:
            for mii in miis:
                if not mii.relationships:
                    raise ValueError(
                        f"EventCreatorAgent requires '{mii.name}' to have mapped relationships "
                        "-- run RelationshipAgent first."
                    )
        for apartment in apartments:
            if not apartment.location:
                raise ValueError(
                    f"EventCreatorAgent requires '{apartment.name}' to have an assigned location "
                    "-- run IslandLayoutAgent first."
                )
            if not apartment.designed:
                raise ValueError(
                    f"EventCreatorAgent requires '{apartment.name}' to be designed "
                    "-- run ApartmentDesignerAgent first."
                )
        for i, mii in enumerate(miis):
            apartment = apartments[i % len(apartments)]
            other = miis[(i + 1) % len(miis)]
            relationship = mii.relationships.get(other.name, "acquaintances")
            template = self.TEMPLATES[i % len(self.TEMPLATES)]
            fallback = template.format(
                mii=mii.name, other=other.name, relationship=relationship,
                feature=apartment.feature, location=apartment.location,
            )
            description = self.llm.generate(
                system="You invent one short, open-ended island 'event' (drama, crush, song, or mix-up) for a Tomodachi-Life-style Mii, reflecting its personality and its relationship to another Mii.",
                prompt=(
                    f"Mii: {mii.name} ({mii.role}, traits: {mii.traits})\n"
                    f"Other Mii: {other.name}, relationship: {relationship}\n"
                    f"Apartment: {apartment.name} at {apartment.location} ({apartment.feature})"
                ),
                fallback=fallback,
            )
            events.append(
                Event(
                    event_id=i + 1,
                    description=description,
                    involves_mii=mii.name,
                    other_mii=other.name if other.name != mii.name else None,
                    takes_place_in=apartment.name,
                )
            )
        self._log(f"generated {len(events)} event(s)")
        return events


class SkitWriterAgent(BaseAgent):
    role = "Skit Writer Agent"
    goal = "Given an event and its Mii, write the thought-bubble dialogue and stage directions for that skit."
    backstory = "Produces the skit's 'script' the Director later blocks into gameplay -- the thought-bubble text and stage direction that make an island event feel like a tiny sitcom, voiced in each Mii's own synthesized pattern."

    """
    Input:  an Event from EventCreatorAgent, plus the Mii enriched by
            MiiVoiceAgent (needs .voice_pattern) and MiiAppearanceAgent
            (needs .appearance), and the apartment enriched by
            IslandLayoutAgent (needs .location) and
            ApartmentDesignerAgent (needs .designed).
    Output: Skit consumed by DirectorAgent.
    """

    def run(self, event: Event, miis: List[Mii], apartments: List[Apartment]) -> Skit:
        mii = next((m for m in miis if m.name == event.involves_mii), None)
        apartment = next((a for a in apartments if a.name == event.takes_place_in), None)
        if mii is not None and not mii.voice_pattern:
            raise ValueError(
                f"SkitWriterAgent requires '{mii.name}' to have a voice pattern "
                "-- run MiiVoiceAgent first."
            )
        if mii is not None and not mii.appearance:
            raise ValueError(
                f"SkitWriterAgent requires '{mii.name}' to have an appearance spec "
                "-- run MiiAppearanceAgent first."
            )
        if apartment is not None and not apartment.location:
            raise ValueError(
                f"SkitWriterAgent requires '{apartment.name}' to have an assigned location "
                "-- run IslandLayoutAgent first."
            )
        if apartment is not None and not apartment.designed:
            raise ValueError(
                f"SkitWriterAgent requires '{apartment.name}' to be designed "
                "-- run ApartmentDesignerAgent first."
            )
        fallback_lines = [
            f"INT. {apartment.name.upper() if apartment else 'ISLAND'} - {apartment.location.upper() if apartment else 'DAY'}",
            f"({mii.name if mii else 'A Mii'} looks like: {mii.appearance if mii else 'an island resident'}.)",
            f"({mii.name if mii else 'A Mii'}'s voice: {mii.voice_pattern if mii else 'a chirpy synthesized voice'}.)",
            f"{mii.name if mii else 'MII'}: (thought bubble) \"...huh?!\"",
            f"* {event.description}",
        ]
        skit_text = self.llm.generate(
            system="You write a short Tomodachi-Life-style skit: thought-bubble dialogue and stage directions for one event, reflecting the Mii's voice pattern.",
            prompt=f"Event: {event.description}\nMii: {mii}\nApartment: {apartment}",
            fallback="\n".join(fallback_lines),
        )
        lines = skit_text.split("\n") if skit_text else fallback_lines
        self._log(f"wrote skit for event #{event.event_id} ({len(lines)} lines)")
        return Skit(event_id=event.event_id, lines=lines)


class DirectorAgent(BaseAgent):
    role = "Director Agent"
    goal = "Take the Skit Writer's script and stage it as the animated moment the player actually watches."
    backstory = "This crew's other 'One Wow' agent: converts script into the active gameplay the player sees on the island."

    """
    Input:  the Skit from SkitWriterAgent, the active Event, and
            apartments enriched by IslandLayoutAgent (needs .location,
            used as the physical staging location instead of just the
            apartment's name).
    Output: List[StagedMoment] -- the actual gameplay behavior; this is
            the crew's terminal, player-visible output.
    """

    def run(self, skit: Skit, event: Event, apartments: List[Apartment]) -> List[StagedMoment]:
        if not skit.lines:
            raise ValueError(
                f"DirectorAgent has nothing to stage for event #{event.event_id} "
                "-- SkitWriterAgent returned an empty skit."
            )
        apartment = next((a for a in apartments if a.name == event.takes_place_in), None)
        location = apartment.location if apartment and apartment.location else (event.takes_place_in or "the island")
        staged = [StagedMoment(actor=event.involves_mii, action=f"act out: {event.description}", location=location)]
        if event.other_mii:
            staged.append(StagedMoment(actor=event.other_mii, action="react on cue", location=location))
        staged.append(StagedMoment(actor="Camera", action="pop up the thought bubble and pan in", location=location))
        self._log(f"staged {len(staged)} moment(s) for event #{event.event_id} at {location}")
        return staged


class NewscasterAgent(BaseAgent):
    role = "Newscaster Agent"
    goal = "Recap the day's resolved event as an island news bulletin."
    backstory = (
        "Tomodachi Life closes every day with a news broadcast recapping the island's drama -- "
        "the Newscaster is what turns one staged moment into the headline the whole island "
        "gossips about tomorrow."
    )

    """
    Input:  the staged moments from DirectorAgent and the active Event.
    Output: a NewsBulletin -- this crew's second terminal, player-visible
            output (alongside the staged moments themselves).
    """

    def run(self, staged_moments: List[StagedMoment], event: Event) -> NewsBulletin:
        if not staged_moments:
            raise ValueError(
                f"NewscasterAgent has nothing to report for event #{event.event_id} "
                "-- DirectorAgent returned no staged moments."
            )
        fallback = f"BREAKING: {event.description}"
        headline = self.llm.generate(
            system="You write one punchy Tomodachi-Life-style news-ticker headline recapping this event.",
            prompt=f"Event: {event.description}\nStaged moments: {staged_moments}",
            fallback=fallback,
        )
        self._log(f"filed news bulletin for event #{event.event_id}")
        return NewsBulletin(event_id=event.event_id, headline=headline)


# ---------------------------------------------------------------------------
# Prep-time agents (spun up by the Island Orchestrator)
# ---------------------------------------------------------------------------


class MiiAppearanceAgent(BaseAgent):
    role = "Mii Appearance Agent"
    goal = "Design a Mii's face, hairstyle, and outfit from their personality."
    backstory = "Tomodachi Life's Mii creator is half the fun -- a Mii with no bespoke look reads as a placeholder, not a character."

    """
    Input:  a Mii already enriched by MiiPersonalityAgent (needs .traits).
    Output: an appearance spec, written into mii.appearance so
            SkitWriterAgent can require and use it downstream.
    """

    def run(self, mii: Mii) -> str:
        if not mii.traits:
            raise ValueError(
                f"MiiAppearanceAgent requires '{mii.name}' to carry personality traits "
                "-- run MiiPersonalityAgent first."
            )
        fallback = (
            f"{mii.name}: a {mii.role} with a look reflecting "
            f"{', '.join(mii.traits)} -- face shape, hairstyle, and outfit chosen to read at a glance."
        )
        spec = self.llm.generate(
            system="You write a one-paragraph Mii appearance spec (face, hairstyle, outfit), based on its traits.",
            prompt=f"Mii: {mii}",
            fallback=fallback,
        )
        mii.appearance = spec
        self._log(f"designed appearance for {mii.name}")
        return spec


class ApartmentDesignerAgent(BaseAgent):
    role = "Apartment Designer Agent"
    goal = "Design an apartment or facility and its signature interactive feature."
    backstory = "Every facility on the island earns its place with one memorable interactive feature -- the Apartment Designer is what keeps facilities from being blank rooms."

    """
    Input:  an Apartment with a raw .feature hint.
    Output: an enriched design spec, written back into apartment.feature,
            plus apartment.designed = True so every downstream agent
            (Event Creator, Skit Writer) can require and confirm a
            designed facility, not just the raw seed text.
    """

    def run(self, apartment: Apartment) -> str:
        fallback = f"{apartment.name} ({apartment.kind}): built around {apartment.feature}."
        spec = self.llm.generate(
            system="You write a one-paragraph facility design spec, emphasizing the interactive feature.",
            prompt=f"Apartment: {apartment}",
            fallback=fallback,
        )
        apartment.feature = spec
        apartment.designed = True
        self._log(f"designed apartment {apartment.name}")
        return spec


class IslandLayoutAgent(BaseAgent):
    role = "Island Layout Agent"
    goal = "Place apartments and facilities along the island's streets."
    backstory = "Tomodachi Life's pacing depends on which street a facility sits on -- the same cafe reads differently on Main Street than tucked away on a quiet lane."

    """
    Input:  the list of Apartments/facilities on the island.
    Output: a street-layout narrative, and each apartment is mutated in
            place with a .location, which EventCreator, SkitWriter, and
            DirectorAgent all require.
    """

    ZONES = ["Main Street", "Sunset Row", "Blossom Lane", "Groove Street", "Harborview Walk", "Plaza Corner"]

    def run(self, apartments: List[Apartment]) -> str:
        if not apartments:
            self._log("no apartments yet -> nothing to lay out")
            return "(no apartments yet)"
        for i, apartment in enumerate(apartments):
            apartment.location = self.ZONES[i % len(self.ZONES)]
        names = ", ".join(f"{a.name} ({a.location})" for a in apartments)
        fallback = f"Layout: {names}, arranged along the island's main loop."
        spec = self.llm.generate(
            system="You write a short island-layout description placing the given facilities along their assigned streets.",
            prompt=f"Apartments and streets: {[(a.name, a.location) for a in apartments]}",
            fallback=fallback,
        )
        self._log(f"assigned locations: {[(a.name, a.location) for a in apartments]}")
        return spec


class IslandOrchestrator(BaseAgent):
    role = "Island Orchestrator"
    goal = "Spin up the right prep-time agent for a designer's content request and return its output."
    backstory = "Prompted by the designer with the island content they expect; dispatches to a sub-agent and reports back."

    def __init__(self, llm: LLMClient):
        super().__init__(llm)
        self.voice_agent = MiiVoiceAgent(llm)
        self.appearance_agent = MiiAppearanceAgent(llm)
        self.apartment_agent = ApartmentDesignerAgent(llm)
        self.layout_agent = IslandLayoutAgent(llm)

    def run(self, request_kind: str, payload):
        self._log(f"dispatching '{request_kind}' request")
        if request_kind == "voice":
            return self.voice_agent.run(payload)
        if request_kind == "appearance":
            return self.appearance_agent.run(payload)
        if request_kind == "apartment":
            return self.apartment_agent.run(payload)
        if request_kind == "layout":
            return self.layout_agent.run(payload)
        raise ValueError(f"Unknown island request kind: {request_kind}")
