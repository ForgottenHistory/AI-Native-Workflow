#!/usr/bin/env python3
"""
Architect Agent Server

Port: 5001
Role: Proposes architecture and tech stack based on requirements
"""

import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from fastapi import HTTPException
from base_agent_server import BaseAgentServer, create_error_response


# Request/Response Models

class ProposeRequest(BaseModel):
    """Request to propose architecture."""
    project_name: str
    requirements: str
    context: Optional[Dict[str, Any]] = None


class ProposeResponse(BaseModel):
    """Response with architecture proposal."""
    success: bool
    proposal: str
    tech_stack: Dict[str, str]
    reasoning: str
    conversation_turn: int


class RespondRequest(BaseModel):
    """Request to respond to coder feedback."""
    project_name: str
    coder_feedback: str
    previous_proposal: str
    conversation_turn: int


class RespondResponse(BaseModel):
    """Response to coder feedback."""
    success: bool
    response: str
    revised_proposal: Optional[str] = None
    consensus_signal: Optional[str] = None
    conversation_turn: int


# Agent Server

class ArchitectServer(BaseAgentServer):
    """Architect agent server."""

    def __init__(self):
        system_prompt = """You are an Architect AI specializing in software architecture design.

Your role:
- Analyze project requirements
- Propose appropriate tech stacks and architectures
- Consider trade-offs (performance, maintainability, complexity)
- Collaborate with Coder to reach architectural consensus
- Provide clear reasoning for your decisions

When proposing architecture:
1. Be SPECIFIC (exact frameworks, tools, versions if relevant)
2. Consider the Coder's implementation concerns
3. Optimize for simplicity and maintainability
4. Signal consensus with "CONSENSUS:" when agreement is reached

You are in a multi-turn conversation with a Coder agent. Be collaborative and open to feedback."""

        super().__init__(
            agent_name="Architect",
            port=5001,
            system_prompt=system_prompt,
            max_turns=20
        )

        # Setup Architect-specific routes
        self._setup_architect_routes()

    def _setup_architect_routes(self):
        """Setup Architect-specific routes."""

        @self.app.post("/architect/propose", response_model=ProposeResponse)
        async def propose_architecture(request: ProposeRequest):
            """Propose initial architecture based on requirements."""
            try:
                prompt = f"""Project: {request.project_name}

Requirements:
{request.requirements}

Propose a specific tech stack and architecture. Include:
- Framework choice with rationale
- Styling approach
- Key implementation decisions
- Build/dev tools

Be specific and concrete. This is Turn 1 of the architectural dialogue."""

                response = await self.query_agent(prompt, verbose=True)

                # Extract tech stack (simplified - could use structured output)
                tech_stack = self._extract_tech_stack(response)

                return ProposeResponse(
                    success=True,
                    proposal=response,
                    tech_stack=tech_stack,
                    reasoning=response,  # Full response contains reasoning
                    conversation_turn=1
                )

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/architect/respond", response_model=RespondResponse)
        async def respond_to_feedback(request: RespondRequest):
            """Respond to coder's feedback."""
            try:
                prompt = f"""The Coder evaluated your proposal and provided this feedback:

{request.coder_feedback}

Your previous proposal was:
{request.previous_proposal}

Respond to their feedback. Address concerns, refine the architecture if needed.
If you've reached a good solution, signal with "CONSENSUS: [summary]"

This is Turn {request.conversation_turn + 1} of the dialogue."""

                response = await self.query_agent(prompt, verbose=True)

                # Check for consensus signal
                consensus_signal = None
                if "CONSENSUS:" in response or "CONSENSUS" in response:
                    # Extract consensus line
                    for line in response.split('\n'):
                        if "CONSENSUS" in line:
                            consensus_signal = line.strip()
                            break

                return RespondResponse(
                    success=True,
                    response=response,
                    revised_proposal=response if consensus_signal else None,
                    consensus_signal=consensus_signal,
                    conversation_turn=request.conversation_turn + 1
                )

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    def _extract_tech_stack(self, response: str) -> Dict[str, str]:
        """
        Extract tech stack from response.

        This is a simplified extraction. Could use structured output
        or more sophisticated parsing.
        """
        tech_stack = {}

        # Common keywords to look for
        frameworks = ['React', 'Vue', 'Svelte', 'Preact', 'Angular', 'Next.js', 'Astro']
        styling = ['Tailwind', 'CSS', 'SCSS', 'styled-components', 'CSS Modules']
        build_tools = ['Vite', 'Webpack', 'Parcel', 'esbuild']

        response_lower = response.lower()

        for fw in frameworks:
            if fw.lower() in response_lower:
                tech_stack['framework'] = fw
                break

        for style in styling:
            if style.lower() in response_lower:
                tech_stack['styling'] = style
                break

        for tool in build_tools:
            if tool.lower() in response_lower:
                tech_stack['build_tool'] = tool
                break

        return tech_stack


async def main():
    """Run the Architect agent server."""
    server = ArchitectServer()

    # Initialize client on startup
    await server.startup()

    # Run server (this blocks)
    try:
        server.run()
    finally:
        await server.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
