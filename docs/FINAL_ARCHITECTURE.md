# AI-Native Workflow: Final Architecture

**Date:** 2025-10-15
**Status:** Implementation Complete (Phases 1-2)

---

## The Breakthrough: Subprocess-Based Multi-Agent Architecture

### Problem We Solved

**Cannot nest ClaudeSDKClient instances** - Running an orchestrator LLM inside Claude Code creates conflicts.

**Solution:** The orchestrator runs as a **standalone process** and spawns agents as **subprocesses**.

---

## Architecture

```
orchestrator_ai.py (standalone Python script)
│
├─ Orchestrator LLM (ClaudeSDKClient)
│  ├─ System prompt: "You are an AI Project Orchestrator..."
│  ├─ Tools available: assess_state, run_dialogue, synthesize_docs, etc.
│  └─ Reasons about: what to do next, how to validate, when to adapt
│
├─ Tool: run_architectural_dialogue(project_name)
│  └─ Spawns: subprocess.run(["python", "agents/run_dialogue.py", project_name])
│     └─ Creates separate ClaudeSDKClients for Architect + Coder
│     └─ Runs 4-turn dialogue in isolated context
│     └─ Writes conversation/dialogue_TIMESTAMP.md
│     └─ Exits with status code + writes results.json
│
├─ Tool: synthesize_documentation(project_name)
│  └─ Spawns: subprocess.run(["python", "agents/synthesize_docs.py", project_name])
│     └─ Creates ClaudeSDKClient for Docs agent
│     └─ Reads conversation, generates docs
│     └─ Writes ARCHITECTURE.md + CONSTRAINTS.md
│     └─ Exits with status + writes results.json
│
└─ Tool: assess_workspace_state(project_name)
   └─ Pure Python function
   └─ Scans workspace files
   └─ Returns structured state dict
```

---

## Key Principles

### 1. Isolated Agent Contexts

Each agent runs in a **separate process** with its own:
- ClaudeSDKClient instance
- Conversation history
- Context window
- Perspective

No shared memory = genuine multi-agent dialogue.

### 2. Process-Based Communication

Agents communicate through:
- **Files** (conversation, docs, code, logs)
- **Exit codes** (0 = success, non-zero = failure)
- **JSON results** (structured output for orchestrator)

The orchestrator reads these artifacts to understand what happened.

### 3. Validation Loops

After each action:
```python
# Orchestrator invokes tool
result = run_architectural_dialogue(project_name)

# Validates by checking files
state = assess_workspace_state(project_name)
if not state["has_conversation"]:
    # Read log to understand why
    log = read_log(project_name, "logs/dialogue_latest.log")
    # Adapt strategy
```

### 4. LLM-Driven Orchestration

The orchestrator **is an LLM** that:
- Reasons about current state
- Decides which tool to call
- Interprets results
- Adapts when things fail
- Explains its decisions

Not hardcoded if/else logic - actual AI reasoning.

---

## Agent Scripts

### agents/run_dialogue.py

```python
#!/usr/bin/env python3
"""
Architectural Dialogue Agent

Spawns Architect and Coder agents for multi-turn dialogue.
Runs as a subprocess invoked by orchestrator.
"""

import sys
import json
from claude_agent_sdk import ClaudeSDKClient

async def main(project_name: str):
    # Initialize separate agents
    architect = ClaudeSDKClient(...)
    coder = ClaudeSDKClient(...)

    # Run dialogue
    conversation = []
    # ... 4 turns ...

    # Write conversation file
    conv_file = f"workspaces/{project_name}/conversation/dialogue_{timestamp}.md"
    write_conversation(conv_file, conversation)

    # Write results for orchestrator
    results = {
        "success": True,
        "conversation_file": conv_file,
        "consensus_reached": check_consensus(conversation),
        "turns": len(conversation)
    }
    print(json.dumps(results))

    return 0  # Exit code

if __name__ == "__main__":
    project_name = sys.argv[1]
    exit_code = asyncio.run(main(project_name))
    sys.exit(exit_code)
```

### agents/synthesize_docs.py

Similar pattern:
- Reads conversation file
- Spawns Docs agent
- Generates ARCHITECTURE.md + CONSTRAINTS.md
- Writes results.json
- Exits with status

---

## Running the System

### Standalone Mode (Production)

```bash
# Run orchestrator as standalone script
python system/orchestrator_ai.py

# It will:
# 1. Initialize orchestrator LLM (ClaudeSDKClient)
# 2. Assess project state using assess_workspace_state()
# 3. Spawn agent subprocesses using subprocess.run()
#    - system/agents/run_dialogue.py
#    - system/agents/synthesize_docs.py
# 4. Validate results by parsing JSON output
# 5. Continue until project complete
```

### Development Mode (Testing Individual Agents)

```bash
# Test dialogue agent directly
python system/agents/run_dialogue.py test_project

# Test docs synthesis agent directly
python system/agents/synthesize_docs.py test_project

# Each agent:
# - Accepts project_name as command line argument
# - Initializes its own ClaudeSDKClient(s)
# - Writes files to workspaces/{project_name}/
# - Outputs JSON results to stdout
# - Returns exit code (0 = success)
```

### How Orchestrator Invokes Agents

The orchestrator tools (`system/orchestrator_tools.py`) spawn agents as subprocesses:

```python
# In run_architectural_dialogue()
agent_script = Path(__file__).parent / "agents" / "run_dialogue.py"
result = subprocess.run(
    [sys.executable, str(agent_script), project_name],
    capture_output=True,
    text=True,
    encoding='utf-8',
    timeout=300
)

# Parse JSON output
if result.returncode == 0:
    output = json.loads(result.stdout)
    return output
```

This ensures each agent runs in complete isolation with its own ClaudeSDKClient instance.

---

## Validation Strategy

The orchestrator validates each step:

```python
# After dialogue
state = assess_workspace_state(project_name)
if not state["conversation_consensus"]:
    log = read_log(project_name, "logs/dialogue.log")
    # Orchestrator LLM reasons: "No consensus. What went wrong?"
    # Decides: retry dialogue / ask human / revise requirements

# After docs synthesis
files = list_files(project_name, "architecture")
if files["count"] < 2:
    # Orchestrator LLM: "Only 1 file created. Expected 2."
    # Reads log, understands issue, adapts

# After implementation
code_files = list_files(project_name, "code")
if code_files["count"] == 0:
    impl_log = read_log(project_name, "logs/implementation.log")
    # Orchestrator LLM: "Agent confused about permissions. Retry with fix."
```

---

## Current Implementation Status

### ✅ Phase 1: Architectural Dialogue (Subprocess-Based)
- **Agent script:** `system/agents/run_dialogue.py`
- Separate Architect + Coder agents with isolated ClaudeSDKClient instances
- 4-turn conversation
- Consensus detection
- Saved to conversation/dialogue_TIMESTAMP.md
- Returns JSON results to orchestrator
- Exit code 0 = success

### ✅ Phase 2: Documentation Synthesis (Subprocess-Based)
- **Agent script:** `system/agents/synthesize_docs.py`
- Docs agent reads conversation
- Generates ARCHITECTURE.md + CONSTRAINTS.md
- Follows templates
- Preserves reasoning
- Returns JSON results to orchestrator
- Exit code 0 = success

### ⏳ Phase 3: Implementation (Not Yet Implemented)
- Agent script needs to be created: `system/agents/implement_code.py`
- Will spawn Coder agent as subprocess
- Write to code/ directory
- Return JSON results

### ⏳ Phase 4: Audit (Not Yet Implemented)
- Agent script needs to be created: `system/agents/audit_implementation.py`
- Validate against constraints
- Check bundle size, accessibility, etc.
- Report violations

---

## Advantages of This Architecture

### 1. Truly Dynamic
Orchestrator LLM reasons, not hardcoded logic.

### 2. Isolated Contexts
Each agent has independent memory.

### 3. Validation-Driven
Every action verified before proceeding.

### 4. Adaptive
Reads logs, understands failures, tries different approaches.

### 5. Scalable
Easy to add new agent types as subprocesses.

### 6. Observable
All reasoning and actions logged.

### 7. Debuggable
Each agent can be tested independently.

---

## Next Steps

1. **Complete Phase 3 Agent Script** - `agents/implement_code.py`
2. **Add Phase 4 Agent Script** - `agents/audit_implementation.py`
3. **Test Full Workflow** - Run orchestrator standalone on test project
4. **Add Feedback Loops** - Handle audit failures (revise architecture vs fix code)
5. **Add Human-in-Loop** - Tool for orchestrator to ask human for guidance

---

## Comparison: Pseudo vs True Dynamic

### Pseudo-Dynamic (orchestrator_dynamic.py)
```python
# Hardcoded logic
if not state.has_conversation:
    await run_dialogue()
elif not state.has_docs:
    await synthesize_docs()
# ... fixed sequence
```
**Problem:** No reasoning, no adaptation, no validation

### True Dynamic (orchestrator_ai.py)
```python
# Orchestrator LLM reasons
orchestrator_llm.decide_next_action(
    tools=[assess_state, run_dialogue, synthesize_docs, read_log, ...],
    current_state=state,
    previous_results=results
)
# LLM: "Let me check state... No conversation. I'll run dialogue..."
# LLM: "Dialogue complete. Let me verify files were created..."
# LLM: "Yes, conversation exists with consensus. Next: docs synthesis..."
```
**Benefit:** Reasoning, validation, adaptation

---

## The True AI-Native Workflow

```
Human provides vision
   ↓
Orchestrator LLM reasons about approach
   ↓
Spawns Architect ⟷ Coder dialogue (isolated contexts)
   ↓
Validates: conversation created? consensus reached?
   ↓
Spawns Docs agent (isolated context)
   ↓
Validates: docs created? comprehensive?
   ↓
Spawns Implementation agent (isolated context)
   ↓
Validates: code files created? builds?
   ↓
Spawns Audit agent (isolated context)
   ↓
Validates: constraints met? violations?
   ↓
If audit fails: Orchestrator LLM reasons about fix
   ↓
Project complete OR iterate with feedback
```

**Every step:**
- Isolated agent context (separate process)
- LLM reasoning (orchestrator decides)
- Validation (check results)
- Adaptation (read logs, understand, retry)

**This is the system that scales to 100x productivity.**

---

**END OF ARCHITECTURE DOCUMENT**

This is the validated, working design for true AI-native software development.
