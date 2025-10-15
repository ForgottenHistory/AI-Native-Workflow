#!/usr/bin/env python3
"""
Orchestrator Tools

Tools that the AI Orchestrator Agent can invoke to manage the workflow.
Each tool returns structured data for the orchestrator to reason about.
"""

import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import json
import sys


# Workspace root directory
WORKSPACE_ROOT = Path("workspaces")


def assess_workspace_state(project_name: str) -> Dict[str, Any]:
    """
    Tool: Assess the current state of a project workspace.

    Checks what files exist and returns structured information about
    the project's current phase and completeness.

    Returns:
        dict with keys:
        - has_requirements: bool
        - has_conversation: bool
        - has_architecture: bool
        - has_constraints: bool
        - has_code: bool
        - has_implementation_log: bool
        - has_audit_log: bool
        - files: list[str] (all files in workspace)
        - current_phase: str
        - conversation_consensus: bool (if conversation exists)
    """
    workspace = WORKSPACE_ROOT / project_name

    result = {
        "project_name": project_name,
        "workspace_path": str(workspace),
        "has_requirements": False,
        "has_conversation": False,
        "has_architecture": False,
        "has_constraints": False,
        "has_code": False,
        "has_implementation_log": False,
        "has_audit_log": False,
        "files": [],
        "current_phase": "uninitialized",
        "conversation_consensus": False
    }

    if not workspace.exists():
        return result

    # Check for requirements
    requirements_file = workspace / "requirements.md"
    result["has_requirements"] = requirements_file.exists()

    # Check for conversation
    conversation_dir = workspace / "conversation"
    if conversation_dir.exists():
        conv_files = list(conversation_dir.glob("*.md"))
        result["has_conversation"] = len(conv_files) > 0

        # Check for consensus in latest conversation
        if conv_files:
            latest = max(conv_files, key=lambda p: p.stat().st_mtime)
            content = latest.read_text(encoding='utf-8')
            result["conversation_consensus"] = ("CONSENSUS" in content and "AGREED" in content)

    # Check for architecture docs
    arch_dir = workspace / "architecture"
    if arch_dir.exists():
        result["has_architecture"] = (arch_dir / "ARCHITECTURE.md").exists()
        result["has_constraints"] = (arch_dir / "CONSTRAINTS.md").exists()

    # Check for code
    code_dir = workspace / "code"
    if code_dir.exists():
        code_files = (
            list(code_dir.glob("**/*.py")) +
            list(code_dir.glob("**/*.js")) +
            list(code_dir.glob("**/*.ts")) +
            list(code_dir.glob("**/*.tsx")) +
            list(code_dir.glob("**/*.jsx"))
        )
        result["has_code"] = len(code_files) > 0

    # Check for logs
    logs_dir = workspace / "logs"
    if logs_dir.exists():
        result["has_implementation_log"] = len(list(logs_dir.glob("implementation_*.md"))) > 0
        result["has_audit_log"] = len(list(logs_dir.glob("audit_*.md"))) > 0

    # List all files
    if workspace.exists():
        result["files"] = [
            str(f.relative_to(workspace))
            for f in workspace.rglob("*")
            if f.is_file()
        ]

    # Infer current phase
    if not result["has_requirements"]:
        result["current_phase"] = "uninitialized"
    elif not result["has_conversation"] or not result["conversation_consensus"]:
        result["current_phase"] = "architectural_dialogue"
    elif not result["has_architecture"] or not result["has_constraints"]:
        result["current_phase"] = "documentation_synthesis"
    elif not result["has_code"]:
        result["current_phase"] = "implementation"
    elif not result["has_audit_log"]:
        result["current_phase"] = "audit"
    else:
        result["current_phase"] = "complete"

    return result


async def run_architectural_dialogue(project_name: str) -> Dict[str, Any]:
    """
    Tool: Run Architect <-> Coder architectural dialogue.

    Spawns the dialogue agent as a subprocess to maintain isolated contexts.

    Returns:
        dict with keys:
        - success: bool
        - conversation_file: str (path to saved conversation)
        - consensus_reached: bool
        - turns: int
        - error: str (if failed)
    """
    workspace = WORKSPACE_ROOT / project_name
    workspace.mkdir(parents=True, exist_ok=True)

    # Check for requirements
    requirements_file = workspace / "requirements.md"
    if not requirements_file.exists():
        return {
            "success": False,
            "error": "No requirements.md file found in workspace"
        }

    try:
        # Spawn dialogue agent as subprocess
        agent_script = Path(__file__).parent / "agents" / "run_dialogue.py"

        result = subprocess.run(
            [sys.executable, str(agent_script), project_name],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=300  # 5 minute timeout
        )

        # Parse JSON output from subprocess
        if result.returncode == 0:
            output = json.loads(result.stdout)
            return output
        else:
            # Try to parse error from stdout/stderr
            error_msg = result.stderr if result.stderr else result.stdout
            try:
                error_json = json.loads(result.stdout)
                return error_json
            except:
                return {
                    "success": False,
                    "error": f"Agent subprocess failed: {error_msg}"
                }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Dialogue agent timed out after 5 minutes"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to spawn dialogue agent: {str(e)}"
        }


async def synthesize_documentation(project_name: str) -> Dict[str, Any]:
    """
    Tool: Synthesize ARCHITECTURE.md and CONSTRAINTS.md from conversation.

    Spawns the docs agent as a subprocess to maintain isolated context.

    Returns:
        dict with keys:
        - success: bool
        - files_created: list[str]
        - error: str (if failed)
    """
    workspace = WORKSPACE_ROOT / project_name

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

    try:
        # Spawn docs agent as subprocess
        agent_script = Path(__file__).parent / "agents" / "synthesize_docs.py"

        result = subprocess.run(
            [sys.executable, str(agent_script), project_name],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=300  # 5 minute timeout
        )

        # Parse JSON output from subprocess
        if result.returncode == 0:
            output = json.loads(result.stdout)
            return output
        else:
            # Try to parse error from stdout/stderr
            error_msg = result.stderr if result.stderr else result.stdout
            try:
                error_json = json.loads(result.stdout)
                return error_json
            except:
                return {
                    "success": False,
                    "error": f"Agent subprocess failed: {error_msg}"
                }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Docs agent timed out after 5 minutes"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to spawn docs agent: {str(e)}"
        }


def list_files(project_name: str, directory: str = "") -> Dict[str, Any]:
    """
    Tool: List files in a workspace directory.

    Returns:
        dict with keys:
        - success: bool
        - files: list[str]
        - count: int
        - error: str (if failed)
    """
    workspace = WORKSPACE_ROOT / project_name
    target_dir = workspace / directory if directory else workspace

    if not target_dir.exists():
        return {
            "success": False,
            "error": f"Directory does not exist: {directory}"
        }

    try:
        files = [
            str(f.relative_to(workspace))
            for f in target_dir.rglob("*")
            if f.is_file()
        ]

        return {
            "success": True,
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def read_log(project_name: str, log_path: str) -> Dict[str, Any]:
    """
    Tool: Read a log file from the workspace.

    Returns:
        dict with keys:
        - success: bool
        - content: str
        - error: str (if failed)
    """
    workspace = WORKSPACE_ROOT / project_name
    full_path = workspace / log_path

    if not full_path.exists():
        return {
            "success": False,
            "error": f"Log file not found: {log_path}"
        }

    try:
        content = full_path.read_text(encoding='utf-8')
        return {
            "success": True,
            "content": content,
            "size": len(content)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def read_file(project_name: str, file_path: str) -> Dict[str, Any]:
    """
    Tool: Read any file from the workspace.

    Returns:
        dict with keys:
        - success: bool
        - content: str
        - error: str (if failed)
    """
    workspace = WORKSPACE_ROOT / project_name
    full_path = workspace / file_path

    if not full_path.exists():
        return {
            "success": False,
            "error": f"File not found: {file_path}"
        }

    try:
        content = full_path.read_text(encoding='utf-8')
        return {
            "success": True,
            "content": content,
            "size": len(content)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# TODO: implement_from_architecture - Phase 3
# TODO: audit_implementation - Phase 4


if __name__ == "__main__":
    # Test the tools
    print("Testing orchestrator tools...")

    # Test assess_workspace_state
    state = assess_workspace_state("test_landing_page")
    print(f"\nWorkspace state: {json.dumps(state, indent=2)}")
