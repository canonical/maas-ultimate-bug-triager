from datetime import datetime, timezone

from starlette.testclient import TestClient

from maas_ultimate_bug_triager.models.action import AnalysisResponse
from maas_ultimate_bug_triager.models.bug import BugDetail, BugSummary


def test_list_bugs_success(client: TestClient, mock_launchpad_service):
    bugs = [
        BugSummary(
            id=1,
            title="Bug 1",
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
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == 1


def test_list_bugs_launchpad_error(client: TestClient, mock_launchpad_service):
    mock_launchpad_service.fetch_untriaged_bugs.side_effect = Exception(
        "LP error"
    )
    response = client.get("/api/bugs")
    assert response.status_code == 502


def test_get_bug_success(client: TestClient, mock_launchpad_service):
    detail = BugDetail(
        id=1,
        title="Bug 1",
        status="New",
        importance="Undecided",
        owner="user1",
        date_created=datetime(2024, 1, 1, tzinfo=timezone.utc),
        tags=["tag1"],
        description="desc",
        comments=[],
        attachments=[],
    )
    mock_launchpad_service.fetch_bug_details.return_value = detail
    response = client.get("/api/bugs/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_get_bug_not_found_key_error(client: TestClient, mock_launchpad_service):
    mock_launchpad_service.fetch_bug_details.side_effect = KeyError(
        "not found"
    )
    response = client.get("/api/bugs/999")
    assert response.status_code == 404


def test_get_bug_not_found_value_error(client: TestClient, mock_launchpad_service):
    mock_launchpad_service.fetch_bug_details.side_effect = ValueError(
        "No MAAS task"
    )
    response = client.get("/api/bugs/999")
    assert response.status_code == 404


def test_get_bug_launchpad_error(client: TestClient, mock_launchpad_service):
    mock_launchpad_service.fetch_bug_details.side_effect = Exception(
        "LP error"
    )
    response = client.get("/api/bugs/1")
    assert response.status_code == 502


def test_analyze_bug_success(client, mock_launchpad_service, mock_ai_service):
    detail = BugDetail(
        id=1,
        title="Bug 1",
        status="New",
        importance="Undecided",
        owner="user1",
        date_created=datetime(2024, 1, 1, tzinfo=timezone.utc),
        tags=["tag1"],
        description="desc",
        comments=[],
        attachments=[],
    )
    mock_launchpad_service.fetch_bug_details.return_value = detail
    analysis = AnalysisResponse(
        bug_id=1,
        is_triaged=False,
        reasoning="Needs more info",
        suggested_actions=[],
    )
    mock_ai_service.analyze_bug.return_value = analysis
    response = client.post("/api/bugs/1/analyze")
    assert response.status_code == 200
    data = response.json()
    assert data["bug_id"] == 1
    assert data["is_triaged"] is False


def test_analyze_bug_not_found(client, mock_launchpad_service):
    mock_launchpad_service.fetch_bug_details.side_effect = KeyError(
        "not found"
    )
    response = client.post("/api/bugs/999/analyze")
    assert response.status_code == 404


def test_analyze_bug_launchpad_error(client, mock_launchpad_service):
    mock_launchpad_service.fetch_bug_details.side_effect = Exception(
        "LP error"
    )
    response = client.post("/api/bugs/1/analyze")
    assert response.status_code == 502


def test_analyze_bug_ai_error(client, mock_launchpad_service, mock_ai_service):
    detail = BugDetail(
        id=1,
        title="Bug 1",
        status="New",
        importance="Undecided",
        owner="user1",
        date_created=datetime(2024, 1, 1, tzinfo=timezone.utc),
        tags=["tag1"],
        description="desc",
        comments=[],
        attachments=[],
    )
    mock_launchpad_service.fetch_bug_details.return_value = detail
    mock_ai_service.analyze_bug.side_effect = Exception("AI error")
    response = client.post("/api/bugs/1/analyze")
    assert response.status_code == 502


def test_apply_actions_success(client: TestClient, mock_launchpad_service):
    mock_launchpad_service.get_bug_task_url.return_value = (
        "http://lp/bug/1/task"
    )
    body = {
        "actions": [
            {"type": "ADD_COMMENT", "content": "test comment"},
            {"type": "ADD_TAG", "tag": "test-tag"},
        ]
    }
    response = client.post("/api/bugs/1/actions", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["applied"] == ["ADD_COMMENT", "ADD_TAG"]
    assert data["errors"] == []
    assert data["bug_id"] == 1


def test_apply_actions_partial_failure(client, mock_launchpad_service):
    mock_launchpad_service.add_comment.side_effect = Exception(
        "Comment failed"
    )
    mock_launchpad_service.get_bug_task_url.return_value = (
        "http://lp/bug/1/task"
    )
    body = {
        "actions": [
            {"type": "ADD_COMMENT", "content": "test comment"},
            {"type": "SET_STATUS", "status": "Triaged"},
        ]
    }
    response = client.post("/api/bugs/1/actions", json=body)
    assert response.status_code == 200
    data = response.json()
    assert "ADD_COMMENT" in [e["action_type"] for e in data["errors"]]
    assert "SET_STATUS" in data["applied"]


def test_apply_actions_all_fail(client: TestClient, mock_launchpad_service):
    mock_launchpad_service.add_comment.side_effect = Exception("fail")
    mock_launchpad_service.add_tag.side_effect = Exception("fail")
    body = {
        "actions": [
            {"type": "ADD_COMMENT", "content": "test"},
            {"type": "ADD_TAG", "tag": "t"},
        ]
    }
    response = client.post("/api/bugs/1/actions", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["applied"] == []
    assert len(data["errors"]) == 2


def test_cors_headers_present(client: TestClient):
    response = client.options(
        "/api/bugs",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" in response.headers
    assert (
        response.headers["access-control-allow-origin"]
        == "http://localhost:5173"
    )
