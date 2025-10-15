"""
Base Agent Server Infrastructure

Provides common functionality for all agent servers:
- FastAPI app setup
- ClaudeSDKClient initialization
- Health check endpoint
- Context reset endpoint
- Error handling
- Logging
"""

import asyncio
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import sys

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions


class BaseAgentServer:
    """Base class for all agent servers."""

    def __init__(
        self,
        agent_name: str,
        port: int,
        system_prompt: str,
        max_turns: int = 20
    ):
        self.agent_name = agent_name
        self.port = port
        self.system_prompt = system_prompt
        self.max_turns = max_turns

        self.client: Optional[ClaudeSDKClient] = None
        self.app = FastAPI(title=f"{agent_name} Agent Server")
        self.start_time = time.time()

        # Setup routes
        self._setup_routes()

    def _setup_routes(self):
        """Setup common routes for all agent servers."""

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "agent": self.agent_name.lower(),
                "connected": self.client is not None,
                "uptime_seconds": time.time() - self.start_time
            }

        @self.app.post("/reset")
        async def reset_context():
            """Reset agent context (disconnect and reconnect)."""
            try:
                if self.client:
                    await self.client.disconnect()
                await self._initialize_client()
                return {
                    "success": True,
                    "message": f"{self.agent_name} context reset"
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    async def _initialize_client(self):
        """Initialize ClaudeSDKClient with system prompt."""
        print(f"[{self.agent_name}] Initializing ClaudeSDKClient...")

        self.client = ClaudeSDKClient(
            options=ClaudeAgentOptions(
                system_prompt=self.system_prompt,
                max_turns=self.max_turns
            )
        )

        await self.client.connect()
        print(f"[{self.agent_name}] Connected successfully")

    async def query_agent(self, prompt: str, verbose: bool = True) -> str:
        """
        Send a query to the agent and get response.

        Args:
            prompt: The prompt to send to the agent
            verbose: Whether to print the interaction

        Returns:
            The agent's response text
        """
        if not self.client:
            raise RuntimeError(f"{self.agent_name} client not initialized")

        if verbose:
            print(f"\n[{self.agent_name}] Prompt:\n{prompt}\n")

        response_text = []

        try:
            response_generator = self.client.send_message(prompt)

            async for chunk in response_generator:
                if hasattr(chunk, 'text') and chunk.text:
                    response_text.append(chunk.text)
                    if verbose:
                        print(chunk.text, end='', flush=True)

            if verbose:
                print("\n")

            return ''.join(response_text)

        except Exception as e:
            print(f"\n[{self.agent_name}] Error: {e}")
            raise

    async def startup(self):
        """Startup tasks - initialize client."""
        await self._initialize_client()

    async def shutdown(self):
        """Shutdown tasks - disconnect client."""
        if self.client:
            await self.client.disconnect()
            print(f"[{self.agent_name}] Disconnected")

    def run(self):
        """Run the server."""
        import uvicorn

        print(f"\n{'='*60}")
        print(f"{self.agent_name} Agent Server")
        print(f"Port: {self.port}")
        print(f"Base URL: http://localhost:{self.port}")
        print(f"{'='*60}\n")

        uvicorn.run(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )


class ErrorResponse(BaseModel):
    """Standard error response format."""
    success: bool = False
    error: str
    error_type: str
    details: Optional[Dict[str, Any]] = None


def create_error_response(
    error_message: str,
    error_type: str = "agent_error",
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create a standard error response."""
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": error_message,
            "error_type": error_type,
            "details": details or {}
        }
    )
