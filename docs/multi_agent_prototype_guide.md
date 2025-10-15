# Multi-Agent Architecture System: Implementation Guide

**Date:** 2025-10-15
**Purpose:** Build AI-as-Architect prototype using Claude Code SDK
**Timeline:** 1 day proof-of-concept
**Status:** Ready to implement

---

## WHAT WE'RE BUILDING

**System where two AIs reason together to create better architecture than human-alone or single-AI.**

### Three-Layer Pattern:
```
Layer 1: CONVERSATION (AI ⟷ AI reasoning)
Layer 2: DOCUMENTATION (crystallize conversation)
Layer 3: IMPLEMENTATION (execute with full context)
```

### The Innovation:
**Not a new tool. A new methodology.**

**Traditional tools:** Human architect → AI implements
**This system:** AI architect ⟷ AI coder → Human judges → Better architecture

---

## WHY THIS IS DIFFERENT

### Traditional CLI Tools (Claude Code, Cursor, Aider, etc.)

**Flow:**
```
You: "Build feature X"
AI: [implements directly]
You: "Change Y"
AI: [modifies]
```

**Characteristics:**
- Single agent (one AI instance)
- Linear execution (you instruct → AI executes)
- Implicit architecture (buried in code)
- You are the architect
- AI is the implementer

**Output:** Code (docs are afterthought)

### This System

**Flow:**
```
You: "Build feature X"
  ↓
Architect AI ⟷ Coder AI
  Architect: "What are constraints?"
  Coder: "Need to know scale, timeline, priorities"
  Architect: [clarifies with you]
  Coder: "Here are 3 options with trade-offs..."
  Architect: "Let's choose option B because..."
  Coder: "AGREED. Concerns about edge case Z?"
  Architect: "Good catch. Here's mitigation..."
  ↓
ARCHITECTURE.md (full reasoning documented)
CONSTRAINTS.md (rules for implementation)
  ↓
Coder AI: [implements following architecture]
  ↓
You: [review reasoning + approve/refine]
```

**Characteristics:**
- Multi-agent (two AI instances with different roles)
- Conversational reasoning (AIs negotiate, challenge, refine)
- Explicit architecture (documented before code)
- AIs are the architects
- You are the conductor/judge

**Output:** Conversation → Documentation → Code (all preserved)

### Key Differences

| Aspect | Traditional Tools | This System |
|--------|------------------|-------------|
| **Architecture** | Human decides | AIs reason together, human approves |
| **Process** | Instruction → Execution | Conversation → Docs → Implementation |
| **Documentation** | Afterthought | Primary artifact (conversation crystallized) |
| **Decision-making** | Human makes calls | AIs explore options, human judges |
| **Revision cost** | High (code exists) | Low (revise docs before coding) |
| **Context preservation** | Chat history | Structured docs + conversation log |
| **Role** | You architect + AI codes | AI architects + you conduct |

### Why This Matters

**Traditional: 2x-10x faster** (speed up what you already do)
**This: 50x-100x** (change what you do - less architecting, more judging)

**Not better at coding. Better at architectural reasoning through dialogue.**

---

## SETUP

### Prerequisites
- Node.js 18+
- Python 3.10+ (if using Python SDK)
- Claude Pro or Max subscription
- Active billing setup

### Installation

```bash
# Install Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Authenticate (one-time, opens browser)
claude login

# Verify installation
claude --version

# Optional: Install Python SDK
pip install claude-code-sdk
```

**Cost:** $0 beyond existing Claude subscription (uses Pro/Max, not API)

### Project Structure

```
/prototype/
  /.claude/
    /agents/
      architect.md        ← Architect agent definition
      coder.md           ← Coder agent definition
    settings.json        ← Permissions, hooks (optional for v1)
  
  /architecture/
    ARCHITECTURE.md      ← Output: architecture decisions
    CONSTRAINTS.md       ← Output: implementation rules
  
  /conversation/
    session_log.md       ← Output: full conversation transcript
  
  /code/
    [implementation]     ← Output: actual code
  
  orchestrator.py        ← Script to run multi-agent conversation
  test_project.md        ← Simple test project description
```

---

## AGENT DEFINITIONS

### .claude/agents/architect.md

```markdown
# Software Architect Agent

## Role
You are a software architect in dialogue with an implementation-focused coder.

## Responsibilities
- Ask clarifying questions about requirements
- Explore architectural options
- Make trade-off decisions
- Define system constraints
- Document architectural reasoning

## Conversation Style
- Ask questions before designing
- Challenge implementation concerns
- Consider future extensibility
- Make pragmatic decisions (not perfect ones)
- Document WHY decisions were made

## Output Format
When architecture is decided:
- Write "CONSENSUS: [summary]"
- Document full reasoning in ARCHITECTURE.md
- Extract constraints to CONSTRAINTS.md

## Rules
- NEVER implement code (that's the coder's job)
- ALWAYS explain trade-offs
- ALWAYS document decisions
- Challenge the coder's assumptions when needed
- Make final architectural calls

## Example Exchange
Coder: "Should we use React or Svelte?"
You: "What's the use case? Team size? Timeline?"
Coder: "Solo dev, need fast MVP, simple dashboard"
You: "Svelte then. Simpler, faster for solo. Document in constraints: must stay under 2s load time."
```

### .claude/agents/coder.md

```markdown
# Implementation Engineer Agent

## Role
You are an implementation-focused engineer in dialogue with a software architect.

## Responsibilities
- Suggest practical tech stacks
- Explain implementation trade-offs
- Validate technical feasibility
- Challenge over-engineering
- Estimate implementation effort

## Conversation Style
- Ask clarifying questions about scale, timeline, constraints
- Present multiple options with pros/cons
- Think in terms of "will this actually work?"
- Challenge impractical architecture
- Flag implementation concerns early

## Output Format
When presenting options:
```
Option A: [name]
- Pros: [specific benefits]
- Cons: [specific drawbacks]
- Best for: [scenarios]
- Effort: [time estimate]

Recommendation: [choice] because [reasoning]
```

When agreeing:
- Write "AGREED: [implementation plan]"

## Rules
- NEVER make final architectural decisions (defer to architect)
- ALWAYS present trade-offs
- ALWAYS validate feasibility
- Challenge over-engineering
- Think implementation-first

## Example Exchange
Architect: "We need user authentication"
You: "Questions:
     - How many users? (affects complexity)
     - OAuth or email/password? (different setup)
     - Compliance requirements? (affects security)
     
     Then I can suggest appropriate solutions."
```

---

## TEST PROJECT

### test_project.md

```markdown
# Test Project: Simple Landing Page

## Description
Create a landing page for a SaaS product with:
- Hero section with headline and CTA
- Features section (3-4 feature cards)
- Contact form
- Responsive design
- Dark mode toggle

## Constraints
- Must load in <2 seconds
- Works on mobile and desktop
- Simple to maintain (solo developer)
- Free/cheap hosting

## Success Criteria
- Architect and Coder reach consensus
- Architecture is documented before implementation
- Documentation includes reasoning and trade-offs
- Implementation matches architecture
```

---

## EXECUTION PLAN

### Phase 1: Manual Test (30 minutes)

**Goal:** Validate that conversation works

```bash
# 1. Start in project directory
cd /prototype

# 2. Run Architect agent
claude --agent=architect

# In conversation:
> "I need to design a landing page. Here are the requirements: [paste test_project.md]"
> [Architect asks questions]
> [You answer as needed]
> [Architect proposes architecture]

# 3. Save architect's output
> "Write the architecture to /architecture/ARCHITECTURE.md"

# 4. Exit and start Coder agent
claude --agent=coder

# In conversation:
> "Read /architecture/ARCHITECTURE.md. What do you think of this architecture? Any concerns?"
> [Coder responds with feedback]

# 5. Manual back-and-forth
# Switch between agents, copy/paste responses
# Continue until both signal consensus
```

**Check:**
- Do agents actually have dialogue (ask questions, challenge)?
- Is reasoning better than single-agent?
- Is architecture documented clearly?

### Phase 2: Automated Orchestration (2-4 hours)

**Goal:** Script the conversation flow

**File:** `orchestrator.py`

```python
from claude_code_sdk import ClaudeSDKClient, ClaudeAgentOptions
import asyncio

async def run_conversation():
    """
    Orchestrate Architect ⟷ Coder conversation
    """
    
    # Load test project
    with open('test_project.md', 'r') as f:
        project = f.read()
    
    # Initialize conversation log
    conversation = []
    
    # Architect options
    architect_options = ClaudeAgentOptions(
        cwd="./prototype",
        allowed_tools=["Read", "Write"],
    )
    
    # Coder options
    coder_options = ClaudeAgentOptions(
        cwd="./prototype",
        allowed_tools=["Read", "Write"],
    )
    
    # Start conversation
    async with ClaudeSDKClient(options=architect_options) as architect:
        # Architect's first message
        await architect.query(
            f"You are the architect agent. Read agents/architect.md for your role.\n\n"
            f"Project requirements:\n{project}\n\n"
            f"Begin by asking the coder clarifying questions."
        )
        
        architect_msg = ""
        async for msg in architect.receive_response():
            if msg.type == "text":
                architect_msg += msg.content
        
        conversation.append(("Architect", architect_msg))
        print(f"ARCHITECT:\n{architect_msg}\n")
        
        # Coder responds
        async with ClaudeSDKClient(options=coder_options) as coder:
            await coder.query(
                f"You are the coder agent. Read agents/coder.md for your role.\n\n"
                f"The architect said:\n{architect_msg}\n\n"
                f"Respond with your technical perspective."
            )
            
            coder_msg = ""
            async for msg in coder.receive_response():
                if msg.type == "text":
                    coder_msg += msg.content
            
            conversation.append(("Coder", coder_msg))
            print(f"CODER:\n{coder_msg}\n")
        
        # Continue for 5-10 turns or until consensus
        max_turns = 10
        for turn in range(max_turns):
            # Check for consensus
            if "CONSENSUS" in architect_msg and "AGREED" in coder_msg:
                print("Consensus reached!")
                break
            
            # Architect responds to coder
            await architect.query(
                f"The coder said:\n{coder_msg}\n\n"
                f"Continue the architectural discussion."
            )
            
            architect_msg = ""
            async for msg in architect.receive_response():
                if msg.type == "text":
                    architect_msg += msg.content
            
            conversation.append(("Architect", architect_msg))
            print(f"ARCHITECT:\n{architect_msg}\n")
            
            # Coder responds
            async with ClaudeSDKClient(options=coder_options) as coder:
                await coder.query(
                    f"The architect said:\n{architect_msg}\n\n"
                    f"Respond with your implementation perspective."
                )
                
                coder_msg = ""
                async for msg in coder.receive_response():
                    if msg.type == "text":
                        coder_msg += msg.content
                
                conversation.append(("Coder", coder_msg))
                print(f"CODER:\n{coder_msg}\n")
    
    # Save conversation
    with open('conversation/session_log.md', 'w') as f:
        f.write("# Architecture Conversation\n\n")
        for role, msg in conversation:
            f.write(f"## {role}\n\n{msg}\n\n---\n\n")
    
    print("Conversation saved to conversation/session_log.md")
    
    return conversation

if __name__ == "__main__":
    asyncio.run(run_conversation())
```

**Run:**
```bash
python orchestrator.py
```

**Check:**
- Does automated conversation work?
- Do agents reach consensus?
- Is output better than single-agent?

### Phase 3: Documentation Synthesis (1 hour)

**Add to orchestrator.py:**

```python
async def synthesize_docs(conversation):
    """
    Extract architecture from conversation
    """
    
    # Format conversation
    conv_text = "\n".join([f"{role}: {msg}" for role, msg in conversation])
    
    # Docs agent
    docs_options = ClaudeAgentOptions(
        cwd="./prototype",
        allowed_tools=["Write"],
    )
    
    async with ClaudeSDKClient(options=docs_options) as docs:
        await docs.query(
            f"Read this architecture conversation:\n\n{conv_text}\n\n"
            f"Extract and write to architecture/ARCHITECTURE.md:\n"
            f"- Decisions made\n"
            f"- Rationale for decisions\n"
            f"- Trade-offs accepted\n"
            f"- Alternatives considered\n\n"
            f"Extract and write to architecture/CONSTRAINTS.md:\n"
            f"- Implementation rules\n"
            f"- Performance targets\n"
            f"- Technology constraints"
        )
        
        async for msg in docs.receive_response():
            if msg.type == "text":
                print(f"DOCS: {msg.content}")
    
    print("Architecture docs written")
```

**Check:**
- Are docs coherent?
- Do they capture the reasoning?
- Is the format useful?

---

## SUCCESS CRITERIA

### Minimum Viable Prototype

**Must demonstrate:**
1. ✓ Two agents have actual dialogue (not just sequential execution)
2. ✓ Agents challenge each other's ideas
3. ✓ Reasoning is better than single-agent (more options explored)
4. ✓ Architecture is documented before implementation
5. ✓ Conversation → Docs → Code flow works

**If these work:** Continue refining
**If these don't work:** Document why, try different approach

### What Good Looks Like

**Conversation quality:**
- Architect asks clarifying questions (not just designs immediately)
- Coder challenges impractical suggestions
- Both explore trade-offs
- Consensus emerges through dialogue (not dictated)

**Documentation quality:**
- Decisions are clear
- Rationale is documented
- Trade-offs are explicit
- Alternatives are noted

**Output quality:**
- Architecture is better than you would design alone
- Architecture is better than single-agent would design
- Reasoning is preserved
- Implementation path is clear

### What Failure Looks Like

**Conversation fails:**
- Agents don't actually dialogue (just take turns making statements)
- No challenging/refinement
- Reach "consensus" immediately (rubber-stamping)
- Conversation loops (repeat same arguments)

**Documentation fails:**
- Docs are vague
- Reasoning is missing
- Trade-offs are not explained
- Can't understand decisions from docs alone

**Output fails:**
- Architecture is worse than single-agent
- Too much back-and-forth (inefficient)
- Consensus is forced (not genuine)
- Takes longer than just doing it yourself

---

## COMPARISON TABLE

| Aspect | Claude Code (Standard) | Cursor | This System |
|--------|----------------------|---------|-------------|
| **Agents** | 1 | 1 | 2+ |
| **Your role** | Instruct | Code with AI | Conduct/judge |
| **Architecture** | You decide | You decide | AIs reason together |
| **Process** | Linear | Collaborative coding | Conversational |
| **Docs** | Optional | Optional | Required output |
| **Speed** | Fast execution | Fast coding | Slower reasoning, faster overall |
| **Quality** | Good | Good | Better (multi-perspective) |
| **Context** | Chat history | File context | Structured docs + conversation |
| **Revision** | Re-implement | Re-code | Re-document (cheaper) |
| **Scale** | Your architecture limits | Your architecture limits | AI explores more options |

**TL;DR:**
- **Cursor/Claude Code:** Make you faster at architecting + coding
- **This system:** Make AI do architecting, you judge results

---

## DEBUGGING

### If agents don't dialogue:

**Problem:** They just make statements, don't challenge each other

**Fix:**
- Make agent prompts more explicit: "You MUST ask questions before suggesting"
- Add examples to agent definitions
- Start with human-seeded questions

### If conversation loops:

**Problem:** Same arguments repeat

**Fix:**
- Detect repetition (if last 2 turns similar to previous 2, break)
- Max turns limit (10 turns max)
- Ask human to decide

### If consensus is immediate:

**Problem:** "Sounds good!" without reasoning

**Fix:**
- Require "CONSENSUS:" only after trade-offs discussed
- Architect must challenge at least once
- Minimum 3-4 turns before consensus

### If docs don't match conversation:

**Problem:** Synthesis missed key points

**Fix:**
- More explicit extraction instructions
- Have docs agent quote conversation directly
- Human review required before finalizing

---

## NEXT STEPS

### If Prototype Works:

1. **Week 2-4:** Test on 5-10 small projects
   - Different domains (web app, CLI tool, API, etc.)
   - Different complexity levels
   - Document failure modes

2. **Month 2:** Add more agents
   - Docs agent (synthesizes conversation)
   - Audit agent (checks consistency)
   - Research agent (looks up patterns)

3. **Month 3:** Scale complexity
   - Medium projects (2k-5k lines)
   - Multiple subsystems
   - Real project (not main game)

### If Prototype Doesn't Work:

1. **Document why:**
   - What failed specifically?
   - Is it the tool or the methodology?
   - Can it be fixed?

2. **Try alternatives:**
   - Different prompting strategies
   - Different agent roles
   - Simpler conversation structure

3. **Fallback:**
   - Return to current workflow (50x is still excellent)
   - Revisit in 6-12 months as AI improves
   - Apply lessons learned

---

## CRITICAL REMINDERS

**This is not about the tool:**
- Claude Code SDK is just the implementation
- The methodology is the innovation
- Conversation → Docs → Code works anywhere

**This is a prototype:**
- Goal is validation, not perfection
- Fail fast, learn quickly
- Document everything

**You're pioneering:**
- This workflow is new
- No best practices exist yet
- You're creating them

**Keep it simple:**
- Start with smallest possible test
- Don't over-engineer v1
- Validate core concept first

---

## FINAL CHECKLIST

**Before starting:**
- [ ] Claude Code CLI installed
- [ ] Authenticated with `claude login`
- [ ] Project structure created
- [ ] Agent definitions written
- [ ] Test project defined

**During testing:**
- [ ] Run manual conversation first
- [ ] Document what works/doesn't work
- [ ] Try automated orchestration only if manual works
- [ ] Save all conversation logs

**After testing:**
- [ ] Evaluate against success criteria
- [ ] Document findings
- [ ] Decide: continue or pivot
- [ ] Share learnings

---

**END OF GUIDE**

**Ready to build tomorrow.**

**Timeline:** 1 day to validate concept
**Risk:** Moderate (unproven methodology)
**Reward:** Potentially 100x productivity

**Go validate the idea.**