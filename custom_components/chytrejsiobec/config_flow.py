"""Config flow for ChytrejsiObec integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("api_token"): str,
        vol.Optional("name", default="ChytrejsiObec"): str,
        vol.Optional(
            "device_classes", 
            default="RainfallMeter,MeteoStation"
        ): str,
    }
)


class ChytrejsiObecConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ChytrejsiObec."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate the API token
            try:
                await self._test_credentials(
                    user_input["api_token"],
                    user_input.get("device_classes", "RainfallMeter,MeteoStation")
                )
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception: %s", err)
                errors["base"] = "unknown"
            else:
                # Create entry
                await self.async_set_unique_id(user_input["api_token"])
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=user_input.get("name", "ChytrejsiObec"),
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "api_token_hint": "Example: townname.chytrejsiobec.cz",
                "device_classes_hint": "Comma-separated list of device types",
            },
        )

    async def _test_credentials(self, api_token: str, device_classes: str) -> bool:
        """Test if we can authenticate with the host."""
        session = async_get_clientsession(self.hass)
        
        url = "https://api.chytrejsiobec.cz/api/device/list"
        params = {
            "status": "OK,WARNING,ERROR",
            "deviceClass": device_classes,
        }
        headers = {
            "Authorization": api_token,
            "User-Agent": "Home-Assistant",
        }

        async with session.get(url, params=params, headers=headers) as response:
            response.raise_for_status()
            data = await response.json()
            
            if data.get("status") != "ok":
                raise Exception(f"API error: {data.get('err_msg')}")
            
            return True