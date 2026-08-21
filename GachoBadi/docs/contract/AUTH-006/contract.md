# Contract: Style Guide Agent Implementation

## Assignment Overview
Implement an automated, self-correcting AI loop (Generator → Evaluator → Refiner) that rigorously enforces the specific aesthetic and narrative rules of Gachō Badi - a community-building game where the goose helps residents reconnect rather than cause mischief.

## Game Context
Gachō Badi follows a cozy, community-building tone where:
- The goose is a quiet community-builder, not a mischievous visitor (gdd.txt: "not mischief for its own sake ... quiet community-builder")
- Tasks are about bringing residents together through indirect, physical-comedy problem solving that is consistent with GDD character personalities
- Residents have distinct personalities that shape how tasks play out, e.g., "reserved and cowardly" residents need gentle solutions (gdd.txt: "personality isn't flavor text sitting on top of a task")
- Dialogue and interactions are consistent with the game's cozy, low-stakes tone and specific character backstories
- Content must be derived entirely from the existing Game Design Document (GDD) and prior assignments

## Style Guide Rules (Derived from GDD)
Based on the GDD's execution requirements, content must follow these three distinct constraint types:

### 1. Tone/Vibe Guidelines
- Content must maintain the game's community-oriented, cozy tone 
- No mischief or chaotic behavior - this is a quiet community-builder not an "untitled goose game" with mischief for its own sake
- Dialogue should be dry and understated rather than overly enthusiastic (gdd.txt: "characters must refer to magic as 'The Weave' and tech as 'Rust'" would be too enthusiastic) 
- Focus on reuniting friends, mending relationships, and strengthening community bonds
- Reference specific resident personalities when applicable (e.g., "a reserved baker might react differently than an excitable teacher")

### 2. Vocabulary/Lore Accuracy
- Use specific terms from the GDD: residents who have drifted apart are "drifted apart", not "estranged"
- Reference specific building types like "bakery", "garden shed", "mailbox stand", "school", "gym", "boutique" 
- Characters refer to items based on their actual functionality in the game world (gdd.txt: "characters must refer to magic as 'The Weave' and tech as 'Rust'" is for a different game)
- Use role-based terminology when applicable: 'teacher', 'baker', 'gardener' (based on gdd.txt 6 roles for residents)
- No invented behavior or terms outside of established Item Interaction schema
- Specific examples from GDD:
  - Resident: "Hazel the baker" (gdd.txt: "a baker is usually seen near the bakery")
  - Location: "Hazel's Bakery" 
  - Building interaction: "the hose can spray water, which makes a resident react with irritation or laughter" (in Item Interaction schema)

### 3. Formatting/Structuring Conventions
- All content must follow existing GDD formatting conventions for dialogue and narrative
- Task descriptions should be concise and directly action-oriented  
- Use a consistent structure for describing relationship states: close friends, drifted apart, friendly rivals, a budding crush (gdd.txt: "Relationship Agent generates both a pairwise social state")
- Reference specific resident backstories from the Relationship Agent when appropriate
- Content must be written as in-game datapad logs or similar game-specific format
- Specific formatting examples: 
  - Resident: "a reserved baker" with personality traits that inform interaction style
  - Task premise: "'drifted apart' relationship state between two residents
  - Dialogue structure should be consistent with "dry and understated" tone

## System Components

### Evaluator Agent
Analyzes generator output against style guide rules and returns a SCORE (1-10) + REASON.
- Must evaluate tone consistency, vocabulary accuracy, and formatting compliance based on GDD-specific examples
- Output strictly as "SCORE: [X/10]" and "REASON: [detailed explanation of what rules were violated]"
- Cannot intervene in the loop - must only identify violations  
- Prompt example: "Review the following text. Grade it on a scale of 1-10 based on these GDD rules about tone, specific vocabulary, and formatting conventions (refer to GDD sections for examples). Output your response strictly as SCORE: [X/10] and REASON: [Your detailed explanation of what rules were violated]."

### Refiner Agent  
Takes original content and Evaluator's REASON and automatically rewrites content to score 10/10
- Must fix identified violations to match exact aesthetic and narrative standards
- Must not invent new concepts or vocabulary outside what's established 
- Must maintain consistency with existing GDD rules
- Prompt example: "Take the original text and the Evaluator's REASON, and rewrite the text so that it scores a perfect 10/10 on the GDD style guide. Focus on maintaining the community-oriented tone, using correct character-specific vocabulary, and following GDD formatting conventions."

## Before/After Demonstration Examples
Demonstrations using actual content generated for your game using the existing workflow:

### Example 1: Tone Violation (from NPC dialogue generation)
Before: "The goose loudly honked at Hazel and she jumped in surprise! 'Oh my goodness - you startled me!' she exclaimed with enthusiasm."
After: "The goose honked near Hazel by the bakery. She looked up, recognized the goose, and gave a small nod in acknowledgment."

### Example 2: Vocabulary/Lore Inaccuracy (from Item Interaction usage)  
Before: "The goose picked up an old toy from the mailbox and dropped it where the resident would find it - she was so surprised!"
After: "The goose retrieved a personal letter from Hazel's mailbox stand. A resident recognized it as a sentimental connection and looked thoughtful."

### Example 3: Formatting/Length Issues (from Task Creator)
Before: "Wow! The goose grabbed a bundle of old letters from the counter, dropped them right where the resident would find them - everything was just perfect."
After: "The goose retrieved an old letter from the mailbox stand. A resident recognized it as a personal memento and looked up in recognition."

## Pipeline Integration

This Style Guide Agent will run immediately after NPC Dialogue Agent execution to ensure all character dialogue adheres to the game's cozy, community-centered tone where the goose is a quiet community-builder rather than mischief-maker, with dialogue that reflects the specific vocabularies and personality traits described in the GDD, and maintains proper relationship state references from the Relationship Agent.

## Implementation Status
- [x] Contract created and reviewed (Status: READY FOR REVIEW)
- [ ] Implementation in progress 
- [ ] Testing completed
- [ ] Final verification run