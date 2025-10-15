# AI-Native Workflow: Implementation Status

**Date:** 2025-10-15
**Status:** Subprocess-Based Multi-Agent Architecture Implemented

---

## What's Been Implemented

### 1. Subprocess-Based Agent Architecture ✅

The breakthrough solution to the nested ClaudeSDKClient problem:

**Problem:** Cannot nest ClaudeSDKClient instances - running orchestrator LLM inside Claude Code creates conflicts.

**Solution:** Orchestrator runs as standalone process and spawns agents as subprocesses.

### 2. Standalone Agent Scripts ✅

Created executable agent scripts that run as independent processes:

#### `system/agents/run_dialogue.py`
- Spawns separate Architect and Coder agents
- Each agent has its own ClaudeSDKClient instance
- Runs 4-turn architectural dialogue
- Detects consensus (CONSENSUS + AGREED markers)
- Writes conversation file: `workspaces/{project}/conversation/dialogue_TIMESTAMP.md`
- Returns JSON results to stdout
- Exit code 0 = success, non-zero = failure

#### `system/agents/synthesize_docs.py`
- Spawns Docs agent with its own ClaudeSDKClient
- Reads latest conversation file
- Loads templates from `system/templates/`
- Generates ARCHITECTURE.md and CONSTRAINTS.md
- Writes to `workspaces/{project}/architecture/`
- Returns JSON results to stdout
- Exit code 0 = success, non-zero = failure

### 3. Orchestrator Tools (Updated) ✅

Modified `system/orchestrator_tools.py` to spawn subprocesses:

**Before (nested SDK clients):**
```python
async def run_architectural_dialogue(project_name):
    architect_client = await create_architect_agent()  # ❌ Nested
    coder_client = await create_coder_agent()          # ❌ Nested
    # ... run dialogue ...
```

**After (subprocess-based):**
```python
async def run_architectural_dialogue(project_name):
    agent_script = Path(__file__).parent / "agents" / "run_dialogue.py"
    result = subprocess.run(
        [sys.executable, str(agent_script), project_name],
        capture_output=True,
        text=True,
        timeout=300
    )
    return json.loads(result.stdout)  # ✅ Isolated subprocess
```

### 4. AI Orchestrator (LLM-Driven) ✅

`system/orchestrator_ai.py` implements the orchestrator as an LLM agent:

- Orchestrator itself is a ClaudeSDKClient with system prompt
- Has tools available:
  - `assess_workspace_state()` - Check what files exist
  - `run_architectural_dialogue()` - Spawn dialogue subprocess
  - `synthesize_documentation()` - Spawn docs subprocess
  - `list_files()` - Verify files were created
  - `read_log()` - Understand what happened
  - `read_file()` - Check file contents
- **Current limitation:** Tools called programmatically, not by LLM decision-making yet

### 5. Workspace Organization ✅

Clean separation of workflow engine vs generated outputs:

```
AI-Native-Workflow/
├── docs/                    # Methodology documentation
│   ├── FINAL_ARCHITECTURE.md
│   ├── AI_ORCHESTRATOR_DESIGN.md
│   └── IMPLEMENTATION_STATUS.md (this file)
├── system/                  # Workflow engine
│   ├── orchestrator_ai.py
│   ├── orchestrator_tools.py
│   ├── agents/
│   │   ├── run_dialogue.py
│   │   └── synthesize_docs.py
│   ├── templates/
│   │   ├── ARCHITECTURE_TEMPLATE.md
│   │   └── CONSTRAINTS_TEMPLATE.md
│   └── utils/
│       └── agent_utils.py
└── workspaces/              # Generated outputs (gitignored)
    └── {project_name}/
        ├── requirements.md
        ├── conversation/
        └── architecture/
```

---

## How It Works

### Agent Isolation

Each agent runs in a **separate process**:

```
orchestrator_ai.py (Process 1)
│
├─ Orchestrator LLM (ClaudeSDKClient #1)
│  └─ Tools: assess_state, run_dialogue, synthesize_docs, etc.
│
├─ Invokes: run_dialogue_tool()
│  └─ subprocess.run(["python", "agents/run_dialogue.py", project])
│     └─ Process 2:
│        ├─ Architect LLM (ClaudeSDKClient #2)
│        └─ Coder LLM (ClaudeSDKClient #3)
│        └─ Exits with JSON results
│
├─ Invokes: synthesize_docs_tool()
│  └─ subprocess.run(["python", "agents/synthesize_docs.py", project])
│     └─ Process 3:
│        └─ Docs LLM (ClaudeSDKClient #4)
│        └─ Exits with JSON results
```

No shared memory = genuine multi-agent dialogue.

### Communication Protocol

Agents communicate through:

1. **Files** - Conversation, docs, code, logs written to workspace
2. **Exit Codes** - 0 = success, non-zero = failure
3. **JSON Results** - Structured output to stdout for orchestrator to parse
4. **Logs** - Detailed execution logs for debugging

### Example: Running Dialogue Agent

```bash
# Orchestrator invokes
$ python system/agents/run_dialogue.py test_project

# Agent runs in isolated process
# - Creates separate ClaudeSDKClients for Architect and Coder
# - Runs 4-turn conversation
# - Writes conversation/dialogue_20251015_143022.md

# Outputs JSON to stdout
{
  "success": true,
  "conversation_file": "conversation/dialogue_20251015_143022.md",
  "consensus_reached": true,
  "turns": 4
}

# Exits with code 0
```

Orchestrator parses this JSON to understand what happened.

---

## What's Not Yet Implemented

### Phase 3: Implementation Agent ⏳

Need to create `system/agents/implement_code.py`:

```python
#!/usr/bin/env python3
"""
Implementation Agent - Standalone Subprocess

Generates code from ARCHITECTURE.md and CONSTRAINTS.md.
"""

async def implement_code(project_name: str) -> dict:
    # Read architecture docs
    # Spawn Coder agent
    # Generate code files
    # Write to workspaces/{project}/code/
    # Return JSON results
```

**Challenges to solve:**
- Permission callbacks for Write tool
- Workspace-scoped file creation
- Validation that files were created

### Phase 4: Audit Agent ⏳

Need to create `system/agents/audit_implementation.py`:

```python
#!/usr/bin/env python3
"""
Audit Agent - Standalone Subprocess

Validates implementation against constraints.
"""

async def audit_implementation(project_name: str) -> dict:
    # Read CONSTRAINTS.md
    # Read code files
    # Check bundle size, accessibility, etc.
    # Return violations/warnings
```

### LLM-Driven Tool Selection ⏳

Currently, orchestrator calls tools programmatically:

```python
# Current (programmatic)
if not state["has_conversation"]:
    result = await run_architectural_dialogue(project_name)
```

**Goal:** Orchestrator LLM decides which tools to call:

```python
# Future (LLM-driven)
orchestrator_llm.reason_and_use_tools()
# LLM: "No conversation exists. I'll run dialogue tool."
# LLM: "Dialogue succeeded. Let me verify..."
# LLM: "Files created. Now I'll synthesize docs..."
```

This may require:
- MCP tool integration
- Custom tool registration with Claude SDK
- Function calling configuration

---

## How to Test

### Test Individual Agents

```bash
# Create test project workspace
mkdir -p workspaces/test_project
echo "# Test Project" > workspaces/test_project/requirements.md

# Test dialogue agent
python system/agents/run_dialogue.py test_project

# Test docs agent (after dialogue completes)
python system/agents/synthesize_docs.py test_project
```

### Test Orchestrator (Standalone)

**Note:** Cannot test from within Claude Code due to nested SDK conflicts.

Run as standalone Python script:

```bash
python system/orchestrator_ai.py
```

This will:
1. Initialize orchestrator LLM
2. Create test project
3. Run dialogue subprocess
4. Validate results
5. Run docs subprocess
6. Validate results
7. Log everything to `workspaces/{project}/logs/orchestrator_*.log`

---

## Key Files

| File | Purpose | Status |
|------|---------|--------|
| `system/orchestrator_ai.py` | LLM orchestrator that spawns agents | ✅ Implemented |
| `system/orchestrator_tools.py` | Tools that spawn subprocesses | ✅ Updated |
| `system/agents/run_dialogue.py` | Architect ⟷ Coder dialogue subprocess | ✅ Implemented |
| `system/agents/synthesize_docs.py` | Docs generation subprocess | ✅ Implemented |
| `system/agents/implement_code.py` | Code generation subprocess | ⏳ Not yet |
| `system/agents/audit_implementation.py` | Constraint validation subprocess | ⏳ Not yet |
| `system/utils/agent_utils.py` | Shared utilities for agent creation | ✅ Implemented |
| `docs/FINAL_ARCHITECTURE.md` | Complete architecture documentation | ✅ Updated |

---

## Next Steps

1. **Create `implement_code.py` agent script**
   - Solve permission callback issues
   - Implement workspace-scoped Write tool
   - Test code generation

2. **Create `audit_implementation.py` agent script**
   - Parse constraints
   - Analyze code files
   - Report violations

3. **Test full workflow standalone**
   - Run orchestrator outside Claude Code
   - Verify all phases work end-to-end
   - Debug any subprocess issues

4. **Enable LLM tool selection**
   - Research MCP integration
   - Configure function calling
   - Allow orchestrator to reason about which tools to use

5. **Add feedback loops**
   - Handle audit failures
   - Decide: revise architecture vs fix code
   - Implement retry logic

6. **Add human-in-loop**
   - Tool for orchestrator to ask questions
   - Critical decision points
   - Approval gates

---

## Success Criteria

The system is working when:

1. ✅ Orchestrator runs as standalone process
2. ✅ Agents spawn as isolated subprocesses
3. ✅ Dialogue creates conversation with consensus
4. ✅ Docs synthesis generates ARCHITECTURE.md + CONSTRAINTS.md
5. ⏳ Implementation generates working code
6. ⏳ Audit validates against constraints
7. ⏳ Orchestrator LLM makes tool decisions autonomously
8. ⏳ System handles failures and adapts strategy

---

## Breakthrough Insights

### 1. Cannot Nest ClaudeSDKClient Instances
Running orchestrator as SDK client while inside Claude Code = timeout errors.

**Solution:** Orchestrator runs standalone, spawns agents as subprocesses.

### 2. Isolated Contexts Are Essential
If agents share memory, it's just one agent talking to itself.

**Solution:** Each agent subprocess has its own ClaudeSDKClient instance.

### 3. File-Based Communication Works
Agents signal completion via files, exit codes, and JSON output.

**Solution:** Orchestrator reads these artifacts to validate and adapt.

### 4. Validation Is Critical
Previous orchestrator looped on failures without detecting them.

**Solution:** Check files after each action, read logs to understand failures.

### 5. LLM Orchestration Scales
Hardcoded logic doesn't adapt to novel situations.

**Solution:** Orchestrator is an LLM that reasons about state and decides actions.

---

**This architecture enables true AI-native software development: An AI that orchestrates other AIs.**
