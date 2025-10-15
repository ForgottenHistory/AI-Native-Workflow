#!/usr/bin/env python3
"""
Agent Server Launcher

Starts all agent servers in the background.
Each server runs in its own process.
"""

import subprocess
import time
import sys
from pathlib import Path
import requests

# Server configurations
SERVERS = [
    {
        "name": "Architect",
        "script": "servers/architect_server.py",
        "port": 5001
    },
    {
        "name": "Coder",
        "script": "servers/coder_server.py",
        "port": 5002
    },
    {
        "name": "Docs",
        "script": "servers/docs_server.py",
        "port": 5003
    }
]

def check_server_health(port: int, retries: int = 10) -> bool:
    """Check if server is healthy."""
    url = f"http://localhost:{port}/health"

    for i in range(retries):
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return True
        except:
            time.sleep(1)

    return False


def start_servers():
    """Start all agent servers."""
    print("=" * 60)
    print("AI-Native Workflow: Starting Agent Servers")
    print("=" * 60)
    print()

    processes = []
    system_dir = Path(__file__).parent

    for server in SERVERS:
        print(f"Starting {server['name']} Agent Server (Port {server['port']})...")

        script_path = system_dir / server['script']

        # Start server in background
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(system_dir)
        )

        processes.append({
            "name": server['name'],
            "port": server['port'],
            "process": process
        })

        print(f"  → Process started (PID: {process.pid})")

    print()
    print("Waiting for servers to initialize...")
    print()

    # Wait for all servers to become healthy
    all_healthy = True
    for server_info in processes:
        print(f"Checking {server_info['name']} health...", end=" ", flush=True)

        if check_server_health(server_info['port']):
            print("✓ Healthy")
        else:
            print("✗ Failed to start")
            all_healthy = False

    print()

    if all_healthy:
        print("=" * 60)
        print("All Agent Servers Running!")
        print("=" * 60)
        print()
        print("Agent Servers:")
        for server in SERVERS:
            print(f"  - {server['name']}: http://localhost:{server['port']}")
        print()
        print("Orchestration:")
        print(f"  - Run workflows via Claude Code")
        print()
        print("To stop servers:")
        print(f"  - Press Ctrl+C or run: python stop_agents.py")
        print()
        print("=" * 60)

        # Keep script running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nStopping servers...")
            for server_info in processes:
                server_info['process'].terminate()
            print("All servers stopped.")

    else:
        print("Some servers failed to start. Check logs above.")
        # Terminate any started processes
        for server_info in processes:
            server_info['process'].terminate()
        sys.exit(1)


if __name__ == "__main__":
    start_servers()
