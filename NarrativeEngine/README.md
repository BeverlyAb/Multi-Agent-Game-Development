# Narrative Engine Prototype

A fully functional Python-based narrative engine for dynamic storytelling in RPG games with persistent state tracking, context-aware responses, and automatic state management. It applied GLM-4.7-Flash as opposed to the frontier Claude models.

## Surprising Feature

In narrative_ledger.json, it did save my turns as "memories", even the ones that were just gibberish. I liked that it reinforced the RAG concept. As a user, I thought the session ended after the 5 turns and it would reset, but having the ledger meant it "saved" my previous gameplay. 

## World Description: The Crypt of Eternal Shadows

An ancient dungeon filled with mysterious secrets, magical artifacts, and dangerous creatures. Players explore interconnected chambers with hidden passages, encountering ancient lore, trapped areas, and potentially hostile beings. The world is designed to react dynamically to player actions, tracking their choices and reputation throughout their journey.

## What the Ledger Tracks

The JSON facts ledger (`narrative_ledger.json`) maintains the current state of the game world:

- **player_name**: Player's name identifier
- **location**: Current dungeon chamber or area
- **health**: Player's current health points
- **inventory**: Items collected during the adventure
- **reputation**: Track of allies and enemies based on player choices
- **story_flags**: Boolean flags marking discovered story points or triggered events
- **encounters**: History of creature and NPC encounters
- **quests**: Active and completed quest objectives
- **memories**: Chronological record of player actions for continuity
- **turn_count**: Number of actions taken by the player


## Technical Implementation

The narrative engine is a complete Python implementation featuring:

- **JSON-based persistent state management** for automatic game state saving
- **Context-aware response generation** that maintains narrative continuity
- **Automatic state updates** through JSON parsing of DM responses
- **Memory tracking** for story consistency and character development
- **Simulation capabilities** for demonstration and testing
- **Clean separation** between narrative generation and game state management

## Key Files

- **narrative_engine.py** - Core engine implementation with simulation logic
- **test_engine.py** - Testing script for interactive sessions
- **debug_engine.py** - Debugging and validation script
- **demo_engine.py** - Full demonstration showcasing all features
- **narrative_ledger.json** - Persistent storage for game state
- **Assignment #8_ Narrative Engine Prototype (Optional).txt** - Original assignment description

## Usage Examples

### Interactive Game Session
```python
from narrative_engine import NarrativeEngine

engine = NarrativeEngine()
while True:
    user_input = input("> ")
    response = engine.generate_response(user_input)
    print(response)
    if user_input.lower() == 'quit':
        break
```

### Demonstration
```bash
python3 demo_engine.py
```

### Testing
```bash
python3 test_engine.py
```

## Engine Features

- **State Initialization**: Creates fresh game state from template
- **Action Parsing**: Identifies player intent from input
- **Narrative Generation**: Creates contextually appropriate responses
- **State Update Parsing**: Extracts and applies JSON state changes from responses
- **Memory Management**: Tracks chronological history of actions
- **Persistence**: Automatically saves state to JSON file
- **Turn Counting**: Tracks progress through the narrative

## Implementation Details

The engine uses a simple yet effective pattern for automatic state updates:

```
[UPDATE JSON: {"location": "corridor_with_runes", "health": 95}]
```

When the AI generates narrative responses, the engine parses these update codes and automatically updates the game state accordingly. This allows for dynamic, responsive storytelling without manual state management.

## Testing Results

The narrative engine has been thoroughly tested and demonstrates:

- ✅ Consistent state management across multiple turns
- ✅ Accurate location and attribute updates
- ✅ Narrative continuity in responses
- ✅ Effective JSON persistence and loading
- ✅ Memory tracking for story consistency
- ✅ Reputation and quest system readiness

## Future Enhancements

Potential improvements for the narrative engine:

- Integration with LLM providers for enhanced narrative generation
- Multi-location world support with navigation systems
- NPC dialogue and interaction systems
- Combat mechanics and damage tracking
- Inventory system with item usage
- Dynamic event system for surprise encounters
- Save/load game functionality
- Multi-player support

## Architecture Notes

The engine is designed with modularity in mind:
- Separate concerns for narrative generation vs. state management
- Clear interfaces for future LLM integration
- Extensible state structure for adding new game mechanics
- Simple file-based persistence for ease of debugging and deployment

## Interesting Design Patterns

- **State-Driven Narrative**: Game state directly influences narrative responses
- **Automatic State Synchronization**: Ledger updates happen seamlessly during play
- **Memory-Based Continuity**: Historical context is stored and applied to responses
- **Hybrid Simulation**: Can simulate LLM responses without external dependencies
