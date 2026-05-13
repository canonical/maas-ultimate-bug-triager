from fastapi import HTTPException, Request

from maas_ultimate_bug_triager.services.ai import AIService
from maas_ultimate_bug_triager.services.launchpad import LaunchpadService


def get_launchpad_service(request: Request) -> LaunchpadService:
    service = getattr(request.app.state, "launchpad_service", None)
    if service is None:
        raise HTTPException(503, "Launchpad service not available")
    return service


def get_ai_service(request: Request) -> AIService:
    service = getattr(request.app.state, "ai_service", None)
    if service is None:
        raise HTTPException(503, "AI service not available")
    return service
