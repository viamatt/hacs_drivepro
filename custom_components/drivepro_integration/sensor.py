"""Sensor platform for integration_blueprint."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription

from .entity import DriveproIntegrationEntity

from .data import (DriveproVehicle)
from .const import LOGGER


if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import DriveproDataUpdateCoordinator
    from .data import DriveproIntegrationConfigEntry

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="drivepro",
        name="DrivePro Integration Sensor",
        icon="mdi:car",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: DriveproIntegrationConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    #LOGGER.debug("Drivepro Setup Sensors %s",entry.runtime_data.coordinator.data)

    sensors = []
    config_vehicle:DriveproVehicle
    for config_vehicle in entry.runtime_data.coordinator.data["Vehicles"]:
            sensors.append(DriveproIntegrationSensor(                 
                 coordinator=entry.runtime_data.coordinator,
                 vehicle=DriveproVehicle(config_vehicle),
                 entity_description = SensorEntityDescription(
                    key="drivepro.Label",
                    name="DrivePro Vehicle Label",
                    icon="mdi:car",
    )))
    ## add all the sensors
    async_add_entities(sensors, True)
    # async_add_entities(
    #     DriveproIntegrationSensor(
    #         coordinator=entry.runtime_data.coordinator,
    #         entity_description=entity_description,
    #     )
    #     for entity_description in ENTITY_DESCRIPTIONS
    


class DriveproIntegrationSensor(DriveproIntegrationEntity, SensorEntity):
    """drivepro_integration Sensor class."""

    def __init__(
        self,
        coordinator: DriveproDataUpdateCoordinator,
        vehicle: DriveproVehicle,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        LOGGER.debug("Drivepro INIT Sensor %s",vehicle)
        super().__init__(coordinator,vehicle)
        self.vehicle=vehicle
        self._attr_unique_id = f"{vehicle.FleetFleetVehicleId}-{entity_description.key}"
        self.entity_description = entity_description
      

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        return self.coordinator.data.get("body")
