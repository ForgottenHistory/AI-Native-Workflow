#!/usr/bin/env python3
"""
Coder Agent Server

Port: 5002
Role: Evaluates architecture proposals and implements code
"""

import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from fastapi import HTTPException
from base_agent_server import BaseAgentServer, create_error_response


# Request/Response Models

class EvaluateRequest(BaseModel):
    """Request to evaluate architect's proposal."""
    project_name: str
    architect_proposal: str
    conversation_turn: int


class EvaluateResponse(BaseModel):
    """Response with evaluation."""
    success: bool
    evaluation: str
    agreements: List[str]
    concerns: List[str]
    alternatives: List[str]
    effort_estimate: str
    conversation_turn: int


class FinalizeRequest(BaseModel):
    """Request for final approval."""
    project_name: str
    architect_response: str
    conversation_turn: int


class FinalizeResponse(BaseModel):
    """Final approval response."""
    success: bool
    final_evaluation: str
    approved: bool
    conversation_turn: int


class ImplementRequest(BaseModel):
    """Request to implement code."""
    project_name: str
    architecture_doc: str
    constraints_doc: str
    workspace_path: str


class ImplementResponse(BaseModel):
    """Implementation response."""
    success: bool
    files_created: List[str]
    summary: str
    next_steps: List[str]


# Agent Server

class CoderServer(BaseAgentServer):
    """Coder agent server."""

    def __init__(self):
        system_prompt = """You are a Coder AI specializing in software implementation.

Your role:
- Evaluate architectural proposals for implementation feasibility
- Identify concerns about complexity, maintainability, performance
- Suggest practical alternatives when needed
- Implement code following architecture and constraints
- Write clean, well-documented, production-ready code

When evaluating architecture:
1. Identify what you AGREE with
2. Raise specific CONCERNS (complexity, bundle size, compatibility)
3. Suggest BETTER alternatives if applicable
4. Estimate implementation EFFORT
5. Signal approval with "AGREED:" when satisfied

When implementing:
1. Follow ARCHITECTURE.md exactly
2. Respect all CONSTRAINTS.md requirements
3. Write production-quality code
4. Include comments and documentation
5. Use modern best practices

You are collaborating with an Architect. Be constructive and specific in feedback."""

        super().__init__(
            agent_name="Coder",
            port=5002,
            system_prompt=system_prompt,
            max_turns=20
        )

        # Setup Coder-specific routes
        self._setup_coder_routes()

    def _setup_coder_routes(self):
        """Setup Coder-specific routes."""

        @self.app.post("/coder/evaluate", response_model=EvaluateResponse)
        async def evaluate_proposal(request: EvaluateRequest):
            """Evaluate architect's proposal."""
            try:
                prompt = f"""The Architect proposed this architecture:

{request.architect_proposal}

Evaluate this proposal. What do you AGREE with? What CONCERNS do you have?
Any BETTER alternatives? Estimate implementation EFFORT (hours/complexity).

Be specific and constructive. This is Turn {request.conversation_turn + 1} of the dialogue."""

                response = await self.query_agent(prompt, verbose=True)

                # Extract structured data (simplified)
                agreements = self._extract_list(response, "AGREE")
                concerns = self._extract_list(response, "CONCERN")
                alternatives = self._extract_list(response, "ALTERNATIVE")
                effort = self._extract_effort(response)

                return EvaluateResponse(
                    success=True,
                    evaluation=response,
                    agreements=agreements,
                    concerns=concerns,
                    alternatives=alternatives,
                    effort_estimate=effort,
                    conversation_turn=request.conversation_turn + 1
                )

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/coder/finalize", response_model=FinalizeResponse)
        async def finalize_architecture(request: FinalizeRequest):
            """Give final approval or concerns."""
            try:
                prompt = f"""The Architect responded to your feedback:

{request.architect_response}

Give your final evaluation. If the architecture is good, signal "AGREED: [summary]".
If you still have concerns, state them clearly.

This is Turn {request.conversation_turn + 1} (final turn of dialogue)."""

                response = await self.query_agent(prompt, verbose=True)

                # Check for approval
                approved = "AGREED" in response or "APPROVED" in response

                return FinalizeResponse(
                    success=True,
                    final_evaluation=response,
                    approved=approved,
                    conversation_turn=request.conversation_turn + 1
                )

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/coder/implement", response_model=ImplementResponse)
        async def implement_code(request: ImplementRequest):
            """Implement code from architecture docs."""
            try:
                prompt = f"""Implement the complete project following this architecture:

ARCHITECTURE:
{request.architecture_doc}

CONSTRAINTS:
{request.constraints_doc}

Generate ALL necessary code files. Be comprehensive and production-ready.
List each file you create with its purpose.

The code will be written to: {request.workspace_path}/code/"""

                response = await self.query_agent(prompt, verbose=True)

                # In real implementation, agent would use Write tool
                # For now, return what would be created
                files_created = self._extract_files(response)

                return ImplementResponse(
                    success=True,
                    files_created=files_created,
                    summary="Implementation complete (files listed in response)",
                    next_steps=["Review code", "Test implementation", "Run build"]
                )

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    def _extract_list(self, text: str, keyword: str) -> List[str]:
        """Extract list items containing keyword."""
        items = []
        for line in text.split('\n'):
            if keyword in line.upper():
                # Extract the item
                item = line.strip('- ').strip()
                if item and item not in items:
                    items.append(item)
        return items[:5]  # Limit to 5 items

    def _extract_effort(self, text: str) -> str:
        """Extract effort estimate from text."""
        keywords = ['hour', 'day', 'week', 'simple', 'complex', 'moderate']
        text_lower = text.lower()

        for keyword in keywords:
            if keyword in text_lower:
                # Find sentence containing keyword
                for sentence in text.split('.'):
                    if keyword in sentence.lower():
                        return sentence.strip()

        return "Moderate complexity"

    def _extract_files(self, text: str) -> List[str]:
        """Extract file names from implementation response."""
        files = []
        # Look for common code file extensions
        import re
        patterns = [
            r'`([^`]+\.(html|js|jsx|css|json|md|ts|tsx))`',
            r'"([^"]+\.(html|js|jsx|css|json|md|ts|tsx))"',
            r'([a-zA-Z0-9_/-]+\.(html|js|jsx|css|json|md|ts|tsx))'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                file = match[0] if isinstance(match, tuple) else match
                if file and file not in files:
                    files.append(file)

        return files[:20]  # Limit to 20 files


async def main():
    """Run the Coder agent server."""
    server = CoderServer()

    # Initialize client on startup
    await server.startup()

    # Run server (this blocks)
    try:
        server.run()
    finally:
        await server.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
