"""Custom types for integration_blueprint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import DriveproIntegrationApiClient
    from .coordinator import DriveproDataUpdateCoordinator


type DriveproIntegrationConfigEntry = ConfigEntry[DriveproIntegrationData]


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

    def __init__(self, d=None):
        if d is not None:
            for key, value in d.items():
                setattr(self, key, value)