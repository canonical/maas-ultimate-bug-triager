from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from maas_ultimate_bug_triager.dependencies import get_ai_service
from maas_ultimate_bug_triager.services.ai import AIService

router = APIRouter(prefix="/api/config")


class AIModelResponse(BaseModel):
    model: str
    available_models: list[str]


class SetAIModelRequest(BaseModel):
    model: str


@router.get("/ai-model")
async def get_ai_model(
    service: AIService = Depends(get_ai_service),
) -> AIModelResponse:
    return AIModelResponse(
        model=service.config.model,
        available_models=service.get_available_models(),
    )


@router.put("/ai-model")
async def set_ai_model(
    body: SetAIModelRequest,
    service: AIService = Depends(get_ai_service),
) -> AIModelResponse:
    available = service.get_available_models()
    if body.model not in available:
        raise HTTPException(
            422,
            detail=(
                f"Invalid model: {body.model}. "
                f"Available: {available}"
            ),
        )
    service.set_model(body.model)
    return AIModelResponse(
        model=service.config.model,
        available_models=service.get_available_models(),
    )
