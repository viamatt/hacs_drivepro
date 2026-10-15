"""DriveproIntegrationEntity class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, LOGGER
from .coordinator import DriveproDataUpdateCoordinator, DriveproDetailsCoordinator

if TYPE_CHECKING:
    from .data import DriveproVehicle


def vehicle_device_info(domain: str, vehicle: DriveproVehicle) -> DeviceInfo:
    """Return the device a vehicle's entities belong to."""
    return DeviceInfo(
        identifiers={(domain, vehicle.FleetVehicleId)},
        name=vehicle.Label,
        model=vehicle.Model,
        manufacturer=vehicle.Manufacturer,
    )


class DriveproIntegrationEntity(CoordinatorEntity[DriveproDataUpdateCoordinator]):
    """DriveproIntegrationEntity class."""

    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: DriveproDataUpdateCoordinator,
        vehicle: DriveproVehicle,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.vehicle = vehicle
        self._attr_unique_id = vehicle.FleetVehicleId
        self._attr_device_info = vehicle_device_info(
            coordinator.config_entry.domain, vehicle
        )

    def _handle_coordinator_update(self) -> None:
        """Refresh this entity's vehicle from the coordinator data."""
        self._refresh_vehicle()
        super()._handle_coordinator_update()

    def _refresh_vehicle(self) -> None:
        """Replace this entity's vehicle with the latest coordinator data."""
        for config_vehicle in self.coordinator.data.get("Vehicles", []):
            if config_vehicle["FleetVehicleId"] == self.vehicle.FleetVehicleId:
                self.vehicle = type(self.vehicle)(config_vehicle)
                LOGGER.debug(
                    "DrivePro refreshed vehicle %s for %s",
                    self.vehicle.FleetVehicleId,
                    self.__class__.__name__,
                )
                break
        else:
            LOGGER.warning(
                "DrivePro vehicle %s was missing from coordinator refresh",
                self.vehicle.FleetVehicleId,
            )


class DriveproDetailsEntity(CoordinatorEntity[DriveproDetailsCoordinator]):
    """An entity for a vehicle's trips or details (MOT, tax and reminders)."""

    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: DriveproDetailsCoordinator,
        vehicle: DriveproVehicle,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.vehicle = vehicle
        self._attr_device_info = vehicle_device_info(
            coordinator.config_entry.domain, vehicle
        )

    @property
    def last_trip(self) -> dict[str, Any] | None:
        """The vehicle's most recent completed trip, if any."""
        return ((self.coordinator.data or {}).get("trips") or {}).get(
            self.vehicle.FleetVehicleId
        )

    @property
    def details(self) -> dict[str, Any] | None:
        """The vehicle's details, once fetched."""
        return ((self.coordinator.data or {}).get("details") or {}).get(
            self.vehicle.FleetVehicleId
        )
