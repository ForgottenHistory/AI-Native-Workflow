"""
AI-Native Workflow Orchestration

Functions for orchestrating multi-agent workflow via HTTP requests to agent servers.

This module is designed to be used by Claude Code as the orchestrator.
Claude Code calls these functions to autonomously run the workflow.
"""

import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


# Workspace root
WORKSPACE_ROOT = Path(__file__).parent.parent / "workspaces"

# Agent server URLs
ARCHITECT_URL = "http://localhost:5001"
CODER_URL = "http://localhost:5002"
DOCS_URL = "http://localhost:5003"


def check_servers_running() -> Dict[str, bool]:
    """
    Check which agent servers are running.

    Returns:
        dict mapping server name to running status
    """
    import requests

    servers = {
        "Architect": f"{ARCHITECT_URL}/health",
        "Coder": f"{CODER_URL}/health",
        "Docs": f"{DOCS_URL}/health"
    }

    status = {}
    for name, url in servers.items():
        try:
            response = requests.get(url, timeout=2)
            status[name] = response.status_code == 200
        except:
            status[name] = False

    return status


def run_architectural_dialogue_api(
    project_name: str,
    requirements: str
) -> Dict[str, Any]:
    """
    Run architectural dialogue via agent server APIs.

    This replaces the subprocess approach with HTTP requests.

    Args:
        project_name: Name of the project
        requirements: Project requirements text

    Returns:
        dict with conversation, consensus, files created
    """
    import requests

    workspace = WORKSPACE_ROOT / project_name
    workspace.mkdir(parents=True, exist_ok=True)

    conversation = []

    print("\n" + "="*60)
    print(f"ARCHITECTURAL DIALOGUE: {project_name}")
    print("="*60 + "\n")

    # Turn 1: Architect proposes
    print("[TURN 1] Architect proposing architecture...")
    try:
        response = requests.post(
            f"{ARCHITECT_URL}/architect/propose",
            json={
                "project_name": project_name,
                "requirements": requirements,
                "context": {}
            },
            timeout=180
        )
        response.raise_for_status()
        arch_proposal = response.json()

        conversation.append({
            "role": "Architect",
            "message": arch_proposal["proposal"]
        })

        print(f"✓ Architect proposed: {arch_proposal['tech_stack']}")

    except Exception as e:
        return {
            "success": False,
            "error": f"Architect proposal failed: {e}"
        }

    # Turn 2: Coder evaluates
    print("\n[TURN 2] Coder evaluating proposal...")
    try:
        response = requests.post(
            f"{CODER_URL}/coder/evaluate",
            json={
                "project_name": project_name,
                "architect_proposal": arch_proposal["proposal"],
                "conversation_turn": 1
            },
            timeout=180
        )
        response.raise_for_status()
        coder_eval = response.json()

        conversation.append({
            "role": "Coder",
            "message": coder_eval["evaluation"]
        })

        print(f"✓ Coder evaluated:")
        print(f"  Agreements: {len(coder_eval['agreements'])}")
        print(f"  Concerns: {len(coder_eval['concerns'])}")

    except Exception as e:
        return {
            "success": False,
            "error": f"Coder evaluation failed: {e}"
        }

    # Turn 3: Architect responds
    print("\n[TURN 3] Architect responding to feedback...")
    try:
        response = requests.post(
            f"{ARCHITECT_URL}/architect/respond",
            json={
                "project_name": project_name,
                "coder_feedback": coder_eval["evaluation"],
                "previous_proposal": arch_proposal["proposal"],
                "conversation_turn": 2
            },
            timeout=180
        )
        response.raise_for_status()
        arch_response = response.json()

        conversation.append({
            "role": "Architect",
            "message": arch_response["response"]
        })

        consensus_signal = arch_response.get("consensus_signal")
        if consensus_signal:
            print(f"✓ Consensus signal: {consensus_signal}")

    except Exception as e:
        return {
            "success": False,
            "error": f"Architect response failed: {e}"
        }

    # Turn 4: Coder finalizes
    print("\n[TURN 4] Coder finalizing...")
    try:
        response = requests.post(
            f"{CODER_URL}/coder/finalize",
            json={
                "project_name": project_name,
                "architect_response": arch_response["response"],
                "conversation_turn": 3
            },
            timeout=180
        )
        response.raise_for_status()
        coder_final = response.json()

        conversation.append({
            "role": "Coder",
            "message": coder_final["final_evaluation"]
        })

        approved = coder_final["approved"]
        print(f"✓ Architecture {'APPROVED' if approved else 'NOT APPROVED'}")

    except Exception as e:
        return {
            "success": False,
            "error": f"Coder finalization failed: {e}"
        }

    # Save conversation
    conv_dir = workspace / "conversation"
    conv_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conv_file = conv_dir / f"dialogue_{timestamp}.md"

    with open(conv_file, 'w', encoding='utf-8') as f:
        f.write("# Architectural Dialogue\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Project:** {project_name}\n")
        f.write(f"**Consensus:** {'YES' if approved else 'NO'}\n\n")
        f.write("---\n\n")

        for turn in conversation:
            f.write(f"## {turn['role']}\n\n{turn['message']}\n\n---\n\n")

    print(f"\n✓ Conversation saved: {conv_file.relative_to(workspace)}")

    return {
        "success": True,
        "conversation_file": str(conv_file.relative_to(workspace)),
        "consensus_reached": approved,
        "turns": len(conversation),
        "conversation": conversation
    }


def synthesize_documentation_api(project_name: str) -> Dict[str, Any]:
    """
    Synthesize documentation via Docs agent server API.

    Args:
        project_name: Name of the project

    Returns:
        dict with files created and status
    """
    import requests

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

    latest_conv = max(conv_files, key=lambda p: p.stat().st_mtime)

    # Parse conversation
    conversation = _parse_conversation_file(latest_conv)

    # Load templates
    templates_dir = Path(__file__).parent / "templates"
    arch_template = (templates_dir / "ARCHITECTURE_TEMPLATE.md").read_text(encoding='utf-8')
    constraints_template = (templates_dir / "CONSTRAINTS_TEMPLATE.md").read_text(encoding='utf-8')

    print("\n" + "="*60)
    print(f"DOCUMENTATION SYNTHESIS: {project_name}")
    print("="*60 + "\n")

    print("Synthesizing ARCHITECTURE.md and CONSTRAINTS.md...")

    try:
        response = requests.post(
            f"{DOCS_URL}/docs/synthesize",
            json={
                "project_name": project_name,
                "conversation": conversation,
                "templates": {
                    "architecture_template": arch_template,
                    "constraints_template": constraints_template
                }
            },
            timeout=300
        )
        response.raise_for_status()
        docs_result = response.json()

        # Save files
        arch_dir = workspace / "architecture"
        arch_dir.mkdir(parents=True, exist_ok=True)

        arch_file = arch_dir / "ARCHITECTURE.md"
        arch_file.write_text(docs_result["architecture_doc"], encoding='utf-8')

        constraints_file = arch_dir / "CONSTRAINTS.md"
        constraints_file.write_text(docs_result["constraints_doc"], encoding='utf-8')

        print(f"✓ Created: {arch_file.relative_to(workspace)}")
        print(f"✓ Created: {constraints_file.relative_to(workspace)}")

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
            "error": f"Documentation synthesis failed: {e}"
        }


def _parse_conversation_file(file_path: Path) -> List[Dict[str, str]]:
    """Parse conversation file into structured format."""
    content = file_path.read_text(encoding='utf-8')
    conversation = []

    sections = content.split("## ")
    for section in sections[1:]:  # Skip header
        lines = section.split('\n', 1)
        if len(lines) >= 2:
            role = lines[0].strip()
            message = lines[1].strip().rstrip('---').strip()
            conversation.append({
                "role": role,
                "message": message
            })

    return conversation


def run_full_workflow(project_name: str, requirements: str) -> Dict[str, Any]:
    """
    Run the complete AI-native workflow autonomously.

    This is the main orchestration function that Claude Code calls.

    Phases:
    1. Assess project state
    2. Run architectural dialogue (if needed)
    3. Synthesize documentation (if needed)
    4. Implement code (if needed)
    5. Audit implementation (if needed)

    Args:
        project_name: Name of the project
        requirements: Project requirements text

    Returns:
        dict with complete workflow results
    """
    workspace = WORKSPACE_ROOT / project_name
    workspace.mkdir(parents=True, exist_ok=True)

    # Save requirements
    req_file = workspace / "requirements.md"
    req_file.write_text(requirements, encoding='utf-8')

    results = {
        "project_name": project_name,
        "workspace": str(workspace),
        "phases_completed": []
    }

    # Phase 1: Architectural Dialogue
    dialogue_result = run_architectural_dialogue_api(project_name, requirements)
    if not dialogue_result["success"]:
        results["error"] = dialogue_result["error"]
        return results

    results["dialogue"] = dialogue_result
    results["phases_completed"].append("dialogue")

    # Phase 2: Documentation Synthesis
    docs_result = synthesize_documentation_api(project_name)
    if not docs_result["success"]:
        results["error"] = docs_result["error"]
        return results

    results["documentation"] = docs_result
    results["phases_completed"].append("documentation")

    # TODO: Phase 3: Implementation
    # TODO: Phase 4: Audit

    print("\n" + "="*60)
    print("WORKFLOW COMPLETE")
    print("="*60)
    print(f"\nProject: {project_name}")
    print(f"Workspace: {workspace}")
    print(f"Phases completed: {', '.join(results['phases_completed'])}")
    print()

    results["success"] = True
    return results
