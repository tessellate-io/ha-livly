"""Config flow for Livly integration."""

from __future__ import annotations

import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import LivlyApiClient, LivlyAuthError
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_ID_TOKEN,
    CONF_PHONE_NUMBER,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN_EXPIRES_AT,
    CONF_USER_ID,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# Common country codes
COUNTRY_CODES = [
    {"value": "+1", "label": "+1 (US/Canada)"},
    {"value": "+44", "label": "+44 (UK)"},
    {"value": "+61", "label": "+61 (Australia)"},
    {"value": "+49", "label": "+49 (Germany)"},
    {"value": "+33", "label": "+33 (France)"},
    {"value": "+39", "label": "+39 (Italy)"},
    {"value": "+34", "label": "+34 (Spain)"},
    {"value": "+31", "label": "+31 (Netherlands)"},
    {"value": "+46", "label": "+46 (Sweden)"},
    {"value": "+47", "label": "+47 (Norway)"},
    {"value": "+45", "label": "+45 (Denmark)"},
    {"value": "+358", "label": "+358 (Finland)"},
    {"value": "+41", "label": "+41 (Switzerland)"},
    {"value": "+43", "label": "+43 (Austria)"},
    {"value": "+32", "label": "+32 (Belgium)"},
    {"value": "+48", "label": "+48 (Poland)"},
    {"value": "+351", "label": "+351 (Portugal)"},
    {"value": "+353", "label": "+353 (Ireland)"},
    {"value": "+81", "label": "+81 (Japan)"},
    {"value": "+82", "label": "+82 (South Korea)"},
    {"value": "+86", "label": "+86 (China)"},
    {"value": "+91", "label": "+91 (India)"},
    {"value": "+65", "label": "+65 (Singapore)"},
    {"value": "+64", "label": "+64 (New Zealand)"},
    {"value": "+55", "label": "+55 (Brazil)"},
    {"value": "+52", "label": "+52 (Mexico)"},
]

CONF_COUNTRY_CODE = "country_code"
CONF_PHONE_LOCAL = "phone_local"


class LivlyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Livly."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._client: LivlyApiClient | None = None
        self._phone_number: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step - phone number entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            country_code = user_input[CONF_COUNTRY_CODE]
            phone_local = user_input[CONF_PHONE_LOCAL]

            # Strip any non-digit characters from the local number
            phone_digits = re.sub(r"\D", "", phone_local)

            if not phone_digits:
                errors["base"] = "invalid_phone_format"
            else:
                # Combine country code and local number
                phone_number = f"{country_code}{phone_digits}"
                self._phone_number = phone_number

                # Create API client and request OTP
                session = async_get_clientsession(self.hass)
                self._client = LivlyApiClient(session)

                try:
                    await self._client.request_otp(phone_number)
                    return await self.async_step_otp()
                except LivlyAuthError as err:
                    _LOGGER.error("Failed to send OTP: %s", err)
                    errors["base"] = "otp_send_failed"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_COUNTRY_CODE, default="+1"): SelectSelector(
                        SelectSelectorConfig(
                            options=COUNTRY_CODES,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(CONF_PHONE_LOCAL): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.TEL)
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_otp(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle OTP verification step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            otp_code = user_input["otp_code"].strip()

            # Validate OTP format (must be exactly 6 digits)
            if not re.match(r"^\d{6}$", otp_code):
                errors["base"] = "invalid_otp_format"
            else:
                try:
                    await self._client.verify_otp(self._phone_number, otp_code)

                    # Get user info to obtain user ID
                    await self._client.get_user_info()

                    # Use last 4 digits for unique ID and title (privacy)
                    phone_last4 = self._phone_number[-4:]

                    # Create the config entry
                    await self.async_set_unique_id(f"livly_{phone_last4}")
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=f"Livly (***{phone_last4})",
                        data={
                            CONF_PHONE_NUMBER: self._phone_number,
                            CONF_ACCESS_TOKEN: self._client.access_token,
                            CONF_REFRESH_TOKEN: self._client.refresh_token,
                            CONF_ID_TOKEN: self._client.id_token,
                            CONF_TOKEN_EXPIRES_AT: self._client.token_expires_at,
                            CONF_USER_ID: self._client.user_id,
                        },
                    )
                except LivlyAuthError as err:
                    _LOGGER.error("OTP verification failed")
                    errors["base"] = "invalid_otp"

        # Mask phone number in UI (show only last 4 digits)
        masked_phone = f"***{self._phone_number[-4:]}"

        return self.async_show_form(
            step_id="otp",
            data_schema=vol.Schema(
                {
                    vol.Required("otp_code"): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "phone_number": masked_phone,
            },
        )
