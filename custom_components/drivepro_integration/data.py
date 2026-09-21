"""Custom types for the DrivePro integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import DriveproIntegrationApiClient
    from .coordinator import DriveproDataUpdateCoordinator


type DriveproIntegrationConfigEntry = ConfigEntry[DriveproIntegrationData]


class ValueWithUnit(NamedTuple):
    """A value with a corresponding unit."""

    value: int | float | None
    unit: str | None


@dataclass
class DriveproIntegrationData:
    """Data for the DrivePro integration."""

    client: DriveproIntegrationApiClient
    coordinator: DriveproDataUpdateCoordinator
    integration: Integration


def _optional_int(value: float | None) -> int | None:
    """Convert a value to int, preserving None."""
    return int(value) if value is not None else None


class DriveproVehicle:
    """Models state of one vehicle."""

    FleetVehicleId: str
    Label: str
    Manufacturer: str | None
    Model: str | None
    RegistrationNumber: str | None
    Vin: str | None
    ValidFrom: str | None
    DriverId: str | None
    DriverName: str | None
    Mode: str | None
    CurrentOdo: float | None
    IgnOnSeconds: int | None
    Type: int | None
    ArmState: str | None
    Product: int | None
    TrackerId: str | None
    EntityGroupId: str | None
    EntityGroupName: str | None
    Co2EmissionsGramKm: int | None
    ModelYear: int | None
    ReArmOnIgnOff: bool | None
    AutoCarbonOffset: bool | None
    GenerateArmedMovementAlerts: bool | None
    CanChangeProductTier: bool | None
    MapPin: str | None
    LastSeenTimestamp: str | None
    LastSeenLocationName: str | None
    LastSeenSpeedKph: float | None
    LastSeenHeading: int | None

    # Location fields
    SupplyMilliVoltage: int | None
    SupplyVoltage: float | None
    BatteryMilliVoltage: int | None
    BatteryVoltage: float | None
    Latitude: float | None
    Longitude: float | None
    Heading: int | None
    SpeedKph: float | None
    AltitudeMeters: float | None
    DtcFaultCount: int | None
    LocationName: str | None
    Action: str | None
    TripOdoMeters: float | None
    VehicleIgnOnSeconds: int | None
    RoadClass: int | None
    CountryCode: str | None

    # VehicleEntitlements fields
    Range: int | None
    TrackingFreqency: int | None
    HasEmergencyContacts: bool | None
    HasRealtime: bool | None
    HasFuelLog: bool | None
    HasReports: bool | None
    HasGeofencing: bool | None
    HasAlertsNotifications: bool | None
    HasReminders: bool | None
    HasDocuments: bool | None
    HasCrashDetection: bool | None
    HasExpenses: bool | None
    MediaUploadSpaceGb: float | None
    HasMediaUpload: bool | None

    # HardwareOptions fields
    HasCamera: bool | None
    SupportsDigitalInIgnSense: bool | None
    SupportsSleepModes: bool | None

    def __init__(self, vehicle_data: dict | None = None) -> None:
        """Initialize the vehicle from raw DrivePro API data."""
        if vehicle_data is None:
            return
        self._parse_vehicle(vehicle_data)
        self._parse_location(vehicle_data.get("Location") or {})
        self._parse_entitlements(vehicle_data.get("VehicleEntitlements") or {})
        self._parse_hardware(vehicle_data.get("HardwareOptions") or {})

    def _parse_vehicle(self, d: dict) -> None:
        """Parse the top-level vehicle fields."""
        self.FleetVehicleId = d["FleetVehicleId"]
        self.Label = d["Label"]
        self.Manufacturer = d.get("Manufacturer") or None
        self.Model = d.get("Model") or None
        self.RegistrationNumber = d.get("RegistrationNumber") or None
        self.Vin = d.get("Vin") or None
        self.ValidFrom = d.get("ValidFrom")
        self.DriverId = d.get("DriverId")
        self.DriverName = d.get("DriverName") or None
        self.Mode = d.get("Mode")
        self.CurrentOdo = d.get("CurrentOdo")
        self.IgnOnSeconds = d.get("IgnOnSeconds")
        self.Type = d.get("Type")
        self.ArmState = d.get("ArmState")
        self.Product = d.get("Product")
        self.TrackerId = d.get("TrackerId")
        self.EntityGroupId = d.get("EntityGroupId")
        self.EntityGroupName = d.get("EntityGroupName") or None
        self.Co2EmissionsGramKm = d.get("Co2EmissionsGramKm")
        self.ModelYear = d.get("ModelYear")
        self.ReArmOnIgnOff = d.get("ReArmOnIgnOff")
        self.AutoCarbonOffset = d.get("AutoCarbonOffset")
        self.GenerateArmedMovementAlerts = d.get("GenerateArmedMovementAlerts")
        self.CanChangeProductTier = d.get("CanChangeProductTier")
        self.MapPin = d.get("MapPin")
        self.LastSeenTimestamp = d.get("LastSeenTimestamp")
        self.LastSeenLocationName = d.get("LastSeenLocationName")
        self.LastSeenSpeedKph = d.get("LastSeenSpeedKph")
        self.LastSeenHeading = d.get("LastSeenHeading")

    def _parse_location(self, location: dict) -> None:
        """Parse the Location sub-object."""
        supply_mv = location.get("SupplyMilliVoltage")
        self.SupplyMilliVoltage = _optional_int(supply_mv)
        self.SupplyVoltage = supply_mv / 1000 if supply_mv is not None else None
        battery_mv = location.get("BatteryMilliVoltage")
        self.BatteryMilliVoltage = _optional_int(battery_mv)
        self.BatteryVoltage = battery_mv / 1000 if battery_mv is not None else None
        self.Latitude = location.get("Latitude")
        self.Longitude = location.get("Longitude")
        self.Heading = location.get("Heading")
        self.SpeedKph = location.get("SpeedKph")
        self.AltitudeMeters = location.get("AltitudeMeters")
        self.DtcFaultCount = location.get("DtcFaultCount")
        self.LocationName = location.get("LocationName")
        self.Action = location.get("Action")
        self.TripOdoMeters = location.get("TripOdoMeters")
        self.VehicleIgnOnSeconds = location.get("VehicleIgnOnSeconds")
        self.RoadClass = location.get("RoadClass")
        self.CountryCode = location.get("CountryCode")

    def _parse_entitlements(self, entitlements: dict) -> None:
        """Parse the VehicleEntitlements sub-object."""
        self.Range = entitlements.get("Range")
        self.TrackingFreqency = entitlements.get("TrackingFreqency")
        self.HasEmergencyContacts = entitlements.get("HasEmergencyContacts")
        self.HasRealtime = entitlements.get("HasRealtime")
        self.HasFuelLog = entitlements.get("HasFuelLog")
        self.HasReports = entitlements.get("HasReports")
        self.HasGeofencing = entitlements.get("HasGeofencing")
        self.HasAlertsNotifications = entitlements.get("HasAlertsNotifications")
        self.HasReminders = entitlements.get("HasReminders")
        self.HasDocuments = entitlements.get("HasDocuments")
        self.HasCrashDetection = entitlements.get("HasCrashDetection")
        self.HasExpenses = entitlements.get("HasExpenses")
        self.MediaUploadSpaceGb = entitlements.get("MediaUploadSpaceGb")
        self.HasMediaUpload = entitlements.get("HasMediaUpload")

    def _parse_hardware(self, hardware: dict) -> None:
        """Parse the HardwareOptions sub-object."""
        self.HasCamera = hardware.get("HasCamera")
        self.SupportsDigitalInIgnSense = hardware.get("SupportsDigitalInIgnSense")
        self.SupportsSleepModes = hardware.get("SupportsSleepModes")
