"""API client for Livly."""

import logging
import time
from typing import Any

import aiohttp

from .const import (
    AUTH_CLIENT_ID,
    DEFAULT_HEADERS,
    ENDPOINT_OAUTH_TOKEN,
    ENDPOINT_PACKAGES_FILTERED,
    ENDPOINT_PASSWORDLESS_START,
    ENDPOINT_USER_ME,
    OAUTH_GRANT_TYPE_OTP,
    OAUTH_GRANT_TYPE_REFRESH,
    OAUTH_SCOPE,
)

_LOGGER = logging.getLogger(__name__)


class LivlyAuthError(Exception):
    """Exception for authentication errors."""


class LivlyApiError(Exception):
    """Exception for API errors."""


class LivlyApiClient:
    """API client for Livly."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._id_token: str | None = None
        self._token_expires_at: float = 0
        self._user_id: int | None = None

    @property
    def access_token(self) -> str | None:
        """Return the access token."""
        return self._access_token

    @property
    def refresh_token(self) -> str | None:
        """Return the refresh token."""
        return self._refresh_token

    @property
    def id_token(self) -> str | None:
        """Return the ID token."""
        return self._id_token

    @property
    def token_expires_at(self) -> float:
        """Return the token expiration timestamp."""
        return self._token_expires_at

    @property
    def user_id(self) -> int | None:
        """Return the user ID."""
        return self._user_id

    def set_tokens(
        self,
        access_token: str,
        refresh_token: str,
        id_token: str,
        expires_at: float,
    ) -> None:
        """Set the authentication tokens."""
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._id_token = id_token
        self._token_expires_at = expires_at

    def set_user_id(self, user_id: int) -> None:
        """Set the user ID."""
        self._user_id = user_id

    async def request_otp(self, phone_number: str) -> bool:
        """Request an OTP code to be sent via SMS.

        Args:
            phone_number: Phone number in format +[country_code][digits]

        Returns:
            True if OTP was sent successfully.

        Raises:
            LivlyAuthError: If the request fails.
        """
        payload = {
            "client_id": AUTH_CLIENT_ID,
            "phone_number": phone_number,
            "send": "code",
            "connection": "sms",
        }

        try:
            async with self._session.post(
                ENDPOINT_PASSWORDLESS_START,
                json=payload,
            ) as response:
                if response.status == 200:
                    return True
                _LOGGER.error("OTP request failed with status %s", response.status)
                raise LivlyAuthError(f"Failed to send OTP: {response.status}")
        except aiohttp.ClientError as err:
            _LOGGER.error("OTP request error: %s", err)
            raise LivlyAuthError(f"Connection error: {err}") from err

    async def verify_otp(self, phone_number: str, otp_code: str) -> dict[str, Any]:
        """Verify the OTP code and obtain tokens.

        Args:
            phone_number: Phone number used for OTP request.
            otp_code: 6-digit OTP code from SMS.

        Returns:
            Token response dictionary.

        Raises:
            LivlyAuthError: If verification fails.
        """
        payload = {
            "client_id": AUTH_CLIENT_ID,
            "scope": OAUTH_SCOPE,
            "username": phone_number,
            "grant_type": OAUTH_GRANT_TYPE_OTP,
            "otp": otp_code,
            "realm": "sms",
        }

        try:
            async with self._session.post(
                ENDPOINT_OAUTH_TOKEN,
                json=payload,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self._access_token = data["access_token"]
                    self._refresh_token = data["refresh_token"]
                    self._id_token = data["id_token"]
                    self._token_expires_at = time.time() + data["expires_in"]
                    return data
                _LOGGER.error("OTP verification failed with status %s", response.status)
                raise LivlyAuthError(f"Invalid OTP code: {response.status}")
        except aiohttp.ClientError as err:
            _LOGGER.error("OTP verification error: %s", err)
            raise LivlyAuthError(f"Connection error: {err}") from err

    async def refresh_access_token(self) -> bool:
        """Refresh the access token using the refresh token.

        Note: This refresh mechanism may need adjustment - it's untested
        and based on standard OAuth2 refresh token flow.

        Returns:
            True if token was refreshed successfully.

        Raises:
            LivlyAuthError: If refresh fails.
        """
        if not self._refresh_token:
            raise LivlyAuthError("No refresh token available")

        payload = {
            "client_id": AUTH_CLIENT_ID,
            "grant_type": OAUTH_GRANT_TYPE_REFRESH,
            "refresh_token": self._refresh_token,
        }

        try:
            async with self._session.post(
                ENDPOINT_OAUTH_TOKEN,
                json=payload,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self._access_token = data["access_token"]
                    self._refresh_token = data.get("refresh_token", self._refresh_token)
                    self._id_token = data.get("id_token", self._id_token)
                    self._token_expires_at = time.time() + data["expires_in"]
                    return True
                _LOGGER.error("Token refresh failed with status %s", response.status)
                raise LivlyAuthError(f"Token refresh failed: {response.status}")
        except aiohttp.ClientError as err:
            _LOGGER.error("Token refresh error: %s", err)
            raise LivlyAuthError(f"Connection error: {err}") from err

    def _get_auth_headers(self) -> dict[str, str]:
        """Get headers for authenticated API requests."""
        headers = DEFAULT_HEADERS.copy()
        headers["Authorization"] = f"Bearer {self._access_token}"
        return headers

    async def _ensure_valid_token(self) -> None:
        """Ensure we have a valid access token, refreshing if needed."""
        if not self._access_token:
            raise LivlyAuthError("Not authenticated")

        # Refresh if token expires in less than 5 minutes
        if time.time() > self._token_expires_at - 300:
            await self.refresh_access_token()

    async def get_user_info(self) -> dict[str, Any]:
        """Get the current user's information.

        Returns:
            User data dictionary.

        Raises:
            LivlyApiError: If the request fails.
        """
        await self._ensure_valid_token()

        try:
            async with self._session.get(
                f"{ENDPOINT_USER_ME}?v=202404",
                headers=self._get_auth_headers(),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self._user_id = data["Data"]["userId"]
                    return data["Data"]
                _LOGGER.error("Get user info failed with status %s", response.status)
                raise LivlyApiError(f"Failed to get user info: {response.status}")
        except aiohttp.ClientError as err:
            _LOGGER.error("Get user info error: %s", err)
            raise LivlyApiError(f"Connection error: {err}") from err

    async def get_pending_packages(self) -> list[dict[str, Any]]:
        """Get pending packages for the current user.

        Returns:
            List of pending packages.

        Raises:
            LivlyApiError: If the request fails.
        """
        await self._ensure_valid_token()

        if not self._user_id:
            await self.get_user_info()

        url = ENDPOINT_PACKAGES_FILTERED.format(user_id=self._user_id)
        payload = {
            "historyOrInventory": "Inventory",
            "sort": {
                "direction": "Desc",
                "type": "ScannedByTimestamp",
            },
        }

        try:
            async with self._session.post(
                url,
                headers=self._get_auth_headers(),
                json=payload,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("Data", [])
                _LOGGER.error("Get packages failed with status %s", response.status)
                raise LivlyApiError(f"Failed to get packages: {response.status}")
        except aiohttp.ClientError as err:
            _LOGGER.error("Get packages error: %s", err)
            raise LivlyApiError(f"Connection error: {err}") from err
