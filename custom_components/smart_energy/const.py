"""Constants for the Smart Energy integration."""

from __future__ import annotations

DOMAIN = "smart_energy"
DEFAULT_NAME = "Smart Energy"

# Config keys
CONF_TODAY_ENTITY = "today_entity"
CONF_TOMORROW_ENTITY = "tomorrow_entity"
CONF_PRICES_ATTRIBUTE = "prices_attribute"
CONF_WINDOWS = "windows"
CONF_HEATMAP_HOURS = "heatmap_hours"
CONF_DEFAULT_WINDOW = "default_window"

# Defaults tuned for the Strømligning integration (MTrab)
DEFAULT_TODAY_ENTITY = "sensor.stromligning_spotprice_vat"
DEFAULT_TOMORROW_ENTITY = "binary_sensor.stromligning_tomorrow_spotprice_vat"
DEFAULT_PRICES_ATTRIBUTE = "prices"
DEFAULT_WINDOWS = [2, 3, 4]
DEFAULT_HEATMAP_HOURS = 12
DEFAULT_DEFAULT_WINDOW = 3

# How often the engine recalculates (minutes). Cheap: it only reads states.
UPDATE_INTERVAL_MINUTES = 1

# Number of heatmap levels (0 = cheapest .. LEVELS-1 = most expensive)
HEATMAP_LEVELS = 5

# Trend values
TREND_BETTER_TODAY = "better_today"
TREND_BETTER_TOMORROW = "better_tomorrow"
TREND_EQUAL = "equal"
