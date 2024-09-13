"""BlueprintEntity class."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION
from .coordinator import DriveproDataUpdateCoordinator
from .data import DriveproVehicle

class DriveproIntegrationEntity(CoordinatorEntity[DriveproDataUpdateCoordinator]):
    """BlueprintEntity class."""

    _attr_attribution = ATTRIBUTION

    def __init__(self,coordinator: DriveproDataUpdateCoordinator,vehicle: DriveproVehicle) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = vehicle.VehicleId
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    coordinator.config_entry.domain,
                    vehicle.VehicleId,
                ),                
            },
            name=vehicle.Label
        )
