"""Sensor platform for integration_blueprint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfSpeed,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory

from .const import LOGGER
from .data import DriveproVehicle
from .entity import DriveproIntegrationEntity

if TYPE_CHECKING:
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import DriveproDataUpdateCoordinator
    from .data import DriveproIntegrationConfigEntry


@dataclass
class DriveproSensorEntityDescription(SensorEntityDescription):
    """Describes a Drivepro sensor entity."""


SENSOR_TYPES: tuple[DriveproSensorEntityDescription, ...] = (
    DriveproSensorEntityDescription(
        key="SupplyVoltage",
        name="Supply Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DriveproSensorEntityDescription(
        key="BatteryVoltage",
        name="Battery Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DriveproSensorEntityDescription(
        key="CurrentOdo",
        name="Odometer",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:counter",
    ),
    DriveproSensorEntityDescription(
        key="TripOdoMeters",
        name="Trip Odometer",
        native_unit_of_measurement=UnitOfLength.METERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:map-marker-distance",
    ),
    DriveproSensorEntityDescription(
        key="LastSeenSpeedKph",
        name="Speed",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:speedometer",
    ),
    DriveproSensorEntityDescription(
        key="LastSeenHeading",
        name="Heading",
        native_unit_of_measurement="°",
        icon="mdi:compass",
    ),
    DriveproSensorEntityDescription(
        key="IgnOnSeconds",
        name="Ignition On Time",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:timer-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DriveproSensorEntityDescription(
        key="DtcFaultCount",
        name="Fault Count",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:alert-circle-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DriveproSensorEntityDescription(
        key="Co2EmissionsGramKm",
        name="CO2 Emissions",
        native_unit_of_measurement="g/km",
        icon="mdi:molecule-co2",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DriveproSensorEntityDescription(
        key="ModelYear",
        name="Model Year",
        icon="mdi:calendar",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DriveproSensorEntityDescription(
        key="ArmState",
        name="Arm State",
        icon="mdi:shield-lock-outline",
    ),
    DriveproSensorEntityDescription(
        key="Mode",
        name="Mode",
        icon="mdi:car-info",
    ),
    DriveproSensorEntityDescription(
        key="RegistrationNumber",
        name="Registration Number",
        icon="mdi:card-text-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DriveproSensorEntityDescription(
        key="Vin",
        name="VIN",
        icon="mdi:identifier",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DriveproSensorEntityDescription(
        key="DriverName",
        name="Driver",
        icon="mdi:account",
    ),
    DriveproSensorEntityDescription(
        key="LastSeenLocationName",
        name="Location",
        icon="mdi:map-marker",
    ),
    DriveproSensorEntityDescription(
        key="EntityGroupName",
        name="Group",
        icon="mdi:folder-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    DriveproSensorEntityDescription(
        key="CountryCode",
        name="Country",
        icon="mdi:flag-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: DriveproIntegrationConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    sensors = []
    config_vehicle: DriveproVehicle
    for config_vehicle in entry.runtime_data.coordinator.data["Vehicles"]:
        vehicle = DriveproVehicle(config_vehicle)
        for description in SENSOR_TYPES:
            if getattr(vehicle, description.key, None) is None:
                continue
            sensors.append(
                DriveproIntegrationSensor(
                    coordinator=entry.runtime_data.coordinator,
                    vehicle=vehicle,
                    description=description,
                )
            )
    async_add_entities(sensors, update_before_add=True)


class DriveproIntegrationSensor(DriveproIntegrationEntity, SensorEntity):
    """drivepro_integration Sensor class."""

    def __init__(
        self,
        coordinator: DriveproDataUpdateCoordinator,
        vehicle: DriveproVehicle,
        description: DriveproSensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator, vehicle)
        self.vehicle = vehicle
        self.entity_description = description
        self._attr_unique_id = f"{vehicle.FleetVehicleId}-{description.key}"
        self._attr_name = f"{vehicle.Label} {description.name}"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._refresh_vehicle()
        value = getattr(self.vehicle, self.entity_description.key)
        LOGGER.debug(
            "DrivePro updated sensor '%s' of %s to %s",
            self.entity_description.key,
            self.vehicle.Label,
            value,
        )
        self._attr_native_value = value
        super()._handle_coordinator_update()
