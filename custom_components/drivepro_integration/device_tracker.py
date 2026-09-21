"""Device tracker platform for the DrivePro integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity

from .data import DriveproVehicle
from .entity import DriveproIntegrationEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import DriveproDataUpdateCoordinator
    from .data import DriveproIntegrationConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: DriveproIntegrationConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the tracker platform."""
    trackers = []
    config_vehicle: DriveproVehicle
    for config_vehicle in entry.runtime_data.coordinator.data["Vehicles"]:
        vehicle = DriveproVehicle(config_vehicle)
        trackers.append(
            DriveproDeviceTracker(
                coordinator=entry.runtime_data.coordinator,
                vehicle=vehicle,
            )
        )
    async_add_entities(trackers, update_before_add=True)


class DriveproDeviceTracker(DriveproIntegrationEntity, TrackerEntity):
    """DrivePro device tracker."""

    _attr_force_update = False
    _attr_icon = "mdi:car"

    def __init__(
        self,
        coordinator: DriveproDataUpdateCoordinator,
        vehicle: DriveproVehicle,
    ) -> None:
        """Initialize the Tracker."""
        super().__init__(coordinator, vehicle)
        self.vehicle = vehicle
        self._attr_unique_id = vehicle.FleetVehicleId
        self._attr_name = vehicle.Label

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        return {
            "heading": self.vehicle.Heading,
            "speed_kph": self.vehicle.SpeedKph,
            "location_name": self.vehicle.LocationName,
            "driver_name": self.vehicle.DriverName,
        }

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        return self.vehicle.Latitude

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        return self.vehicle.Longitude

    @property
    def source_type(self) -> SourceType:
        """Return the source type, eg gps or router, of the device."""
        return SourceType.GPS
