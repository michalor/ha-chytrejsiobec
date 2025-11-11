"""The ChytrejsiObec integration."""
from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
import async_timeout
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

        try:
            async with async_timeout.timeout(10):
                async with self.session.get(
                    API_URL, params=params, headers=headers
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    if data.get("status") != "ok":
                        raise UpdateFailed(f"API returned error: {data.get('err_msg')}")
                    
                    return data.get("data", [])
                    
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}")