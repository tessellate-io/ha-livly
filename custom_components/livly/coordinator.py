"""Data update coordinator for Livly."""

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import LivlyApiClient, LivlyApiError, LivlyAuthError
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_ID_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN_EXPIRES_AT,
    DOMAIN,
    UPDATE_INTERVAL_MINUTES,
)

_LOGGER = logging.getLogger(__name__)


class LivlyDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage fetching Livly data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: LivlyApiClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )
        self._client = client
        self._entry = entry
        self._sync_enabled = True
        self._last_update_time: datetime | None = None

    @property
    def sync_enabled(self) -> bool:
        """Return whether sync is enabled."""
        return self._sync_enabled

    @property
    def last_update_time(self) -> datetime | None:
        """Return the last successful update time."""
        return self._last_update_time

    async def async_set_sync_enabled(self, enabled: bool) -> None:
        """Enable or disable syncing."""
        self._sync_enabled = enabled
        if enabled:
            # Resume polling and fetch immediately
            self.update_interval = timedelta(minutes=UPDATE_INTERVAL_MINUTES)
            await self.async_request_refresh()
        else:
            # Stop polling by setting interval to None
            self.update_interval = None
        self.async_update_listeners()

    @property
    def client(self) -> LivlyApiClient:
        """Return the API client."""
        return self._client

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        # Skip fetching if sync is disabled, return existing data
        if not self._sync_enabled:
            if self.data:
                return self.data
            return {"pending_packages": [], "pending_count": 0}

        try:
            packages = await self._client.get_pending_packages()

            # Update stored tokens if they were refreshed
            await self._update_stored_tokens()

            # Track last successful update time
            self._last_update_time = dt_util.utcnow()

            return {
                "pending_packages": packages,
                "pending_count": len(packages),
            }
        except LivlyAuthError as err:
            _LOGGER.error("Authentication error: %s", err)
            raise UpdateFailed(f"Authentication error: {err}") from err
        except LivlyApiError as err:
            _LOGGER.error("API error: %s", err)
            raise UpdateFailed(f"API error: {err}") from err

    async def _update_stored_tokens(self) -> None:
        """Update stored tokens if they changed during refresh."""
        current_data = dict(self._entry.data)
        updated = False

        if self._client.access_token != current_data.get(CONF_ACCESS_TOKEN):
            current_data[CONF_ACCESS_TOKEN] = self._client.access_token
            updated = True
        if self._client.refresh_token != current_data.get(CONF_REFRESH_TOKEN):
            current_data[CONF_REFRESH_TOKEN] = self._client.refresh_token
            updated = True
        if self._client.id_token != current_data.get(CONF_ID_TOKEN):
            current_data[CONF_ID_TOKEN] = self._client.id_token
            updated = True
        if self._client.token_expires_at != current_data.get(CONF_TOKEN_EXPIRES_AT):
            current_data[CONF_TOKEN_EXPIRES_AT] = self._client.token_expires_at
            updated = True

        if updated:
            self.hass.config_entries.async_update_entry(self._entry, data=current_data)
