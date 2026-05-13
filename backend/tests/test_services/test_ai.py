from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from maas_ultimate_bug_triager.config import AIConfig
from maas_ultimate_bug_triager.models.action import AnalysisResponse
from maas_ultimate_bug_triager.models.bug import Attachment, BugDetail, Comment
from maas_ultimate_bug_triager.services.ai import AIService, _build_prompt


@pytest.fixture
def mock_client():
    with patch("maas_ultimate_bug_triager.services.ai.genai.Client") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def service(mock_client):
    config = AIConfig(api_key="test-key")
    return AIService(config)


def _make_bug(**overrides) -> BugDetail:
    defaults = dict(
        id=1,
        title="Machine fails to deploy",
        status="New",
        importance="Undecided",
        owner="reporter@example.com",
        date_created="2025-01-01T00:00:00Z",
        tags=["deployment"],
        description="The machine fails to deploy with an error message.",
        comments=[
            Comment(
                author="commenter@example.com",
                date="2025-01-02T00:00:00Z",
                content="I can reproduce this issue.",
            )
        ],
        attachments=[
            Attachment(
                id=10,
                title="screenshot.png",
                content_type="image/png",
                size=2048,
            )
        ],
    )
    defaults.update(overrides)
    return BugDetail(**defaults)


def _canned_response(data: dict, use_parsed: bool = True):
    response = MagicMock()
    if use_parsed:
        response.parsed = data
        response.text = json.dumps(data)
    else:
        response.parsed = None
        response.text = json.dumps(data)
    return response


@pytest.mark.asyncio
async def test_analyze_bug_returns_analysis_response(service, mock_client):
    response_data = {
        "bug_id": 1,
        "is_triaged": False,
        "reasoning": "The bug lacks steps to reproduce.",
        "suggested_actions": [
            {"type": "SET_STATUS", "status": "Incomplete"},
            {
                "type": "ADD_COMMENT",
                "content": "Could you provide steps to reproduce?",
            },
        ],
    }
    mock_client.models.generate_content.return_value = _canned_response(response_data)

    result = await service.analyze_bug(_make_bug())

    assert isinstance(result, AnalysisResponse)
    assert result.bug_id == 1
    assert result.is_triaged is False
    assert result.reasoning == "The bug lacks steps to reproduce."
    assert len(result.suggested_actions) == 2


@pytest.mark.asyncio
async def test_analyze_bug_parses_text_when_no_parsed(service, mock_client):
    response_data = {
        "bug_id": 1,
        "is_triaged": True,
        "reasoning": "The bug is well triaged.",
        "suggested_actions": [],
    }
    mock_client.models.generate_content.return_value = _canned_response(
        response_data, use_parsed=False
    )

    result = await service.analyze_bug(_make_bug())

    assert isinstance(result, AnalysisResponse)
    assert result.bug_id == 1
    assert result.is_triaged is True


@pytest.mark.asyncio
async def test_analyze_bug_invalid_json_raises(service, mock_client):
    mock_response = MagicMock()
    mock_response.parsed = None
    mock_response.text = "not valid json"
    mock_client.models.generate_content.return_value = mock_response

    with pytest.raises((json.JSONDecodeError, ValidationError)):
        await service.analyze_bug(_make_bug())


@pytest.mark.asyncio
async def test_analyze_bug_invalid_schema_raises(service, mock_client):
    response_data = {
        "bug_id": 1,
        "is_triaged": "not_a_bool",
        "reasoning": "bad data",
        "suggested_actions": [],
    }
    mock_response = MagicMock()
    mock_response.parsed = None
    mock_response.text = json.dumps(response_data)
    mock_client.models.generate_content.return_value = mock_response

    with pytest.raises(ValidationError):
        await service.analyze_bug(_make_bug())


def test_set_model(service):
    assert service.config.model == "gemini-2.5-pro"
    service.set_model("gemini-2.5-flash")
    assert service.config.model == "gemini-2.5-flash"


def test_get_available_models(service):
    models = service.get_available_models()
    assert models == ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"]


def test_prompt_includes_bug_fields():
    bug = _make_bug()
    prompt = _build_prompt(bug)

    assert str(bug.id) in prompt
    assert bug.title in prompt
    assert bug.status in prompt
    assert bug.importance in prompt
    assert bug.owner in prompt
    assert str(bug.date_created) in prompt
    assert "deployment" in prompt
    assert bug.description in prompt
    assert bug.comments[0].author in prompt
    assert bug.comments[0].content in prompt
    assert "screenshot.png" in prompt


def test_prompt_handles_empty_collections():
    bug = _make_bug(tags=[], comments=[], attachments=[])
    prompt = _build_prompt(bug)

    assert "None" in prompt
    assert "No comments." in prompt
    assert "No attachments." in prompt


@pytest.mark.asyncio
async def test_analyze_bug_calls_generate_content_with_correct_params(
    service, mock_client
):
    response_data = {
        "bug_id": 1,
        "is_triaged": True,
        "reasoning": "ok",
        "suggested_actions": [],
    }
    mock_client.models.generate_content.return_value = _canned_response(response_data)

    await service.analyze_bug(_make_bug())

    call_args = mock_client.models.generate_content.call_args
    assert call_args.kwargs["model"] == "gemini-2.5-pro"
    config_arg = call_args.kwargs["config"]
    assert config_arg.response_mime_type == "application/json"
    assert not hasattr(config_arg, "response_schema") or config_arg.response_schema is None
