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
    Manufacturer: str
    Model:str
    SupplyMilliVoltage: int
    SupplyVoltage: float
    Latitude:float
    Longitude:float
    Heading:int

    def __init__(self, d=None):
        if d is not None:
            self.FleetVehicleId=d["FleetVehicleId"]
            self.Label=d["Label"]
            self.Manufacturer=d["Manufacturer"]
            self.Model=d["Model"]
            self.SupplyMilliVoltage=int(d["Location"]["SupplyMilliVoltage"])
            self.SupplyVoltage=int(d["Location"]["SupplyMilliVoltage"])/1000
            #
            self.Latitude=float(d["Location"]["Latitude"])
            self.Longitude=float(d["Location"]["Longitude"])
            self.Heading=int(d["Location"]["Heading"])
