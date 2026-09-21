"""Binary sensor platform for integration_blueprint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import callback

from .const import LOGGER
from .data import DriveproVehicle
from .entity import DriveproIntegrationEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import DriveproDataUpdateCoordinator
    from .data import DriveproIntegrationConfigEntry


@dataclass
class DriveproBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Drivepro binary_sensor entity."""


BINARY_SENSOR_TYPES: tuple[DriveproBinarySensorEntityDescription, ...] = (
    DriveproBinarySensorEntityDescription(
        key="Armed",
        name="Armed",
        device_class=BinarySensorDeviceClass.LOCK,
        icon="mdi:shield-lock-outline",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: DriveproIntegrationConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    binary_sensors = []
    config_vehicle: DriveproVehicle
    for config_vehicle in entry.runtime_data.coordinator.data["Vehicles"]:
        vehicle = DriveproVehicle(config_vehicle)
        binary_sensors.extend(
            DriveproIntegrationBinarySensor(
                coordinator=entry.runtime_data.coordinator,
                vehicle=vehicle,
                description=description,
            )
            for description in BINARY_SENSOR_TYPES
        )
    async_add_entities(binary_sensors, update_before_add=True)


class DriveproIntegrationBinarySensor(DriveproIntegrationEntity, BinarySensorEntity):
    """drivepro_integration binary_sensor class."""

    def __init__(
        self,
        coordinator: DriveproDataUpdateCoordinator,
        vehicle: DriveproVehicle,
        description: DriveproBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary_sensor class."""
        super().__init__(coordinator, vehicle)
        self.vehicle = vehicle
        self.entity_description = description
        self._attr_unique_id = f"{vehicle.FleetVehicleId}-{description.key}"
        self._attr_name = f"{vehicle.Label} {description.name}"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._refresh_vehicle()
        is_on = (
            self.vehicle.ArmState == "STATEARMED"
            if self.entity_description.key == "Armed"
            else bool(getattr(self.vehicle, self.entity_description.key))
        )
        LOGGER.debug(
            "DrivePro updated binary_sensor '%s' of %s to %s",
            self.entity_description.key,
            self.vehicle.Label,
            is_on,
        )
        self._attr_is_on = is_on
        super()._handle_coordinator_update()
