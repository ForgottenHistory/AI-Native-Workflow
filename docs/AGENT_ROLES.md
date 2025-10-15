# Agent Roles & Domain Model

**Date:** 2025-10-15
**Status:** Validated prototype (Architect + Coder dialogue proven)
**Context Limit:** 200k tokens per agent (Claude Code)

---

## Core Principle

**NO OVERLAPPING WRITE PERMISSIONS**

Each agent owns exactly ONE domain. Clear accountability. Single source of truth per domain.

All agents communicate through documentation, not direct coupling.

---

## The Four Agents

### 1. ARCHITECT AGENT

**Domain:** ARCHITECTURE (System Design)

**Owns (Writes):**
- `/architecture/ARCHITECTURE.md` - System design decisions
- `/architecture/CONSTRAINTS.md` - Rules for implementation
- `/architecture/DECISIONS.md` - Why choices were made

**Reads:**
- Requirements (from user)
- Existing architecture
- Coder feedback (via conversation)
- `/logs/AUDIT_LOG.md` (violations to address)

**Responsibilities:**
- Propose tech stacks and architectures
- Make trade-off decisions
- Define system constraints (performance, security, scalability)
- Respond to implementation feedback
- Make final architectural calls
- Document reasoning behind decisions

**Cannot:**
- Write code
- Modify implementation files
- Update implementation logs
- Fix violations directly (only revise architecture)

**Context Window:** 200k tokens (design-focused)

**Conversation Partner:** Coder (stateful dialogue)

---

### 2. CODER AGENT

**Domain:** CODE (Implementation)

**Owns (Writes):**
- `/code/*` - All implementation files
- `/tests/*` - Test files
- `/logs/IMPLEMENTATION_LOG.md` - What changed, when, why

**Reads:**
- `/architecture/ARCHITECTURE.md` (what to build)
- `/architecture/CONSTRAINTS.md` (rules to follow)
- Relevant code files
- `/logs/AUDIT_LOG.md` (violations to fix)
- Task details

**Responsibilities:**
- Evaluate architectural feasibility (during dialogue)
- Suggest practical alternatives
- Implement code according to architecture
- Write comprehensive tests
- Log all implementation changes with reasoning
- Challenge over-engineering
- Estimate implementation effort
- Fix violations flagged by Audit agent

**Cannot:**
- Change architectural decisions
- Modify CONSTRAINTS.md
- Skip architectural approval
- Write documentation (only logs implementation changes)

**Context Window:** 200k tokens (implementation-focused)

**Conversation Partner:** Architect (stateful dialogue)

---

### 3. DOCS AGENT

**Domain:** DOCUMENTATION (Synthesis & Maintenance)

**Owns (Writes):**
- `/status/CURRENT_STATE.md` - System status, completion tracking
- `/status/FILE_REGISTRY.md` - File ownership map
- `/docs/*` - User-facing documentation
- `/logs/CONVERSATION_LOG.md` - Dialogue history

**Reads:**
- Conversation transcripts (Architect ⟷ Coder dialogue)
- `/architecture/ARCHITECTURE.md` (to ensure docs match)
- `/logs/IMPLEMENTATION_LOG.md` (code changes)
- All documentation
- Code files (for drift detection)

**Responsibilities:**
- Synthesize conversations into structured docs
- Maintain FILE_REGISTRY.md (who owns what)
- Update CURRENT_STATE.md (what's done, what's next)
- Check consistency between docs and code
- Flag documentation drift
- Preserve conversation history
- Generate summaries for long conversations

**Cannot:**
- Write code
- Make architectural decisions
- Change constraints
- Fix violations
- Participate in Architect ⟷ Coder dialogue

**Context Window:** 200k tokens (documentation-focused)

**Conversation Partner:** None (reads outputs from others)

---

### 4. AUDIT AGENT

**Domain:** VALIDATION (Constraint Enforcement)

**Owns (Writes):**
- `/logs/AUDIT_LOG.md` - Violations, warnings, compliance checks

**Reads:**
- `/architecture/CONSTRAINTS.md` (rules to enforce)
- `/logs/IMPLEMENTATION_LOG.md` (recent changes)
- `/architecture/ARCHITECTURE.md` (intended design)
- Code files (to validate compliance)
- Test results

**Responsibilities:**
- Check constraints mechanically
- Validate architecture compliance
- Detect contradictions
- Flag violations with severity levels
- Run performance checks
- Verify documentation consistency
- Surface edge cases

**Cannot:**
- Fix violations (only flags them)
- Make architectural decisions
- Write code
- Override constraints
- Write documentation

**Context Window:** 200k tokens (validation-focused)

**Conversation Partner:** None (performs mechanical validation)

---

## Domain Isolation Matrix

| Agent | Architecture Docs | Code | Documentation | Audit Logs | Conversation |
|-------|------------------|------|---------------|-----------|--------------|
| **Architect** | ✅ **WRITES** | ❌ Reads only | ❌ Reads only | ❌ Reads only | ✅ Architect ⟷ Coder |
| **Coder** | ❌ Reads only | ✅ **WRITES** | ❌ Never | ❌ Reads only | ✅ Architect ⟷ Coder |
| **Docs** | ❌ Reads only | ❌ Reads only | ✅ **WRITES** | ❌ Reads only | ❌ Reads only |
| **Audit** | ❌ Reads only | ❌ Reads only | ❌ Reads only | ✅ **WRITES** | ❌ Reads only |

---

## Communication Protocol

### Phase 1: Architectural Dialogue (Conversation)
```
User provides vision
    ↓
Architect & Coder have stateful dialogue
    - Architect proposes architecture
    - Coder evaluates feasibility
    - Architect refines based on feedback
    - Coder signals AGREED when satisfied
    ↓
CONSENSUS reached
```

### Phase 2: Documentation (Crystallization)
```
Architect writes ARCHITECTURE.md, CONSTRAINTS.md
    ↓
Docs agent reads conversation → writes CONVERSATION_LOG.md
    ↓
Docs agent creates FILE_REGISTRY.md entry
```

### Phase 3: Implementation (Execution)
```
Coder reads ARCHITECTURE.md + CONSTRAINTS.md
    ↓
Coder implements → writes code
    ↓
Coder writes IMPLEMENTATION_LOG.md (what changed)
```

### Phase 4: Validation (Audit)
```
Audit agent reads CONSTRAINTS.md + IMPLEMENTATION_LOG.md
    ↓
Audit agent checks code → writes AUDIT_LOG.md
    ↓
If violations → Coder reads AUDIT_LOG.md → fixes issues
    ↓
Repeat Phase 4 until clean
```

### Phase 5: Status Update (Documentation)
```
Docs agent reads all logs + code changes
    ↓
Docs agent updates CURRENT_STATE.md
    ↓
Docs agent checks for documentation drift
```

### Phase 6: User Approval
```
User reviews CURRENT_STATE.md + AUDIT_LOG.md
    ↓
User provides judgment (does this solve the problem?)
    ↓
If approved → next feature
If issues → return to appropriate phase with feedback
```

---

## Key Insights from Prototype

### What We Validated (2025-10-15)

✅ **Stateful Architect ⟷ Coder dialogue works**
- Separate ClaudeSDKClient instances maintain independent reasoning
- Coder challenged Architect's assumptions
- Architect refined based on implementation feedback
- Result: Better architecture than either agent alone

✅ **Domain isolation prevents conflicts**
- Each agent knows its boundaries
- No overlapping write permissions
- Clear accountability

✅ **Message passing through docs works**
- Architect writes ARCHITECTURE.md
- Coder reads it and implements
- Communication is asynchronous and documented

### What's Next

🔜 **Docs agent** - Synthesizes conversation into ARCHITECTURE.md
🔜 **Audit agent** - Validates constraints mechanically
🔜 **Multi-turn refinement** - Multiple conversation rounds
🔜 **Complex projects** - Test on larger codebases

---

## Consensus Markers

**Architect signals:**
- "CONSENSUS: [summary]"
- "Let's go with [decision]"
- "I approve this approach"

**Coder signals:**
- "AGREED: [implementation plan]"
- "This architecture is sound"
- "Ready to implement"

**Both must signal before moving to implementation.**

---

## Failure Modes & Mitigations

### Agents Don't Reach Consensus
- **Cause:** Vague requirements, unclear constraints
- **Mitigation:** Max 10 turns, then escalate to user

### Conversation Loops (Repeat Arguments)
- **Cause:** Missing information, insufficient context
- **Mitigation:** Detect repetition, ask user for clarification

### Implementation Doesn't Match Architecture
- **Cause:** Coder misunderstood, architecture too vague
- **Mitigation:** Audit agent catches violations, block commit

### Documentation Drift
- **Cause:** Docs become stale over time
- **Mitigation:** Docs agent runs consistency checks, flags drift

---

## File Structure

```
/project/
  /architecture/
    ARCHITECTURE.md          ← Architect writes
    CONSTRAINTS.md           ← Architect writes
    DECISIONS.md             ← Architect writes

  /code/
    [implementation files]   ← Coder writes

  /tests/
    [test files]            ← Coder writes

  /logs/
    CONVERSATION_LOG.md      ← Docs writes (from Architect ⟷ Coder dialogue)
    IMPLEMENTATION_LOG.md    ← Coder writes
    AUDIT_LOG.md            ← Audit writes

  /status/
    CURRENT_STATE.md        ← Docs writes
    FILE_REGISTRY.md        ← Docs writes

  /docs/
    [user documentation]     ← Docs writes
```

---

## Critical Requirements

1. **Documentation Discipline** - Keep docs in sync with reality
2. **Clear Domain Boundaries** - Non-overlapping write permissions
3. **Single Source of Truth** - One canonical definition per concept
4. **Human in Loop** - User reviews architectural direction and approves trade-offs
5. **Mechanical Validation** - Automated constraint checking
6. **Iterative Refinement** - First iteration is 80%, refine to 100%+

---

## The New Development Flow

**Traditional:**
```
Human thinks → Human implements → Done (limited by human knowledge)
```

**AI-Assisted:**
```
Human thinks → AI implements → 80% (faster but still human-limited)
```

**AI-Native (This System):**
```
Human vision → Architect ⟷ Coder dialogue → 80%
    ↓
Human reviews → Refines → 95%
    ↓
Audit validates → Fixes → 100%
    ↓
Human discovers better approach → 90% (higher ceiling)
    ↓
Iterate → 105% (beyond original vision)
```

**Each iteration:**
- AI surfaces knowledge user didn't have
- User synthesizes into better understanding
- AI implements with more context
- Discover new possibilities
- **Ceiling keeps rising**

---

**Status:** Architect + Coder dialogue validated. Next: Add Docs and Audit agents.

**Timeline:** 2-4 weeks to fully validate all four agents on real projects.
