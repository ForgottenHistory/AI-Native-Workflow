# AI Orchestrator Agent Design

**Date:** 2025-10-15
**Status:** Design Phase
**Purpose:** Replace pseudo-dynamic orchestrator with true AI reasoning

---

## The Problem with Current "Dynamic" Orchestrator

The current orchestrator is **pseudo-dynamic**:
- State assessment: Hardcoded file checks
- Decision logic: Hardcoded if/else tree
- Execution: Sequential, no validation
- Failure handling: None (just loops)

It follows a **static sequence**: Dialogue → Docs → Implementation → (loop if failed)

**It cannot:**
- Validate that actions succeeded
- Reason about why failures happened
- Adapt strategy based on outcomes
- Learn from logs
- Make novel decisions

---

## True AI Orchestrator Architecture

### Core Concept

**The orchestrator itself is an LLM agent** with tools to:
1. Invoke specialist agents (Architect, Coder, Docs, Audit)
2. Assess workspace state (what files exist)
3. Read logs (what happened)
4. Validate results (did it work?)
5. Reason about next actions

### System Prompt

```
You are an AI Project Orchestrator managing a multi-agent software development workflow.

Your role:
- Assess project state by checking what files exist
- Decide which agent to invoke next based on current state
- Validate that each action succeeded before proceeding
- Read logs to understand what happened and why
- Adapt strategy when actions fail
- Guide the project to completion

Specialist agents you can invoke:
- Architectural Dialogue: Architect ⟷ Coder discuss tech stack
- Documentation Synthesis: Extract decisions into ARCHITECTURE.md + CONSTRAINTS.md
- Implementation: Generate code from architecture
- Audit: Validate code against constraints

Always validate after each action:
- Check if expected files were created
- Read logs to see what the agent did
- Verify success before proceeding
- If failure, understand why and adapt

Work iteratively until the project is complete.
```

### Available Tools

#### 1. `assess_workspace_state(project_name: str) -> dict`
Returns what exists in the workspace:
```json
{
  "has_requirements": true,
  "has_conversation": true,
  "has_architecture": true,
  "has_constraints": true,
  "has_code": false,
  "files": ["requirements.md", "conversation/dialogue_*.md", ...],
  "current_phase": "implementation"
}
```

#### 2. `run_architectural_dialogue(project_name: str) -> dict`
Invokes Architect ⟷ Coder dialogue:
```json
{
  "success": true,
  "conversation_file": "conversation/dialogue_20251015.md",
  "consensus_reached": true,
  "turns": 4,
  "log_path": "logs/dialogue_20251015.log"
}
```

#### 3. `synthesize_documentation(project_name: str) -> dict`
Invokes Docs agent to create ARCHITECTURE.md + CONSTRAINTS.md:
```json
{
  "success": true,
  "files_created": [
    "architecture/ARCHITECTURE.md",
    "architecture/CONSTRAINTS.md"
  ],
  "log_path": "logs/docs_synthesis_20251015.log"
}
```

#### 4. `implement_from_architecture(project_name: str) -> dict`
Invokes Coder agent to generate code:
```json
{
  "success": true,
  "files_created": 18,
  "code_directory": "code/",
  "log_path": "logs/implementation_20251015.log"
}
```

#### 5. `audit_implementation(project_name: str) -> dict`
Invokes Audit agent to validate constraints:
```json
{
  "success": true,
  "violations": 0,
  "warnings": 2,
  "passed": true,
  "log_path": "logs/audit_20251015.log"
}
```

#### 6. `read_log(project_name: str, log_path: str) -> str`
Reads a specific log file to understand what happened:
```
Returns full log content as string
```

#### 7. `list_files(project_name: str, directory: str) -> list[str]`
Lists files in a workspace directory:
```json
["package.json", "src/App.tsx", "src/main.tsx", ...]
```

#### 8. `read_file(project_name: str, file_path: str) -> str`
Reads a specific file (for verification):
```
Returns file content as string
```

---

## Orchestrator Reasoning Pattern

### Example Flow 1: Success Case

```
Orchestrator: Let me assess the current state.
[uses assess_workspace_state]

Result: has_requirements=true, but no conversation, docs, or code.

Orchestrator: I need to start with architectural dialogue.
[uses run_architectural_dialogue]

Result: {success: true, consensus_reached: true}

Orchestrator: Let me verify by reading the conversation file.
[uses read_file("conversation/dialogue_20251015.md")]

Content shows "CONSENSUS:" and "AGREED:" markers. Good!

Orchestrator: Next, I'll synthesize documentation.
[uses synthesize_documentation]

Result: {success: true, files_created: 2}

Orchestrator: Let me verify the docs were created.
[uses assess_workspace_state]

Result: has_architecture=true, has_constraints=true. Perfect!

Orchestrator: Now I'll implement the code.
[uses implement_from_architecture]

Result: {success: true, files_created: 18}

Orchestrator: Let me verify code files exist.
[uses list_files("code/")]

Result: 18 files listed. Good!

Orchestrator: Finally, let me audit the implementation.
[uses audit_implementation]

Result: {passed: true, violations: 0}

Orchestrator: Project complete!
```

### Example Flow 2: Failure & Adaptation

```
Orchestrator: Let me implement the code.
[uses implement_from_architecture]

Result: {success: true, files_created: 0}

Orchestrator: Wait, it says success but no files created? Let me investigate.
[uses read_log("logs/implementation_20251015.log")]

Log shows: "I see the issue - Write tool requires reading files first..."
The agent was confused about permissions!

Orchestrator: The implementation agent had permission issues. Let me try again with clearer instructions.
[uses implement_from_architecture with retry]

Result: {success: true, files_created: 18}

Orchestrator: Better! Let me verify.
[uses list_files("code/")]

Result: 18 files. Success!
```

### Example Flow 3: Audit Failures

```
Orchestrator: Let me audit the implementation.
[uses audit_implementation]

Result: {passed: false, violations: 3}

Orchestrator: Audit failed. Let me read the audit log.
[uses read_log("logs/audit_20251015.log")]

Violations:
- Bundle size >250KB (actual: 350KB)
- Missing dark mode toggle
- Accessibility score 82 (target: 95)

Orchestrator: I need to fix these violations. Options:
1. Revise architecture (if constraints are wrong)
2. Fix implementation (if code is wrong)

Let me read the CONSTRAINTS.md to check if 250KB is realistic.
[uses read_file("architecture/CONSTRAINTS.md")]

Constraint says <250KB is required. Let me fix the implementation.
[uses implement_from_architecture with specific fixes]

Orchestrator: Now let me re-audit.
[uses audit_implementation]

Result: {passed: true}

Success!
```

---

## Benefits of AI Orchestrator

### 1. True Dynamic Routing
Not hardcoded logic - actual reasoning about what to do next based on context.

### 2. Validation at Every Step
Checks that actions succeeded before proceeding.

### 3. Failure Adaptation
Reads logs, understands what went wrong, tries different approaches.

### 4. Learning from Logs
Uses logs as memory to understand project history.

### 5. Novel Problem Solving
Can handle situations not anticipated in code:
- "Implementation succeeded but created wrong files? Let me check..."
- "Dialogue took 10 turns without consensus? Let me ask human for clarification."
- "Audit found performance issue? Let me read the architecture to see if we can relax constraints."

### 6. Explainable Decisions
The LLM's reasoning is visible - we can see WHY it made each decision.

---

## Implementation Plan

### Step 1: Build Orchestrator Tools (Python functions)
Each tool is a Python function that:
- Takes project_name as parameter
- Invokes appropriate agents
- Returns structured result dict
- Saves detailed logs

### Step 2: Create Orchestrator Agent
Initialize ClaudeSDKClient with:
- System prompt (orchestrator role)
- Tools (all 8 tools available)
- max_turns=50 (allow many iterations)

### Step 3: Simple Invocation
```python
orchestrator = AIOrchestrator()
await orchestrator.orchestrate(
    project_name="test_landing_page",
    requirements="Build a modern landing page..."
)
```

The orchestrator reasons and uses tools autonomously until completion.

### Step 4: Add Human-in-Loop
For critical decisions:
```python
# Orchestrator can use this tool
def ask_human(question: str, options: list[str]) -> str:
    """Ask human for guidance on complex decision."""
    print(f"[HUMAN INPUT] {question}")
    for i, opt in enumerate(options):
        print(f"  {i+1}. {opt}")
    return input("Your choice: ")
```

---

## Success Criteria

The AI Orchestrator should:

1. **Validate every action** - Check results before proceeding
2. **Read logs to understand** - Use logs as information source
3. **Adapt to failures** - Try different approaches when things fail
4. **Reason explicitly** - Show decision-making process
5. **Complete projects** - Guide workflow to successful completion
6. **Handle edge cases** - Deal with unexpected situations gracefully

---

## Comparison: Pseudo vs True Dynamic

### Pseudo-Dynamic (Current)
```python
def decide_next_action(state):
    if not state.has_conversation:
        return RUN_DIALOGUE
    elif not state.has_docs:
        return SYNTHESIZE_DOCS
    # ... hardcoded logic
```
**Problem:** Cannot adapt, no validation, no reasoning

### True Dynamic (AI Orchestrator)
```python
# Orchestrator LLM with tools
orchestrator.reason(
    "What exists? What succeeded? What failed? What should I do next?"
)
orchestrator.use_tool("assess_workspace_state")
orchestrator.use_tool("read_log", path="...")
orchestrator.decide_and_act()
```
**Benefit:** Adaptive, validates, reasons, learns

---

## Next Steps

1. Implement the 8 orchestrator tools
2. Create AI Orchestrator agent with tools
3. Test on simple project (landing page)
4. Compare vs pseudo-dynamic orchestrator
5. Document adaptive behaviors observed
6. Add more tools as needed (human input, git operations, etc.)

---

**This is the true AI-native workflow: An AI that orchestrates other AIs.**
