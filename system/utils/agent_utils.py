"""
Shared utilities for agent management and interaction.
"""

import re
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ResultMessage
)


def strip_emojis(text: str) -> str:
    """Remove emojis from text for Windows console compatibility."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\u2705"  # white heavy check mark
        "\u274C"  # cross mark
        "\u2714"  # check mark
        "\u2716"  # heavy multiplication x
        "\u26A0"  # warning
        "\u2B50"  # star
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)


async def query_agent(client: ClaudeSDKClient, agent_name: str, prompt: str, verbose: bool = True) -> str:
    """
    Send query to an agent and collect response.

    Args:
        client: The Claude SDK client instance
        agent_name: Name for logging/display
        prompt: The prompt to send
        verbose: Whether to print output to console

    Returns:
        The full agent response as text
    """
    if verbose:
        print(f"\n{'='*80}")
        print(f"{agent_name}:")
        print("-" * 80)

    await client.query(prompt)

    response_parts = []
    async for message in client.receive_response():
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    if verbose:
                        # Print with emojis stripped for Windows console
                        print(strip_emojis(block.text), end='', flush=True)
                    # But save the original text with emojis
                    response_parts.append(block.text)
        elif isinstance(message, ResultMessage):
            if verbose and message.total_cost_usd and message.total_cost_usd > 0:
                print(f"\n[$] Cost: ${message.total_cost_usd:.4f}")

    full_response = ''.join(response_parts)
    if verbose:
        print()  # Newline after response

    return full_response


async def create_architect_agent() -> ClaudeSDKClient:
    """Create and connect an Architect agent."""
    architect_prompt = (
        "You are a software architect. Propose concrete tech stacks and architectures. "
        "Explain trade-offs. Make pragmatic decisions. When you see feedback from a coder, "
        "respond directly to their points. Signal 'CONSENSUS:' when finalizing."
    )

    options = ClaudeAgentOptions(
        system_prompt=architect_prompt,
        max_turns=5
    )

    print("[*] Initializing Architect agent...")
    client = ClaudeSDKClient(options=options)
    await client.connect()
    print("[OK] Architect connected\n")

    return client


async def create_coder_agent() -> ClaudeSDKClient:
    """Create and connect a Coder agent."""
    coder_prompt = (
        "You are an implementation engineer. Evaluate architectural proposals for feasibility. "
        "Suggest practical alternatives. Challenge over-engineering. Estimate effort. "
        "When you see a proposal from an architect, evaluate it constructively. "
        "Signal 'AGREED:' when satisfied."
    )

    options = ClaudeAgentOptions(
        system_prompt=coder_prompt,
        max_turns=5
    )

    print("[*] Initializing Coder agent...")
    client = ClaudeSDKClient(options=options)
    await client.connect()
    print("[OK] Coder connected\n")

    return client


async def create_docs_agent() -> ClaudeSDKClient:
    """Create and connect a Docs agent."""
    docs_prompt = (
        "You are a documentation synthesizer. Read conversations and OUTPUT structured markdown documentation. "
        "When asked to create ARCHITECTURE.md or CONSTRAINTS.md, OUTPUT the complete markdown content as text. "
        "DO NOT use tools. DO NOT try to write files. Just OUTPUT markdown text directly. "
        "Preserve decisions, trade-offs, rationale, and the 'why' behind decisions."
    )

    options = ClaudeAgentOptions(
        system_prompt=docs_prompt,
        max_turns=3
    )

    print("[*] Initializing Docs agent...")
    client = ClaudeSDKClient(options=options)
    await client.connect()
    print("[OK] Docs agent connected\n")

    return client


async def create_audit_agent() -> ClaudeSDKClient:
    """Create and connect an Audit agent."""
    audit_prompt = (
        "You are a constraint validation agent. Check code and architecture against defined constraints. "
        "Report violations, inconsistencies, and compliance status. "
        "Be mechanical and objective - flag any deviation from stated rules."
    )

    options = ClaudeAgentOptions(
        system_prompt=audit_prompt,
        max_turns=2
    )

    print("[*] Initializing Audit agent...")
    client = ClaudeSDKClient(options=options)
    await client.connect()
    print("[OK] Audit agent connected\n")

    return client
