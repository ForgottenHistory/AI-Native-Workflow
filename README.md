# AI-Native Workflow System

A revolutionary approach to software development using conversational multi-agent AI systems.

## Core Concept

**Traditional AI development:** Linear (prompt → output)
**AI-native development:** **Conversational** (dialogue → understanding → output)

This system uses multi-agent dialogue between specialized AI agents (Architect, Coder, Docs, Audit) to produce better software through iterative reasoning and crystallized documentation.

## Architecture

### Three-Layer System

1. **CONVERSATION Layer** (Reasoning)
   - Agents explore options through dialogue
   - Challenge assumptions and surface knowledge
   - Reach consensus through iteration

2. **DOCUMENTATION Layer** (Crystallization)
   - Conversation synthesized into structured artifacts
   - Architecture docs, constraints, decisions, rationale
   - Single source of truth for all agents

3. **IMPLEMENTATION Layer** (Execution)
   - Build with full context from conversation + docs
   - Autonomous implementation with constraint validation
   - Audit loops ensure compliance

### Agent Roles

- **Architect Agent**: Proposes tech stacks, makes architectural decisions, defines constraints
- **Coder Agent**: Evaluates feasibility, implements code, challenges over-engineering
- **Docs Agent**: Synthesizes conversations into structured documentation
- **Audit Agent**: Validates constraints, checks consistency, flags violations

All agents communicate through documentation - no direct coupling.

## Project Structure

```
AI-Native-Workflow/
├── docs/                          # Methodology documentation
│   ├── ai_architect_system.md     # Full system specification
│   ├── multi_agent_prototype_guide.md
│   ├── AGENT_ROLES.md
│   └── PROTOTYPE_STATUS.md        # Current implementation status
│
├── system/                        # The workflow engine (reusable)
│   ├── agents/                    # Agent definitions
│   ├── templates/                 # Document templates
│   │   ├── ARCHITECTURE_TEMPLATE.md
│   │   └── CONSTRAINTS_TEMPLATE.md
│   ├── orchestrator_stateful.py   # Static workflow (Phase 1-3 validated)
│   └── utils/                     # Shared utilities
│
├── tests/                         # Test cases
│   ├── test_project.md
│   ├── test_docs_agent.py
│   └── test_implementation.py
│
└── workspaces/                    # Generated outputs (gitignored)
    └── [project_name]/
        ├── architecture/          # ARCHITECTURE.md, CONSTRAINTS.md
        ├── code/                  # Generated implementation
        ├── conversation/          # Dialogue transcripts
        └── logs/                  # Implementation logs, audit logs
```

## Current Status

**Phase 1-3: VALIDATED ✅**

- ✅ Architect ⟷ Coder dialogue (measurable quality improvement)
- ✅ Documentation synthesis (ARCHITECTURE.md, CONSTRAINTS.md)
- ✅ Implementation from docs (working code, builds successfully)

**Next: Dynamic Orchestrator** (state-based decision engine, feedback loops)

## Getting Started

### Prerequisites

- Python 3.10+
- Claude Agent SDK (`pip install claude-agent-sdk`)
- Claude Pro/Max subscription (for SDK access)

### Quick Start

```bash
# Clone the repository
git clone <repo-url>
cd AI-Native-Workflow

# Run the static orchestrator (Phase 1-3 validated)
cd system
python orchestrator_stateful.py

# Outputs will be in workspaces/ directory
```

### Testing

```bash
# Test documentation synthesis
python tests/test_docs_agent.py

# Test implementation
python tests/test_implementation.py
```

## Productivity Claims

- **50x** (proven today): Human architect + AI implementer
- **100x** (target 3-5 years): AI architect + human conductor

The system has demonstrated measurable architecture improvements through multi-agent dialogue compared to single-agent approaches.

## Documentation

- **[ai_architect_system.md](docs/ai_architect_system.md)** - Full methodology (1136 lines)
- **[PROTOTYPE_STATUS.md](docs/PROTOTYPE_STATUS.md)** - Implementation status and validation results
- **[AGENT_ROLES.md](docs/AGENT_ROLES.md)** - Four-agent domain model
- **[multi_agent_prototype_guide.md](docs/multi_agent_prototype_guide.md)** - Implementation guide

## Philosophy

**Conversation is not overhead. Conversation IS the product.**

Documentation and code follow naturally from high-quality architectural dialogue. By using LLM strengths (iterative reasoning, knowledge surfacing, trade-off exploration) and human strengths (judgment, taste, vision), we achieve unprecedented development velocity.

## License

[To be determined]

## Contributing

This is an experimental research project. Contributions, feedback, and discussions welcome as we pioneer this new development methodology.

---

**Status:** Prototype Phase
**Last Updated:** 2025-10-15
**Next Milestone:** Dynamic Orchestrator Implementation
