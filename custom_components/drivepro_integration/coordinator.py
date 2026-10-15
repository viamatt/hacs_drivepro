"""DataUpdateCoordinator for the DrivePro integration."""

from __future__ import annotations

import asyncio
import time
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    DriveproIntegrationApiClientAuthenticationError,
    DriveproIntegrationApiClientError,
)
from .const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import DriveproIntegrationConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class DriveproDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: DriveproIntegrationConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            data = await self.config_entry.runtime_data.client.async_get_data()
            vehicles = data.get("Vehicles", [])
            LOGGER.debug(
                "DrivePro coordinator refresh succeeded: %d vehicle(s) (%s)",
                len(vehicles),
                ", ".join(str(vehicle.get("FleetVehicleId")) for vehicle in vehicles),
            )
        except DriveproIntegrationApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except DriveproIntegrationApiClientError as exception:
            raise UpdateFailed(exception) from exception
        else:
            return data


# Trips and details are fetched one vehicle at a time; the API allows 60 calls a
# minute to each of these endpoints, so space them out
DETAILS_UPDATE_INTERVAL = timedelta(minutes=10)
DETAILS_REFRESH_SECONDS = 3600
SECONDS_BETWEEN_VEHICLE_CALLS = 1.1


class DriveproDetailsCoordinator(DataUpdateCoordinator):
    """
    Fetch each vehicle's last trip, and hourly its MOT, tax and reminders.

    data is {"trips": {vehicle id: trip or None}, "details": {vehicle id: details}}
    """

    config_entry: DriveproIntegrationConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        vehicle_coordinator: DriveproDataUpdateCoordinator,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=f"{DOMAIN}_details",
            update_interval=DETAILS_UPDATE_INTERVAL,
        )
        self.vehicle_coordinator = vehicle_coordinator
        self._details_fetched = 0.0

    def refresh_details_next_update(self) -> None:
        """Fetch the details again on the next update, e.g. after a change."""
        self._details_fetched = 0.0

    async def _async_update_data(self) -> Any:
        """Fetch the last trip, and when due the details, of every vehicle."""
        client = self.config_entry.runtime_data.client
        previous = self.data or {"trips": {}, "details": {}}
        trips = dict(previous["trips"])
        details = dict(previous["details"])
        fetch_details = time.monotonic() - self._details_fetched >= (
            DETAILS_REFRESH_SECONDS
        )
        vehicle_ids = [
            vehicle["FleetVehicleId"]
            for vehicle in (self.vehicle_coordinator.data or {}).get("Vehicles", [])
        ]
        failures = 0
        first_call = True
        for vehicle_id in vehicle_ids:
            calls = [("trips", client.async_get_last_trip)]
            if fetch_details:
                calls.append(("details", client.async_get_vehicle_details))
            for key, fetch in calls:
                if not first_call:
                    await asyncio.sleep(SECONDS_BETWEEN_VEHICLE_CALLS)
                first_call = False
                try:
                    result = await fetch(vehicle_id)
                except DriveproIntegrationApiClientAuthenticationError as exception:
                    raise ConfigEntryAuthFailed(exception) from exception
                except DriveproIntegrationApiClientError as exception:
                    # Keep the vehicle's last known values and carry on with the rest
                    failures += 1
                    LOGGER.debug(
                        "DrivePro %s fetch failed for %s: %s",
                        key,
                        vehicle_id,
                        exception,
                    )
                    continue
                (trips if key == "trips" else details)[vehicle_id] = result
        if vehicle_ids and failures == len(vehicle_ids) * (2 if fetch_details else 1):
            msg = "Every DrivePro trip and details request failed"
            raise UpdateFailed(msg)
        if fetch_details:
            self._details_fetched = time.monotonic()
        LOGGER.debug(
            "DrivePro details refresh: %d vehicle(s), details %s, %d failure(s)",
            len(vehicle_ids),
            "fetched" if fetch_details else "kept",
            failures,
        )
        return {"trips": trips, "details": details}
