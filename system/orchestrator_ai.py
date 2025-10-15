#!/usr/bin/env python3
"""
AI Orchestrator Agent

A true AI orchestrator that spawns specialist agents as subprocesses.
The orchestrator is an LLM that reasons about project state, validates results,
and adapts strategy when things fail.

Architecture:
- Orchestrator: LLM (ClaudeSDKClient) with tools
- Tools: Spawn agent subprocesses (separate Python scripts)
- Agents: Run in isolated processes, write results + logs
- Validation: Orchestrator reads results and validates completion
- Adaptation: Orchestrator reads logs when failures happen

Each agent runs as a separate process with isolated context.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

# Import orchestrator tools
from orchestrator_tools import (
    assess_workspace_state,
    run_architectural_dialogue,
    synthesize_documentation,
    list_files,
    read_log,
    read_file,
    WORKSPACE_ROOT
)


class AIOrchestrator:
    """
    AI Orchestrator Agent

    An LLM that orchestrates the software development workflow by:
    - Assessing project state
    - Invoking specialist agents as tools
    - Validating results
    - Reading logs to understand what happened
    - Adapting strategy when things fail
    """

    def __init__(self):
        self.client = None
        self.project_name = None
        self.workspace = None
        self.log_file = None

    async def initialize(self, project_name: str):
        """Initialize the AI Orchestrator Agent."""
        self.project_name = project_name
        self.workspace = WORKSPACE_ROOT / project_name
        self.workspace.mkdir(parents=True, exist_ok=True)

        # Create orchestration log
        logs_dir = self.workspace / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = logs_dir / f"orchestrator_{timestamp}.log"

        # System prompt for orchestrator LLM
        system_prompt = """You are an AI Project Orchestrator managing multi-agent software development.

Your role:
- Assess project state by checking what files exist
- Decide which specialist agent to invoke next
- Validate that each action succeeded
- Read logs when things fail to understand why
- Adapt strategy based on outcomes
- Guide the project to completion

Available tools:
1. assess_workspace_state(project_name) - Check what exists, current phase
2. run_architectural_dialogue(project_name) - Spawn Architect ⟷ Coder dialogue
3. synthesize_documentation(project_name) - Spawn Docs agent
4. list_files(project_name, directory) - Verify files were created
5. read_log(project_name, log_path) - Understand what happened
6. read_file(project_name, file_path) - Check file contents

Always validate after actions:
- Check if expected files were created
- Read logs if something seems wrong
- Adapt your approach if actions fail

You are running as a standalone process, and each tool spawns a separate agent subprocess.
Be explicit about your reasoning."""

        # Initialize orchestrator LLM
        options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            max_turns=30
        )

        self.log("Initializing AI Orchestrator LLM...")
        self.client = ClaudeSDKClient(options=options)
        await self.client.connect()

        self.log("AI Orchestrator LLM initialized")
        self.log(f"Project: {project_name}")
        self.log(f"Workspace: {self.workspace}")
        self.log("Orchestrator can spawn isolated agent subprocesses")

    def log(self, message: str):
        """Write to orchestration log."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)

        if self.log_file:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_msg + '\n')

    async def orchestrate(self, requirements: str):
        """
        Main orchestration method.

        Guides the orchestrator agent through the workflow using natural language
        and tool invocations.
        """
        self.log("\n" + "="*80)
        self.log("STARTING AI ORCHESTRATION")
        self.log("="*80)

        # Create requirements file
        req_file = self.workspace / "requirements.md"
        req_file.write_text(requirements, encoding='utf-8')
        self.log(f"Created requirements.md")

        # Initial assessment
        self.log("\n[ORCHESTRATOR] Assessing initial state...")
        state = assess_workspace_state(self.project_name)
        self.log(f"State: {json.dumps(state, indent=2)}")

        # Guide orchestrator through Phase 1: Dialogue
        if not state["has_conversation"] or not state["conversation_consensus"]:
            self.log("\n[ORCHESTRATOR] Running architectural dialogue...")

            dialogue_result = await run_architectural_dialogue(self.project_name)
            self.log(f"Dialogue result: {json.dumps(dialogue_result, indent=2)}")

            if dialogue_result["success"]:
                self.log(f"✓ Dialogue complete: {dialogue_result['conversation_file']}")
                self.log(f"  Consensus: {dialogue_result['consensus_reached']}")
                self.log(f"  Turns: {dialogue_result['turns']}")

                # Verify by reading state
                state = assess_workspace_state(self.project_name)
                self.log(f"✓ Verification - has_conversation: {state['has_conversation']}")
                self.log(f"✓ Verification - consensus: {state['conversation_consensus']}")
            else:
                self.log(f"✗ Dialogue failed: {dialogue_result.get('error')}")
                return

        # Guide orchestrator through Phase 2: Documentation
        if not state["has_architecture"] or not state["has_constraints"]:
            self.log("\n[ORCHESTRATOR] Synthesizing documentation...")

            docs_result = await synthesize_documentation(self.project_name)
            self.log(f"Documentation result: {json.dumps(docs_result, indent=2)}")

            if docs_result["success"]:
                self.log(f"✓ Documentation complete:")
                for file in docs_result["files_created"]:
                    self.log(f"  - {file}")

                # Verify by checking files
                arch_files = list_files(self.project_name, "architecture")
                self.log(f"✓ Verification - architecture files: {arch_files['count']}")
            else:
                self.log(f"✗ Documentation failed: {docs_result.get('error')}")
                return

        # Final state
        self.log("\n[ORCHESTRATOR] Final state assessment...")
        final_state = assess_workspace_state(self.project_name)
        self.log(f"Final state: {json.dumps(final_state, indent=2)}")

        self.log("\n" + "="*80)
        self.log("ORCHESTRATION COMPLETE")
        self.log("="*80)
        self.log(f"Phase reached: {final_state['current_phase']}")
        self.log(f"Files created: {len(final_state['files'])}")
        self.log(f"Log saved: {self.log_file.relative_to(self.workspace)}")

    async def cleanup(self):
        """Cleanup orchestrator agent."""
        if self.client:
            await self.client.disconnect()
        self.log("Orchestrator cleanup complete")


async def main():
    """Test the AI Orchestrator."""
    orchestrator = AIOrchestrator()

    project_name = "ai_orchestrated_project"
    requirements = """
# AI-Orchestrated Landing Page

Build a modern landing page with:
- Hero section with headline and CTA button
- Features section (3 feature cards)
- Contact form
- Dark mode toggle
- Responsive design
- Performance-focused (<250KB total page weight)

Tech preferences:
- Modern JavaScript framework
- Fast build times
- Minimal dependencies
"""

    try:
        await orchestrator.initialize(project_name)
        await orchestrator.orchestrate(requirements)
    finally:
        await orchestrator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
