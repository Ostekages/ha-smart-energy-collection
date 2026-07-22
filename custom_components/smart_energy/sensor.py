"""Sensor platform for Smart Energy.

Philosophy (from the design): a *few* sensors with *rich* attributes, not 50
thin sensors. The main ``sensor.smart_energy`` exposes everything the dashboard
needs; two small helper sensors expose clean values for automations.
"""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN
from .coordinator import SmartEnergyCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Smart Energy sensors."""
    coordinator: SmartEnergyCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            SmartEnergyMainSensor(coordinator, entry),
            SmartEnergyBestTodaySensor(coordinator, entry),
            SmartEnergyTrendSensor(coordinator, entry),
        ]
    )


class SmartEnergyBase(CoordinatorEntity[SmartEnergyCoordinator], SensorEntity):
    """Shared device wiring."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SmartEnergyCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=DEFAULT_NAME,
            manufacturer="Smart Energy",
            model="Price engine",
        )


class SmartEnergyMainSensor(SmartEnergyBase):
    """Main sensor: current price + all the rich attributes."""

    _attr_icon = "mdi:transmission-tower"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, coordinator: SmartEnergyCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_main"
        self._attr_name = None  # takes the device name -> "Smart Energy"

    @property
    def native_value(self):
        return self.coordinator.data.get("current")

    @property
    def native_unit_of_measurement(self):
        return self.coordinator.data.get("unit")

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        attrs = {
            "current": data.get("current"),
            "next_hours": data.get("next_hours"),
            "best_today": data.get("best_today"),
            "best_tomorrow": data.get("best_tomorrow"),
            "trend": data.get("trend"),
            "has_tomorrow": data.get("has_tomorrow"),
            "updated": data.get("updated"),
        }
        # Flatten best_windows -> best_2h, best_3h, best_4h ...
        for key, window in (data.get("best_windows") or {}).items():
            attrs[f"best_{key}"] = window
        return attrs


class SmartEnergyBestTodaySensor(SmartEnergyBase):
    """State = ``13-16`` style label of the best window from now."""

    _attr_icon = "mdi:star-outline"

    def __init__(self, coordinator: SmartEnergyCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_best_today"
        self._attr_name = "Best today"

    @property
    def native_value(self):
        return self.coordinator.data.get("best_today_label")

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.get("best_today") or {}


class SmartEnergyTrendSensor(SmartEnergyBase):
    """State = better_today / better_tomorrow / equal."""

    _attr_icon = "mdi:trending-down"

    def __init__(self, coordinator: SmartEnergyCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_trend"
        self._attr_name = "Trend"

    @property
    def native_value(self):
        return self.coordinator.data.get("trend")

    @property
    def extra_state_attributes(self):
        return {
            "best_today": self.coordinator.data.get("best_today_label"),
            "best_tomorrow": self.coordinator.data.get("best_tomorrow_label"),
        }
