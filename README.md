# MultiAgent Game Development

# Gachō Badi (Goose Buddy)

**GDD Draft #4** — July 30, 2026


> **Revision note:** this draft responds directly to `GDDreview.txt`'s feedback (Game Specificity 2.5/3, Player Experience Clarity 1.5/2.5, Agent Role Clarity 1/2, Technical Feasibility 1/1.5, Presentation 0.75/1). Specifically: the task system is now bounded with real numbers instead of left fuzzy, goose control vs. building placement is disambiguated, the AI Architecture section is restructured so every agent leads with what the player sees before how it works, "One Wow" is now defined, the Scene Orchestrator's dev-time agents are explicitly separated from the six runtime agents instead of blurring into them, a Scope & First Playable Slice section replaces the "no timeline" gap, and the ChatGPT aside is tightened rather than left as a disruptive mid-document note.

## Executive Summary

Tomodachi Life meets Untitled Goose Game to form Gachō Badi. Users build their island of customizable residents and buildings in the presence of a precocious goose. It combines the creation aspect and resident interaction (aka "drama") of Tomodachi Life with the goal/task based gameplay and simple directional maneuverability of Untitled Goose Game — but where Untitled Goose Game's goose causes chaos for its own sake, Gachō Badi's goose is a quiet community-builder. Every task the goose completes nudges residents a little closer together — not only into romance, but into friendships, mended neighborly ties, and a stronger sense of belonging on the island — and the island only reaches harmony once the goose has helped everyone on it connect.

Main game play is to build the island and use the Goose to draw residents and locations together. Unlike Untitled Goose Game, the goose's antics aren't mischief for its own sake — every task the goose completes is really a small act of connection: reuniting old friends, welcoming a newcomer into the group, mending a neighborly falling-out, or nudging two residents toward romance, told through the same indirect, physical-comedy problem solving Untitled Goose Game is known for. Romance is just one thread among many — friendship and a sense of community are just as central to what the goose is building. Tasks will appear as residents and shops or homes are built. The game ends once all available tasks are completed and the island is united.

## Game Mechanics (player-facing actions and loop)

There are two distinct player actions, and they don't overlap: the player directly drives the goose — the same directional buttons and honk/pick up/duck/dash commands are the only way to move or act, for the entire game — and, separately, the player spends credits through a build menu to place new residents and buildings onto the island. The player never directly controls a resident, and never drags a building around by hand; placement is a menu choice, not a physical action.

A lone goose inhabits the island. In this tutorial-like stage, the goose (controlled by the user via directional buttons and interaction commands, e.g. honk, pick up items, duck, dash, etc.) must complete a few simple tasks (e.g. pick up trash, swim at the edge of the island, etc.).

Every task the goose completes contributes to credit. Credits enable the user to create and introduce residents or "actors" and buildings to the island. Notably all residents will have personality (e.g. irritable, friendly, cowardly, etc.) and "roles" (e.g. baker, teacher, gym instructor, etc.). Buildings will have "interactive" architecture that residents and the goose can play with (e.g. gate that can open and close, hose that can spout water, mailbox that can hold mail, etc.).

Tasks are actions that the goose must perform on residents or buildings, framed around bringing residents together rather than causing them trouble. For example, the task can be for the goose to get two residents who've drifted apart to reconnect. This is an open-ended solution, which more often than not, requires an indirect interaction. One possible solution is to grab a memento one resident dropped and return it to them in front of the friend they've lost touch with, giving the two a reason to talk. Another solution is to honk at a resident carrying two coffees so they notice their neighbor sitting alone and offer to share one, warming the resident up to a neighbor they'd drifted from. Note that the availability of tasks is dependent on the residents and architecture available and that most tasks can be completed in any order (i.e. most tasks are non-sequential).

**Scoping the task system concretely:** the island's roster is a fixed, pre-authored list, not an infinite stream — for the first playable slice that's 6 roles (baker, teacher, gym instructor, poet, shopkeeper, gardener) and 6 building types (bakery, school, gym, boutique, mailbox stand, garden shed). Each new resident or building typically opens up 2-4 tasks (roughly one per plausible relationship or building pairing the Task Creator Agent can reach), so a fully-populated island caps out around 30-40 total tasks, not an unbounded number. "All roles and locations unlocked" means every entry on that fixed roster has been placed by the player at least once — it's a checklist with a known length, not a claim that content generation itself runs out (the Task Creator Agent could keep inventing flavor text indefinitely; the roster it draws from can't grow past what's been authored).

The creativity comes from the open-ended solutions and the endless possibilities based on the residents' roles, personalities, relationships, and layout of buildings.

### Game loop

The goose completes tasks based on the available residents and locations. The more tasks they complete, more credits they have and are able to populate the island with more residents and buildings. With more residents and buildings, more tasks appear. The cycle continues between tasks generation and completion, credit gathering, and island expansion.

### Game Completion

Once all roles and locations are unlocked and all tasks are completed, every resident has been brought together by the goose, the island will live in harmony, and the game ends.

## Scope & First Playable Slice

This is a semester project, not a shipped game, so attempting the full runtime pipeline against an open-ended roster from day one isn't realistic — this section exists because an earlier review correctly flagged that the GDD had no timeline or scoping acknowledgment. The first playable slice is a single vertical scenario: one resident archetype (a baker, "Hazel"), one building ("Hazel's Bakery"), and the one task chain needed to reconnect Hazel with a single drifted-apart neighbor. The target is core gameplay — goose movement, one resolvable task, and one screenplay-plus-verb-plan-driven moment — working end to end within 3 weeks. Everything else (additional roles/buildings, extra task variety, visual polish, story or level content) is deliberately deferred until after that core loop is proven, not attempted alongside it.

- **Week 1:** Character Personality Agent and Relationship Agent working for 2 hardcoded residents (Hazel and one drifted-apart neighbor), validated in isolation — no goose gameplay yet.
- **Week 2:** Scene Orchestrator, Character Appearance Agent, Building Designer Agent, and Island Layout Agent wired up for the one building; Task Creator Agent generating the one task from that fixed scenario.
- **Week 3:** Writer Agent, Goose Solution Planner Agent, and Director Agent staging that one task end-to-end in engine, with basic goose movement and honk/grab/duck/dash controls. This is the point core gameplay is playable — a player can move the goose, trigger the task, and watch it resolve.

Everything past week 3 is additive, not load-bearing: the Newscaster Agent, additional roles/buildings, task variety, resident/building aesthetics, and any extra levels or story content get built on top of a core loop that already works, not as a prerequisite for it. If that 3-week core loop isn't fun with one resident and one building, more content won't fix that — so no time is spent on embellishment before that checkpoint.

## AI Architecture

*(what each agent does in the game, described through its effect on gameplay)*

> **Note:** this section was rewritten after building working, tested reference crews for both parent games (a Tomodachi Life crew and an Untitled Goose Game crew — see `../TomodachiLife_Multi_Agent` and `../UntitledGooseGame_Multi_Agent`). Building those surfaced two gaps the original 8-agent list didn't cover — nothing tracked how residents felt about each other, and nothing guaranteed a task was actually solvable with the goose's own moves — so this version folds in the pieces of each reference crew Gachō Badi actually needs, on top of the roles that still held up.

These eleven agents split into two groups that run at different times — an earlier draft blurred this line, so it's explicit now. Six **Runtime Gameplay Agents** generate what the player sees while actually playing; the other five are a **Dev-Time Content Pipeline** a programmer/designer calls when adding a new resident, building, or layout to the fixed roster above, never during play. The Scene Orchestrator and its three sub-agents (Character Appearance, Building Designer, Island Layout) are entirely in that second, build-time group — they report to the Scene Orchestrator, not to the player.

Two of the six runtime agents are marked **"One Wow"** below. That label means a single bad generation from that agent is immediately visible to the player and breaks the island's illusion — a task that makes no sense, or a resident who doesn't react to the goose at all — so these two get first claim on polish and testing budget. The other agents' mistakes are more forgivable because their output gets filtered through a "One Wow" agent before the player ever sees it.

### Runtime Gameplay Agents (run during play)

#### Character Personality Agent
**Player sees:** every resident acting consistently with a defined personality — the same baker who's tuned "excitable" visibly reacts differently to a honk than a "reserved" teacher would.
**How:** takes in the user's input of the actor's movement (scaling from slow to fast), speech (reserved to candid), energy (flat to excited), intelligence (dull to astute) and sets their personality (e.g. sociable and forgiving).

#### Relationship Agent *(new)*
**Player sees:** residents who clearly used to know each other, or clearly don't get along, before the goose ever does anything — two "drifted apart" neighbors visibly avoid each other's buildings; a "close friends" pair are often seen together.
**How:** borrowed from the Tomodachi Life reference crew's Relationship Agent. Reads every resident's personality and tracks how each pair feels about each other (e.g. close friends, drifted apart, friendly rivals, a budding crush) — without this, a task like "these two used to be close" would mean nothing.

#### Task Creator Agent — *"One Wow"*
**Player sees:** the actual to-do list on screen — the tasks that tell the player what the goose is trying to accomplish this session.
**How:** takes in the available roles, buildings, and resident relationships on the island and generates a list of tasks that nudge two or more residents toward connection — friendship and community belonging as much as romance — rather than mischief for its own sake.

#### Goose Solution Planner Agent *(new)*
**Player sees:** nothing directly — it runs before a task is ever shown. Its only visible trace is that every task the player receives is provably solvable, and it's the source of the in-game hint if the player asks for one.
**How:** borrowed from the Untitled Goose Game reference crew's Goose Verb Planner Agent. Given a task, plans at least one valid indirect solution using only the goose's own verbs (honk, grab, pick up, duck, dash, etc.) and never dialogue, since the goose itself never speaks.

#### Writer Agent
**Player sees:** the actual dialogue bubbles and reaction lines residents speak once the goose triggers a task.
**How:** given a set of actors (and their personalities and relationships to each other), generates text based dialogue and actions between them, similar to how a screenplay shows dialogue lines and directional cues.

#### Director Agent — *"One Wow"*
**Player sees:** the moment itself — the resident actually walking over and reacting, following the Writer's dialogue, while the goose performs whatever verb sequence resolves the task. This is the active gameplay the player is watching and controlling.
**How:** takes the output of the Writer Agent (the "screenplay") together with the Goose Solution Planner's verb plan, and controls both the residents (aka actors) and the goose's staged actions to follow them.

#### Newscaster Agent *(new)*
**Player sees:** a short island bulletin or bit of overheard gossip after a task resolves, so the island visibly feels like it remembers what the goose just did.
**How:** borrowed from the Tomodachi Life reference crew's Newscaster Agent — recaps a resolved task as a headline.

### Dev-Time Content Pipeline (runs only when a programmer/designer adds new content — never during play)

#### Scene Orchestrator
**Player sees:** nothing directly — this is purely a build-time tool. It's prompted by the programmer/designer when adding a new resident or building to the fixed roster, and dispatches to whichever of the three sub-agents below matches the request, handing back code and placement instructions.

#### Character Appearance Agent
**Player sees:** what a new resident actually looks like once the designer adds them to the roster.
**How:** plays a role in creating an actor's appearance from their personality.

#### Building Designer Agent
**Player sees:** what a new building's interactive feature does once it's placed on the island — the gate that opens, the hose that sprays.
**How:** plays a role in developing the buildings.

#### Island Layout Agent
**Player sees:** where a new building physically sits on the island map.
**How:** plays a role in developing the appearance of the island.

## Technical Strategy (agent roles, token budget, API constraints)

Token budgets below are rough estimates — I have educational ChatGPT access and used it to project plausible per-agent costs, since I don't have production usage data to base them on yet.

**Constraints and risks:** all runtime agents share a single API account's rate limit, so the Task Creator's batch generation and the Director's staging calls get queued rather than fired in parallel once more than 2-3 tasks are active at once. Individual prompts are kept under roughly 2,000 input tokens specifically so a handful of concurrent agent calls stay well inside a typical 128k-token context window. Cost is also the reason the First Playable Slice above hardcodes 2 residents and 1 building rather than generating a full roster from day one — most of the token budget below is spent validating the pipeline at that small scale before scaling up.

| Agent | Input Budget | Output Budget | Invocation Pattern |
|---|---|---|---|
| Personality Agent | 300–700 | 150–300 | Once during creation or editing |
| Relationship Agent | 400–900 | 150–400 | Once per resident pair, refreshed after major tasks |
| Writer Agent | 800–1,800 | 250–700 | Important interactions |
| Director Agent | 700–1,500 | 300–700 | Major scenes only |
| Task Creator | 1,200–2,500 | 700–1,500 | Batch generation |
| Goose Solution Planner | 900–2,000 | 400–1,000 | Once per task, at generation time |
| Newscaster Agent | 300–700 | 100–300 | After each resolved task |
| Appearance Agent | 300–800 | 100–300 | Character creation |
| Building Designer | 800–1,800 | 300–900 | Building creation |
| Island Layout Agent | 1,000–2,500 | 300–1,000 | Layout changes |
| Scene Orchestrator | 3,000–12,000 | 2,000–8,000 | Development time only |

*Approximate budgets per invocation.*

