from datetime import datetime, timezone
from unittest.mock import call

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
        reasoning="Needs more info",
        suggested_actions=[],
    )
    mock_ai_service.analyze_bug.return_value = analysis
    response = client.post("/api/bugs/1/analyze")
    assert response.status_code == 200
    data = response.json()
    assert data["bug_id"] == 1
    assert data["reasoning"] == "Needs more info"


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


def test_apply_actions_reorders_comment_before_status(
    client: TestClient, mock_launchpad_service
):
    mock_launchpad_service.get_bug_task_url.return_value = (
        "http://lp/bug/1/task"
    )
    mock_launchpad_service.fetch_bug_details.return_value = BugDetail(
        id=1,
        title="Bug",
        status="New",
        importance="Undecided",
        owner="user",
        date_created=datetime(2024, 1, 1, tzinfo=timezone.utc),
        tags=[],
        description="d",
        comments=[],
        attachments=[],
    )
    body = {
        "actions": [
            {"type": "SET_STATUS", "status": "Triaged"},
            {"type": "ADD_COMMENT", "content": "triaging comment"},
        ]
    }
    response = client.post("/api/bugs/1/actions", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["applied"] == ["ADD_COMMENT", "SET_STATUS"]
    assert data["errors"] == []
    assert mock_launchpad_service.method_calls[0] == call.fetch_bug_details(1)
    assert mock_launchpad_service.method_calls[1] == call.add_comment(
        1, "triaging comment"
    )
    assert mock_launchpad_service.method_calls[2] == call.get_bug_task_url(1)
    assert mock_launchpad_service.method_calls[3] == call.set_status(
        "http://lp/bug/1/task", "Triaged"
    )


def test_apply_actions_incomplete_bug_gets_reset_to_new(
    client: TestClient, mock_launchpad_service
):
    mock_launchpad_service.get_bug_task_url.return_value = (
        "http://lp/bug/1/task"
    )
    mock_launchpad_service.fetch_bug_details.return_value = BugDetail(
        id=1,
        title="Bug",
        status="Incomplete",
        importance="Undecided",
        owner="user",
        date_created=datetime(2024, 1, 1, tzinfo=timezone.utc),
        tags=[],
        description="d",
        comments=[],
        attachments=[],
    )
    body = {
        "actions": [
            {"type": "ADD_COMMENT", "content": "need more info"},
            {"type": "SET_STATUS", "status": "Incomplete"},
        ]
    }
    response = client.post("/api/bugs/1/actions", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["applied"] == ["SET_STATUS", "ADD_COMMENT", "SET_STATUS"]
    assert data["errors"] == []
    assert mock_launchpad_service.method_calls[0] == call.fetch_bug_details(1)
    assert mock_launchpad_service.method_calls[1] == call.get_bug_task_url(1)
    assert mock_launchpad_service.method_calls[2] == call.set_status(
        "http://lp/bug/1/task", "New"
    )
    assert mock_launchpad_service.method_calls[3] == call.add_comment(
        1, "need more info"
    )
    assert mock_launchpad_service.method_calls[4] == call.get_bug_task_url(1)
    assert mock_launchpad_service.method_calls[5] == call.set_status(
        "http://lp/bug/1/task", "Incomplete"
    )


def test_apply_actions_non_incomplete_bug_no_reset(
    client: TestClient, mock_launchpad_service
):
    mock_launchpad_service.get_bug_task_url.return_value = (
        "http://lp/bug/1/task"
    )
    mock_launchpad_service.fetch_bug_details.return_value = BugDetail(
        id=1,
        title="Bug",
        status="New",
        importance="Undecided",
        owner="user",
        date_created=datetime(2024, 1, 1, tzinfo=timezone.utc),
        tags=[],
        description="d",
        comments=[],
        attachments=[],
    )
    body = {
        "actions": [
            {"type": "ADD_COMMENT", "content": "triaging"},
            {"type": "SET_STATUS", "status": "Triaged"},
        ]
    }
    response = client.post("/api/bugs/1/actions", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["applied"] == ["ADD_COMMENT", "SET_STATUS"]
    assert data["errors"] == []


def test_apply_actions_no_comment_no_fetch(client: TestClient, mock_launchpad_service):
    mock_launchpad_service.get_bug_task_url.return_value = (
        "http://lp/bug/1/task"
    )
    body = {
        "actions": [
            {"type": "SET_STATUS", "status": "Triaged"},
            {"type": "ADD_TAG", "tag": "triaged"},
        ]
    }
    response = client.post("/api/bugs/1/actions", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["applied"] == ["ADD_TAG", "SET_STATUS"]
    mock_launchpad_service.fetch_bug_details.assert_not_called()
