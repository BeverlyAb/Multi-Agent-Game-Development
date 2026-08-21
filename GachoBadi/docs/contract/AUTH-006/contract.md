# Contract: Style Guide Agent Implementation

## Assignment Overview
Implement an automated, self-correcting AI loop (Generator → Evaluator → Refiner) that rigorously enforces the specific aesthetic and narrative rules of Gachō Badi - a community-building game where the goose helps residents reconnect rather than cause mischief.

## Game Context
Gachō Badi follows a cozy, community-building tone where:
- The goose is a quiet community-builder, not a mischievous visitor
- Tasks are about bringing residents together through indirect, physical-comedy problem solving
- Residents have personalities that shape how tasks play out
- Dialogue and interactions are consistent with the game's cozy, low-stakes tone
- Content must be derived entirely from the existing Game Design Document (GDD) and prior assignments

## Style Guide Rules (Derived from GDD)
Based on the GDD's execution requirements, content must follow these three distinct constraint types:

### 1. Tone/Vibe Guidelines
- Content must maintain the game's community-oriented, cozy tone 
- No mischief or chaotic behavior - this is a quiet community-builder not an "untitled goose game" with mischief for its own sake
- Dialogue should be dry and understated rather than overly enthusiastic
- Focus on reuniting friends, mending relationships, and strengthening community bonds

### 2. Vocabulary/Lore Accuracy
- Use specific terms from the GDD: residents who have drifted apart are "drifted apart", not "estranged"
- Reference specific building types like "bakery", "garden shed", "mailbox stand", "school", "gym", "boutique" 
- Characters refer to items based on their actual functionality in the game world
- Use proper role-based terminology when applicable ('teacher', 'baker', 'gardener')
- No invented behavior or terms outside of established Item Interaction schema

### 3. Formatting/Structuring Conventions
- All content must follow existing GDD formatting conventions for dialogue and narrative
- Task descriptions should be concise and directly action-oriented  
- Use a consistent structure for describing relationship states (close friends, drifted apart)
- Reference specific resident backstories from the Relationship Agent when appropriate
- Content must be written as in-game datapad logs or similar game-specific format

## System Components
### Evaluator Agent
Analyzes generator output against style guide rules and returns a SCORE (1-10) + REASON.
- Must evaluate tone consistency, vocabulary accuracy, and formatting compliance
- Output strictly as "SCORE: [X/10]" and "REASON: [detailed explanation of what rules were violated]"
- Cannot intervene in the loop - must only identify violations

### Refiner Agent  
Takes original content and Evaluator's REASON and automatically rewrites content to score 10/10
- Must fix identified violations to match exact aesthetic and narrative standards
- Must not invent new concepts or vocabulary outside what's established 
- Must maintain consistency with existing GDD rules

## Before/After Demonstration Examples
### Example 1: Tone Violation
Before: "The goose excitedly honked at the resident in front of the bakery, who was thrilled to see them!"
After: "The goose honked near the resident at the bakery. The resident looked up and nodded in recognition."

### Example 2: Vocabulary/Lore Inaccuracy  
Before: "The goose dropped a sparkly toy for the resident to find - the resident was surprised!"
After: "The goose dropped a memento at the mailbox stand. The resident picked it up, recognized the sentimental connection, and looked thoughtful."

### Example 3: Formatting/Length Issues
Before: "A huge surprise! The goose grabbed a bundle of old letters from the counter, dropped them right where the resident would find them - everything was just perfect."
After: "The goose retrieved an old letter from the mailbox stand. A resident recognized it as a personal memento and looked up in recognition."

## Pipeline Integration

This Style Guide Agent will run immediately after NPC dialogue generation to ensure all character interactions adhere to the game's cozy, community-centered tone where the goose is a quiet community-builder rather than mischief-maker, with dialogue that reflects the specific vocabularies and personality traits described in the GDD.

## Implementation Status
- [ ] Contract created and reviewed (Status: READY FOR REVIEW)
- [ ] Implementation in progress 
- [ ] Testing completed
- [ ] Final verification run