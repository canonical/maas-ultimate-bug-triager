from starlette.testclient import TestClient


def test_get_ai_model(client: TestClient, mock_ai_service):
    mock_ai_service.config.model = "gemini-2.5-pro"
    mock_ai_service.get_available_models.return_value = [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    ]
    response = client.get("/api/config/ai-model")
    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "gemini-2.5-pro"
    assert data["available_models"] == [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    ]


def test_set_ai_model(client: TestClient, mock_ai_service):
    mock_ai_service.get_available_models.return_value = [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    ]
    mock_ai_service.config.model = "gemini-2.5-pro"

    def set_model(model):
        mock_ai_service.config.model = model

    mock_ai_service.set_model.side_effect = set_model

    response = client.put("/api/config/ai-model", json={"model": "gemini-2.5-flash"})
    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "gemini-2.5-flash"


def test_set_ai_model_invalid(client: TestClient, mock_ai_service):
    mock_ai_service.get_available_models.return_value = [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    ]
    response = client.put("/api/config/ai-model", json={"model": "invalid-model"})
    assert response.status_code == 422


def test_config_cors_headers(client: TestClient):
    response = client.options(
        "/api/config/ai-model",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
