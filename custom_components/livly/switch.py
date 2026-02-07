"""Switch platform for Livly integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_PHONE_NUMBER, DOMAIN
from .coordinator import LivlyDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Livly switch based on a config entry."""
    coordinator: LivlyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([LivlySyncSwitch(coordinator, entry)])


class LivlySyncSwitch(CoordinatorEntity[LivlyDataUpdateCoordinator], SwitchEntity):
    """Switch to enable/disable automatic syncing."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LivlyDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_sync_enabled"
        self._attr_name = "Sync Enabled"
        self._attr_icon = "mdi:sync"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        phone_last4 = self._entry.data[CONF_PHONE_NUMBER][-4:]
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": f"Livly (***{phone_last4})",
            "manufacturer": "Livly",
        }

    @property
    def is_on(self) -> bool:
        """Return true if sync is enabled."""
        return self.coordinator.sync_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable syncing."""
        await self.coordinator.async_set_sync_enabled(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable syncing."""
        await self.coordinator.async_set_sync_enabled(False)
