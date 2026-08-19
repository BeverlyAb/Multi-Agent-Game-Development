# Workflow Cycle: Reviewer and Implementer Agents

## Overview

The Gachō Badi project uses a structured workflow where reviewer and implementer agents work in a defined cycle to manage contracts, ensuring quality control and proper implementation of system changes while maintaining architectural integrity.

## The Contract Lifecycle Process

### 1. Human Initiates Process by Creating New Contract
- Human determines the task or problem requiring resolution 
- Creates new contract directory under `docs/contract/<ID>/`  
- Writes `contract.md` defining Problem, Desired Outcome, Requirements, etc.
- Sets status to `READY FOR REVIEW`

### 2. Reviewer Agent Evaluates Contract
- The Reviewer agent reads `contract.md`
- Runs analysis against project requirements and architecture
- Creates `docs/contract/<ID>/review.md` with findings (P0-P3 severity levels)
- Sets status to `NEEDS HUMAN INPUT` if issues remain open, or `READY FOR APPROVAL` if all resolved

### 3. Human Resolves Issues in Contract
- Human reviews the review findings and addresses them
- Either updates contract parameters or makes decisions on ambiguities  
- Updates status appropriately (often back to `READY FOR REVIEW`)

### 4. Implementer Agent Handles Implementation
- The Implementer agent reads the final contract version
- Makes source code changes, creates test implementations, updates documentation 
- Writes `docs/contract/<ID>/response.md` documenting what was done
- Sets status to `READY FOR APPROVAL`

### 5. Final Review and Closure
- Reviewer re-runs evaluation to verify implementation addresses all findings
- If satisfied with resolved issues, sets status to `READY FOR APPROVAL`
- Human performs final verification then sets status to `CLOSED`

## Agent Responsibilities

### Reviewer Agent
- Evaluates contract quality, feasibility, and architectural alignment 
- Identifies problems (P0/P1/P2/F) in requirements or implementation approaches
- Creates detailed review documentation
- Sets appropriate contract status based on findings

### Implementer Agent  
- Makes code changes to fix issues or implement features
- Creates/updates tests and documentation
- Follows repository coding rules in AGENTS.md exactly
- Writes comprehensive response documentation of what was implemented

## Key Constraints

1. **Status Determination**: Each status is determined by exactly one actor (human for DRAFT/CLOSED, agents for middle statuses)
2. **Non-Power Cycling**: Agents cannot move a contract to `READY FOR REVIEW` directly - they only work from a status that's already been set to `READY FOR REVIEW`
3. **No Force Pushes**: Git changes follow strict rules - no force pushing or rewriting history
4. **Documentation Required**: Every task must produce final documentation in the appropriate contract directories  

## Example Cycle Using AUTH-004

1. **Human** creates `docs/contract/AUTH-004/contract.md` describing issue with "Grab near" tasks  
2. **Reviewer agent** analyzes the contract and produces `docs/contract/AUTH-004/review.md`
3. **Human resolves** issues identified in review (if any)
4. **Implementer agent** implements solution by documenting system improvements
5. **Reviewer re-runs** evaluation to verify all findings addressed  
6. **Human closes** the contract after final verification

## Key Design Principles

- **Agent Independence**: Reviewers and implementers operate independently on same contract data, with separate responsibility layers
- **Structured Documentation**: All decisions and changes must be documented permanently in the repository
- **Architectural Integrity**: Code changes follow strict coding rules to maintain system stability 
- **Quality Control**: Multiple validation points ensure implementation meets requirements