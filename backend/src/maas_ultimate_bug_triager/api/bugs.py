import logging
import time

from fastapi import APIRouter, Depends, HTTPException

from maas_ultimate_bug_triager.dependencies import (
    get_ai_service,
    get_launchpad_service,
)
from maas_ultimate_bug_triager.models.action import (
    ActionsRequest,
    ActionType,
    ApplyActionsResponse,
)
from maas_ultimate_bug_triager.models.bug import BugDetail, BugSummary
from maas_ultimate_bug_triager.services.ai import AIService
from maas_ultimate_bug_triager.services.launchpad import LaunchpadService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bugs")


@router.get("")
async def list_bugs(
    service: LaunchpadService = Depends(get_launchpad_service),
) -> list[BugSummary]:
    logger.debug("GET /api/bugs: starting...")
    start = time.time()
    try:
        result = service.fetch_untriaged_bugs()
        logger.debug(
            "GET /api/bugs: %d bugs in %.2fs",
            len(result),
            time.time() - start,
        )
        return result
    except Exception as e:
        logger.exception("Failed to fetch untriaged bugs")
        raise HTTPException(502, detail=str(e))


@router.get("/{bug_id}")
async def get_bug(
    bug_id: int,
    service: LaunchpadService = Depends(get_launchpad_service),
) -> BugDetail:
    logger.debug("GET /api/bugs/%d: starting...", bug_id)
    start = time.time()
    try:
        result = service.fetch_bug_details(bug_id)
        logger.debug("GET /api/bugs/%d: done in %.2fs", bug_id, time.time() - start)
        return result
    except (KeyError, ValueError):
        raise HTTPException(404, detail=f"Bug {bug_id} not found")
    except Exception as e:
        logger.exception("Failed to fetch bug %s", bug_id)
        raise HTTPException(502, detail=str(e))


@router.post("/{bug_id}/analyze")
async def analyze_bug(
    bug_id: int,
    service: LaunchpadService = Depends(get_launchpad_service),
    ai_service: AIService = Depends(get_ai_service),
):
    logger.debug("POST /api/bugs/%d/analyze: starting...", bug_id)
    start = time.time()
    try:
        detail = service.fetch_bug_details(bug_id)
        logger.debug("  fetch_bug_details took %.2fs", time.time() - start)
    except (KeyError, ValueError):
        raise HTTPException(404, detail=f"Bug {bug_id} not found")
    except Exception as e:
        logger.exception("Failed to fetch bug %s for analysis", bug_id)
        raise HTTPException(502, detail=str(e))
    t0 = time.time()
    try:
        result = await ai_service.analyze_bug(detail)
        logger.debug("  AI analysis took %.2fs", time.time() - t0)
        logger.debug(
            "POST /api/bugs/%d/analyze: total %.2fs",
            bug_id,
            time.time() - start,
        )
        return result
    except Exception as e:
        logger.exception("AI analysis failed for bug %s", bug_id)
        raise HTTPException(502, detail=str(e))


@router.post("/{bug_id}/actions")
async def apply_actions(
    bug_id: int,
    body: ActionsRequest,
    service: LaunchpadService = Depends(get_launchpad_service),
) -> ApplyActionsResponse:
    logger.debug("POST /api/bugs/%d/actions: %d actions", bug_id, len(body.actions))
    start = time.time()
    applied: list[str] = []
    errors: list[dict] = []
    for action in body.actions:
        t0 = time.time()
        try:
            if action.type == ActionType.ADD_COMMENT:
                service.add_comment(bug_id, action.content)
            elif action.type == ActionType.SET_STATUS:
                bug_task_url = service.get_bug_task_url(bug_id)
                service.set_status(bug_task_url, action.status)
            elif action.type == ActionType.SET_IMPORTANCE:
                bug_task_url = service.get_bug_task_url(bug_id)
                service.set_importance(bug_task_url, action.importance)
            elif action.type == ActionType.ADD_TAG:
                service.add_tag(bug_id, action.tag)
            elif action.type == ActionType.REMOVE_TAG:
                service.remove_tag(bug_id, action.tag)
            applied.append(action.type.value)
            logger.debug("  action %s took %.2fs", action.type.value, time.time() - t0)
        except Exception as e:
            errors.append({"action_type": action.type.value, "error": str(e)})
            logger.debug(
                "  action %s FAILED in %.2fs: %s",
                action.type.value,
                time.time() - t0,
                e,
            )
    logger.debug("POST /api/bugs/%d/actions: total %.2fs", bug_id, time.time() - start)
    return ApplyActionsResponse(bug_id=bug_id, applied=applied, errors=errors)
