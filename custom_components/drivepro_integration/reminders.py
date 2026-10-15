"""Helpers for DrivePro dates, MOT, tax and reminders."""

from __future__ import annotations

import re
from datetime import UTC, date, datetime
from typing import Any

# DrivePro already reports these from the DVLA as MOT Due and Tax Due sensors, so
# reminders with these names fold into those sensors instead of duplicating them
COMPLIANCE_REMINDER_KEYS = {"mot": "MotDueDate", "tax": "TaxDueDate"}

_FRACTION = re.compile(r"(\.\d{6})\d+")


def parse_api_datetime(value: str | None) -> datetime | None:
    """
    Parse a DrivePro date and time, which is UTC with or without a trailing Z.

    .NET writes up to 7 fractional digits; Python takes at most 6.
    """
    if not value or value.startswith("0001-"):
        return None
    try:
        parsed = datetime.fromisoformat(_FRACTION.sub(r"\1", value.replace("Z", "")))
    except ValueError:
        return None
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed


def parse_api_date(value: str | None) -> date | None:
    """Parse a DrivePro date (sent as midnight UTC)."""
    parsed = parse_api_datetime(value)
    return parsed.date() if parsed else None


def _reminder_key(reminder: dict[str, Any]) -> str:
    """Return a reminder's type, lower case and without a trailing 'due'."""
    key = (reminder.get("Type") or "").strip().lower()
    key = key.removesuffix(" due").strip()
    return "tax" if key == "road tax" else key


def reminder_label(reminder: dict[str, Any]) -> str:
    """Return a reminder's name without a trailing 'Due', e.g. 'Service'."""
    label = (reminder.get("Type") or "Reminder").strip()
    if label.lower().endswith(" due"):
        label = label[: -len(" due")].rstrip()
    return label or "Reminder"


def compliance_reminder(
    details: dict[str, Any] | None,
    compliance_key: str,
) -> dict[str, Any] | None:
    """Return the reminder that matches an MOT or tax due date, if there is one."""
    for reminder in ((details or {}).get("Compliance") or {}).get("Reminders") or []:
        if COMPLIANCE_REMINDER_KEYS.get(_reminder_key(reminder)) == compliance_key:
            return reminder
    return None


def own_reminders(
    details: dict[str, Any] | None,
    *,
    has_compliance: bool,
) -> list[dict[str, Any]]:
    """
    Return the reminders that get their own entities.

    When the vehicle has MOT and tax sensors, reminders named MOT or Tax are
    left out, so two entities never share a name.
    """
    reminders = ((details or {}).get("Compliance") or {}).get("Reminders") or []
    return [
        reminder
        for reminder in reminders
        if reminder.get("ReminderId")
        and not (has_compliance and _reminder_key(reminder) in COMPLIANCE_REMINDER_KEYS)
    ]


def reminder_labels(reminders: list[dict[str, Any]]) -> dict[str, str]:
    """
    Return each reminder's name, keyed by reminder id.

    Reminders of the same type are numbered (Service, Service 2) so their
    entities' names stay unique.
    """
    labels: dict[str, str] = {}
    used: dict[str, int] = {}
    for reminder in sorted(reminders, key=lambda r: r["ReminderId"]):
        label = reminder_label(reminder)
        count = used.get(label.lower(), 0) + 1
        used[label.lower()] = count
        labels[reminder["ReminderId"]] = label if count == 1 else f"{label} {count}"
    return labels


def find_reminder(
    details: dict[str, Any] | None,
    reminder_id: str,
) -> dict[str, Any] | None:
    """Return a reminder by id, if the vehicle still has it."""
    for reminder in ((details or {}).get("Compliance") or {}).get("Reminders") or []:
        if reminder.get("ReminderId") == reminder_id:
            return reminder
    return None
