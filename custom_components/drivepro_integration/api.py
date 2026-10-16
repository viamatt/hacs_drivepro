"""DrivePro Fleet API client."""

from __future__ import annotations

import asyncio
import socket
import time
from typing import Any
from urllib.parse import quote

import aiohttp
import async_timeout

from .const import LOGGER

API_BASE_URL = "https://www.drivepro.io"
VEHICLES_PAGE_SIZE = 100
# Stop paging after this many pages, in case the API ever ignores the page number
VEHICLES_MAX_PAGES = 50
# Renew the access token this long before it expires
TOKEN_EXPIRY_MARGIN_SECONDS = 300
# Used when the token response has no expires_in (DrivePro issues 24 hour tokens)
DEFAULT_TOKEN_LIFETIME_SECONDS = 3600


class DriveproIntegrationApiClientError(Exception):
    """Exception to indicate a general API error."""


class DriveproIntegrationApiClientCommunicationError(
    DriveproIntegrationApiClientError,
):
    """Exception to indicate a communication error."""


class DriveproIntegrationApiClientAuthenticationError(
    DriveproIntegrationApiClientError,
):
    """Exception to indicate an authentication error."""


class DriveproIntegrationApiClientAccountSuspendedError(
    DriveproIntegrationApiClientError,
):
    """Exception to indicate the DrivePro account is suspended or in debit."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise DriveproIntegrationApiClientAuthenticationError(
            msg,
        )
    response.raise_for_status()
    # DrivePro redirects every request from a suspended or in-debit account to its
    # reactivation web page, which then arrives here as HTML instead of JSON
    if "/activate/reactivate" in response.url.path.lower():
        msg = (
            "DrivePro has paused API access because the account is suspended or "
            "has an unpaid balance. Sign in at https://www.drivepro.io to "
            "reactivate it"
        )
        raise DriveproIntegrationApiClientAccountSuspendedError(msg)
    if response.content_type != "application/json":
        msg = (
            f"DrivePro returned a {response.content_type} page instead of data "
            f"(from {response.url.path})"
        )
        raise DriveproIntegrationApiClientCommunicationError(msg)


class DriveproIntegrationApiClient:
    """DrivePro Fleet API client."""

    def __init__(
        self,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Drivepro API Client."""
        self._username = username
        self._password = password
        self._session = session
        self._access_token: str | None = None
        self._access_token_expires = 0.0
        self._token_lock = asyncio.Lock()

    async def async_get_access_token(self) -> Any:
        """Get tokens from the API."""
        LOGGER.debug("Drivepro Fetch Tokens")
        data = aiohttp.FormData()
        data.add_field("grant_type", "client_credentials")
        data.add_field("client_id", self._username)
        data.add_field("client_secret", self._password)
        return await self._api_wrapper(
            method="post",
            url=f"{API_BASE_URL}/oAuth/Token",
            formdata=data,
            headers={"Content-type": "application/x-www-form-urlencoded"},
        )

    async def _async_access_token(self, *, force_refresh: bool = False) -> str:
        """Return the cached access token, fetching a new one near its expiry."""
        async with self._token_lock:
            if (
                force_refresh
                or self._access_token is None
                or time.monotonic() >= self._access_token_expires
            ):
                tokens = await self.async_get_access_token()
                lifetime = float(
                    tokens.get("expires_in") or DEFAULT_TOKEN_LIFETIME_SECONDS
                )
                self._access_token = tokens["access_token"]
                self._access_token_expires = time.monotonic() + max(
                    lifetime - TOKEN_EXPIRY_MARGIN_SECONDS,
                    0,
                )
                LOGGER.debug("DrivePro access token received, valid %ss", lifetime)
            return self._access_token

    async def _authorized_request(self, method: str, url: str) -> Any:
        """Call the API with the access token, renewing it once if rejected."""
        token = await self._async_access_token()
        try:
            return await self._api_wrapper(
                method=method,
                url=url,
                headers={"Authorization": "Bearer " + token},
            )
        except DriveproIntegrationApiClientAuthenticationError:
            LOGGER.debug("DrivePro access token rejected, fetching a new one")
            token = await self._async_access_token(force_refresh=True)
            return await self._api_wrapper(
                method=method,
                url=url,
                headers={"Authorization": "Bearer " + token},
            )

    async def async_get_data(self) -> Any:
        """Get every vehicle on the account, one page at a time."""
        LOGGER.debug("DrivePro fetching vehicle data")
        vehicles: list[dict] = []
        for page in range(VEHICLES_MAX_PAGES):
            page_data = await self._authorized_request(
                method="get",
                url=(
                    f"{API_BASE_URL}/FleetApi/GetVehicles"
                    f"?Page={page}&PageSize={VEHICLES_PAGE_SIZE}"
                ),
            )
            page_vehicles = page_data.get("Vehicles") or []
            vehicles.extend(page_vehicles)
            if len(page_vehicles) < VEHICLES_PAGE_SIZE:
                break
        else:
            LOGGER.warning(
                "DrivePro stopped fetching vehicles after %d pages",
                VEHICLES_MAX_PAGES,
            )
        LOGGER.debug("DrivePro vehicle data received: %d vehicle(s)", len(vehicles))
        return {"Count": len(vehicles), "Vehicles": vehicles}

    async def async_get_vehicle_details(self, vehicle_id: str) -> Any:
        """Get one vehicle's details, including its MOT, tax and reminders."""
        return await self._authorized_request(
            method="get",
            url=f"{API_BASE_URL}/FleetApi/GetVehicleDetails?VehicleId={vehicle_id}",
        )

    async def async_get_last_trip(self, vehicle_id: str) -> dict | None:
        """Get a vehicle's most recent completed trip, or None if it has none."""
        trips = await self._authorized_request(
            method="get",
            url=(
                f"{API_BASE_URL}/FleetApi/GetVehicleTrips"
                f"?VehicleId={vehicle_id}&Page=0&PageSize=1"
            ),
        )
        # A plain list of trips, or (like the paged range queries) {"Trips": [...]}
        if isinstance(trips, dict):
            trips = trips.get("Trips")
        return trips[0] if trips else None

    async def async_acknowledge_reminder(
        self,
        vehicle_id: str,
        reminder_id: str,
        note: str = "",
    ) -> None:
        """Mark a reminder as done, which schedules its next occurrence."""
        LOGGER.debug("Drivepro Acknowledge Reminder %s of %s", reminder_id, vehicle_id)
        result = await self._authorized_request(
            method="post",
            url=(
                f"{API_BASE_URL}/FleetApi/ReminderAck?VehicleId={vehicle_id}"
                f"&ReminderScheduleId={reminder_id}&Note={quote(note)}"
            ),
        )
        if (result or {}).get("Result") != "Ok":
            msg = f"Reminder {reminder_id} was not acknowledged: {result}"
            raise DriveproIntegrationApiClientError(msg)

    async def async_set_arm_state(self, vehicle_id: str, armed: bool) -> Any:  # noqa: FBT001
        """Arm or disarm a vehicle."""
        LOGGER.debug("Drivepro Set Arm State %s -> %s", vehicle_id, armed)
        return await self._authorized_request(
            method="post",
            url=(
                f"{API_BASE_URL}/FleetApi/SetArmState"
                f"?VehicleId={vehicle_id}&NewState={'true' if armed else 'false'}"
            ),
        )

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        jsondata: dict | None = None,
        formdata: aiohttp.FormData | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=jsondata,
                    data=formdata,
                )
                _verify_response_or_raise(response)
                return await response.json()

        except DriveproIntegrationApiClientError:
            # Already classified (e.g. invalid credentials) - don't re-wrap it below
            raise
        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise DriveproIntegrationApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise DriveproIntegrationApiClientCommunicationError(
                msg,
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise DriveproIntegrationApiClientError(
                msg,
            ) from exception
