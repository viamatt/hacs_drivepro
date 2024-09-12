"""Sample API Client."""

from __future__ import annotations

import socket
from typing import Any

import aiohttp
import async_timeout


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


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise DriveproIntegrationApiClientAuthenticationError(
            msg,
        )
    response.raise_for_status()


class DriveproIntegrationApiClient:
    """Sample API Client."""

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

    async def async_get_access_token(self) -> Any:
        """Get tokens from the API."""
        return await self._api_wrapper(
            method="post",
            url="https://www.drivepro.io/oAuth/Token",
            data={"grant_type": "client_credentials",
                  "client_id": self._username,
                  "client_secret": self._password
                  },
                  headers={"Content-type": "application/x-www-form-urlencoded"}
        )

    async def async_get_data(self) -> Any:
        """Get data from the API."""
        tokens = await self.async_get_access_token()

        return await self._api_wrapper(
            method="get",
            url="https://www.drivepro.io/FleetApi/GetVehicles",
            headers={"Authorization": "Bearer "+tokens.access_token},

        )

    async def async_set_title(self, value: str) -> Any:
        """Get data from the API."""
        return await self._api_wrapper(
            method="patch",
            url="https://jsonplaceholder.typicode.com/posts/1",
            data={"title": value},
            headers={"Content-type": "application/json; charset=UTF-8"},
        )

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                _verify_response_or_raise(response)
                return await response.json()

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
