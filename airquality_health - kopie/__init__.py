"""Air quality health norms integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_PM10_ENTITY,
    CONF_PM10_NORM,
    CONF_PM25_ENTITY,
    CONF_PM25_NORM,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import AirQualityHealthCoordinator, parse_config

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_PM10_ENTITY): cv.entity_id,
                vol.Required(CONF_PM25_ENTITY): cv.entity_id,
                vol.Optional(CONF_PM10_NORM): vol.Coerce(float),
                vol.Optional(CONF_PM25_NORM): vol.Coerce(float),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up integration and import YAML config if present."""
    hass.data.setdefault(DOMAIN, {})
    if DOMAIN not in config:
        return True

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=config[DOMAIN],
        )
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Set up from config entry."""
    cfg = parse_config(entry.data)
    coordinator = AirQualityHealthCoordinator(hass, cfg, instance_id=entry.entry_id)
    await coordinator.async_initialize()

    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Unload config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    coordinator: AirQualityHealthCoordinator | None = hass.data[DOMAIN].pop(entry.entry_id, None)
    if coordinator is not None:
        await coordinator.async_shutdown()

    return True
