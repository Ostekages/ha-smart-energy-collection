"""Data coordinator: the Smart Energy engine."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import homeassistant.util.dt as dt_util

from .const import (
    CONF_DEFAULT_WINDOW,
    CONF_HEATMAP_HOURS,
    CONF_PRICES_ATTRIBUTE,
    CONF_TODAY_ENTITY,
    CONF_TOMORROW_ENTITY,
    CONF_WINDOWS,
    DEFAULT_DEFAULT_WINDOW,
    DEFAULT_HEATMAP_HOURS,
    DEFAULT_PRICES_ATTRIBUTE,
    DEFAULT_TODAY_ENTITY,
    DEFAULT_TOMORROW_ENTITY,
    DEFAULT_WINDOWS,
    DOMAIN,
    HEATMAP_LEVELS,
    TREND_BETTER_TODAY,
    TREND_BETTER_TOMORROW,
    TREND_EQUAL,
    UPDATE_INTERVAL_MINUTES,
)
from .helpers import (
    aggregate_hourly,
    build_levels,
    current_price,
    filter_future,
    find_best_window,
    merge_prices,
    parse_prices,
    window_label,
)

_LOGGER = logging.getLogger(__name__)


class SmartEnergyCoordinator(DataUpdateCoordinator):
    """Reads the Strømligning sensors and computes intelligent price data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        options = {**entry.data, **entry.options}

        self.today_entity: str = options.get(CONF_TODAY_ENTITY, DEFAULT_TODAY_ENTITY)
        self.tomorrow_entity: str = options.get(
            CONF_TOMORROW_ENTITY, DEFAULT_TOMORROW_ENTITY
        )
        self.prices_attribute: str = options.get(
            CONF_PRICES_ATTRIBUTE, DEFAULT_PRICES_ATTRIBUTE
        )
        self.windows: list[int] = list(options.get(CONF_WINDOWS, DEFAULT_WINDOWS))
        self.default_window: int = int(
            options.get(CONF_DEFAULT_WINDOW, DEFAULT_DEFAULT_WINDOW)
        )
        self.heatmap_hours: int = int(
            options.get(CONF_HEATMAP_HOURS, DEFAULT_HEATMAP_HOURS)
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )

    def _read_prices(self, entity_id: str) -> list[dict]:
        """Read and parse the price array from a source entity."""
        state = self.hass.states.get(entity_id)
        if state is None:
            _LOGGER.debug("Source entity %s not found", entity_id)
            return []
        raw = state.attributes.get(self.prices_attribute)
        return parse_prices(raw)

    def _source_unit(self) -> str | None:
        state = self.hass.states.get(self.today_entity)
        if state is None:
            return None
        return state.attributes.get("unit_of_measurement")

    async def _async_update_data(self) -> dict:
        now = dt_util.now()
        today_date = now.date()

        today = self._read_prices(self.today_entity)
        tomorrow = self._read_prices(self.tomorrow_entity)
        all_prices = merge_prices(today, tomorrow)

        hourly_all = aggregate_hourly(all_prices)
        future = filter_future(hourly_all, now)

        future_today = [h for h in future if h["start"].date() == today_date]
        hourly_tomorrow = [h for h in hourly_all if h["start"].date() > today_date]

        # Best contiguous window from *now* forward, per configured duration.
        best_windows: dict[str, dict | None] = {}
        for duration in self.windows:
            window = find_best_window(future, duration)
            best_windows[f"{duration}h"] = self._serialise_window(window)

        best_today = find_best_window(future_today, self.default_window)
        best_tomorrow = find_best_window(hourly_tomorrow, self.default_window)

        trend = self._trend(best_today, best_tomorrow)

        return {
            "current": current_price(all_prices, now),
            "unit": self._source_unit(),
            "updated": now.isoformat(),
            "windows": self.windows,
            "default_window": self.default_window,
            "best_windows": best_windows,
            "best_today": self._serialise_window(best_today),
            "best_today_label": window_label(best_today),
            "best_tomorrow": self._serialise_window(best_tomorrow),
            "best_tomorrow_label": window_label(best_tomorrow),
            "trend": trend,
            "next_hours": build_levels(
                future[: self.heatmap_hours], HEATMAP_LEVELS
            ),
            "has_tomorrow": bool(hourly_tomorrow),
        }

    @staticmethod
    def _serialise_window(window: dict | None) -> dict | None:
        if not window:
            return None
        return {
            "start": window["start"].isoformat(),
            "end": window["end"].isoformat(),
            "label": window_label(window),
            "average_price": window["average_price"],
        }

    @staticmethod
    def _trend(
        best_today: dict | None, best_tomorrow: dict | None
    ) -> str | None:
        if best_today is None and best_tomorrow is None:
            return None
        if best_tomorrow is None:
            return TREND_BETTER_TODAY
        if best_today is None:
            return TREND_BETTER_TOMORROW
        if best_tomorrow["average_price"] < best_today["average_price"]:
            return TREND_BETTER_TOMORROW
        if best_tomorrow["average_price"] > best_today["average_price"]:
            return TREND_BETTER_TODAY
        return TREND_EQUAL
