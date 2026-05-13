from __future__ import annotations

import logging

import keyring
from launchpadlib.credentials import (
    AccessToken,
    AuthorizeRequestTokenWithBrowser,
    Credentials,
    KeyringCredentialStore,
    RequestTokenAuthorizationEngine,
)
from launchpadlib.launchpad import Launchpad
from lazr.restfulclient.errors import Unauthorized

from maas_ultimate_bug_triager.config import LaunchpadConfig

logger = logging.getLogger(__name__)

CONSUMER_KEY = "maas-ultimate-bug-triager"
SERVICE_ROOT = "production"
UNIQUE_CONSUMER_ID = f"{CONSUMER_KEY}@{SERVICE_ROOT}"


class _ConsumerAuthorizer(AuthorizeRequestTokenWithBrowser):
    """Authorizer using an application-specific consumer with WRITE_PUBLIC access.

    The default AuthorizeRequestTokenWithBrowser discards consumer_name
    and always uses DESKTOP_INTEGRATION with a SystemWideConsumer. This
    subclass uses an application-specific consumer with WRITE_PUBLIC
    access, which is more appropriate for a standalone application and
    avoids DESKTOP_INTEGRATION permission issues.
    """

    def __init__(self, service_root: str, consumer_name: str) -> None:
        RequestTokenAuthorizationEngine.__init__(
            self,
            service_root,
            consumer_name=consumer_name,
            allow_access_levels=["WRITE_PUBLIC"],
        )


def _load_from_keyring() -> Credentials | None:
    store = KeyringCredentialStore(fallback=False)
    return store.load(UNIQUE_CONSUMER_ID)


def _delete_from_keyring() -> None:
    try:
        keyring.delete_password("launchpadlib", UNIQUE_CONSUMER_ID)
    except keyring.errors.PasswordDeleteError:
        pass


def _validate_credentials(credentials: Credentials) -> Launchpad | None:
    try:
        lp = Launchpad(credentials, None, None, service_root=SERVICE_ROOT)
        lp.projects["maas"]
        logger.debug("Launchpad credentials validated successfully")
        return lp
    except Unauthorized:
        logger.info("Launchpad credentials are invalid or expired")
        return None
    except Exception:
        logger.exception("Unexpected error validating Launchpad credentials")
        return None


def _config_to_credentials(config: LaunchpadConfig) -> Credentials:
    access_token = AccessToken(config.oauth_token, config.oauth_token_secret)
    return Credentials(
        consumer_name=config.consumer_key, access_token=access_token
    )


def try_stored_credentials(
    config: LaunchpadConfig | None = None,
) -> Launchpad | None:
    """Try to get a Launchpad instance from stored credentials (non-interactive).

    Checks the system keyring first, then the config file if provided.
    Returns None if no valid credentials are found.
    """
    credentials = _load_from_keyring()
    if credentials is not None:
        lp = _validate_credentials(credentials)
        if lp is not None:
            logger.info("Using cached Launchpad credentials from keyring")
            return lp
        logger.info("Keyring credentials are invalid, removing them")
        _delete_from_keyring()

    if config is not None and config.oauth_token and config.oauth_token_secret:
        logger.info("Trying config file credentials")
        credentials = _config_to_credentials(config)
        lp = _validate_credentials(credentials)
        if lp is not None:
            logger.info("Config credentials valid, saving to keyring")
            store = KeyringCredentialStore(fallback=False)
            store.save(credentials, UNIQUE_CONSUMER_ID)
            return lp

    return None


def get_launchpad_credentials(
    config: LaunchpadConfig | None = None,
) -> Launchpad:
    """Get a Launchpad instance, opening the browser for auth if needed.

    First tries stored credentials (keyring, then config file).
    If no valid credentials are found, opens the browser for interactive
    OAuth authorization and saves the new credentials to the keyring.
    """
    lp = try_stored_credentials(config)
    if lp is not None:
        return lp

    logger.info("Opening browser for Launchpad authentication...")
    store = KeyringCredentialStore(fallback=False)
    auth_engine = _ConsumerAuthorizer(SERVICE_ROOT, CONSUMER_KEY)
    lp = Launchpad.login_with(
        application_name=CONSUMER_KEY,
        service_root=SERVICE_ROOT,
        authorization_engine=auth_engine,
        credential_store=store,
    )
    logger.info("Launchpad authentication successful, credentials saved to keyring")
    return lp
