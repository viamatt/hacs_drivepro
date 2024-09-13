"""Sensor platform for integration_blueprint."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription

from .entity import DriveproIntegrationEntity

from .data import (DriveproVehicle)
from .const import LOGGER
from collections.abc import Callable
from dataclasses import dataclass
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .coordinator import DriveproDataUpdateCoordinator
from .data import DriveproIntegrationConfigEntry
from homeassistant.components.device_tracker import SourceType, TrackerEntity


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: DriveproIntegrationConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the tracker platform."""

    trackers = []
    config_vehicle:DriveproVehicle
    for config_vehicle in entry.runtime_data.coordinator.data["Vehicles"]:
            veh=DriveproVehicle(config_vehicle)
            trackers.append(DriveproDeviceTracker(                 
                 coordinator=entry.runtime_data.coordinator,
                 vehicle=veh,
            ))
    ## add all the sensors
    async_add_entities(trackers, True)
    
    


class DriveproDeviceTracker(DriveproIntegrationEntity, TrackerEntity):
    """MyBMW device tracker."""

    _attr_force_update = False
    _attr_icon = "mdi:car"

    def __init__(
        self,
        coordinator: DriveproDataUpdateCoordinator,
        vehicle: DriveproVehicle,
    ) -> None:
        """Initialize the Tracker."""
        super().__init__(coordinator, vehicle)
        self.vehicle=vehicle
        self._attr_unique_id = vehicle.FleetVehicleId
        self._attr_name = None
        self

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {**self._attrs, "direction": self.vehicle.Heading}

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        return self.vehicle.Latitude     
    
    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        return self.vehicle.Lonitude

    @property
    def source_type(self) -> SourceType:
        """Return the source type, eg gps or router, of the device."""
        return SourceType.GPS