"""Custom types for integration_blueprint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, NamedTuple, Optional, Tuple, Union
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import DriveproIntegrationApiClient
    from .coordinator import DriveproDataUpdateCoordinator


type DriveproIntegrationConfigEntry = ConfigEntry[DriveproIntegrationData]

class ValueWithUnit(NamedTuple):
    """A value with a corresponding unit."""

    value: Optional[Union[int, float]]
    unit: Optional[str]

@dataclass
class DriveproIntegrationData:
    """Data for the Blueprint integration."""

    client: DriveproIntegrationApiClient
    coordinator: DriveproDataUpdateCoordinator
    integration: Integration


class DriveproVehicle:
    """Models state of one vehicle."""
    FleetVehicleId: str
    Label: str
    Manufacturer: Optional[str]
    Model: Optional[str]
    RegistrationNumber: Optional[str]
    Vin: Optional[str]
    ValidFrom: Optional[str]
    DriverId: Optional[str]
    DriverName: Optional[str]
    Mode: Optional[str]
    CurrentOdo: Optional[float]
    IgnOnSeconds: Optional[int]
    Type: Optional[int]
    ArmState: Optional[str]
    Product: Optional[int]
    TrackerId: Optional[str]
    EntityGroupId: Optional[str]
    EntityGroupName: Optional[str]
    Co2EmissionsGramKm: Optional[int]
    ModelYear: Optional[int]
    ReArmOnIgnOff: Optional[bool]
    AutoCarbonOffset: Optional[bool]
    GenerateArmedMovementAlerts: Optional[bool]
    CanChangeProductTier: Optional[bool]
    MapPin: Optional[str]
    LastSeenTimestamp: Optional[str]
    LastSeenLocationName: Optional[str]
    LastSeenSpeedKph: Optional[float]
    LastSeenHeading: Optional[int]

    # Location fields
    SupplyMilliVoltage: Optional[int]
    SupplyVoltage: Optional[float]
    BatteryMilliVoltage: Optional[int]
    BatteryVoltage: Optional[float]
    Latitude: Optional[float]
    Longitude: Optional[float]
    Heading: Optional[int]
    SpeedKph: Optional[float]
    AltitudeMeters: Optional[float]
    DtcFaultCount: Optional[int]
    LocationName: Optional[str]
    Action: Optional[str]
    TripOdoMeters: Optional[float]
    VehicleIgnOnSeconds: Optional[int]
    RoadClass: Optional[int]
    CountryCode: Optional[str]

    # VehicleEntitlements fields
    Range: Optional[int]
    TrackingFreqency: Optional[int]
    HasEmergencyContacts: Optional[bool]
    HasRealtime: Optional[bool]
    HasFuelLog: Optional[bool]
    HasReports: Optional[bool]
    HasGeofencing: Optional[bool]
    HasAlertsNotifications: Optional[bool]
    HasReminders: Optional[bool]
    HasDocuments: Optional[bool]
    HasCrashDetection: Optional[bool]
    HasExpenses: Optional[bool]
    MediaUploadSpaceGb: Optional[float]
    HasMediaUpload: Optional[bool]

    # HardwareOptions fields
    HasCamera: Optional[bool]
    SupportsDigitalInIgnSense: Optional[bool]
    SupportsSleepModes: Optional[bool]

    def __init__(self, d=None):
        if d is not None:
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

            location = d.get("Location") or {}
            supply_mv = location.get("SupplyMilliVoltage")
            self.SupplyMilliVoltage = int(supply_mv) if supply_mv is not None else None
            self.SupplyVoltage = supply_mv / 1000 if supply_mv is not None else None
            battery_mv = location.get("BatteryMilliVoltage")
            self.BatteryMilliVoltage = int(battery_mv) if battery_mv is not None else None
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

            entitlements = d.get("VehicleEntitlements") or {}
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

            hardware = d.get("HardwareOptions") or {}
            self.HasCamera = hardware.get("HasCamera")
            self.SupportsDigitalInIgnSense = hardware.get("SupportsDigitalInIgnSense")
            self.SupportsSleepModes = hardware.get("SupportsSleepModes")
