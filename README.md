# Multi-Agent Game Development Pipeline

This project provides a pipeline runner for multi-agent game development that coordinates agents through iterative design, review, and implementation phases.

## Project Structure

```
multi-agent-game-dev/
├── run.py                   # Main entry point  
├── pipeline_runner.py       # Core pipeline logic
├── tasks/
│   └── game_feature.md      # Example task specification
├── workflow_templates/      # Documentation templates for each phase
├── config/
│   └── agent_configs.py     # Agent role configurations
└── requirements.txt         # Project dependencies
```

## Key Features

- **Iterative workflow** with Design → Review → Implementation phases
- **Multi-agent coordination** through defined roles (designer, reviewer, implementer, tester)
- **Automated documentation generation** for each phase  
- **Flexible configuration** that can support different game development tasks

## Usage

1. Define a goal in `tasks/game_feature.md`
2. Run the pipeline:
```bash
python run.py
```

The system will execute the iterative process through all phases and generate documentation in the `workflow_templates/` directory.

## Pipeline Phases

### Phase 1: Design (Contract Creation)
Creates initial contract with requirements, constraints, and success criteria

### Phase 2: Review  
Evaluates design and provides technical feedback and recommendations  

### Phase 3: Implementation
Executes changes based on feedback and documents the implementation details

## Running the Example

```bash
cd "/mnt/c/Users/N_TAIL_COMP0/Desktop/Code/MultiAgentGameDevelopment/Multi-Agent-Game-Development"
python run.py
```

This will demonstrate a complete multi-agent workflow for implementing a game feature.