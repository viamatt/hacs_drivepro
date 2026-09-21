"""Switch platform for the DrivePro integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import callback

from .const import LOGGER
from .data import DriveproVehicle
from .entity import DriveproIntegrationEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import DriveproDataUpdateCoordinator
    from .data import DriveproIntegrationConfigEntry


@dataclass
class DriveproSwitchEntityDescription(SwitchEntityDescription):
    """Describes a Drivepro switch entity."""


SWITCH_TYPES: tuple[DriveproSwitchEntityDescription, ...] = (
    DriveproSwitchEntityDescription(
        key="Armed",
        name="Armed",
        icon="mdi:shield-lock-outline",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: DriveproIntegrationConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    switches = []
    config_vehicle: DriveproVehicle
    for config_vehicle in entry.runtime_data.coordinator.data["Vehicles"]:
        vehicle = DriveproVehicle(config_vehicle)
        switches.extend(
            DriveproIntegrationSwitch(
                coordinator=entry.runtime_data.coordinator,
                vehicle=vehicle,
                description=description,
            )
            for description in SWITCH_TYPES
        )
    async_add_entities(switches, update_before_add=True)


class DriveproIntegrationSwitch(DriveproIntegrationEntity, SwitchEntity):
    """drivepro_integration switch class."""

    def __init__(
        self,
        coordinator: DriveproDataUpdateCoordinator,
        vehicle: DriveproVehicle,
        description: DriveproSwitchEntityDescription,
    ) -> None:
        """Initialize the switch class."""
        super().__init__(coordinator, vehicle)
        self.vehicle = vehicle
        self.entity_description = description
        self._attr_unique_id = f"{vehicle.FleetVehicleId}-{description.key}"
        self._attr_name = f"{vehicle.Label} {description.name}"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._refresh_vehicle()
        LOGGER.debug(
            "DrivePro updated switch '%s' of %s to %s",
            self.entity_description.key,
            self.vehicle.Label,
            self.vehicle.ArmState == "STATEARMED",
        )
        self._attr_is_on = self.vehicle.ArmState == "STATEARMED"
        super()._handle_coordinator_update()

    async def async_turn_on(self, **_: Any) -> None:
        """Arm the vehicle."""
        await self._async_set_arm_state(armed=True)

    async def async_turn_off(self, **_: Any) -> None:
        """Disarm the vehicle."""
        await self._async_set_arm_state(armed=False)

    async def _async_set_arm_state(self, *, armed: bool) -> None:
        """Call the API to set the arm state and refresh the coordinator."""
        client = self.coordinator.config_entry.runtime_data.client
        await client.async_set_arm_state(self.vehicle.FleetVehicleId, armed)
        await self.coordinator.async_request_refresh()
