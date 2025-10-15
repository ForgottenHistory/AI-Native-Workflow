#!/usr/bin/env python3
"""
Dynamic Multi-Agent Orchestrator

Intelligently routes workflow based on project state rather than static sequence.
Uses state assessment to decide which agent should run next and handles feedback loops.
"""

import asyncio
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ResultMessage
)


class ProjectPhase(Enum):
    """Current phase of the project."""
    UNINITIALIZED = "uninitialized"
    ARCHITECTURAL_DIALOGUE = "architectural_dialogue"
    DOCUMENTATION_SYNTHESIS = "documentation_synthesis"
    IMPLEMENTATION = "implementation"
    AUDIT = "audit"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class ProjectState:
    """Represents the current state of a project in the workspace."""
    workspace_path: Path
    project_name: str

    # What exists?
    has_requirements: bool = False
    has_conversation: bool = False
    has_architecture_doc: bool = False
    has_constraints_doc: bool = False
    has_code: bool = False
    has_implementation_log: bool = False
    has_audit_log: bool = False

    # What's the status?
    current_phase: ProjectPhase = ProjectPhase.UNINITIALIZED
    dialogue_consensus: bool = False
    implementation_success: Optional[bool] = None
    audit_passed: Optional[bool] = None

    # Context for decision-making
    last_error: Optional[str] = None
    human_feedback: Optional[str] = None

    def __repr__(self):
        return (
            f"ProjectState(phase={self.current_phase.value}, "
            f"docs={self.has_architecture_doc and self.has_constraints_doc}, "
            f"code={self.has_code}, "
            f"audit={self.audit_passed})"
        )


class ActionType(Enum):
    """Types of actions the orchestrator can take."""
    RUN_DIALOGUE = "run_dialogue"
    SYNTHESIZE_DOCS = "synthesize_docs"
    IMPLEMENT_CODE = "implement_code"
    RUN_AUDIT = "run_audit"
    UPDATE_DOCS = "update_docs"
    ASK_HUMAN = "ask_human"
    COMPLETE = "complete"
    ABORT = "abort"


@dataclass
class OrchestratorAction:
    """An action for the orchestrator to execute."""
    action_type: ActionType
    reason: str
    inputs: Dict = None

    def __repr__(self):
        return f"Action({self.action_type.value}: {self.reason})"


class DynamicOrchestrator:
    """
    Intelligent orchestrator that assesses project state and decides which agent to run.

    Unlike the static orchestrator, this dynamically routes based on what exists
    and handles feedback loops when things fail.
    """

    def __init__(self, workspace_root: Path = None):
        self.workspace_root = workspace_root or Path("workspaces")
        self.workspace_root.mkdir(parents=True, exist_ok=True)

        # Agent clients (initialized on demand)
        self.architect_client = None
        self.coder_client = None
        self.docs_client = None
        self.audit_client = None

        # State tracking
        self.current_state: Optional[ProjectState] = None
        self.action_history: List[OrchestratorAction] = []

        # Logging
        self.log_file = None

    def assess_project_state(self, project_name: str) -> ProjectState:
        """
        Assess the current state of a project by checking what files exist.

        This is the key function that enables dynamic routing - it tells us
        where we are and what's been done.
        """
        workspace_path = self.workspace_root / project_name
        state = ProjectState(
            workspace_path=workspace_path,
            project_name=project_name
        )

        # Check if workspace exists
        if not workspace_path.exists():
            print(f"[STATE] New project: {project_name}")
            state.current_phase = ProjectPhase.UNINITIALIZED
            return state

        # Check for requirements/input
        requirements_file = workspace_path / "requirements.md"
        state.has_requirements = requirements_file.exists()

        # Check for conversation transcript
        conversation_dir = workspace_path / "conversation"
        if conversation_dir.exists():
            conversation_files = list(conversation_dir.glob("*.md"))
            state.has_conversation = len(conversation_files) > 0

            # Check for consensus markers in latest conversation
            if conversation_files:
                latest = max(conversation_files, key=lambda p: p.stat().st_mtime)
                content = latest.read_text(encoding='utf-8')
                state.dialogue_consensus = ("CONSENSUS" in content and "AGREED" in content)

        # Check for architecture documentation
        arch_dir = workspace_path / "architecture"
        if arch_dir.exists():
            state.has_architecture_doc = (arch_dir / "ARCHITECTURE.md").exists()
            state.has_constraints_doc = (arch_dir / "CONSTRAINTS.md").exists()

        # Check for implementation
        code_dir = workspace_path / "code"
        if code_dir.exists():
            code_files = list(code_dir.glob("**/*.py")) + list(code_dir.glob("**/*.js")) + \
                        list(code_dir.glob("**/*.ts")) + list(code_dir.glob("**/*.tsx"))
            state.has_code = len(code_files) > 0

        # Check for logs
        logs_dir = workspace_path / "logs"
        if logs_dir.exists():
            state.has_implementation_log = (logs_dir / "IMPLEMENTATION_LOG.md").exists()
            audit_logs = list(logs_dir.glob("AUDIT_LOG_*.md"))
            state.has_audit_log = len(audit_logs) > 0

            # Check audit result from latest log
            if audit_logs:
                latest_audit = max(audit_logs, key=lambda p: p.stat().st_mtime)
                content = latest_audit.read_text(encoding='utf-8')
                state.audit_passed = "PASS" in content and "FAIL" not in content

        # Determine current phase based on what exists
        state.current_phase = self._infer_phase(state)

        print(f"[STATE] {state}")
        return state

    def _infer_phase(self, state: ProjectState) -> ProjectPhase:
        """Infer the current project phase from what exists."""
        if not state.has_requirements:
            return ProjectPhase.UNINITIALIZED

        if not state.has_conversation or not state.dialogue_consensus:
            return ProjectPhase.ARCHITECTURAL_DIALOGUE

        if not state.has_architecture_doc or not state.has_constraints_doc:
            return ProjectPhase.DOCUMENTATION_SYNTHESIS

        if not state.has_code:
            return ProjectPhase.IMPLEMENTATION

        if state.has_code and not state.has_audit_log:
            return ProjectPhase.AUDIT

        if state.audit_passed is False:
            return ProjectPhase.FAILED  # Will trigger feedback loop

        if state.audit_passed is True:
            return ProjectPhase.COMPLETE

        return ProjectPhase.UNINITIALIZED

    def decide_next_action(self, state: ProjectState) -> OrchestratorAction:
        """
        Decision engine: Given current state, what should we do next?

        This is where the intelligence lives - it maps states to actions.
        """

        # Case 1: New project, no requirements
        if state.current_phase == ProjectPhase.UNINITIALIZED:
            if not state.has_requirements:
                return OrchestratorAction(
                    action_type=ActionType.ASK_HUMAN,
                    reason="No requirements found. Need project description to start.",
                    inputs={"need": "requirements.md"}
                )

        # Case 2: Have requirements, need architectural dialogue
        if state.current_phase == ProjectPhase.ARCHITECTURAL_DIALOGUE:
            if not state.has_conversation:
                return OrchestratorAction(
                    action_type=ActionType.RUN_DIALOGUE,
                    reason="No conversation exists. Starting Architect <-> Coder dialogue.",
                    inputs={"requirements_path": state.workspace_path / "requirements.md"}
                )
            elif state.has_conversation and not state.dialogue_consensus:
                return OrchestratorAction(
                    action_type=ActionType.RUN_DIALOGUE,
                    reason="Conversation exists but no consensus reached. Continuing dialogue.",
                    inputs={"resume": True}
                )

        # Case 3: Have consensus, need documentation
        if state.current_phase == ProjectPhase.DOCUMENTATION_SYNTHESIS:
            return OrchestratorAction(
                action_type=ActionType.SYNTHESIZE_DOCS,
                reason="Dialogue consensus reached. Synthesizing architecture documentation.",
                inputs={
                    "conversation_path": state.workspace_path / "conversation",
                    "output_path": state.workspace_path / "architecture"
                }
            )

        # Case 4: Have docs, need implementation
        if state.current_phase == ProjectPhase.IMPLEMENTATION:
            return OrchestratorAction(
                action_type=ActionType.IMPLEMENT_CODE,
                reason="Architecture documented. Starting implementation.",
                inputs={
                    "architecture_path": state.workspace_path / "architecture",
                    "output_path": state.workspace_path / "code"
                }
            )

        # Case 5: Have code, need audit
        if state.current_phase == ProjectPhase.AUDIT:
            return OrchestratorAction(
                action_type=ActionType.RUN_AUDIT,
                reason="Implementation complete. Running constraint validation.",
                inputs={
                    "constraints_path": state.workspace_path / "architecture" / "CONSTRAINTS.md",
                    "code_path": state.workspace_path / "code",
                    "output_path": state.workspace_path / "logs"
                }
            )

        # Case 6: Audit failed - feedback loop
        if state.current_phase == ProjectPhase.FAILED:
            if state.audit_passed is False:
                return OrchestratorAction(
                    action_type=ActionType.ASK_HUMAN,
                    reason="Audit failed. Review violations and decide: fix implementation or revise architecture?",
                    inputs={
                        "audit_log": state.workspace_path / "logs",
                        "options": ["fix_implementation", "revise_architecture", "accept_violations"]
                    }
                )

        # Case 7: Complete
        if state.current_phase == ProjectPhase.COMPLETE:
            return OrchestratorAction(
                action_type=ActionType.COMPLETE,
                reason="Project complete: docs generated, code implemented, audit passed."
            )

        # Fallback: shouldn't reach here
        return OrchestratorAction(
            action_type=ActionType.ASK_HUMAN,
            reason=f"Unknown state: {state}. Human intervention required."
        )

    async def execute_action(self, action: OrchestratorAction, state: ProjectState):
        """
        Execute the decided action.

        This is where we actually run agents based on what the decision engine chose.
        """
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from utils.agent_utils import strip_emojis

        print(f"\n{'='*80}")
        print(f"[ACTION] {strip_emojis(str(action))}")
        print(f"{'='*80}\n")

        self.action_history.append(action)

        if action.action_type == ActionType.RUN_DIALOGUE:
            await self._execute_dialogue(action, state)

        elif action.action_type == ActionType.SYNTHESIZE_DOCS:
            await self._execute_docs_synthesis(action, state)

        elif action.action_type == ActionType.IMPLEMENT_CODE:
            await self._execute_implementation(action, state)

        elif action.action_type == ActionType.RUN_AUDIT:
            await self._execute_audit(action, state)

        elif action.action_type == ActionType.ASK_HUMAN:
            self._ask_human(action, state)

        elif action.action_type == ActionType.COMPLETE:
            print(f"\n[SUCCESS] Project '{state.project_name}' complete!")
            print(f"  Workspace: {state.workspace_path}")
            print(f"  Actions taken: {len(self.action_history)}")

        else:
            print(f"[ERROR] Unknown action type: {action.action_type}")

    async def _execute_dialogue(self, action: OrchestratorAction, state: ProjectState):
        """Run Architect <-> Coder dialogue."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from utils.agent_utils import query_agent, create_architect_agent, create_coder_agent

        print("[DIALOGUE] Starting architectural dialogue...")

        # Initialize agents if needed
        if not self.architect_client:
            self.architect_client = await create_architect_agent()
        if not self.coder_client:
            self.coder_client = await create_coder_agent()

        # Load requirements
        requirements_path = action.inputs.get("requirements_path")
        project_description = requirements_path.read_text(encoding='utf-8')

        # Run dialogue (4 turns)
        conversation_log = []

        # Turn 1: Architect proposes
        architect_msg_1 = await query_agent(
            self.architect_client,
            "ARCHITECT (Turn 1)",
            f"""Project requirements:
{project_description}

Propose a specific tech stack and architecture. Include:
- Framework choice
- Styling approach
- Form handling (if needed)
- Dark mode implementation (if needed)
- Hosting

Be specific and concrete."""
        )
        conversation_log.append(("Architect", architect_msg_1))

        # Turn 2: Coder evaluates
        coder_msg_1 = await query_agent(
            self.coder_client,
            "CODER (Turn 1)",
            f"""The architect proposed this architecture:

{architect_msg_1}

Evaluate this proposal. What do you AGREE with? What CONCERNS do you have?
Any BETTER alternatives? Estimate implementation EFFORT."""
        )
        conversation_log.append(("Coder", coder_msg_1))

        # Turn 3: Architect responds
        architect_msg_2 = await query_agent(
            self.architect_client,
            "ARCHITECT (Turn 2)",
            f"""The coder's evaluation:

{coder_msg_1}

Respond to their feedback. Address concerns, refine the architecture, or defend choices.
Move toward consensus."""
        )
        conversation_log.append(("Architect", architect_msg_2))

        # Turn 4: Coder final evaluation
        coder_msg_2 = await query_agent(
            self.coder_client,
            "CODER (Turn 2)",
            f"""The architect's response:

{architect_msg_2}

Final evaluation. Signal 'AGREED:' if architecture is good, or raise final concerns."""
        )
        conversation_log.append(("Coder", coder_msg_2))

        # Check for consensus
        has_consensus = (
            ("CONSENSUS" in architect_msg_2 or "CONSENSUS" in architect_msg_1) and
            ("AGREED" in coder_msg_2 or "AGREED" in coder_msg_1)
        )

        print(f"\n[CONSENSUS] {'YES' if has_consensus else 'NO'}")

        # Save conversation
        conversation_dir = state.workspace_path / "conversation"
        conversation_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = conversation_dir / f"dialogue_{timestamp}.md"

        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("# Multi-Agent Architectural Dialogue\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Project:** {state.project_name}\n")
            f.write(f"**Turns:** {len(conversation_log)}\n")
            f.write(f"**Consensus:** {'YES' if has_consensus else 'NO'}\n\n")
            f.write("---\n\n")

            for role, message in conversation_log:
                f.write(f"## {role}\n\n")
                f.write(f"{message}\n\n")
                f.write("---\n\n")

        print(f"[SAVE] Conversation saved to: {log_file.relative_to(state.workspace_path)}")

    async def _execute_docs_synthesis(self, action: OrchestratorAction, state: ProjectState):
        """Run Docs agent to synthesize documentation."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from utils.agent_utils import query_agent, create_docs_agent

        print("[DOCS] Synthesizing documentation...")

        # Initialize docs agent if needed
        if not self.docs_client:
            self.docs_client = await create_docs_agent()

        # Load conversation
        conversation_dir = action.inputs.get("conversation_path")
        conversation_files = list(conversation_dir.glob("*.md"))
        if not conversation_files:
            print("[ERROR] No conversation files found!")
            return

        latest = max(conversation_files, key=lambda p: p.stat().st_mtime)
        conversation_text = latest.read_text(encoding='utf-8')

        # Load templates
        templates_dir = Path(__file__).parent / "templates"
        arch_template = (templates_dir / "ARCHITECTURE_TEMPLATE.md").read_text(encoding='utf-8')
        constraints_template = (templates_dir / "CONSTRAINTS_TEMPLATE.md").read_text(encoding='utf-8')

        # Synthesize ARCHITECTURE.md
        print("[DOC] Generating ARCHITECTURE.md...")
        architecture_doc = await query_agent(
            self.docs_client,
            "DOCS AGENT (Architecture)",
            f"""Read this Architect <-> Coder dialogue and OUTPUT the complete ARCHITECTURE.md content as markdown text:

CONVERSATION:
{conversation_text}

TEMPLATE TO FOLLOW:
{arch_template}

TASK: Extract all architectural decisions, tech stack choices, trade-offs, and rationale from the conversation above. OUTPUT the complete ARCHITECTURE.md markdown content following the template format. Replace [placeholders] with actual content from the conversation. Be specific with numbers and technologies.

IMPORTANT: Do NOT use any tools. Do NOT try to write files. Just OUTPUT the markdown text directly in your response. Your entire response should be the ARCHITECTURE.md content ready to save.""",
            verbose=False
        )

        # Save ARCHITECTURE.md
        output_path = action.inputs.get("output_path")
        output_path.mkdir(parents=True, exist_ok=True)
        arch_file = output_path / "ARCHITECTURE.md"
        arch_file.write_text(architecture_doc, encoding='utf-8')
        print(f"[SAVE] {arch_file.relative_to(state.workspace_path)}")

        # Synthesize CONSTRAINTS.md
        print("[DOC] Generating CONSTRAINTS.md...")
        constraints_doc = await query_agent(
            self.docs_client,
            "DOCS AGENT (Constraints)",
            f"""Read this Architect <-> Coder dialogue and OUTPUT the complete CONSTRAINTS.md content as markdown text:

CONVERSATION:
{conversation_text}

TEMPLATE TO FOLLOW:
{constraints_template}

TASK: Extract all constraints, performance budgets, testing requirements, and rules from the conversation above. OUTPUT the complete CONSTRAINTS.md markdown content following the template format. Make constraints testable and specific. Include performance numbers mentioned in the dialogue.

IMPORTANT: Do NOT use any tools. Do NOT try to write files. Just OUTPUT the markdown text directly in your response. Your entire response should be the CONSTRAINTS.md content ready to save.""",
            verbose=False
        )

        # Save CONSTRAINTS.md
        constraints_file = output_path / "CONSTRAINTS.md"
        constraints_file.write_text(constraints_doc, encoding='utf-8')
        print(f"[SAVE] {constraints_file.relative_to(state.workspace_path)}")

    async def _execute_implementation(self, action: OrchestratorAction, state: ProjectState):
        """Run Coder agent to implement from architecture."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from utils.agent_utils import query_agent
        from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, PermissionResultAllow, PermissionResultDeny, ToolPermissionContext

        print("[IMPLEMENTATION] Generating code...")

        # Load architecture and constraints
        architecture_path = action.inputs.get("architecture_path")
        arch_file = architecture_path / "ARCHITECTURE.md"
        constraints_file = architecture_path / "CONSTRAINTS.md"

        if not arch_file.exists() or not constraints_file.exists():
            print(f"[ERROR] Missing architecture docs!")
            return

        architecture = arch_file.read_text(encoding='utf-8')
        constraints = constraints_file.read_text(encoding='utf-8')

        print(f"[OK] Loaded ARCHITECTURE.md ({len(architecture)} chars)")
        print(f"[OK] Loaded CONSTRAINTS.md ({len(constraints)} chars)")

        # Create permission callback that allows writes to this workspace's code/ dir
        workspace_str = str(state.workspace_path)
        async def workspace_code_writes(
            tool_name: str,
            input_data: dict,
            context: ToolPermissionContext
        ) -> PermissionResultAllow | PermissionResultDeny:
            """Allow writes only to this workspace's code/ directory."""
            # Always allow read operations
            if tool_name in ["Read", "Glob", "Grep"]:
                return PermissionResultAllow()

            # Allow writes to code/ directory
            if tool_name in ["Write", "Edit"]:
                file_path = input_data.get("file_path", "")

                # Check various path formats
                code_dir = str(state.workspace_path / "code")
                if (file_path.startswith(code_dir) or
                    file_path.startswith(f"{workspace_str}/code/") or
                    file_path.startswith(f"{workspace_str}\\code\\") or
                    "\\code\\" in file_path or "/code/" in file_path):
                    return PermissionResultAllow()

                return PermissionResultDeny(
                    message=f"Can only write to {code_dir}/"
                )

            return PermissionResultDeny(message=f"Tool {tool_name} not allowed")

        # Initialize implementation Coder agent with permissions
        impl_prompt = (
            "You are an implementation engineer. You receive architecture documentation and constraints, "
            "and you implement working code that follows the specifications exactly. "
            "Use the Write tool to create files. "
            "Follow all constraints exactly. Use best practices for the chosen tech stack."
        )

        impl_options = ClaudeAgentOptions(
            system_prompt=impl_prompt,
            max_turns=20,  # Allow many tool uses for implementation
            can_use_tool=workspace_code_writes,
            cwd=str(state.workspace_path)
        )

        print("[*] Initializing implementation Coder agent...")
        impl_client = ClaudeSDKClient(options=impl_options)
        await impl_client.connect()
        print("[OK] Implementation Coder connected\n")

        try:
            # Ask agent to implement
            print("[*] Asking Coder to implement from architecture docs...")
            implementation_response = await query_agent(
                impl_client,
                "CODER (Implementation)",
                f"""You have full architecture and constraints for this project:

ARCHITECTURE.md:
{architecture}

CONSTRAINTS.md:
{constraints}

YOUR TASK:
Implement this project following the architecture and constraints exactly.

REQUIREMENTS:
- Create ALL files needed for a working implementation in the code/ directory
- Follow CONSTRAINTS.md exactly
- Use exact tech stack from ARCHITECTURE.md
- Include all necessary config files, source files, components, etc.
- Make autonomous decisions about structure and implementation approach

IMPORTANT:
- Use the Write tool to create each file
- File paths should be: {state.workspace_path}/code/filename
- You decide what files to create and in what order
- Implement the complete, working project

Begin implementation. Create all project files.""",
                verbose=True
            )

            # Save implementation log
            logs_dir = state.workspace_path / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = logs_dir / f"implementation_{timestamp}.md"

            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("# IMPLEMENTATION LOG\n\n")
                f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Agent:** Implementation Coder\n")
                f.write(f"**Project:** {state.project_name}\n")
                f.write(f"**Method:** Autonomous implementation from architecture docs\n\n")
                f.write("---\n\n")
                f.write("## Agent Response\n\n")
                f.write(f"{implementation_response}\n\n")

            print(f"\n[SAVE] Implementation log: {log_file.relative_to(state.workspace_path)}")

        finally:
            await impl_client.disconnect()

    async def _execute_audit(self, action: OrchestratorAction, state: ProjectState):
        """Run Audit agent to validate constraints."""
        print("[AUDIT] Validating constraints...")
        # TODO: Implement audit execution (new agent)
        pass

    def _ask_human(self, action: OrchestratorAction, state: ProjectState):
        """Present question/options to human and wait for input."""
        print(f"\n{'='*80}")
        print("[HUMAN INPUT REQUIRED]")
        print(f"{'='*80}")
        print(f"\n{action.reason}\n")

        if action.inputs and "options" in action.inputs:
            print("Options:")
            for i, option in enumerate(action.inputs["options"], 1):
                print(f"  {i}. {option}")

        print(f"\n{'='*80}\n")

    async def cleanup_agents(self):
        """Disconnect and cleanup all agent clients."""
        for client_name, client in [
            ("Architect", self.architect_client),
            ("Coder", self.coder_client),
            ("Docs", self.docs_client),
            ("Audit", self.audit_client)
        ]:
            try:
                if client:
                    print(f"[CLEANUP] Disconnecting {client_name} agent...")
                    await client.disconnect()
            except Exception as e:
                print(f"[CLEANUP] Error disconnecting {client_name}: {e}")

    async def orchestrate(self, project_name: str, max_iterations: int = 10):
        """
        Main orchestration loop.

        Continuously assess state → decide action → execute until complete or max iterations.
        """
        # Setup logging
        workspace = self.workspace_root / project_name
        workspace.mkdir(parents=True, exist_ok=True)
        logs_dir = workspace / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = logs_dir / f"orchestration_{timestamp}.log"

        def log(message: str):
            """Write to both console and log file."""
            print(message)
            if self.log_file:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(message + '\n')

        log(f"\n{'='*80}")
        log(f"DYNAMIC ORCHESTRATOR")
        log(f"Project: {project_name}")
        log(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log(f"Log: {self.log_file.relative_to(workspace)}")
        log(f"{'='*80}\n")

        try:
            for iteration in range(max_iterations):
                log(f"\n--- Iteration {iteration + 1}/{max_iterations} ---")

                # 1. Assess current state
                state = self.assess_project_state(project_name)
                self.current_state = state

                # 2. Decide what to do next
                action = self.decide_next_action(state)

                # 3. Execute the action
                await self.execute_action(action, state)

                # 4. Check if we're done
                if action.action_type in [ActionType.COMPLETE, ActionType.ASK_HUMAN, ActionType.ABORT]:
                    break

                # Small delay between iterations
                await asyncio.sleep(0.5)

            else:
                log(f"\n[WARNING] Max iterations ({max_iterations}) reached without completion.")

            log(f"\n{'='*80}")
            log("ORCHESTRATION SUMMARY")
            log(f"{'='*80}")
            log(f"Ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            log(f"Final state: {self.current_state}")
            log(f"Actions taken: {len(self.action_history)}")
            for i, action in enumerate(self.action_history, 1):
                log(f"  {i}. {action.action_type.value}: {action.reason}")
            log(f"{'='*80}\n")

        finally:
            # Cleanup agents
            await self.cleanup_agents()


async def main():
    """Test the dynamic orchestrator."""
    orchestrator = DynamicOrchestrator()

    # Test with a new project
    project_name = "test_landing_page"

    # Create a requirements file for testing
    workspace = orchestrator.workspace_root / project_name
    workspace.mkdir(parents=True, exist_ok=True)

    requirements = workspace / "requirements.md"
    requirements.write_text("""
# Landing Page Project

Build a modern landing page with:
- Hero section with headline and CTA
- Features section (3 features)
- Contact form
- Dark mode toggle
- Responsive design

Target: <250KB total page weight
""", encoding='utf-8')

    # Run orchestration
    await orchestrator.orchestrate(project_name)


if __name__ == "__main__":
    asyncio.run(main())
