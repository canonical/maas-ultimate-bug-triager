"""SSE endpoint for streaming bug reproduction output."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from lp.reproducer import _run_reproduction

from maas_ultimate_bug_triager.dependencies import get_launchpad_service
from maas_ultimate_bug_triager.services.launchpad import LaunchpadService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bugs")


@router.get("/{bug_id}/reproduce")
async def stream_reproduction(
    bug_id: int,
    maas_ip: str,
    service: LaunchpadService = Depends(get_launchpad_service),
):
    """Stream the bug reproduction output as Server-Sent Events.

    The Copilot agent will SSH into the MAAS server and run CLI commands
    to attempt to reproduce the reported issue. Output is streamed in
    real time via SSE.
    """
    logger.debug("GET /api/bugs/%d/reproduce?maas_ip=%s: starting...", bug_id, maas_ip)

    try:
        detail = service.fetch_bug_details(bug_id)
    except (KeyError, ValueError):
        raise HTTPException(404, detail=f"Bug {bug_id} not found")
    except Exception as e:
        logger.exception("Failed to fetch bug %s for reproduction", bug_id)
        raise HTTPException(502, detail=str(e))

    # Convert BugDetail to the lp BugReport format
    from lp.bugs import BugMessage, BugReport

    bug_report = BugReport(
        id=detail.id,
        title=detail.title,
        status=detail.status,
        importance=detail.importance,
        assignee=detail.owner,
        web_link=f"https://bugs.launchpad.net/maas/+bug/{detail.id}",
        description=detail.description,
        messages=[
            BugMessage(
                owner_display_name=c.author,
                date_created=c.date,
                content=c.content,
            )
            for c in detail.comments
        ],
    )

    async def event_stream():
        async for chunk in _run_reproduction(bug_report, maas_ip=maas_ip):
            # SSE format: "data: <text>\n\n"
            for line in chunk.split("\n"):
                if line:
                    yield f"data: {line}\n"
            yield "\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
