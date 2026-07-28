"""Eight agents that generate Undertale-style encounter content: monster
personalities, ACT menus, room design, area layout, bullet patterns,
battle dialogue, and turn staging.

Each class mirrors the CrewAI Agent shape (role / goal / backstory / run)
without depending on the crewai package, so this runs anywhere Python 3
runs. Every agent calls self.llm.generate(..., fallback=...) -- when no
API key is configured (the default), the deterministic fallback is what
executes, so the crew always produces output.
"""
from __future__ import annotations

from typing import List

from llm_client import LLMClient
from models import Attack, BattleDials, BattleScript, Monster, Room, TurnAction


class BaseAgent:
    role: str = "Agent"
    goal: str = ""
    backstory: str = ""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def _log(self, message: str) -> None:
        print(f"  [{self.role}] {message}")


# ---------------------------------------------------------------------------
# Battle-loop agents (run every time the player enters an encounter)
# ---------------------------------------------------------------------------


class MonsterPersonalityAgent(BaseAgent):
    role = "Monster Personality Agent"
    goal = "Turn a monster's tuned battle dials into a coherent personality profile."
    backstory = (
        "Reads designer-set aggression/playfulness/sympathy/chattiness dials and names the "
        "personality that falls out of them -- the same slider-to-trait idea that makes every "
        "Undertale encounter feel written, not rolled."
    )

    DIAL_TABLE = {
        "aggression": {"low": "won't throw the first punch", "high": "attacks on sight"},
        "playfulness": {"low": "dead serious", "high": "cracks jokes mid-fight"},
        "sympathy": {"low": "shows no mercy", "high": "visibly hates hurting you"},
        "chattiness": {"low": "silent", "high": "narrates the whole fight"},
    }

    def _bucket(self, value: int) -> str:
        return "high" if value >= 50 else "low"

    def run(self, name: str, role_title: str, dials: BattleDials) -> Monster:
        traits = [
            self.DIAL_TABLE["aggression"][self._bucket(dials.aggression)],
            self.DIAL_TABLE["playfulness"][self._bucket(dials.playfulness)],
            self.DIAL_TABLE["sympathy"][self._bucket(dials.sympathy)],
            self.DIAL_TABLE["chattiness"][self._bucket(dials.chattiness)],
        ]
        fallback = (
            f"{name} the {role_title} {', '.join(traits)}. "
            f"(aggression/playfulness/sympathy/chattiness: "
            f"{dials.aggression}/{dials.playfulness}/{dials.sympathy}/{dials.chattiness})"
        )
        summary = self.llm.generate(
            system="You write a one-sentence battle-personality summary for an Undertale-style monster from dial values.",
            prompt=f"Name: {name}\nRole: {role_title}\nDials: {dials}\nTraits: {traits}",
            fallback=fallback,
        )
        self._log(f"built battle style for {name} -> {traits}")
        return Monster(name=name, role=role_title, dials=dials, traits=traits, battle_style_summary=summary)


class BulletPatternDesignerAgent(BaseAgent):
    role = "Bullet Pattern Designer Agent"
    goal = "Generate the bullet-hell attack patterns each monster throws at the SOUL this encounter."
    backstory = (
        "One of this crew's two 'One Wow' agents: Undertale's whole identity rests on every "
        "monster's bullet pattern reading as an expression of who they are -- Papyrus's blue "
        "attacks you can walk through, Undyne's inescapable spear wall. A generic pattern here "
        "breaks the illusion for the whole fight."
    )

    """
    Input:  monsters enriched by MonsterPersonalityAgent (need .traits),
            rooms enriched by AreaLayoutAgent (need .location).
    Output: List[Attack] consumed by DialogueWriterAgent.
    Removing MonsterPersonalityAgent or AreaLayoutAgent breaks this agent
    outright (raises ValueError below) rather than degrading silently.
    """

    TEMPLATES = [
        "{monster} peppers the box with bones timed to their own dialogue.",
        "{monster} channels {feature} in {location} into a wave of projectiles.",
        "{monster} telegraphs a big attack, then hesitates halfway through.",
        "{monster} turns the SOUL's own color rules against it for one turn.",
        "{monster} unleashes a signature pattern that only makes sense given their personality.",
    ]

    def run(self, monsters: List[Monster], rooms: List[Room]) -> List[Attack]:
        attacks: List[Attack] = []
        if not monsters or not rooms:
            self._log("no monsters/rooms yet -> no attacks available")
            return attacks
        for monster in monsters:
            if not monster.traits:
                raise ValueError(
                    f"BulletPatternDesignerAgent requires '{monster.name}' to carry battle-style traits "
                    "-- run MonsterPersonalityAgent first."
                )
        for room in rooms:
            if not room.location:
                raise ValueError(
                    f"BulletPatternDesignerAgent requires '{room.name}' to have an assigned location "
                    "-- run AreaLayoutAgent first."
                )
        for i, monster in enumerate(monsters):
            room = rooms[i % len(rooms)]
            template = self.TEMPLATES[i % len(self.TEMPLATES)]
            fallback = template.format(monster=monster.name, feature=room.feature, location=room.location)
            description = self.llm.generate(
                system="You invent one short bullet-hell attack pattern for an Undertale-style monster, reflecting its personality.",
                prompt=(
                    f"Monster: {monster.name} ({monster.role}, traits: {monster.traits})\n"
                    f"Room: {room.name} at {room.location} ({room.feature})"
                ),
                fallback=fallback,
            )
            attacks.append(
                Attack(
                    attack_id=i + 1,
                    description=description,
                    performed_by=monster.name,
                    takes_place_in=room.name,
                )
            )
        self._log(f"designed {len(attacks)} attack(s)")
        return attacks


class DialogueWriterAgent(BaseAgent):
    role = "Dialogue Writer Agent"
    goal = "Given an attack and its monster, write the FIGHT/ACT/ITEM/MERCY box dialogue for that turn."
    backstory = (
        "Produces the turn's 'script' the Battle Director later stages -- the speech-bubble text "
        "and flavor line that make an Undertale fight feel like a conversation with a bullet "
        "pattern attached."
    )

    """
    Input:  an Attack from BulletPatternDesignerAgent, plus the monster
            enriched by ActMenuDesignerAgent (needs .act_options) and the
            room enriched by AreaLayoutAgent (needs .location).
    Output: BattleScript consumed by BattleDirectorAgent.
    """

    def run(self, attack: Attack, monsters: List[Monster], rooms: List[Room], route: str = "Neutral") -> BattleScript:
        monster = next((m for m in monsters if m.name == attack.performed_by), None)
        room = next((r for r in rooms if r.name == attack.takes_place_in), None)
        if monster is not None and not monster.act_options:
            raise ValueError(
                f"DialogueWriterAgent requires '{monster.name}' to have ACT options "
                "-- run ActMenuDesignerAgent first."
            )
        if room is not None and not room.location:
            raise ValueError(
                f"DialogueWriterAgent requires '{room.name}' to have an assigned location "
                "-- run AreaLayoutAgent first."
            )
        fallback_lines = [
            f"* {monster.name if monster else 'A monster'} blocks the way in {room.location if room else 'the Underground'}.",
            f"* ACT options: {', '.join(monster.act_options) if monster else 'Check'}.",
            f"{monster.name if monster else 'MONSTER'}: (on the {route} route) \"...you again.\"",
            f"* {attack.description}",
            "* The SOUL flickers red as the battle begins.",
        ]
        script_text = self.llm.generate(
            system="You write short Undertale-style battle-box dialogue and flavor text for one turn.",
            prompt=f"Attack: {attack.description}\nMonster: {monster}\nRoom: {room}\nRoute: {route}",
            fallback="\n".join(fallback_lines),
        )
        lines = script_text.split("\n") if script_text else fallback_lines
        self._log(f"wrote battle script for attack #{attack.attack_id} ({len(lines)} lines)")
        return BattleScript(attack_id=attack.attack_id, lines=lines)


class BattleDirectorAgent(BaseAgent):
    role = "Battle Director Agent"
    goal = "Take the Dialogue Writer's script and stage it as the SOUL box behavior the player actually sees."
    backstory = (
        "This crew's other 'One Wow' agent: converts script + bullet pattern into the live turn "
        "-- box shape, projectile motion, dialogue timing -- that is Undertale's actual gameplay."
    )

    """
    Input:  the BattleScript from DialogueWriterAgent, the active Attack,
            and rooms enriched by AreaLayoutAgent (needs .location, used
            as the physical staging location instead of just the room's
            name).
    Output: List[TurnAction] -- the actual gameplay behavior; this is the
            crew's terminal, player-visible output.
    """

    def run(self, script: BattleScript, attack: Attack, rooms: List[Room]) -> List[TurnAction]:
        if not script.lines:
            raise ValueError(
                f"BattleDirectorAgent has nothing to stage for attack #{attack.attack_id} "
                "-- DialogueWriterAgent returned an empty script."
            )
        room = next((r for r in rooms if r.name == attack.takes_place_in), None)
        location = room.location if room and room.location else (attack.takes_place_in or "the Underground")
        staged = [
            TurnAction(actor=attack.performed_by, action=f"unleash: {attack.description}", location=location),
            TurnAction(actor="SOUL", action="dodge inside the bullet-hell box", location=location),
        ]
        self._log(f"staged {len(staged)} turn action(s) for attack #{attack.attack_id} at {location}")
        return staged


# ---------------------------------------------------------------------------
# Prep-time agents (spun up by the Encounter Orchestrator before a fight)
# ---------------------------------------------------------------------------


class ActMenuDesignerAgent(BaseAgent):
    role = "ACT Menu Designer Agent"
    goal = "Design the monster-specific ACT options (Check, Flirt, Compliment, ...) from its personality."
    backstory = (
        "Undertale's Mercy route runs entirely on ACT being written per-monster, not generic -- "
        "a monster with no bespoke ACT options can't be spared meaningfully."
    )

    """
    Input:  a Monster already enriched by MonsterPersonalityAgent
            (needs .traits).
    Output: a list of ACT options, written into monster.act_options so
            DialogueWriterAgent can require and use it downstream.
    """

    def run(self, monster: Monster) -> List[str]:
        if not monster.traits:
            raise ValueError(
                f"ActMenuDesignerAgent requires '{monster.name}' to carry battle-style traits "
                "-- run MonsterPersonalityAgent first."
            )
        gentle = "visibly hates hurting you" in monster.traits
        playful = "cracks jokes mid-fight" in monster.traits
        fallback = [
            "Check",
            "Compliment" if playful else ("Comfort" if gentle else "Threaten"),
            "Wait" if gentle else "Insult",
        ]
        raw = self.llm.generate(
            system="You list exactly 3 short ACT menu options (comma separated) for an Undertale-style monster, based on its traits.",
            prompt=f"Monster: {monster}",
            fallback=", ".join(fallback),
        )
        options = [opt.strip() for opt in raw.replace("\n", ",").split(",") if opt.strip()] or fallback
        monster.act_options = options
        self._log(f"designed ACT menu for {monster.name}: {options}")
        return options


class RoomDesignerAgent(BaseAgent):
    role = "Room Designer Agent"
    goal = "Design a room and its environmental feature (puzzle, hazard, or set piece)."
    backstory = "Every screen of the Underground teaches or twists a mechanic -- the Room Designer is what keeps rooms from being blank arenas."

    """
    Input:  a Room with a raw .feature hint.
    Output: an enriched design spec, written back into room.feature so
            every downstream agent (Bullet Pattern Designer, Dialogue
            Writer) reads the designed version, not the raw seed text.
    """

    def run(self, room: Room) -> str:
        fallback = f"{room.name} ({room.kind}): built around {room.feature}."
        spec = self.llm.generate(
            system="You write a one-paragraph room design spec, emphasizing the environmental feature.",
            prompt=f"Room: {room}",
            fallback=fallback,
        )
        room.feature = spec
        self._log(f"designed room {room.name}")
        return spec


class AreaLayoutAgent(BaseAgent):
    role = "Area Layout Agent"
    goal = "Place rooms along the Underground's route from the Ruins to New Home."
    backstory = "Undertale's pacing depends on which area a room sits in -- the same puzzle reads differently in Snowdin than in Hotland."

    """
    Input:  the list of Rooms in this encounter set.
    Output: a route narrative, and each room is mutated in place with a
            .location, which BulletPatternDesigner, DialogueWriter, and
            BattleDirector all require.
    """

    ZONES = ["Ruins", "Snowdin Forest", "Waterfall", "Hotland", "CORE", "New Home"]

    def run(self, rooms: List[Room]) -> str:
        if not rooms:
            self._log("no rooms yet -> nothing to lay out")
            return "(no rooms yet)"
        for i, room in enumerate(rooms):
            room.location = self.ZONES[i % len(self.ZONES)]
        names = ", ".join(f"{r.name} ({r.location})" for r in rooms)
        fallback = f"Route: {names}, following the path from the Ruins down to New Home."
        spec = self.llm.generate(
            system="You write a short area-layout description placing the given rooms along the Underground's route.",
            prompt=f"Rooms and zones: {[(r.name, r.location) for r in rooms]}",
            fallback=fallback,
        )
        self._log(f"assigned locations: {[(r.name, r.location) for r in rooms]}")
        return spec


class EncounterOrchestrator(BaseAgent):
    role = "Encounter Orchestrator"
    goal = "Spin up the right prep-time agent for a designer's content request and return its output."
    backstory = "Prompted by the designer with the encounter they expect; dispatches to a sub-agent and reports back."

    def __init__(self, llm: LLMClient):
        super().__init__(llm)
        self.act_menu_agent = ActMenuDesignerAgent(llm)
        self.room_agent = RoomDesignerAgent(llm)
        self.layout_agent = AreaLayoutAgent(llm)

    def run(self, request_kind: str, payload):
        self._log(f"dispatching '{request_kind}' request")
        if request_kind == "act_menu":
            return self.act_menu_agent.run(payload)
        if request_kind == "room":
            return self.room_agent.run(payload)
        if request_kind == "layout":
            return self.layout_agent.run(payload)
        raise ValueError(f"Unknown encounter request kind: {request_kind}")
