"""Sensor platform for integration_blueprint."""

from __future__ import annotations

from typing import TYPE_CHECKING

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
    LOGGER.debug("Drivepro Setup Sensor %s",entry)

    sensors = []
    config_vehicle:DriveproVehicle
    for config_vehicle in entry:
            sensors.append(DriveproIntegrationSensor(
                 vehicle=config_vehicle,
                 coordinator=entry.runtime_data.coordinator,
                 entity_description = SensorEntityDescription(
                    key="drivepro."+config_vehicle.VehicleId+".Label",
                    name="DrivePro Vehicle Label"+config_vehicle.Label,
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
        super().__init__(coordinator)
        self.entity_description = entity_description

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        return self.coordinator.data.get("body")
