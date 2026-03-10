"""Config flow for airquality_health."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_PM10_ENTITY,
    CONF_PM10_NORM,
    CONF_PM25_ENTITY,
    CONF_PM25_NORM,
    DEFAULT_PM10_NORM,
    DEFAULT_PM25_NORM,
    DOMAIN,
)
from .coordinator import parse_config


class AirQualityHealthConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for airquality_health."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> AirQualityHealthOptionsFlow:
        """Create the options flow."""
        return AirQualityHealthOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle user-initiated setup."""
        if user_input is not None:
            normalized = self._normalize_user_input(user_input)
            if self._already_configured(normalized):
                return self.async_abort(reason="already_configured")
            return self.async_create_entry(title="Air Quality Health", data=normalized)

        return self.async_show_form(step_id="user", data_schema=self._build_schema())

    async def async_step_import(self, user_input: dict[str, Any]) -> FlowResult:
        """Import configuration from YAML."""
        normalized = self._normalize_user_input(user_input)
        if self._already_configured(normalized):
            return self.async_abort(reason="already_configured")
        return self.async_create_entry(title="Air Quality Health", data=normalized)

    def _build_schema(self) -> vol.Schema:
        return vol.Schema(
            {
                vol.Required(CONF_PM10_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_PM25_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_PM10_NORM, default=DEFAULT_PM10_NORM): vol.Coerce(float),
                vol.Optional(CONF_PM25_NORM, default=DEFAULT_PM25_NORM): vol.Coerce(float),
            }
        )

    def _normalize_user_input(self, user_input: dict[str, Any]) -> dict[str, Any]:
        cfg = parse_config(user_input)
        return {
            CONF_PM10_ENTITY: cfg.pm10_entity,
            CONF_PM25_ENTITY: cfg.pm25_entity,
            CONF_PM10_NORM: cfg.pm10_norm,
            CONF_PM25_NORM: cfg.pm25_norm,
        }

    def _already_configured(self, candidate: dict[str, Any]) -> bool:
        pm10 = candidate[CONF_PM10_ENTITY]
        pm25 = candidate[CONF_PM25_ENTITY]
        return any(
            entry.data.get(CONF_PM10_ENTITY) == pm10 and entry.data.get(CONF_PM25_ENTITY) == pm25
            for entry in self._async_current_entries()
        )


class AirQualityHealthOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for airquality_health."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage options."""
        if user_input is not None:
            normalized = parse_config({**self._config_entry.data, **user_input})
            return self.async_create_entry(
                title="",
                data={
                    CONF_PM10_ENTITY: normalized.pm10_entity,
                    CONF_PM25_ENTITY: normalized.pm25_entity,
                    CONF_PM10_NORM: normalized.pm10_norm,
                    CONF_PM25_NORM: normalized.pm25_norm,
                },
            )

        current = {**self._config_entry.data, **self._config_entry.options}
        cfg = parse_config(current)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_PM10_ENTITY,
                        default=cfg.pm10_entity,
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Required(
                        CONF_PM25_ENTITY,
                        default=cfg.pm25_entity,
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Optional(CONF_PM10_NORM, default=cfg.pm10_norm): vol.Coerce(float),
                    vol.Optional(CONF_PM25_NORM, default=cfg.pm25_norm): vol.Coerce(float),
                }
            ),
        )
