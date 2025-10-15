# Agent Server API Protocol

**Version:** 1.0
**Date:** 2025-10-15

---

## Architecture Overview

Each specialist agent runs as an **independent FastAPI server** with its own ClaudeSDKClient instance. The orchestrator (Claude Code) communicates with agents via HTTP requests.

```
Orchestrator (Claude Code)
│
├─> POST http://localhost:5001/architect/propose
├─> POST http://localhost:5002/coder/evaluate
├─> POST http://localhost:5003/docs/synthesize
└─> POST http://localhost:5004/audit/validate
```

---

## Agent Servers

### Port Assignments

| Agent | Port | Base URL |
|-------|------|----------|
| Architect | 5001 | http://localhost:5001 |
| Coder | 5002 | http://localhost:5002 |
| Docs | 5003 | http://localhost:5003 |
| Audit | 5004 | http://localhost:5004 |

### Server Lifecycle

Each server:
1. Initializes ClaudeSDKClient on startup
2. Maintains agent context across requests (conversation history)
3. Exposes REST endpoints for agent actions
4. Returns structured JSON responses
5. Logs all interactions

---

## API Endpoints

### 1. Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "agent": "architect|coder|docs|audit",
  "connected": true,
  "uptime_seconds": 123.45
}
```

### 2. Reset Agent Context

**Endpoint:** `POST /reset`

**Response:**
```json
{
  "success": true,
  "message": "Agent context reset"
}
```

---

## Architect Agent (Port 5001)

### Endpoint: `POST /architect/propose`

Architect proposes initial architecture based on requirements.

**Request:**
```json
{
  "project_name": "landing_page",
  "requirements": "Build a landing page with hero, features, contact form",
  "context": {
    "previous_proposals": [],
    "constraints": []
  }
}
```

**Response:**
```json
{
  "success": true,
  "proposal": "I propose using React with Tailwind CSS...",
  "tech_stack": {
    "framework": "React",
    "styling": "Tailwind CSS",
    "build_tool": "Vite"
  },
  "reasoning": "React provides component reusability...",
  "conversation_turn": 1
}
```

### Endpoint: `POST /architect/respond`

Architect responds to coder feedback.

**Request:**
```json
{
  "project_name": "landing_page",
  "coder_feedback": "I'm concerned about bundle size...",
  "previous_proposal": "...",
  "conversation_turn": 2
}
```

**Response:**
```json
{
  "success": true,
  "response": "Good point about bundle size. Let's use Preact instead...",
  "revised_proposal": "...",
  "consensus_signal": "CONSENSUS: Preact + Tailwind",
  "conversation_turn": 3
}
```

---

## Coder Agent (Port 5002)

### Endpoint: `POST /coder/evaluate`

Coder evaluates architect's proposal.

**Request:**
```json
{
  "project_name": "landing_page",
  "architect_proposal": "I propose React with Tailwind...",
  "conversation_turn": 1
}
```

**Response:**
```json
{
  "success": true,
  "evaluation": "I AGREE with Tailwind but have CONCERNS about React...",
  "agreements": ["Tailwind CSS", "Component-based approach"],
  "concerns": ["Bundle size", "Build complexity"],
  "alternatives": ["Preact", "Vanilla JS with Web Components"],
  "effort_estimate": "4-6 hours",
  "conversation_turn": 2
}
```

### Endpoint: `POST /coder/finalize`

Coder gives final approval or concerns.

**Request:**
```json
{
  "project_name": "landing_page",
  "architect_response": "Let's use Preact instead...",
  "conversation_turn": 3
}
```

**Response:**
```json
{
  "success": true,
  "final_evaluation": "AGREED: This architecture addresses my concerns...",
  "approved": true,
  "conversation_turn": 4
}
```

### Endpoint: `POST /coder/implement`

Coder generates implementation code.

**Request:**
```json
{
  "project_name": "landing_page",
  "architecture_doc": "# Architecture\n...",
  "constraints_doc": "# Constraints\n...",
  "workspace_path": "workspaces/landing_page"
}
```

**Response:**
```json
{
  "success": true,
  "files_created": [
    "code/index.html",
    "code/App.jsx",
    "code/package.json"
  ],
  "summary": "Created landing page with hero, features, contact form",
  "next_steps": ["npm install", "npm run dev"]
}
```

---

## Docs Agent (Port 5003)

### Endpoint: `POST /docs/synthesize`

Docs agent generates architecture documentation from conversation.

**Request:**
```json
{
  "project_name": "landing_page",
  "conversation": [
    {"role": "Architect", "message": "..."},
    {"role": "Coder", "message": "..."}
  ],
  "templates": {
    "architecture": "# Architecture\n...",
    "constraints": "# Constraints\n..."
  }
}
```

**Response:**
```json
{
  "success": true,
  "architecture_doc": "# Architecture\n\n## Tech Stack\nPreact + Tailwind...",
  "constraints_doc": "# Constraints\n\n## Bundle Size\nMax 50KB...",
  "files_created": [
    "architecture/ARCHITECTURE.md",
    "architecture/CONSTRAINTS.md"
  ]
}
```

---

## Audit Agent (Port 5004)

### Endpoint: `POST /audit/validate`

Audit agent validates implementation against constraints.

**Request:**
```json
{
  "project_name": "landing_page",
  "constraints_doc": "# Constraints\n...",
  "code_files": ["code/index.html", "code/App.jsx"],
  "workspace_path": "workspaces/landing_page"
}
```

**Response:**
```json
{
  "success": true,
  "passed": false,
  "violations": [
    {
      "constraint": "Max bundle size 50KB",
      "actual": "67KB",
      "severity": "error"
    }
  ],
  "warnings": [
    {
      "constraint": "Accessibility - ARIA labels",
      "issue": "Contact form missing aria-label",
      "severity": "warning"
    }
  ],
  "recommendations": [
    "Remove unused Tailwind classes",
    "Add aria-labels to form inputs"
  ]
}
```

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "success": false,
  "error": "Error message here",
  "error_type": "validation_error|agent_error|timeout",
  "details": {
    "field": "requirements",
    "issue": "Cannot be empty"
  }
}
```

---

## Orchestrator Workflow

The orchestrator (Claude Code) runs this workflow:

```python
# 1. Check agent health
GET http://localhost:5001/health
GET http://localhost:5002/health

# 2. Run dialogue (4 turns)
POST http://localhost:5001/architect/propose
  → proposal

POST http://localhost:5002/coder/evaluate
  → evaluation

POST http://localhost:5001/architect/respond
  → response, consensus_signal

POST http://localhost:5002/coder/finalize
  → approved

# 3. Synthesize docs
POST http://localhost:5003/docs/synthesize
  → architecture_doc, constraints_doc

# 4. Implement code
POST http://localhost:5002/coder/implement
  → files_created

# 5. Audit implementation
POST http://localhost:5004/audit/validate
  → violations, warnings

# 6. If violations, decide: retry or fix
```

---

## Starting Agent Servers

```bash
# Terminal 1: Architect
python system/servers/architect_server.py

# Terminal 2: Coder
python system/servers/coder_server.py

# Terminal 3: Docs
python system/servers/docs_server.py

# Terminal 4: Audit
python system/servers/audit_server.py
```

Or use launcher script:

```bash
# Starts all servers in background
python system/start_agents.py
```

---

## Benefits

1. **True Isolation** - Each agent is a separate process with own ClaudeSDKClient
2. **No SDK Conflicts** - HTTP communication, no nested clients
3. **Scalable** - Can run agents on different machines
4. **Observable** - Each server logs independently
5. **Debuggable** - Test agents individually via curl/Postman
6. **Restartable** - Restart failed agents without affecting others
7. **Stateful** - Agents maintain conversation context
8. **Language Agnostic** - Could rewrite agents in any language

---

## Future Enhancements

- WebSocket support for streaming responses
- Agent-to-agent direct communication
- Distributed agents across network
- Load balancing for multiple instances
- Persistent storage (Redis/PostgreSQL)
- Authentication/authorization
