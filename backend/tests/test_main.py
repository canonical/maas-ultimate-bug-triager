from datetime import datetime, timezone

from starlette.testclient import TestClient

from maas_ultimate_bug_triager.config import (
    AIConfig,
    AppConfig,
    LaunchpadConfig,
    ServerConfig,
)
from maas_ultimate_bug_triager.main import create_app
from maas_ultimate_bug_triager.models.action import AnalysisResponse
from maas_ultimate_bug_triager.models.bug import BugDetail, BugSummary


def test_app_starts():
    config = AppConfig(
        launchpad=LaunchpadConfig(
            oauth_token="test-token",
            oauth_token_secret="test-secret",
        ),
        ai=AIConfig(api_key="test-key"),
        server=ServerConfig(),
    )
    app = create_app(config)
    assert app.title == "MAAS Ultimate Bug Triager"


def test_unknown_route_returns_404(client: TestClient):
    response = client.get("/nonexistent")
    assert response.status_code == 404


def test_full_workflow(client: TestClient, mock_launchpad_service, mock_ai_service):
    bugs = [
        BugSummary(
            id=1,
            title="Test Bug",
            status="New",
            importance="Undecided",
            owner="user1",
            date_created=datetime(2024, 1, 1, tzinfo=timezone.utc),
            tags=["tag1"],
        )
    ]
    mock_launchpad_service.fetch_untriaged_bugs.return_value = bugs

    response = client.get("/api/bugs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 1

    detail = BugDetail(
        id=1,
        title="Test Bug",
        status="New",
        importance="Undecided",
        owner="user1",
        date_created=datetime(2024, 1, 1, tzinfo=timezone.utc),
        tags=["tag1"],
        description="A test bug description",
        comments=[],
        attachments=[],
    )
    mock_launchpad_service.fetch_bug_details.return_value = detail
    analysis = AnalysisResponse(
        bug_id=1,
        reasoning="Needs more information",
        suggested_actions=[],
    )
    mock_ai_service.analyze_bug.return_value = analysis

    response = client.post("/api/bugs/1/analyze")
    assert response.status_code == 200
    data = response.json()
    assert data["bug_id"] == 1
    assert data["reasoning"] == "Needs more information"
    assert data["reasoning"] == "Needs more information"

    mock_launchpad_service.add_comment.return_value = None
    body = {"actions": [{"type": "ADD_COMMENT", "content": "Needs more info"}]}
    response = client.post("/api/bugs/1/actions", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["bug_id"] == 1
    assert "ADD_COMMENT" in data["applied"]
    assert data["errors"] == []
