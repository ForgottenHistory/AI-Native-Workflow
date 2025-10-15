#!/usr/bin/env python3
"""
Multi-Agent Architecture System with TRUE separate agent conversations.

Uses ClaudeSDKClient to maintain separate stateful conversations for each agent.
"""

import asyncio
from pathlib import Path
from datetime import datetime
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ResultMessage
)


class StatefulArchitecturalDialogue:
    """Manages dialogue between stateful agents including docs synthesis."""

    def __init__(self):
        self.conversation_log = []
        self.architect_client = None
        self.coder_client = None
        self.docs_client = None

    async def initialize_agents(self):
        """Initialize both agents with their system prompts."""

        # Architect system prompt - keep it short to avoid CLI issues
        architect_prompt = (
            "You are a software architect. Propose concrete tech stacks and architectures. "
            "Explain trade-offs. Make pragmatic decisions. When you see feedback from a coder, "
            "respond directly to their points. Signal 'CONSENSUS:' when finalizing."
        )

        # Coder system prompt - keep it short
        coder_prompt = (
            "You are an implementation engineer. Evaluate architectural proposals for feasibility. "
            "Suggest practical alternatives. Challenge over-engineering. Estimate effort. "
            "When you see a proposal from an architect, evaluate it constructively. "
            "Signal 'AGREED:' when satisfied."
        )

        # Create separate clients for each agent
        architect_options = ClaudeAgentOptions(
            system_prompt=architect_prompt,
            max_turns=5  # Allow multi-turn conversation
        )

        coder_options = ClaudeAgentOptions(
            system_prompt=coder_prompt,
            max_turns=5
        )

        print("[*] Initializing Architect agent...")
        self.architect_client = ClaudeSDKClient(options=architect_options)
        await self.architect_client.connect()
        print("[OK] Architect connected\n")

        print("[*] Initializing Coder agent...")
        self.coder_client = ClaudeSDKClient(options=coder_options)
        await self.coder_client.connect()
        print("[OK] Coder connected\n")

    def _strip_emojis(self, text: str) -> str:
        """Remove emojis from text for Windows console compatibility."""
        import re
        # Remove all emoji and other non-ASCII characters for console display
        # But keep common punctuation and symbols
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

    async def query_agent(self, client, agent_name: str, prompt: str) -> str:
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
                        # Print with emojis stripped for Windows console
                        print(self._strip_emojis(block.text), end='', flush=True)
                        # But save the original text with emojis
                        response_parts.append(block.text)
            elif isinstance(message, ResultMessage):
                if message.total_cost_usd and message.total_cost_usd > 0:
                    print(f"\n[$] Cost: ${message.total_cost_usd:.4f}")

        full_response = ''.join(response_parts)
        print()  # Newline after response
        return full_response

    async def run_dialogue(self, project_description: str):
        """Run the architectural dialogue."""

        print("=" * 80)
        print("STATEFUL MULTI-AGENT DIALOGUE")
        print("=" * 80)
        print()

        # Turn 1: Architect proposes
        architect_msg_1 = await self.query_agent(
            client=self.architect_client,
            agent_name="ARCHITECT (Turn 1)",
            prompt=f"""Project requirements:
{project_description}

Propose a specific tech stack and architecture for this landing page. Include:
- Framework choice
- Styling approach
- Form handling
- Dark mode implementation
- Hosting

Be specific and concrete."""
        )
        self.conversation_log.append(("Architect", architect_msg_1))

        # Turn 2: Coder evaluates
        coder_msg_1 = await self.query_agent(
            client=self.coder_client,
            agent_name="CODER (Turn 1)",
            prompt=f"""The architect proposed this architecture:

{architect_msg_1}

Evaluate this proposal. What do you AGREE with? What CONCERNS do you have?
Any BETTER alternatives? Estimate implementation EFFORT."""
        )
        self.conversation_log.append(("Coder", coder_msg_1))

        # Turn 3: Architect responds
        architect_msg_2 = await self.query_agent(
            client=self.architect_client,
            agent_name="ARCHITECT (Turn 2)",
            prompt=f"""The coder's evaluation:

{coder_msg_1}

Respond to their feedback. Address concerns, refine the architecture, or defend choices.
Move toward consensus."""
        )
        self.conversation_log.append(("Architect", architect_msg_2))

        # Turn 4: Coder final evaluation
        coder_msg_2 = await self.query_agent(
            client=self.coder_client,
            agent_name="CODER (Turn 2)",
            prompt=f"""The architect's response:

{architect_msg_2}

Final evaluation. Signal 'AGREED:' if architecture is good, or raise final concerns."""
        )
        self.conversation_log.append(("Coder", coder_msg_2))

        # Check for consensus
        has_consensus = (
            ("CONSENSUS" in architect_msg_2 or "CONSENSUS" in architect_msg_1) and
            ("AGREED" in coder_msg_2 or "AGREED" in coder_msg_1)
        )

        print("\n" + "=" * 80)
        if has_consensus:
            print("[*] CONSENSUS REACHED")
        else:
            print("[!]  Consensus signals not detected")
        print("=" * 80)

        return has_consensus

    async def save_conversation(self):
        """Save conversation log."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = Path("conversation") / f"stateful_session_{timestamp}.md"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("# Stateful Multi-Agent Architectural Dialogue\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Method:** Separate ClaudeSDKClient instances with maintained state\n")
            f.write(f"**Turns:** {len(self.conversation_log)}\n\n")
            f.write("---\n\n")

            for role, message in self.conversation_log:
                f.write(f"## {role}\n\n")
                f.write(f"{message}\n\n")
                f.write("---\n\n")

        print(f"\n[SAVE] Conversation saved to: {log_file}")

    async def initialize_docs_agent(self):
        """Initialize the Docs agent for synthesizing documentation."""
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
        self.docs_client = ClaudeSDKClient(options=docs_options)
        await self.docs_client.connect()
        print("[OK] Docs agent connected\n")

    async def synthesize_documentation(self, project_name: str = "Landing Page"):
        """Have Docs agent synthesize ARCHITECTURE.md and CONSTRAINTS.md from conversation."""
        print("\n" + "=" * 80)
        print("DOCUMENTATION SYNTHESIS PHASE")
        print("=" * 80)
        print()

        # Format conversation for Docs agent
        conversation_text = "\n\n".join([
            f"**{role}:**\n{msg}"
            for role, msg in self.conversation_log
        ])

        # Read templates
        arch_template = Path("ARCHITECTURE_TEMPLATE.md").read_text(encoding='utf-8')
        constraints_template = Path("CONSTRAINTS_TEMPLATE.md").read_text(encoding='utf-8')

        # Request ARCHITECTURE.md
        print("[DOC] Synthesizing ARCHITECTURE.md...")
        architecture_doc = await self.query_agent(
            client=self.docs_client,
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
        constraints_doc = await self.query_agent(
            client=self.docs_client,
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

    async def cleanup(self):
        """Disconnect all agents."""
        for client_name, client in [
            ("Architect", self.architect_client),
            ("Coder", self.coder_client),
            ("Docs", self.docs_client)
        ]:
            try:
                if client:
                    await client.disconnect()
            except Exception:
                pass  # Ignore cleanup errors


async def main():
    """Main entry point."""
    # Load test project
    test_project_file = Path("test_project.md")
    if not test_project_file.exists():
        print(f"Error: {test_project_file} not found")
        return

    project_description = test_project_file.read_text(encoding='utf-8')

    dialogue = StatefulArchitecturalDialogue()

    try:
        # Phase 1: Architectural Dialogue
        await dialogue.initialize_agents()
        consensus = await dialogue.run_dialogue(project_description)
        await dialogue.save_conversation()

        if consensus:
            print("\n[OK] SUCCESS: Agents reached consensus")

            # Phase 2: Documentation Synthesis
            await dialogue.initialize_docs_agent()
            await dialogue.synthesize_documentation(project_name="Landing Page")

            print("\n[SUCCESS] COMPLETE: Architecture dialogue + documentation synthesis")
            print("\nGenerated files:")
            print("  - conversation/stateful_session_*.md (dialogue)")
            print("  - architecture/ARCHITECTURE.md (design decisions)")
            print("  - architecture/CONSTRAINTS.md (implementation rules)")
        else:
            print("\n[!]  INCOMPLETE: Consensus signals not clear")
            print("Skipping documentation synthesis phase.")

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await dialogue.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
