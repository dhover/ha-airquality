"""Coordinator for airquality_health."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_PM10_ENTITY,
    CONF_PM10_NORM,
    CONF_PM25_ENTITY,
    CONF_PM25_NORM,
    DEFAULT_PM10_NORM,
    DEFAULT_PM25_NORM,
    DOMAIN,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class IntegrationConfig:
    """Runtime config."""

    pm10_entity: str
    pm25_entity: str
    pm10_norm: float
    pm25_norm: float


class AirQualityHealthCoordinator(DataUpdateCoordinator[None]):
    """Keep daily stats and exceedance counters."""

    def __init__(self, hass: HomeAssistant, cfg: IntegrationConfig, instance_id: str) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN)
        self.cfg = cfg
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}_{instance_id}_store"
        )
        self._unsubscribers: list[Any] = []
        self._data: dict[str, Any] = {
            "date": dt_util.now().date().isoformat(),
            "pm10_samples": [],
            "pm25_samples": [],
            "last_pm10_avg": None,
            "last_pm25_avg": None,
            "pm10_exceedances": 0,
            "pm25_exceedances": 0,
        }

    async def async_initialize(self) -> None:
        """Load state and start listeners."""
        stored = await self._store.async_load()
        if isinstance(stored, dict):
            self._data.update(stored)
        self._ensure_storage_shape()
        self._prune_old_samples()

        today = dt_util.now().date().isoformat()
        if self._data["date"] != today:
            await self._rollover(today)

        self._unsubscribers.append(
            async_track_state_change_event(
                self.hass,
                [self.cfg.pm10_entity, self.cfg.pm25_entity],
                self._handle_state_change,
            )
        )
        self._unsubscribers.append(
            async_track_time_change(self.hass, self._handle_midnight, hour=0, minute=0, second=5)
        )

        self._capture_initial_values()
        self.async_set_updated_data(None)

    async def async_shutdown(self) -> None:
        """Cleanup listeners."""
        for unsub in self._unsubscribers:
            unsub()
        self._unsubscribers.clear()

    @callback
    def _capture_initial_values(self) -> None:
        self._add_sample_for_entity(self.cfg.pm10_entity)
        self._add_sample_for_entity(self.cfg.pm25_entity)
        self.hass.async_create_task(self._store.async_save(self._data))

    @callback
    def _handle_state_change(self, event: Event) -> None:
        entity_id = event.data.get("entity_id")
        if entity_id is None:
            return

        new_state = event.data.get("new_state")
        if new_state is None:
            return

        today = dt_util.now().date().isoformat()
        if self._data["date"] != today:
            self._rollover_in_memory(today)

        self._add_value(entity_id, new_state.state)
        self.hass.async_create_task(self._store.async_save(self._data))
        self.async_set_updated_data(None)

    async def _handle_midnight(self, _: Any) -> None:
        await self._rollover(dt_util.now().date().isoformat())

    async def _rollover(self, new_date: str) -> None:
        self._rollover_in_memory(new_date)
        await self._store.async_save(self._data)
        self.async_set_updated_data(None)

    @callback
    def _rollover_in_memory(self, new_date: str) -> None:
        pm10_avg = self.current_pm10_average
        pm25_avg = self.current_pm25_average

        self._data["last_pm10_avg"] = pm10_avg
        self._data["last_pm25_avg"] = pm25_avg
        if pm10_avg is not None and pm10_avg > self.cfg.pm10_norm:
            self._data["pm10_exceedances"] += 1
        if pm25_avg is not None and pm25_avg > self.cfg.pm25_norm:
            self._data["pm25_exceedances"] += 1

        self._data["date"] = new_date
        self._data["pm10_samples"] = []
        self._data["pm25_samples"] = []

    @callback
    def _ensure_storage_shape(self) -> None:
        # Migrate older storage shape (sum/count based) to sample-list shape.
        if not isinstance(self._data.get("pm10_samples"), list):
            self._data["pm10_samples"] = []
        if not isinstance(self._data.get("pm25_samples"), list):
            self._data["pm25_samples"] = []
        # Drop deprecated keys from previous rolling/exceedance logic.
        self._data.pop("pm10_incremented_today", None)
        self._data.pop("pm25_incremented_today", None)
        self._data.pop("pm10_exceeded_today", None)
        self._data.pop("pm25_exceeded_today", None)

    @callback
    def _today_start_ts(self) -> float:
        start_local = dt_util.start_of_local_day(dt_util.now())
        return dt_util.as_utc(start_local).timestamp()

    @callback
    def _prune_old_samples(self, now_ts: float | None = None) -> None:
        cutoff = self._today_start_ts() if now_ts is None else now_ts
        self._data["pm10_samples"] = [
            sample
            for sample in self._data["pm10_samples"]
            if isinstance(sample, dict) and sample.get("ts", 0) >= cutoff
        ]
        self._data["pm25_samples"] = [
            sample
            for sample in self._data["pm25_samples"]
            if isinstance(sample, dict) and sample.get("ts", 0) >= cutoff
        ]

    @callback
    def _add_sample_for_entity(self, entity_id: str) -> None:
        state = self.hass.states.get(entity_id)
        if state is None:
            return
        self._add_value(entity_id, state.state)

    @callback
    def _add_value(self, entity_id: str, raw_state: str) -> None:
        try:
            value = float(raw_state)
        except (TypeError, ValueError):
            return

        now_ts = dt_util.utcnow().timestamp()
        cutoff = self._today_start_ts()

        if entity_id == self.cfg.pm10_entity:
            self._data["pm10_samples"].append({"ts": now_ts, "value": value})
            self._data["pm10_samples"] = [
                sample
                for sample in self._data["pm10_samples"]
                if isinstance(sample, dict) and sample.get("ts", 0) >= cutoff
            ]
        elif entity_id == self.cfg.pm25_entity:
            self._data["pm25_samples"].append({"ts": now_ts, "value": value})
            self._data["pm25_samples"] = [
                sample
                for sample in self._data["pm25_samples"]
                if isinstance(sample, dict) and sample.get("ts", 0) >= cutoff
            ]

    @property
    def current_pm10_average(self) -> float | None:
        values = [
            sample["value"]
            for sample in self._data["pm10_samples"]
            if isinstance(sample, dict)
            and isinstance(sample.get("value"), (int, float))
        ]
        if not values:
            return None
        return round(sum(values) / len(values), 2)

    @property
    def current_pm25_average(self) -> float | None:
        values = [
            sample["value"]
            for sample in self._data["pm25_samples"]
            if isinstance(sample, dict)
            and isinstance(sample.get("value"), (int, float))
        ]
        if not values:
            return None
        return round(sum(values) / len(values), 2)

    @property
    def pm10_exceedances(self) -> int:
        return int(self._data["pm10_exceedances"])

    @property
    def pm25_exceedances(self) -> int:
        return int(self._data["pm25_exceedances"])

    @property
    def tracked_date(self) -> str:
        return str(self._data["date"])

    @property
    def pm10_norm(self) -> float:
        return self.cfg.pm10_norm

    @property
    def pm25_norm(self) -> float:
        return self.cfg.pm25_norm


def parse_config(raw_cfg: dict[str, Any]) -> IntegrationConfig:
    """Create runtime config with sane defaults."""
    return IntegrationConfig(
        pm10_entity=str(raw_cfg[CONF_PM10_ENTITY]),
        pm25_entity=str(raw_cfg[CONF_PM25_ENTITY]),
        pm10_norm=float(raw_cfg.get(CONF_PM10_NORM, DEFAULT_PM10_NORM)),
        pm25_norm=float(raw_cfg.get(CONF_PM25_NORM, DEFAULT_PM25_NORM)),
    )
