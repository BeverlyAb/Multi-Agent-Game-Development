# Contract: Workflow Integration for Iterative Review and Implementation

**ID:** AUTH-005  
**Status:** READY FOR REVIEW

## Problem

The current multi-agent system operates in a single-cycle contract workflow where reviewer and implementer agents work on individual contracts sequentially. There is no integrated iterative mechanism to allow continuous refinement of tasks based on constraints, time limits, or convergence criteria. This prevents the system from dynamically adapting to complex requirements that may need multiple iterations to fully resolve.

## Desired Outcome

Implement an integrated workflow mechanism that allows reviewer and implementer agents to iterate continuously until one of the following conditions is met:
- Set number of attempts/iterations reached
- Time duration limit exceeded  
- Task convergence achieved (measurable improvement in task quality)
- Specific convergence criteria defined by constraints

## Requirements

### 1. **Iterative Workflow Framework**
- Enable continuous cycles of review -> implementation -> re-review
- Support configurable termination conditions (iterations, time, convergence)
- Maintain all contract documentation throughout iterations  
- Preserve agent roles while enabling iterative refinement

### 2. **Constraint-based Termination**
- Allow human operator to specify constraints that define when to stop iterations
- Support time-based limits (e.g., 30 minutes max run time)
- Support attempt-based limits (e.g., maximum 5 cycles)
- Support convergence-based termination (e.g., quality threshold reached)
- **Termination Priority:** Time limits take precedence over iteration count, which takes precedence over convergence criteria
- Each iteration must complete successfully before termination is evaluated

### 3. **Pipeline Command Interface**
- Create CLI command interface for initiating iterative workflows with syntax:
  ```
  python3 workflow/cli.py --contract <ID> [options]
  Options:
    --max-iterations <N>   Maximum number of cycles (default: 5)
    --duration <SECONDS>   Maximum time in seconds (default: 1800)
    --convergence-threshold <N>   Quality improvement threshold (0-100, default: 90)
    --output <PATH>        Output directory for logs and state
  ```
- Accept configuration parameters for:
  - Maximum iterations
  - Time duration limits  
  - Convergence criteria thresholds
  - Constraint specifications
- Provide real-time feedback during execution showing:
  - Current iteration number
  - Elapsed time
  - Current convergence score
  - Pending actions/items

### 4. **Workflow Persistence**
- Maintain contract state throughout iterations
- Preserve historical findings, responses, and documentation  
- Store execution logs for debugging/review purposes
- Ensure all contracts remain accessible during multi-cycle operation
- **State Recovery:** On process interruption, system must save current iteration state to allow resumption
- **Failure Handling:** Failed iterations trigger retries with same parameters unless max attempts exceeded

### 5. **Convergence Metrics**
- Define measurable quality indicators for task improvement
- Track convergence metrics across iterations (e.g., finding count reduction, quality score progression)
- Calculate convergence score as composite of:
  - Finding count reduction percentage
  - Constraint compliance improvement
  - Code quality metrics (if applicable)
- Use convergence score to determine if iteration can terminate early

## Constraints

### Technical  
- **Scope:** Extend `workflow/` directory functionality to support iterative execution
- **Dependencies:** No additional dependencies required beyond existing framework
- **API Compatibility:** Must preserve and extend existing agent interfaces 
- **Behavioral Rules:** Follow repository coding rules in `AGENTS.md`

### Process
- **Agent Roles:** Reviewer and implementer agents should maintain distinct roles throughout iterations  
- **Contract Integrity:** All contracts must remain valid at each stage of iteration
- **Human Oversight:** Human operator retains final control over workflow termination
- **Documentation Standard:** All iterations must produce complete contract documentation

## Acceptance Criteria

- [ ] Iterative workflow system supports configurable termination conditions
- [ ] Pipeline CLI accepts configuration parameters for constraints (--max-iterations, --duration, --convergence-threshold, --output)
- [ ] CLI provides real-time feedback showing iteration progress, elapsed time, convergence score
- [ ] System maintains all contract state during multi-cycle operation
- [ ] Agents properly execute their roles within iterative contexts
- [ ] Historical execution logs and documentation preserved throughout process
- [ ] State recovery works after process interruption
- [ ] Failed iterations trigger retries with same parameters
- [ ] All verification checks pass without functional regressions

## Ownership

### Human  
- Owns contract directory, `Status`, sets final `CLOSED` status, defines constraints for iterative workflows.

### Reviewer 
- Executes reviews and creates `docs/contract/<ID>/review.md` within iterative contexts.
- Identifies convergence criteria during iterations. 

### Implementer 
- Executes implementations and creates `docs/contract/<ID>/response.md` within iterative contexts.
- Makes code changes to improve convergence toward defined constraints.

### AGENTS.md
- Defines repository-wide rules and governance, modified only with human approval.

## Implementation Approach

The solution will build upon the existing workflow infrastructure in `workflow/` directory to support iterative execution while maintaining all existing functionality. The key elements include:

1. **Workflow Controller**: Creates central control structure for managing iterative cycles
2. **Constraint Engine**: Processes termination conditions and convergence metrics  
3. **CLI Interface**: Enables human operator to specify constraints and initiate iterations
4. **State Management**: Preserves contract state and documentation during multi-cycle operation
5. **Error Handling**: Manages iteration failures and retries

This approach extends the current capabilities without breaking existing functionality, leveraging the established contract lifecycle patterns already defined in `docs/workflow-lifecycle.md`.