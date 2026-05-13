#!/usr/bin/env python3
"""Reproduce MAAS bugs using the Copilot SDK."""

import asyncio
from collections.abc import AsyncGenerator

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
5. Report what you find — whether you successfully reproduced the bug or not, and any relevant observations. Put all findings in a `report` folder in this directory on a SINGLE FILE named `LP-{bug.id}.md`.
6. Do NOT change anything related to the machine maas-host.
7. If you create VMs, only create with 1 core and at most 8gb of memory.
8. Clean up after yourself when finished (e.g., if creating VMs, delete them after the test. If creating subnets, delete them as well etc.)
9. After `LP-{bug.id}` is created, your task is done and you can end.
"""


async def _run_reproduction(bug: BugReport, maas_ip: str) -> AsyncGenerator[str, None]:
    """Run the bug reproduction logic via the Copilot SDK.

    Yields output strings as they become available, using an internal
    asyncio.Queue to bridge the synchronous event callback with the
    async generator.
    """
    queue: asyncio.Queue[str | None] = asyncio.Queue()

    async def _reproduction_task():
        async with CopilotClient() as client:
            async with await client.create_session(
                on_permission_request=PermissionHandler.approve_all,
                model="claude-haiku-4.5",
            ) as session:
                done = asyncio.Event()

                def on_event(event):
                    match event.data:
                        case AssistantMessageData() as data:
                            queue.put_nowait("----------------\n")
                            queue.put_nowait(data.content + "\n")
                            queue.put_nowait("----------------\n")
                        case AssistantMessageDeltaData() as data:
                            queue.put_nowait(data.delta_content)
                        case ToolExecutionStartData() as data:
                            queue.put_nowait(f"\n[Tool: {data.tool_name}]\n")
                            if data.arguments:
                                import json

                                queue.put_nowait(
                                    f"  Args: {json.dumps(data.arguments, indent=2)}\n"
                                )
                        case ToolExecutionPartialResultData() as data:
                            queue.put_nowait(data.partial_output)
                        case ToolExecutionCompleteData() as data:
                            if data.result and data.result.content:
                                queue.put_nowait(f"\n  Result: {data.result.content}\n")
                            if data.error:
                                queue.put_nowait(f"\n  Error: {data.error.message}\n")
                        case SessionIdleData():
                            done.set()

                session.on(on_event)

                prompt = _build_maas_prompt(bug, maas_ip=maas_ip)
                await session.send(prompt)
                await done.wait()

        # Signal the generator that we're done
        await queue.put(None)

    task = asyncio.create_task(_reproduction_task())

    while True:
        item = await queue.get()
        if item is None:
            break
        yield item

    # Re-raise any exception that occurred in the task
    await task


async def reproduce_bug(bug_report: BugReport, maas_ip: str) -> None:
    """Reproduce a specific MAAS bug using the Copilot SDK.

    The Copilot agent will SSH into the MAAS server and run CLI commands
    to attempt to reproduce the reported issue.

    This async function iterates over the _run_reproduction generator and
    prints each yielded string to stdout (for CLI backward compatibility).
    """
    async for chunk in _run_reproduction(bug_report, maas_ip=maas_ip):
        print(chunk, end="", flush=True)
