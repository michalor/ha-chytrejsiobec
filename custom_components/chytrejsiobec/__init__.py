"""The ChytrejsiObec integration."""
from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
import async_timeout
import asyncio
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "chytrejsiobec"
PLATFORMS = [Platform.SENSOR]

API_URL = "https://api.chytrejsiobec.cz/api/device/list"
DEFAULT_SCAN_INTERVAL = timedelta(minutes=5)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ChytrejsiObec from a config entry."""
    coordinator = ChytrejsiObecDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class ChytrejsiObecDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching ChytrejsiObec data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.api_token = entry.data["api_token"]
        self.device_classes = entry.data.get("device_classes", "RainfallMeter,MeteoStation")
        self.session = async_get_clientsession(hass)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        params = {
            "status": "OK,WARNING,ERROR,GPSNOFIX,ERROR_DATA,WARNING_DATA,BATTERY_LOW,WATER_LOW,1_FLOOD_STAGE,2_FLOOD_STAGE,3_FLOOD_STAGE,3+_FLOOD_STAGE,DROUGHT",
            "deviceClass": self.device_classes,
        }
        
        headers = {
            "Authorization": self.api_token,
            "User-Agent": "Home-Assistant",
        }
        _LOGGER.debug("Fetching devices from %s with params: %s", API_URL, params)
        _LOGGER.debug("Authorization header present: %s", bool(headers.get("Authorization")))

        try:
            async with async_timeout.timeout(10):
                async with self.session.get(API_URL, params=params, headers=headers) as response:
                    _LOGGER.debug("HTTP response status: %s", response.status)

                    # If HTTP error, try to get text for diagnostics
                    if response.status >= 400:
                        try:
                            text = await response.text()
                        except Exception:
                            text = "<could not read response text>"
                        _LOGGER.error(
                            "API HTTP error %s when fetching devices: %s",
                            response.status,
                            text[:1000],
                        )
                        raise UpdateFailed(f"HTTP error {response.status}")

                    # Parse JSON body
                    try:
                        data = await response.json()
                    except Exception as err:
                        # If JSON parsing fails, capture text for debugging
                        text = await response.text()
                        _LOGGER.error("Failed to parse JSON response: %s", text[:1000])
                        raise UpdateFailed(f"Invalid JSON response: {err}")

                    _LOGGER.debug(
                        "API JSON status: %s; keys: %s",
                        data.get("status"),
                        list(data.keys()) if isinstance(data, dict) else type(data),
                    )

                    if data.get("status") != "ok":
                        _LOGGER.error("API returned error message: %s", data.get("err_msg"))
                        raise UpdateFailed(f"API returned error: {data.get('err_msg')}")

                    payload = data.get("data", [])
                    if not payload:
                        _LOGGER.warning(
                            "API returned empty device list (device_classes=%s). This may indicate an issue.",
                            self.device_classes,
                        )

                    return payload

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout when fetching ChytrejsiObec data from %s", API_URL)
            raise UpdateFailed("Timeout fetching data from API")
        except aiohttp.ClientResponseError as err:
            _LOGGER.error("Client response error: %s", err, exc_info=True)
            raise UpdateFailed(f"Client response error: {err}")
        except aiohttp.ClientError as err:
            _LOGGER.error("Error communicating with API: %s", err, exc_info=True)
            raise UpdateFailed(f"Error communicating with API: {err}")
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected error while fetching ChytrejsiObec data: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}")