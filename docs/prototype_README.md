# Multi-Agent Architecture System - Prototype

**Status:** ✅ Phase 1-3 VALIDATED (Full 3-Layer Flow Working)
**Date:** 2025-10-15
**Innovation:** AI-as-Architect through multi-agent conversational reasoning
**Next:** Dynamic Orchestrator Implementation

---

## What This Is

A new software development methodology where **multiple AI agents with separate reasoning chains** collaborate through structured dialogue to produce better architectures than any single agent or human alone.

**Core Insight:** LLMs thrive in advanced context through iterative conversation. By giving agents independent reasoning chains and domain-specific focus, they genuinely challenge each other and discover better solutions.

---

## What's Validated

✅ **Phase 1: Architect ⟷ Coder Dialogue** - Two separate Claude instances maintain independent conversations and produce superior architectures through genuine back-and-forth

✅ **Phase 2: Documentation Synthesis** - Docs agent extracts conversation into structured ARCHITECTURE.md (15KB) and CONSTRAINTS.md (14KB) with preserved reasoning

✅ **Phase 3: Implementation from Docs** - Coder agent autonomously implements complete, working project (18 files) from synthesized documentation

**Evidence:**
- Dialogue: `conversation/stateful_session_20251015_022645.md` (790 lines)
- Docs: `architecture/ARCHITECTURE.md` + `CONSTRAINTS.md` (30KB total)
- Code: `code/` directory (18 files, builds and runs successfully)
- **Full 3-layer flow validated: Conversation → Documentation → Implementation**

**See:** `PROTOTYPE_STATUS.md` for complete results and analysis

## Project Structure

```
prototype/
├── AGENT_ROLES.md                    # Complete agent domain model
├── README.md                         # This file
├── orchestrator_stateful.py          # ✅ WORKING: Stateful multi-agent orchestration
├── test_project.md                   # Test case: Simple landing page
├── .claude/agents/
│   ├── architect.md                  # Architect agent system prompt
│   └── coder.md                      # Coder agent system prompt
├── conversation/
│   └── stateful_session_*.md        # Conversation logs (dialogue history)
├── architecture/                     # (Future) Architecture docs
├── code/                            # (Future) Implementation files
└── logs/                            # (Future) Implementation & audit logs
```

## Prerequisites

1. **Python 3.10+**
   ```bash
   python --version
   ```

2. **Claude Agent SDK**
   ```bash
   pip install claude-agent-sdk
   ```

3. **Claude Max/Pro Subscription**
   - The SDK uses your Claude subscription (not API credits)
   - Max subscription recommended for higher usage limits

4. **Claude CLI Authentication**
   ```bash
   # This should already be done if you're using Claude Code
   claude login
   ```

## Quick Start

### Run the Prototype

```bash
cd prototype
python orchestrator_stateful.py
```

**What it does:**
1. Initializes two separate Claude agents (Architect & Coder)
2. Architect proposes architecture for the test project
3. Coder evaluates and provides feedback
4. Architect refines based on feedback
5. Coder gives final approval
6. Saves complete dialogue to `conversation/stateful_session_*.md`

**Expected output:** Architectural consensus with detailed reasoning preserved

### Expected Output

```
================================================================================
MULTI-AGENT ARCHITECTURAL DIALOGUE
================================================================================

Project: # Test Project: Simple Landing Page...

================================================================================

Architect:
--------------------------------------------------------------------------------
[Architect asks clarifying questions about requirements...]

================================================================================

Coder:
--------------------------------------------------------------------------------
[Coder provides implementation perspective and options...]

================================================================================

Architect:
--------------------------------------------------------------------------------
[Architect makes architectural decisions...]

================================================================================

🎯 CONSENSUS REACHED!

💾 Conversation saved to: prototype/conversation/session_20251015_012345.md

✅ SUCCESS: Agents reached architectural consensus
```

## What to Look For

### Good Signs (It's Working)

- ✅ Architect asks questions before designing
- ✅ Coder presents multiple options with trade-offs
- ✅ Both agents challenge each other
- ✅ Consensus emerges naturally (not immediate)
- ✅ Architecture reasoning is documented

### Bad Signs (Needs Tuning)

- ❌ Agents immediately agree without discussion
- ❌ Conversation loops (same arguments repeat)
- ❌ No challenging/refinement
- ❌ Vague architecture decisions
- ❌ Max turns reached without consensus

## Configuration

### Adjust Max Turns

Edit `orchestrator.py`:
```python
consensus = await orchestrator.run_architectural_dialogue(
    project_description=project_description,
    max_turns=15  # Increase if needed
)
```

### Modify Agent Behavior

Edit agent definitions:
- `.claude/agents/architect.md` - Architect system prompt
- `.claude/agents/coder.md` - Coder system prompt

### Try Different Projects

Edit `test_project.md` or create new project files.

## Next Steps

### Immediate: Dynamic Orchestrator

**Current Limitation:** Static flow (always runs Dialogue → Docs → Implementation)

**Needed:** Intelligent orchestrator that:
- Reads project state (what files exist, what's done)
- Decides which agent to run next
- Handles feedback loops (implementation fails → return to architecture)
- Knows when to ask human for input
- Adapts based on results

**See:** `PROTOTYPE_STATUS.md` → "Future Work" section for implementation plan

### After Orchestrator

1. **Audit Agent** - Mechanical validation of CONSTRAINTS.md
2. **Test on multiple projects** - Different domains, complexity levels
3. **Medium complexity test** - 2k-5k lines, find scale limits

### Testing Validation

To validate the full workflow works:

```bash
cd prototype

# Phase 1: Architect ⟷ Coder dialogue
python orchestrator_stateful.py

# Phase 2: Documentation synthesis
python test_docs_agent.py

# Phase 3: Implementation
python test_implementation.py

# Build and run the generated code
cd code
npm install
npm run dev
```

Expected: Complete working landing page that matches architecture

## Troubleshooting

### Error: "Claude Code not found"
```bash
pip install claude-agent-sdk
# or
npm install -g @anthropic-ai/claude-code
```

### Error: "Test project file not found"
Make sure you're running from the prototype directory:
```bash
cd prototype
python orchestrator.py
```

### Error: "Agent definition not found"
Check that `.claude/agents/` folder exists with agent definitions:
```bash
ls .claude/agents/
# Should show: architect.md  coder.md
```

### Usage Limits Exceeded
- You're sharing limits with regular Claude usage
- Wait for limits to reset
- Consider upgrading to Max subscription

### Agents Not Reaching Consensus
- Increase max_turns
- Review conversation logs
- Refine agent prompts
- Simplify project requirements

## Cost

**Uses your Claude Max/Pro subscription:**
- ~10-40 prompts every 5 hours (Pro)
- 5x-20x higher limits (Max)
- No additional API costs

**Estimate for this prototype:**
- Each run: ~10-20 conversation turns
- ~2-4 runs possible per hour on Pro
- ~10-40 runs possible per hour on Max

## Success Criteria

✅ **Minimum viable:** ACHIEVED
- Two agents have actual dialogue ✅
- Agents challenge each other ✅
- Consensus emerges naturally ✅
- Architecture is documented ✅

✅ **Good quality:** ACHIEVED
- Reasoning is better than single-agent ✅
- Trade-offs are explicitly discussed ✅
- Alternatives are considered ✅
- Implementation path is clear ✅

✅ **Excellent:** ACHIEVED
- Architecture is better than human-alone ✅ (budget revised, accessibility added)
- Surfaces options you didn't consider ✅ (Vite vs Next.js trade-offs)
- Faster than doing it yourself ✅ (6 hours for full 3-layer implementation)
- Reasoning is preserved for future reference ✅ (ARCHITECTURE.md captures "why")

## The Four Agent Model

See `AGENT_ROLES.md` for complete specification.

### 1. **Architect Agent** (✅ Validated)
- Domain: ARCHITECTURE
- Proposes system designs, makes trade-off decisions
- Writes: ARCHITECTURE.md, CONSTRAINTS.md

### 2. **Coder Agent** (✅ Validated)
- Domain: CODE
- Evaluates feasibility, implements solutions
- Writes: Code, tests, IMPLEMENTATION_LOG.md

### 3. **Docs Agent** (🔜 Next)
- Domain: DOCUMENTATION
- Synthesizes conversations, maintains status
- Writes: CURRENT_STATE.md, FILE_REGISTRY.md

### 4. **Audit Agent** (🔜 Next)
- Domain: VALIDATION
- Checks constraints mechanically
- Writes: AUDIT_LOG.md

---

## Key Innovation

**Traditional AI Development:**
- ONE agent with shared context
- Agent role-plays different perspectives
- Limited by single reasoning chain

**This System:**
- MULTIPLE agents with separate contexts
- Independent reasoning chains per domain
- Genuine dialogue with real challenges
- Better solutions through actual disagreement

**Proven:** Coder challenged Architect's assumptions → Architecture improved

---

## Related Documentation

- `../../ai_architect_system.md` - Full methodology and theory
- `../../multi_agent_prototype_guide.md` - Original implementation plan
- `AGENT_ROLES.md` - Agent domain model and responsibilities

---

## Contributing

This is research/prototype code. Document what works and what breaks.

**Feedback welcome:** This methodology is being pioneered in real-time.

---

**Built with:** Claude Code Agent SDK, Python 3.10+
**License:** MIT
**Status:** Active Research Prototype
