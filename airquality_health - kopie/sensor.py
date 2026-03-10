"""Sensors for airquality_health."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.const import CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AirQualityHealthCoordinator


@dataclass(frozen=True, kw_only=True)
class HealthSensorDescription(SensorEntityDescription):
    value_fn: Callable[[AirQualityHealthCoordinator], float | int | None]


SENSORS: tuple[HealthSensorDescription, ...] = (
    HealthSensorDescription(
        key="pm10_daily_avg",
        name="PM10 Daggemiddelde",
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.current_pm10_average,
    ),
    HealthSensorDescription(
        key="pm25_daily_avg",
        name="PM2.5 Daggemiddelde",
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.current_pm25_average,
    ),
    HealthSensorDescription(
        key="pm10_exceedance_count",
        name="PM10 Norm Overschrijdingen",
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: c.pm10_exceedances,
    ),
    HealthSensorDescription(
        key="pm25_exceedance_count",
        name="PM2.5 Norm Overschrijdingen",
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: c.pm25_exceedances,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator: AirQualityHealthCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        AirQualityHealthSensor(coordinator, description, entry.entry_id) for description in SENSORS
    ]
    async_add_entities(entities)


class AirQualityHealthSensor(CoordinatorEntity[AirQualityHealthCoordinator], SensorEntity):
    """Single sensor entity."""

    entity_description: HealthSensorDescription

    def __init__(
        self,
        coordinator: AirQualityHealthCoordinator,
        description: HealthSensorDescription,
        entry_id: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{description.key}"
        self._attr_has_entity_name = True
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Air Quality Health",
            manufacturer="Custom",
            model="PM Health Norm Tracker",
        )

    @property
    def native_value(self) -> float | int | None:
        return self.entity_description.value_fn(self.coordinator)

    @property
    def extra_state_attributes(self) -> dict[str, str | float]:
        return {
            "tracked_date": self.coordinator.tracked_date,
            "pm10_norm": self.coordinator.pm10_norm,
            "pm25_norm": self.coordinator.pm25_norm,
        }
