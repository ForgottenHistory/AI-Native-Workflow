#!/usr/bin/env python3
"""
Documentation Synthesis Agent - Standalone Subprocess

Reads architectural dialogue and generates structured documentation.
Runs as a subprocess invoked by orchestrator tool.

Usage: python synthesize_docs.py <project_name>
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

from utils.agent_utils import query_agent, create_docs_agent


async def synthesize_docs(project_name: str) -> dict:
    """
    Synthesize ARCHITECTURE.md and CONSTRAINTS.md from conversation.

    Returns dict with:
    - success: bool
    - files_created: list[str]
    - error: str (if failed)
    """
    workspace_root = Path(__file__).parent.parent.parent / "workspaces"
    workspace = workspace_root / project_name

    # Find conversation file
    conv_dir = workspace / "conversation"
    if not conv_dir.exists():
        return {
            "success": False,
            "error": "No conversation directory found"
        }

    conv_files = list(conv_dir.glob("*.md"))
    if not conv_files:
        return {
            "success": False,
            "error": "No conversation files found"
        }

    latest_conv = max(conv_files, key=lambda p: p.stat().st_mtime)
    conversation_text = latest_conv.read_text(encoding='utf-8')

    # Load templates
    templates_dir = Path(__file__).parent.parent / "templates"
    arch_template = (templates_dir / "ARCHITECTURE_TEMPLATE.md").read_text(encoding='utf-8')
    constraints_template = (templates_dir / "CONSTRAINTS_TEMPLATE.md").read_text(encoding='utf-8')

    try:
        # Initialize Docs agent
        docs_client = await create_docs_agent()

        # Generate ARCHITECTURE.md
        arch_doc = await query_agent(
            docs_client,
            "DOCS AGENT (Architecture)",
            f"""Read this conversation and OUTPUT complete ARCHITECTURE.md as markdown:

CONVERSATION:
{conversation_text}

TEMPLATE:
{arch_template}

OUTPUT the complete ARCHITECTURE.md content. Do NOT use tools.""",
            verbose=False
        )

        # Generate CONSTRAINTS.md
        constraints_doc = await query_agent(
            docs_client,
            "DOCS AGENT (Constraints)",
            f"""Read this conversation and OUTPUT complete CONSTRAINTS.md as markdown:

CONVERSATION:
{conversation_text}

TEMPLATE:
{constraints_template}

OUTPUT the complete CONSTRAINTS.md content. Do NOT use tools.""",
            verbose=False
        )

        # Save files
        arch_dir = workspace / "architecture"
        arch_dir.mkdir(parents=True, exist_ok=True)

        arch_file = arch_dir / "ARCHITECTURE.md"
        arch_file.write_text(arch_doc, encoding='utf-8')

        constraints_file = arch_dir / "CONSTRAINTS.md"
        constraints_file.write_text(constraints_doc, encoding='utf-8')

        await docs_client.disconnect()

        return {
            "success": True,
            "files_created": [
                str(arch_file.relative_to(workspace)),
                str(constraints_file.relative_to(workspace))
            ]
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
            "error": "Usage: python synthesize_docs.py <project_name>"
        }))
        sys.exit(1)

    project_name = sys.argv[1]

    # Run docs synthesis
    result = await synthesize_docs(project_name)

    # Output JSON results to stdout
    print(json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    asyncio.run(main())
