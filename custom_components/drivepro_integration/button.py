"""Button platform for the DrivePro integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.button import ButtonEntity
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError

from .api import DriveproIntegrationApiClientError
from .data import DriveproVehicle
from .entity import DriveproDetailsEntity
from .reminders import find_reminder, own_reminders, reminder_labels

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import DriveproDetailsCoordinator
    from .data import DriveproIntegrationConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: DriveproIntegrationConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a button to mark each reminder done, as reminders become known."""
    vehicles = [
        DriveproVehicle(config_vehicle)
        for config_vehicle in entry.runtime_data.coordinator.data["Vehicles"]
    ]
    details_coordinator = entry.runtime_data.details_coordinator
    known_reminders: set[str] = set()

    @callback
    def _async_add_reminder_buttons() -> None:
        new_buttons = []
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
                new_buttons.append(
                    DriveproReminderDoneButton(
                        details_coordinator,
                        vehicle,
                        reminder,
                        labels[reminder["ReminderId"]],
                    )
                )
        if new_buttons:
            async_add_entities(new_buttons)

    _async_add_reminder_buttons()
    entry.async_on_unload(
        details_coordinator.async_add_listener(_async_add_reminder_buttons)
    )


class DriveproReminderDoneButton(DriveproDetailsEntity, ButtonEntity):
    """Marks a reminder done, so DrivePro schedules the next one."""

    _attr_icon = "mdi:calendar-check"

    def __init__(
        self,
        coordinator: DriveproDetailsCoordinator,
        vehicle: DriveproVehicle,
        reminder: dict[str, Any],
        label: str,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, vehicle)
        self.reminder_id = reminder["ReminderId"]
        self._attr_unique_id = (
            f"{vehicle.FleetVehicleId}-reminder-{self.reminder_id}-done"
        )
        self._attr_name = f"{vehicle.Label} {label} Done"

    @property
    def available(self) -> bool:
        """Return False once the reminder has been deleted."""
        return (
            super().available
            and find_reminder(self.details, self.reminder_id) is not None
        )

    async def async_press(self) -> None:
        """Acknowledge the reminder and fetch its new due date."""
        client = self.coordinator.config_entry.runtime_data.client
        try:
            await client.async_acknowledge_reminder(
                self.vehicle.FleetVehicleId, self.reminder_id
            )
        except DriveproIntegrationApiClientError as exception:
            msg = f"Couldn't mark {self.name} in DrivePro: {exception}"
            raise HomeAssistantError(msg) from exception
        self.coordinator.refresh_details_next_update()
        await self.coordinator.async_request_refresh()
