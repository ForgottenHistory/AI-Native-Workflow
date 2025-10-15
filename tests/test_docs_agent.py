#!/usr/bin/env python3
"""
Test Docs Agent in isolation using existing conversation log.
"""

import asyncio
import re
from pathlib import Path
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ResultMessage
)


def strip_unicode(text: str) -> str:
    """Remove problematic Unicode characters for Windows console (cp1252)."""
    # Only keep ASCII printable chars, newlines, and tabs
    # This is safest for Windows console output
    return ''.join(c if (ord(c) < 128 or c in '\n\r\t') else '' for c in text)


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
    # Read existing conversation log
    conversation_file = Path("conversation/stateful_session_20251015_022645.md")
    if not conversation_file.exists():
        print(f"Error: {conversation_file} not found")
        return

    conversation_text = conversation_file.read_text(encoding='utf-8')
    print(f"[*] Loaded conversation from: {conversation_file}")
    print(f"[*] Conversation length: {len(conversation_text)} chars\n")

    # Read templates
    arch_template = Path("ARCHITECTURE_TEMPLATE.md").read_text(encoding='utf-8')
    constraints_template = Path("CONSTRAINTS_TEMPLATE.md").read_text(encoding='utf-8')

    # Initialize Docs agent
    docs_prompt = (
        "You are a documentation synthesizer. Read conversations and OUTPUT structured markdown documentation. "
        "When asked to create ARCHITECTURE.md or CONSTRAINTS.md, OUTPUT the complete markdown content as text. "
        "DO NOT use tools. DO NOT try to write files. Just OUTPUT markdown text directly. "
        "Preserve decisions, trade-offs, rationale, and the 'why' behind decisions."
    )

    docs_options = ClaudeAgentOptions(
        system_prompt=docs_prompt,
        max_turns=3
    )

    print("[*] Initializing Docs agent...")
    docs_client = ClaudeSDKClient(options=docs_options)
    await docs_client.connect()
    print("[OK] Docs agent connected\n")

    try:
        # Request ARCHITECTURE.md
        print("[DOC] Synthesizing ARCHITECTURE.md...")
        architecture_doc = await query_agent(
            client=docs_client,
            agent_name="DOCS AGENT (Architecture)",
            prompt=f"""Read this Architect ⟷ Coder dialogue and OUTPUT the complete ARCHITECTURE.md content as markdown text:

CONVERSATION:
{conversation_text}

TEMPLATE TO FOLLOW:
{arch_template}

TASK: Extract all architectural decisions, tech stack choices, trade-offs, and rationale from the conversation above. OUTPUT the complete ARCHITECTURE.md markdown content following the template format. Replace [placeholders] with actual content from the conversation. Be specific with numbers and technologies.

IMPORTANT: Do NOT use any tools. Do NOT try to write files. Just OUTPUT the markdown text directly in your response. Your entire response should be the ARCHITECTURE.md content ready to save."""
        )

        # Save ARCHITECTURE.md
        arch_file = Path("architecture") / "ARCHITECTURE.md"
        arch_file.parent.mkdir(parents=True, exist_ok=True)
        arch_file.write_text(architecture_doc, encoding='utf-8')
        print(f"[OK] Saved to: {arch_file}\n")

        # Request CONSTRAINTS.md
        print("[DOC] Synthesizing CONSTRAINTS.md...")
        constraints_doc = await query_agent(
            client=docs_client,
            agent_name="DOCS AGENT (Constraints)",
            prompt=f"""Read this Architect ⟷ Coder dialogue and OUTPUT the complete CONSTRAINTS.md content as markdown text:

CONVERSATION:
{conversation_text}

TEMPLATE TO FOLLOW:
{constraints_template}

TASK: Extract all constraints, performance budgets, testing requirements, and rules from the conversation above. OUTPUT the complete CONSTRAINTS.md markdown content following the template format. Make constraints testable and specific. Include performance numbers mentioned in the dialogue.

IMPORTANT: Do NOT use any tools. Do NOT try to write files. Just OUTPUT the markdown text directly in your response. Your entire response should be the CONSTRAINTS.md content ready to save."""
        )

        # Save CONSTRAINTS.md
        constraints_file = Path("architecture") / "CONSTRAINTS.md"
        constraints_file.write_text(constraints_doc, encoding='utf-8')
        print(f"[OK] Saved to: {constraints_file}\n")

        print("=" * 80)
        print("[DONE] Documentation synthesis complete!")
        print("=" * 80)
        print("\nGenerated files:")
        print(f"  - {arch_file}")
        print(f"  - {constraints_file}")

    finally:
        await docs_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
