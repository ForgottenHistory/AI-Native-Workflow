#!/usr/bin/env python3
"""
Architectural Dialogue Agent - Standalone Subprocess

Spawns Architect and Coder agents for multi-turn dialogue.
Runs as a subprocess invoked by orchestrator tool.

Usage: python run_dialogue.py <project_name>
Outputs: JSON results to stdout, files to workspace
Exit code: 0 = success, non-zero = failure
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.agent_utils import (
    query_agent,
    create_architect_agent,
    create_coder_agent
)


async def run_dialogue(project_name: str) -> dict:
    """
    Run Architect <-> Coder architectural dialogue.

    Returns dict with:
    - success: bool
    - conversation_file: str
    - consensus_reached: bool
    - turns: int
    - error: str (if failed)
    """
    workspace_root = Path(__file__).parent.parent.parent / "workspaces"
    workspace = workspace_root / project_name
    workspace.mkdir(parents=True, exist_ok=True)

    # Check for requirements
    requirements_file = workspace / "requirements.md"
    if not requirements_file.exists():
        return {
            "success": False,
            "error": "No requirements.md file found in workspace"
        }

    requirements = requirements_file.read_text(encoding='utf-8')

    try:
        # Initialize agents (separate ClaudeSDKClient instances)
        architect_client = await create_architect_agent()
        coder_client = await create_coder_agent()

        conversation_log = []

        # Turn 1: Architect proposes
        architect_msg_1 = await query_agent(
            architect_client,
            "ARCHITECT (Turn 1)",
            f"""Project requirements:
{requirements}

Propose a specific tech stack and architecture. Include:
- Framework choice
- Styling approach
- Key implementation decisions

Be specific and concrete.""",
            verbose=False
        )
        conversation_log.append(("Architect", architect_msg_1))

        # Turn 2: Coder evaluates
        coder_msg_1 = await query_agent(
            coder_client,
            "CODER (Turn 1)",
            f"""The architect proposed:

{architect_msg_1}

Evaluate this proposal. What do you AGREE with? What CONCERNS do you have?
Any BETTER alternatives? Estimate implementation EFFORT.""",
            verbose=False
        )
        conversation_log.append(("Coder", coder_msg_1))

        # Turn 3: Architect responds
        architect_msg_2 = await query_agent(
            architect_client,
            "ARCHITECT (Turn 2)",
            f"""The coder's evaluation:

{coder_msg_1}

Respond to their feedback. Address concerns, refine the architecture.
Move toward consensus.""",
            verbose=False
        )
        conversation_log.append(("Architect", architect_msg_2))

        # Turn 4: Coder final
        coder_msg_2 = await query_agent(
            coder_client,
            "CODER (Turn 2)",
            f"""The architect's response:

{architect_msg_2}

Final evaluation. Signal 'AGREED:' if architecture is good, or raise final concerns.""",
            verbose=False
        )
        conversation_log.append(("Coder", coder_msg_2))

        # Check consensus
        consensus = (
            ("CONSENSUS" in architect_msg_2 or "CONSENSUS" in architect_msg_1) and
            ("AGREED" in coder_msg_2 or "AGREED" in coder_msg_1)
        )

        # Save conversation
        conv_dir = workspace / "conversation"
        conv_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        conv_file = conv_dir / f"dialogue_{timestamp}.md"

        with open(conv_file, 'w', encoding='utf-8') as f:
            f.write("# Architectural Dialogue\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Project:** {project_name}\n")
            f.write(f"**Consensus:** {'YES' if consensus else 'NO'}\n\n")
            f.write("---\n\n")

            for role, msg in conversation_log:
                f.write(f"## {role}\n\n{msg}\n\n---\n\n")

        # Cleanup
        await architect_client.disconnect()
        await coder_client.disconnect()

        return {
            "success": True,
            "conversation_file": str(conv_file.relative_to(workspace)),
            "consensus_reached": consensus,
            "turns": len(conversation_log)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def main():
    """Main entry point for subprocess."""
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "error": "Usage: python run_dialogue.py <project_name>"
        }))
        sys.exit(1)

    project_name = sys.argv[1]

    # Run dialogue
    result = await run_dialogue(project_name)

    # Output JSON results to stdout
    print(json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    asyncio.run(main())
