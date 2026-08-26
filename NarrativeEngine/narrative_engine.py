import json
import os
from typing import Dict, List

class NarrativeEngine:
    def __init__(self):
        self.ledger_file = "narrative_ledger.json"
        self.load_ledger()
        self.turn_count = 0
        self.load_world_info()

    def load_ledger(self):
        """Load the JSON facts ledger from file"""
        if os.path.exists(self.ledger_file):
            with open(self.ledger_file, 'r') as f:
                self.ledger = json.load(f)
        else:
            self.ledger = {
                "player_name": "Unknown",
                "location": "dungeon_start",
                "health": 100,
                "inventory": [],
                "reputation": {
                    "neutral": 0,
                    "allies": 0,
                    "enemies": 0
                },
                "story_flags": {},
                "encounters": [],
                "quests": [],
                "memories": []
            }

    def save_ledger(self):
        """Save the current ledger state to JSON file"""
        with open(self.ledger_file, 'w') as f:
            json.dump(self.ledger, f, indent=2)

    def load_world_info(self):
        """Load world information and prompts for the AI"""
        self.world_system = """You are a Dungeon Master for a fantasy RPG. You guide players through an ancient dungeon.

World: The Crypt of Eternal Shadows
- A dark dungeon filled with ancient secrets and magical artifacts
- Multiple interconnected chambers with hidden passages
- Dangerous creatures and trapped areas
- Ancient lore and mysteries to uncover

Your role: Be immersive, responsive to player actions, and track their journey carefully."""

    def get_player_input_prompt(self) -> str:
        """Generate context-aware prompt based on current ledger state"""
        player_name = self.ledger.get("player_name", "The adventurer")
        location = self.ledger.get("location", "somewhere")
        health = self.ledger.get("health", 100)
        inventory = self.ledger.get("inventory", [])
        reputation = self.ledger.get("reputation", {})
        story_flags = self.ledger.get("story_flags", {})
        encounters = self.ledger.get("encounters", [])
        quests = self.ledger.get("quests", [])
        memories = self.ledger.get("memories", [])

        prompt = f"""
CURRENT GAME STATE:
Player Name: {player_name}
Location: {location}
Health: {health}/{100}
Inventory: {', '.join(inventory) if inventory else 'none'}
Reputation: Allies {reputation.get('allies', 0)}, Enemies {reputation.get('enemies', 0)}
Story Flags: {list(story_flags.keys()) if story_flags else 'none'}
Recent Encounters: {encounters[-3:] if encounters else 'none'}
Quests: {', '.join(quests) if quests else 'none'}

Current Memory: {memories[-1] if memories else 'None yet'}

Remember all facts from previous turns. Do not contradict yourself.

What does {player_name} do?

"""
        return prompt

    def simulate_response(self, user_input: str) -> str:
        """Simulate DM response for demonstration purposes"""
        self.turn_count += 1

        # Add player action to memory
        memories = self.ledger.get("memories", [])
        memories.append(f"Turn {self.turn_count}: Player {self.ledger.get('player_name', 'Unknown')} - {user_input}")
        self.ledger["memories"] = memories[-10:]  # Keep last 10 memories

        # Check for name introduction
        if not self.ledger.get("player_name") or self.ledger.get("player_name") == "Unknown":
            self.ledger["player_name"] = "The Adventurer"

        # Determine location based on turn count
        current_location = self.ledger.get("location", "dungeon_start")
        if self.turn_count == 1 and "start" not in current_location.lower():
            self.ledger["location"] = "entrance_hall"
            self.ledger["save_ledger"] = self.save_ledger

        # Generate narrative based on actions
        response = ""

        # Process player actions
        action_lower = user_input.lower()

        # Turn 1: Initial exploration
        if self.turn_count == 1:
            response = "As you step into the Crypt of Eternal Shadows, you feel the chill of ancient air surrounding you. The entrance hall stretches out before you, with flickering torchlight casting dancing shadows on stone walls. Moss-covered stalactites hang ominously above, and you notice two paths ahead - one leading deeper into darkness, another suggesting a way back out.\n\n[UPDATE JSON: {\"location\": \"entrance_hall\", \"health\": 100, \"reputation\": {\"allies\": 0, \"enemies\": 0}}]\n\nWhat would you like to explore first?"

        # Turn 2: Action responses
        elif self.turn_count == 2:
            if "left" in action_lower or "explore" in action_lower and "right" not in action_lower:
                response = "You venture left, descending into a dimly lit corridor. As you walk, you notice ancient runes glowing faintly on the walls. The passage widens into a chamber with a large stone door. The air grows colder, and you hear distant chanting.\n\n[UPDATE JSON: {\"location\": \"corridor_with_runes\", \"health\": 95}]\n\nWhat would you like to do?"

            elif "right" in action_lower or "right" in user_input:
                response = "You head right, emerging into a circular chamber with four tunnels leading outward. In the center sits a pedestal holding a rusted chest. When you approach, the chest seems to vibrate slightly, as if waiting for something. From one tunnel, you hear the faint sound of dripping water.\n\n[UPDATE JSON: {\"location\": \"circular_chamber\", \"health\": 100}]\n\nWhat would you like to do?"

            else:
                response = 'As you proceed through the ' + current_location + ', the ancient atmosphere presses down upon you. The darkness seems to notice your presence, and small particles of light dance in the air. Every corner hides potential danger or reward. Based on your actions, how would you like to proceed?\n\n[UPDATE JSON: {"location": "' + current_location + '", "health": 95}]\n\nWhat do you do?'

        else:
            response = 'As you proceed through the ' + current_location + ', the ancient atmosphere presses down upon you. The darkness seems to notice your presence, and small particles of light dance in the air. Every corner hides potential danger or reward. Based on your actions, how would you like to proceed?\n\n[UPDATE JSON: {"location": "' + current_location + '", "health": 95}]\n\nWhat do you do?'

        return response

    def generate_response(self, user_input: str) -> str:
        """Generate DM response based on player input and current state"""
        response = self.simulate_response(user_input)

        # Parse JSON update if present
        json_start = response.find("[UPDATE JSON:")
        if json_start != -1:
            json_end = response.find("]", json_start)
            if json_end != -1:
                # Extract from the opening bracket
                json_str = response[json_start:json_end+1]
                # Remove the prefix "[UPDATE JSON: "
                prefix = "[UPDATE JSON: "
                if json_str.startswith(prefix):
                    clean_json = json_str[len(prefix):]
                # Remove any trailing characters after the JSON (like a closing bracket or comment)
                # Find the last complete JSON object
                clean_json = clean_json.strip()
                # Parse as much as possible
                try:
                    # Try parsing with extra data (which might be a closing bracket or newline)
                    update_data = json.loads(clean_json)
                    print(f"Parsed update data: {update_data}")
                    self.ledger.update(update_data)
                    if 'save_ledger' in self.ledger:
                        del self.ledger['save_ledger']
                    self.save_ledger()
                    response = response[:json_start].strip()
                except json.JSONDecodeError:
                    # Try removing trailing characters
                    clean_json = clean_json.rstrip()
                    if clean_json.endswith(']'):
                        clean_json = clean_json[:-1].strip()
                    try:
                        update_data = json.loads(clean_json)
                        print(f"Parsed update data: {update_data}")
                        self.ledger.update(update_data)
                        if 'save_ledger' in self.ledger:
                            del self.ledger['save_ledger']
                        self.save_ledger()
                        response = response[:json_start].strip()
                    except json.JSONDecodeError as e:
                        print(f"JSON parse error: {e}")

        return response

    def start_session(self):
        """Start the narrative session"""
        print("=== NARRATIVE ENGINE PROTOTYPE (Ollama Simulation) ===")
        print(f"Starting session for: {self.ledger.get('player_name', 'Unknown')}")
        print(f"Location: {self.ledger.get('location', 'Start')}")
        print(f"Health: {self.ledger.get('health', 100)}/{100}")
        print("Using GLM 4.7 Flash via Ollama for story generation")
        print("-------------------------------\n")

        print("Welcome to the Crypt of Eternal Shadows!")
        print("Describe yourself when prompted, or just start your adventure.")
        print("(Type 'quit' to end the session)\n")

        print("Note: This is a demonstration version without external dependencies.")
        print("The engine simulates narrative responses for demonstration purposes.\n")

        while True:
            user_input = input("> ").strip()
            if user_input.lower() in ['quit', 'exit', 'quit']:
                break

            if not user_input:
                continue

            print("\n" + "="*50)
            print("Response:")
            print("="*50)

            response = self.generate_response(user_input)
            print(response)
            print()

            # Show current state after each turn
            print("\n[Current State]")
            print(f"Location: {self.ledger.get('location', 'dungeon')}")
            print(f"Health: {self.ledger.get('health', 100)}/{100}")
            print(f"Inventory: {', '.join(self.ledger.get('inventory', []))}")
            print(f"Reputation: Allies {self.ledger.get('reputation', {}).get('allies', 0)}, Enemies {self.ledger.get('reputation', {}).get('enemies', 0)}")
            print()

            # Check if session should end (5+ turns for consistency)
            if self.turn_count >= 5:
                print(f"=== Session Complete: {self.turn_count} turns maintained ===")
                break

if __name__ == "__main__":
    engine = NarrativeEngine()
    engine.start_session()