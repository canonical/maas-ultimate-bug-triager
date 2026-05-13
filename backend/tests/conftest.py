from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.testclient import TestClient

from maas_ultimate_bug_triager.config import (
    AIConfig,
    AppConfig,
    ServerConfig,
)
from maas_ultimate_bug_triager.main import create_app
from maas_ultimate_bug_triager.services.ai import AIService
from maas_ultimate_bug_triager.services.launchpad import LaunchpadService


@pytest.fixture
def mock_launchpad_service():
    return MagicMock(spec=LaunchpadService)


@pytest.fixture
def mock_ai_service():
    service = MagicMock(spec=AIService)
    service.config = AIConfig(api_key="test-key")
    service.analyze_bug = AsyncMock()
    return service


@pytest.fixture
def client(mock_launchpad_service, mock_ai_service):
    config = AppConfig(
        ai=AIConfig(api_key="test-key"),
        server=ServerConfig(),
    )
    app = create_app(config)
    app.state.launchpad_service = mock_launchpad_service
    app.state.ai_service = mock_ai_service
    return TestClient(app)
