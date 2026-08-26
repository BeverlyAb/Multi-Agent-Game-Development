#!/usr/bin/env python3
"""Debug script for Narrative Engine"""
import sys
sys.path.insert(0, '/mnt/c/Users/N_TAIL_COMP0/Desktop/Code/MultiAgentGameDevelopment/Multi-Agent-Game-Development/NarrativeEngine')

from narrative_engine import NarrativeEngine

# Create engine
engine = NarrativeEngine()

# Test one turn
response = engine.generate_response('I enter the crypt')

print("="*60)
print("FULL RESPONSE:")
print("="*60)
print(response)
print("="*60)

# Check where the JSON update starts
if '[UPDATE JSON:' in response:
    json_start = response.find('[UPDATE JSON:')
    print(f"\nJSON start position: {json_start}")
    print(f"JSON text: {response[json_start:json_start+100]}")
else:
    print("\nNo JSON update found in response")

# Check ledger state
print(f"\nCurrent ledger location: {engine.ledger.get('location')}")
print(f"Current ledger health: {engine.ledger.get('health')}")
print(f"Turn count: {engine.turn_count}")

# Test another turn
response2 = engine.generate_response('explore left')
print(f"\n\nTurn 2 - Current ledger location: {engine.ledger.get('location')}")
print(f"Turn 2 - Current ledger health: {engine.ledger.get('health')}")