#!/usr/bin/env python3
"""
Docs Agent Server

Port: 5003
Role: Synthesizes structured documentation from architectural dialogue
"""

from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel

from fastapi import HTTPException
from base_agent_server import BaseAgentServer, create_error_response


# Request/Response Models

class ConversationTurn(BaseModel):
    """Single turn in conversation."""
    role: str
    message: str


class SynthesizeRequest(BaseModel):
    """Request to synthesize documentation."""
    project_name: str
    conversation: List[ConversationTurn]
    templates: Dict[str, str]  # architecture_template, constraints_template


class SynthesizeResponse(BaseModel):
    """Documentation synthesis response."""
    success: bool
    architecture_doc: str
    constraints_doc: str
    files_created: List[str]


# Agent Server

class DocsServer(BaseAgentServer):
    """Docs agent server."""

    def __init__(self):
        system_prompt = """You are a Documentation Specialist AI.

Your role:
- Read architectural dialogues between Architect and Coder
- Extract key decisions, tech stack, architecture patterns
- Synthesize clean, structured documentation
- Follow provided templates exactly
- Preserve important reasoning and rationale

When synthesizing documentation:
1. Extract DECISIONS (what was chosen and why)
2. Extract TECH STACK (specific tools, frameworks, versions)
3. Extract CONSTRAINTS (requirements, limits, guidelines)
4. Follow the template structure
5. Be concise but complete
6. Use markdown formatting

Output only the final documentation content. Do NOT use tools or create files - just output the documentation text."""

        super().__init__(
            agent_name="Docs",
            port=5003,
            system_prompt=system_prompt,
            max_turns=20
        )

        # Setup Docs-specific routes
        self._setup_docs_routes()

    def _setup_docs_routes(self):
        """Setup Docs-specific routes."""

        @self.app.post("/docs/synthesize", response_model=SynthesizeResponse)
        async def synthesize_documentation(request: SynthesizeRequest):
            """Synthesize ARCHITECTURE.md and CONSTRAINTS.md from conversation."""
            try:
                # Format conversation
                conversation_text = self._format_conversation(request.conversation)

                # Generate ARCHITECTURE.md
                arch_prompt = f"""Read this architectural conversation and OUTPUT complete ARCHITECTURE.md following the template:

CONVERSATION:
{conversation_text}

TEMPLATE:
{request.templates.get('architecture_template', '# Architecture')}

OUTPUT the complete ARCHITECTURE.md content as markdown. Do NOT use tools."""

                architecture_doc = await self.query_agent(arch_prompt, verbose=True)

                # Generate CONSTRAINTS.md
                constraints_prompt = f"""Read this conversation and OUTPUT complete CONSTRAINTS.md following the template:

CONVERSATION:
{conversation_text}

TEMPLATE:
{request.templates.get('constraints_template', '# Constraints')}

OUTPUT the complete CONSTRAINTS.md content as markdown. Do NOT use tools."""

                constraints_doc = await self.query_agent(constraints_prompt, verbose=True)

                return SynthesizeResponse(
                    success=True,
                    architecture_doc=architecture_doc,
                    constraints_doc=constraints_doc,
                    files_created=[
                        f"architecture/ARCHITECTURE.md",
                        f"architecture/CONSTRAINTS.md"
                    ]
                )

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    def _format_conversation(self, conversation: List[ConversationTurn]) -> str:
        """Format conversation turns into readable text."""
        formatted = []

        for turn in conversation:
            formatted.append(f"## {turn.role}\n\n{turn.message}\n\n---\n")

        return '\n'.join(formatted)


def main():
    """Run the Docs agent server."""
    server = DocsServer()
    server.run()


if __name__ == "__main__":
    main()
