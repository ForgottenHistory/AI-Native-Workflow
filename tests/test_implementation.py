#!/usr/bin/env python3
"""
Phase 3: Implementation Test

Tests whether Coder agent can implement based on:
- ARCHITECTURE.md (synthesized decisions)
- CONSTRAINTS.md (synthesized rules)
- Conversation context

This validates the full loop: Dialogue → Docs → Code
"""

import asyncio
import re
from pathlib import Path
from datetime import datetime
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ResultMessage,
    PermissionResultAllow,
    PermissionResultDeny,
    ToolPermissionContext
)


def strip_unicode(text: str) -> str:
    """Remove problematic Unicode characters for Windows console (cp1252)."""
    # Only keep ASCII printable chars, newlines, and tabs
    return ''.join(c if (ord(c) < 128 or c in '\n\r\t') else '' for c in text)


async def allow_code_writes(
    tool_name: str,
    input_data: dict,
    context: ToolPermissionContext
) -> PermissionResultAllow | PermissionResultDeny:
    """Allow Write/Edit tools only to code/ directory."""

    # Always allow read operations
    if tool_name in ["Read", "Glob", "Grep"]:
        return PermissionResultAllow()

    # Allow writes only to code/ directory
    if tool_name in ["Write", "Edit"]:
        file_path = input_data.get("file_path", "")

        # Allow code/ directory writes
        if file_path.startswith("code/") or file_path.startswith("./code/"):
            print(f"[ALLOW] {tool_name}: {file_path}")
            return PermissionResultAllow()

        # Deny everything else
        print(f"[DENY] {tool_name}: {file_path} (not in code/)")
        return PermissionResultDeny(
            message="Can only write to code/ directory"
        )

    # Deny all other tools
    return PermissionResultDeny(
        message=f"Tool {tool_name} not allowed"
    )


async def query_agent(client, agent_name: str, prompt: str) -> str:
    """Send query to an agent and collect response."""
    print(f"\n{'='*80}")
    print(f"{agent_name}:")
    print("-" * 80)

    await client.query(prompt)

    response_parts = []
    async for message in client.receive_response():
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    # Print with Unicode stripped for Windows console
                    print(strip_unicode(block.text), end='', flush=True)
                    # But save the original text with all Unicode
                    response_parts.append(block.text)
        elif isinstance(message, ResultMessage):
            if message.total_cost_usd and message.total_cost_usd > 0:
                print(f"\n[$] Cost: ${message.total_cost_usd:.4f}")

    full_response = ''.join(response_parts)
    print()  # Newline after response
    return full_response


async def main():
    print("="*80)
    print("PHASE 3: IMPLEMENTATION TEST")
    print("="*80)
    print()
    print("Testing whether Coder agent can implement based on synthesized docs:")
    print("  - ARCHITECTURE.md (design decisions)")
    print("  - CONSTRAINTS.md (implementation rules)")
    print()

    # Check prerequisites
    arch_file = Path("architecture/ARCHITECTURE.md")
    constraints_file = Path("architecture/CONSTRAINTS.md")

    if not arch_file.exists():
        print(f"[ERROR] {arch_file} not found. Run test_docs_agent.py first.")
        return

    if not constraints_file.exists():
        print(f"[ERROR] {constraints_file} not found. Run test_docs_agent.py first.")
        return

    # Read architecture and constraints
    architecture = arch_file.read_text(encoding='utf-8')
    constraints = constraints_file.read_text(encoding='utf-8')

    print(f"[OK] Loaded ARCHITECTURE.md ({len(architecture)} chars)")
    print(f"[OK] Loaded CONSTRAINTS.md ({len(constraints)} chars)")
    print()

    # Initialize Coder agent
    coder_prompt = (
        "You are an implementation engineer. You receive architecture documentation and constraints, "
        "and you implement working code that follows the specifications exactly. "
        "Use the Write tool to create files in the code/ directory. "
        "Follow all constraints exactly. Use best practices for the chosen tech stack."
    )

    coder_options = ClaudeAgentOptions(
        system_prompt=coder_prompt,
        max_turns=20,  # Allow many tool uses for implementation
        can_use_tool=allow_code_writes,  # Permission callback
        cwd="."  # Set working directory
    )

    print("[*] Initializing Coder agent for implementation...")
    coder_client = ClaudeSDKClient(options=coder_options)
    await coder_client.connect()
    print("[OK] Coder agent connected\n")

    try:
        # Let the Coder agent decide how to implement
        print("[*] Asking Coder agent to implement the landing page...")
        implementation_response = await query_agent(
            client=coder_client,
            agent_name="CODER (Implementation)",
            prompt=f"""You have full architecture and constraints for a landing page project:

ARCHITECTURE.md:
{architecture}

CONSTRAINTS.md:
{constraints}

YOUR TASK:
Implement this landing page following the architecture and constraints exactly.

REQUIREMENTS:
- Create ALL files needed for a working implementation in the code/ directory
- Follow CONSTRAINTS.md exactly (Vite, React, TypeScript, Tailwind, no libraries)
- Use exact tech stack from ARCHITECTURE.md
- Include: package.json, configs, index.html, all src files (components, hooks, etc.)
- Make autonomous decisions about structure and implementation approach

IMPORTANT:
- Use the Write tool to create each file
- File paths should be relative to code/ (e.g., "code/package.json", "code/src/App.tsx")
- You decide what files to create and in what order
- Implement the complete, working project

Begin implementation. Create all project files."""
        )

        # Save implementation log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = Path("logs") / f"implementation_log_{timestamp}.md"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("# IMPLEMENTATION LOG\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Agent:** Coder Agent\n")
            f.write(f"**Project:** Landing Page (from synthesized architecture)\n")
            f.write(f"**Method:** Autonomous implementation from architecture docs\n\n")
            f.write("---\n\n")
            f.write("## Implementation Response\n\n")
            f.write(f"{implementation_response}\n\n")
            f.write("---\n\n")

        print(f"\n[SAVE] Implementation log saved to: {log_file}")

        # Summary
        print("\n" + "="*80)
        print("IMPLEMENTATION COMPLETE")
        print("="*80)
        print("\nGenerated files:")
        print(f"  - {log_file} (implementation transcript)")
        print(f"  - code/ (implementation files created by agent)")
        print("\nNext steps:")
        print("  1. Review files created in code/ directory")
        print("  2. Run: cd code && npm install && npm run dev")
        print("  3. Validate against CONSTRAINTS.md (bundle size, performance)")
        print("\nValidation checklist:")
        print("  - Does code match ARCHITECTURE.md decisions?")
        print("  - Does code follow CONSTRAINTS.md rules?")
        print("  - Is the implementation complete and functional?")
        print("  - Can it actually be built and run?")
        print("  - Did the agent make good autonomous decisions?")

    finally:
        await coder_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
