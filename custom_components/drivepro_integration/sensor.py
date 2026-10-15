"""Sensor platform for the DrivePro integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

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
from .entity import DriveproDetailsEntity, DriveproIntegrationEntity
from .reminders import (
    compliance_reminder,
    find_reminder,
    own_reminders,
    parse_api_date,
    parse_api_datetime,
    reminder_labels,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import DriveproDataUpdateCoordinator, DriveproDetailsCoordinator
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
    vehicles = [
        DriveproVehicle(config_vehicle)
        for config_vehicle in entry.runtime_data.coordinator.data["Vehicles"]
    ]
    async_add_entities(sensors, update_before_add=True)

    # These fill in when the details coordinator's first refresh completes; updating
    # them before adding would hold up setup while every vehicle is fetched
    details_coordinator = entry.runtime_data.details_coordinator
    details_sensors: list[SensorEntity] = []
    for vehicle in vehicles:
        details_sensors.extend(
            DriveproDetailsSensor(details_coordinator, vehicle, description)
            for description in LAST_TRIP_SENSOR_TYPES
        )
        # MOT and tax come from the DVLA, which needs a UK registration
        if vehicle.RegistrationNumber:
            details_sensors.extend(
                DriveproDetailsSensor(details_coordinator, vehicle, description)
                for description in COMPLIANCE_SENSOR_TYPES
            )
    async_add_entities(details_sensors)

    # Reminders are only known once the details arrive, and can be added at any time
    known_reminders: set[str] = set()

    @callback
    def _async_add_reminder_sensors() -> None:
        new_sensors = []
        for vehicle in vehicles:
            details = (
                (details_coordinator.data or {})
                .get("details", {})
                .get(vehicle.FleetVehicleId)
            )
            reminders = own_reminders(
                details, has_compliance=bool(vehicle.RegistrationNumber)
            )
            labels = reminder_labels(reminders)
            for reminder in reminders:
                if reminder["ReminderId"] in known_reminders:
                    continue
                known_reminders.add(reminder["ReminderId"])
                new_sensors.append(
                    DriveproReminderSensor(
                        details_coordinator,
                        vehicle,
                        reminder,
                        labels[reminder["ReminderId"]],
                    )
                )
        if new_sensors:
            async_add_entities(new_sensors)

    _async_add_reminder_sensors()
    entry.async_on_unload(
        details_coordinator.async_add_listener(_async_add_reminder_sensors)
    )


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


@dataclass(frozen=True, kw_only=True)
class DriveproDetailsSensorEntityDescription(SensorEntityDescription):
    """Describes a sensor for a vehicle's last trip or MOT and tax."""

    source: str  # "trip" or "details"
    value_fn: Callable[[dict[str, Any]], Any]
    attributes_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


def _last_trip_attributes(trip: dict[str, Any]) -> dict[str, Any]:
    """Return the extra details of a trip."""
    return {
        "trip_id": trip.get("FleetTripId"),
        "start_time": parse_api_datetime(trip.get("StartTime")),
        "start_address": trip.get("StartPositionAddress"),
        "end_address": trip.get("EndPositionAddress"),
        "driver_name": trip.get("DriverName") or None,
        "max_speed_kph": trip.get("MaxSpeedKph"),
        "average_speed_kph": trip.get("AverageSpeed"),
        "co2_grams": trip.get("Co2EmissionsGrams"),
        "private": trip.get("Private"),
        "note": trip.get("TripRefOrNote"),
    }


def _compliance(details: dict[str, Any]) -> dict[str, Any]:
    return details.get("Compliance") or {}


def _reminder_status(details: dict[str, Any], key: str) -> str | None:
    reminder = compliance_reminder(details, key)
    return reminder.get("Status") if reminder else None


LAST_TRIP_SENSOR_TYPES: tuple[DriveproDetailsSensorEntityDescription, ...] = (
    DriveproDetailsSensorEntityDescription(
        key="LastTripEnd",
        name="Last Trip Ended",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:flag-checkered",
        source="trip",
        value_fn=lambda trip: parse_api_datetime(trip.get("EndTime")),
        attributes_fn=_last_trip_attributes,
    ),
    DriveproDetailsSensorEntityDescription(
        key="LastTripDistance",
        name="Last Trip Distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        suggested_display_precision=1,
        icon="mdi:map-marker-distance",
        source="trip",
        value_fn=lambda trip: trip.get("DistanceKilometers"),
    ),
    DriveproDetailsSensorEntityDescription(
        key="LastTripDuration",
        name="Last Trip Duration",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        suggested_display_precision=0,
        icon="mdi:timer-outline",
        source="trip",
        value_fn=lambda trip: trip.get("DurationMinutes"),
    ),
    DriveproDetailsSensorEntityDescription(
        key="LastTripScore",
        name="Last Trip Score",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:star-circle-outline",
        source="trip",
        value_fn=lambda trip: trip.get("CombinedScore"),
    ),
)

COMPLIANCE_SENSOR_TYPES: tuple[DriveproDetailsSensorEntityDescription, ...] = (
    DriveproDetailsSensorEntityDescription(
        key="MotDueDate",
        name="MOT Due",
        device_class=SensorDeviceClass.DATE,
        icon="mdi:clipboard-check-outline",
        source="details",
        value_fn=lambda details: parse_api_date(_compliance(details).get("MotDueDate")),
        attributes_fn=lambda details: {
            "mot_status": _compliance(details).get("MotStatus"),
            "first_mot": _compliance(details).get("FirstMot"),
            "last_mot_date": parse_api_date(_compliance(details).get("LastMotDate")),
            "last_mot_result": _compliance(details).get("LastMotResult"),
            "last_mot_odometer": _compliance(details).get("LastMotOdometer"),
            "reminder_status": _reminder_status(details, "MotDueDate"),
        },
    ),
    DriveproDetailsSensorEntityDescription(
        key="TaxDueDate",
        name="Tax Due",
        device_class=SensorDeviceClass.DATE,
        icon="mdi:cash-check",
        source="details",
        value_fn=lambda details: parse_api_date(_compliance(details).get("TaxDueDate")),
        attributes_fn=lambda details: {
            "tax_status": _compliance(details).get("TaxStatus"),
            "reminder_status": _reminder_status(details, "TaxDueDate"),
        },
    ),
)


class DriveproDetailsSensor(DriveproDetailsEntity, SensorEntity):
    """A vehicle's last trip, MOT or tax sensor."""

    entity_description: DriveproDetailsSensorEntityDescription

    def __init__(
        self,
        coordinator: DriveproDetailsCoordinator,
        vehicle: DriveproVehicle,
        description: DriveproDetailsSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vehicle)
        self.entity_description = description
        self._attr_unique_id = f"{vehicle.FleetVehicleId}-{description.key}"
        self._attr_name = f"{vehicle.Label} {description.name}"

    @property
    def _source(self) -> dict[str, Any] | None:
        if self.entity_description.source == "trip":
            return self.last_trip
        return self.details

    @property
    def native_value(self) -> Any:
        """Return the value from the latest trip or details."""
        source = self._source
        return self.entity_description.value_fn(source) if source else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the extra details."""
        source = self._source
        if not source or self.entity_description.attributes_fn is None:
            return None
        return self.entity_description.attributes_fn(source)


class DriveproReminderSensor(DriveproDetailsEntity, SensorEntity):
    """
    When one of a vehicle's reminders is next due.

    Its state is the due date or, for a reminder set by distance only, the
    odometer reading it is due at.
    """

    _attr_icon = "mdi:calendar-alert"

    def __init__(
        self,
        coordinator: DriveproDetailsCoordinator,
        vehicle: DriveproVehicle,
        reminder: dict[str, Any],
        label: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, vehicle)
        self.reminder_id = reminder["ReminderId"]
        self._attr_unique_id = f"{vehicle.FleetVehicleId}-reminder-{self.reminder_id}"
        self._attr_name = f"{vehicle.Label} {label} Due"
        self._by_distance = not reminder.get("DueDate") and bool(
            reminder.get("DueOdometerKm")
        )
        if self._by_distance:
            self._attr_device_class = SensorDeviceClass.DISTANCE
            self._attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
            self._attr_icon = "mdi:counter"
        else:
            self._attr_device_class = SensorDeviceClass.DATE

    @property
    def _reminder(self) -> dict[str, Any] | None:
        return find_reminder(self.details, self.reminder_id)

    @property
    def available(self) -> bool:
        """Return False once the reminder has been deleted."""
        return super().available and self._reminder is not None

    @property
    def native_value(self) -> Any:
        """Return when the reminder is due."""
        reminder = self._reminder
        if reminder is None:
            return None
        if self._by_distance:
            return reminder.get("DueOdometerKm")
        return parse_api_date(reminder.get("DueDate"))

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the reminder's status and both due values."""
        reminder = self._reminder
        if reminder is None:
            return None
        return {
            "status": reminder.get("Status"),
            "due_date": parse_api_date(reminder.get("DueDate")),
            "due_odometer_km": reminder.get("DueOdometerKm"),
            "reminder_id": self.reminder_id,
        }
