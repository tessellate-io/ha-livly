"""Sensor platform for Livly integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
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
    """Set up Livly sensor based on a config entry."""
    coordinator: LivlyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([LivlyPendingPackagesSensor(coordinator, entry)])


class LivlyPendingPackagesSensor(CoordinatorEntity[LivlyDataUpdateCoordinator], SensorEntity):
    """Sensor for pending packages count."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: LivlyDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_pending_packages"
        self._attr_name = "Pending Packages"
        self._attr_icon = "mdi:package-variant"

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
    def native_value(self) -> int | None:
        """Return the number of pending packages."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("pending_count", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs: dict[str, Any] = {}

        if self.coordinator.last_update_time:
            attrs["last_checked"] = self.coordinator.last_update_time.isoformat()

        return attrs
