from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from launchpadlib.credentials import AccessToken, Credentials
from lazr.restfulclient.errors import Unauthorized

from maas_ultimate_bug_triager.auth import (
    UNIQUE_CONSUMER_ID,
    _config_to_credentials,
    _delete_from_keyring,
    _load_from_keyring,
    _validate_credentials,
    get_launchpad_credentials,
    try_stored_credentials,
)
from maas_ultimate_bug_triager.config import LaunchpadConfig


@pytest.fixture
def mock_keyring():
    with patch("maas_ultimate_bug_triager.auth.keyring") as kr:
        yield kr


@pytest.fixture
def valid_config():
    return LaunchpadConfig(
        consumer_key="test-app",
        oauth_token="my-token",
        oauth_token_secret="my-secret",
    )


def test_config_to_credentials(valid_config):
    creds = _config_to_credentials(valid_config)
    assert creds.consumer.key == "test-app"
    assert creds.access_token.key == "my-token"
    assert creds.access_token.secret == "my-secret"


def test_load_from_keyring_miss(mock_keyring):
    mock_keyring.get_password.return_value = None
    assert _load_from_keyring() is None


def test_delete_from_keyring(mock_keyring):
    _delete_from_keyring()
    mock_keyring.delete_password.assert_called_once_with(
        "launchpadlib", UNIQUE_CONSUMER_ID
    )


def test_delete_from_keyring_noop(mock_keyring):
    mock_keyring.errors.PasswordDeleteError = type(
        "PasswordDeleteError", (Exception,), {}
    )
    mock_keyring.delete_password.side_effect = (
        mock_keyring.errors.PasswordDeleteError()
    )
    _delete_from_keyring()


def test_validate_credentials_success():
    with patch("maas_ultimate_bug_triager.auth.Launchpad") as MockLP:
        mock_instance = MagicMock()
        MockLP.return_value = mock_instance
        access_token = AccessToken("t", "s")
        credentials = Credentials(consumer_name="test", access_token=access_token)
        result = _validate_credentials(credentials)
        assert result is mock_instance


def test_validate_credentials_unauthorized():
    with patch("maas_ultimate_bug_triager.auth.Launchpad") as MockLP:
        MockLP.return_value = MagicMock()
        MockLP.return_value.projects.__getitem__.side_effect = Unauthorized(
            MagicMock(), MagicMock()
        )
        access_token = AccessToken("t", "s")
        credentials = Credentials(consumer_name="test", access_token=access_token)
        result = _validate_credentials(credentials)
        assert result is None


def test_validate_credentials_other_error():
    with patch("maas_ultimate_bug_triager.auth.Launchpad") as MockLP:
        MockLP.return_value = MagicMock()
        MockLP.return_value.projects.__getitem__.side_effect = ConnectionError(
            "network"
        )
        access_token = AccessToken("t", "s")
        credentials = Credentials(consumer_name="test", access_token=access_token)
        result = _validate_credentials(credentials)
        assert result is None


def test_try_stored_credentials_from_keyring(mock_keyring):
    with patch("maas_ultimate_bug_triager.auth._load_from_keyring") as mock_load, patch(
        "maas_ultimate_bug_triager.auth._validate_credentials"
    ) as mock_validate:
        access_token = AccessToken("cached", "cached-secret")
        mock_creds = Credentials(consumer_name="test", access_token=access_token)
        mock_load.return_value = mock_creds
        mock_lp = MagicMock()
        mock_validate.return_value = mock_lp
        result = try_stored_credentials()
        assert result is mock_lp


def test_try_stored_credentials_expired_keyring(mock_keyring):
    with patch("maas_ultimate_bug_triager.auth._load_from_keyring") as mock_load, patch(
        "maas_ultimate_bug_triager.auth._validate_credentials"
    ) as mock_validate, patch(
        "maas_ultimate_bug_triager.auth._delete_from_keyring"
    ) as mock_delete:
        access_token = AccessToken("expired", "expired-secret")
        mock_creds = Credentials(consumer_name="test", access_token=access_token)
        mock_load.return_value = mock_creds
        mock_validate.return_value = None
        result = try_stored_credentials()
        assert result is None
        mock_delete.assert_called_once()


def test_try_stored_credentials_from_config(mock_keyring, valid_config):
    with patch("maas_ultimate_bug_triager.auth._load_from_keyring") as mock_load, patch(
        "maas_ultimate_bug_triager.auth._validate_credentials"
    ) as mock_validate, patch(
        "maas_ultimate_bug_triager.auth.KeyringCredentialStore"
    ) as MockStore:
        mock_load.return_value = None
        mock_lp = MagicMock()
        mock_validate.return_value = mock_lp
        result = try_stored_credentials(valid_config)
        assert result is mock_lp
        MockStore.return_value.save.assert_called_once()


def test_try_stored_credentials_nothing_available(mock_keyring):
    with patch("maas_ultimate_bug_triager.auth._load_from_keyring") as mock_load:
        mock_load.return_value = None
        assert try_stored_credentials() is None


def test_get_launchpad_credentials_falls_back_to_interactive(mock_keyring):
    with patch(
        "maas_ultimate_bug_triager.auth.try_stored_credentials"
    ) as mock_try, patch(
        "maas_ultimate_bug_triager.auth.Launchpad"
    ) as MockLP:
        mock_try.return_value = None
        mock_lp_instance = MagicMock()
        mock_lp_instance.credentials = Credentials(
            consumer_name="test",
            access_token=AccessToken("fresh", "fresh-secret"),
        )
        MockLP.login_with.return_value = mock_lp_instance
        result = get_launchpad_credentials()
        assert result is mock_lp_instance
        MockLP.login_with.assert_called_once()


def test_launchpad_service_accepts_lp_directly():
    from maas_ultimate_bug_triager.services.launchpad import LaunchpadService

    mock_lp = MagicMock()
    project = MagicMock()
    mock_lp.projects.__getitem__.return_value = project
    svc = LaunchpadService(lp=mock_lp)
    assert svc.lp is mock_lp
    assert svc.project is project


def test_launchpad_service_raises_without_lp_or_config():
    from maas_ultimate_bug_triager.services.launchpad import LaunchpadService

    with pytest.raises(ValueError, match="Either a Launchpad instance"):
        LaunchpadService()
