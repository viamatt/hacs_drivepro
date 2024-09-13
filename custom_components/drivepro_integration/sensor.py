"""Sensor platform for integration_blueprint."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription

from .entity import DriveproIntegrationEntity

from .data import (DriveproVehicle)
from .const import LOGGER
from collections.abc import Callable
from dataclasses import dataclass
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import LENGTH, PERCENTAGE, VOLUME
from .coordinator import DriveproDataUpdateCoordinator
from .data import DriveproIntegrationConfigEntry,ValueWithUnit


@dataclass
class DriveproSensorEntityDescription(SensorEntityDescription):
    """Describes BMW sensor entity."""

    key_class: str | None = None
    unit_type: str | None = None
    value: Callable = lambda x, y: x


def convert_and_round(
    state: ValueWithUnit,
    converter: Callable[[float | None, str], float],
    precision: int,
) -> float | None:
    """Safely convert and round a value from ValueWithUnit."""
    if state.value and state.unit:
        return round(
            converter(state.value, state.unit, precision
        ))
    if state.value:
        return state.value
    return None



SENSOR_TYPES: dict[str, DriveproSensorEntityDescription] = {
    # --- Generic ---
    "SupplyMilliVoltage": DriveproSensorEntityDescription(
        key="SupplyMilliVoltage",
        name="Supply MilliVolts",
        unit_type="mV",
        icon="mdi:current-ac",
    )
}

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
            veh=DriveproVehicle(config_vehicle)
            sensors.append(DriveproIntegrationSensor(                 
                 coordinator=entry.runtime_data.coordinator,
                 vehicle=veh,
                 entity_description = DriveproSensorEntityDescription(
        key=veh.Label+"_"+"SupplyMilliVoltage",
        name=veh.Label+" "+"Supply MilliVolts",
        unit_type="mV",
        icon="mdi:current-dc",
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
        entity_description: DriveproSensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        LOGGER.debug("Drivepro INIT Sensor %s",vehicle)
        super().__init__(coordinator, vehicle)
        self.vehicle=vehicle
        self._attr_unique_id = f"{vehicle.FleetVehicleId}-{entity_description.key}"
        self.entity_description = entity_description
        
      

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        LOGGER.debug(
            "DrivePro Updating sensor '%s' of %s", self.entity_description.key, self.vehicle.Label
        )
        if self.entity_description.key_class is None:
            state = getattr(self.vehicle, self.entity_description.key)
        else:
            state = getattr(
                getattr(self.vehicle, self.entity_description.key_class),
                self.entity_description.key,
            )
        self._attr_native_value = state        
        super()._handle_coordinator_update()
