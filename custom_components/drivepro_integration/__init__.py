"""
Custom integration to integrate DrivePro with Home Assistant.

For more details about this integration, please refer to
https://github.com/viamatt/hacs_drivepro
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import DriveproIntegrationApiClient
from .coordinator import DriveproDataUpdateCoordinator, DriveproDetailsCoordinator
from .data import DriveproIntegrationData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import DriveproIntegrationConfigEntry

PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.DEVICE_TRACKER,
]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: DriveproIntegrationConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    _async_remove_armed_binary_sensors(hass, entry)

    coordinator = DriveproDataUpdateCoordinator(
        hass=hass,
    )
    entry.runtime_data = DriveproIntegrationData(
        client=DriveproIntegrationApiClient(
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
            session=async_get_clientsession(hass),
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
        details_coordinator=DriveproDetailsCoordinator(
            hass=hass,
            vehicle_coordinator=coordinator,
        ),
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # Trips and reminders take a call per vehicle; fetch them without holding up setup
    entry.async_create_background_task(
        hass,
        entry.runtime_data.details_coordinator.async_refresh(),
        "drivepro_details_first_refresh",
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: DriveproIntegrationConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: DriveproIntegrationConfigEntry,
) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


def _async_remove_armed_binary_sensors(
    hass: HomeAssistant,
    entry: DriveproIntegrationConfigEntry,
) -> None:
    """
    Remove the old Armed binary sensors from the entity registry.

    They duplicated the Armed switch, so Assist couldn't tell the two apart.
    """
    registry = er.async_get(hass)
    for registry_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        if registry_entry.domain == Platform.BINARY_SENSOR:
            registry.async_remove(registry_entry.entity_id)
