#!/usr/bin/env python3
"""Reproduce MAAS bugs using the Copilot SDK."""

import asyncio

from copilot import CopilotClient
from copilot.generated.session_events import (
    AssistantMessageData,
    AssistantMessageDeltaData,
    SessionIdleData,
    ToolExecutionCompleteData,
    ToolExecutionPartialResultData,
    ToolExecutionStartData,
)
from copilot.session import PermissionHandler

from .bugs import BugReport


def extract_version(ip: str) -> str:
    # Very specific to the version of the setup script I have.
    return str(int(ip.split(".")[2]) - 60)


def _build_maas_prompt(bug: BugReport, maas_ip: str) -> str:
    """Build a prompt for the Copilot agent to reproduce a MAAS bug.

    The agent is instructed to wrap every MAAS CLI command in an SSH call.
    """
    messages_summary = ""
    if bug.messages:
        for i, msg in enumerate(bug.messages, 1):
            messages_summary += (
                f"\n--- Message {i} by {msg.owner_display_name} ---\n{msg.content}\n"
            )

    return f"""You are a MAAS bug reproduction agent. Your task is to reproduce bug #{bug.id} on a MAAS server.

## Bug Information
- **Title:** {bug.title}
- **Status:** {bug.status}
- **Importance:** {bug.importance}
- **URL:** {bug.web_link}

## Description
{bug.description or "(no description)"}

## Bug Comments / Messages
{messages_summary or "(no messages)"}

## Instructions
1. Analyze the bug description and comments above to understand what needs to be reproduced.
2. To run any MAAS CLI command, you MUST wrap it in an SSH call like this:
   ```
   ssh ubuntu@{maas_ip} "maas admin <COMMAND>"
   ```
   For example: `ssh ubuntu@{maas_ip} "maas admin machines read"`
3. Use the MAAS CLI to inspect the current state of the system and attempt to reproduce the reported issue.
4. You can check the documentation of MAAS in http://{maas_ip}:5240/MAAS/docs/. The code can be found in ~/Canonical/maas-{extract_version(maas_ip)}.
5. Report what you find — whether you successfully reproduced the bug or not, and any relevant observations. Put all findings in a `report` folder in this directory.
6. Do NOT change anything related to the machine maas-host.
7. If you create VMs, only create with 1 core and at most 8gb of memory.
8. Clean up after yourself when finished (e.g., if creating VMs, delete them after the test. If creating subnets, delete them as well etc.)
"""


async def _run_reproduction(bug: BugReport, maas_ip: str) -> None:
    """Run the bug reproduction logic via the Copilot SDK."""
    async with CopilotClient() as client:
        async with await client.create_session(
            on_permission_request=PermissionHandler.approve_all,
            model="claude-haiku-4.5",
        ) as session:
            done = asyncio.Event()

            def on_event(event):
                match event.data:
                    case AssistantMessageData() as data:
                        print("----------------")
                        print(data.content)
                        print("----------------")
                    case AssistantMessageDeltaData() as data:
                        print(data.delta_content, end="", flush=True)
                    case ToolExecutionStartData() as data:
                        print(f"\n[Tool: {data.tool_name}]")
                        if data.arguments:
                            import json

                            print(f"  Args: {json.dumps(data.arguments, indent=2)}")
                    case ToolExecutionPartialResultData() as data:
                        print(data.partial_output, end="", flush=True)
                    case ToolExecutionCompleteData() as data:
                        if data.result and data.result.content:
                            print(f"\n  Result: {data.result.content}")
                        if data.error:
                            print(f"\n  Error: {data.error.message}")
                    case SessionIdleData():
                        done.set()

            session.on(on_event)

            prompt = _build_maas_prompt(bug, maas_ip=maas_ip)
            await session.send(prompt)
            await done.wait()


def reproduce_bug(bug_report: BugReport, maas_ip: str) -> None:
    """Reproduce a specific MAAS bug using the Copilot SDK.

    The Copilot agent will SSH into the MAAS server and run CLI commands
    to attempt to reproduce the reported issue.
    """
    asyncio.run(_run_reproduction(bug_report, maas_ip=maas_ip))
