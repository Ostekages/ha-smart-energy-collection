"""Config flow for Smart Energy."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_DEFAULT_WINDOW,
    CONF_HEATMAP_HOURS,
    CONF_PRICES_ATTRIBUTE,
    CONF_TODAY_ENTITY,
    CONF_TOMORROW_ENTITY,
    CONF_WINDOWS,
    DEFAULT_DEFAULT_WINDOW,
    DEFAULT_HEATMAP_HOURS,
    DEFAULT_NAME,
    DEFAULT_PRICES_ATTRIBUTE,
    DEFAULT_TODAY_ENTITY,
    DEFAULT_TOMORROW_ENTITY,
    DEFAULT_WINDOWS,
    DOMAIN,
)


def _windows_to_str(windows: list[int]) -> str:
    return ", ".join(str(w) for w in windows)


def _str_to_windows(value: Any) -> list[int]:
    if isinstance(value, list):
        return [int(v) for v in value]
    parts = [p.strip() for p in str(value).split(",") if p.strip()]
    return [int(p) for p in parts]


def _schema(defaults: dict) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_TODAY_ENTITY,
                default=defaults.get(CONF_TODAY_ENTITY, DEFAULT_TODAY_ENTITY),
            ): selector.EntitySelector(),
            vol.Required(
                CONF_TOMORROW_ENTITY,
                default=defaults.get(CONF_TOMORROW_ENTITY, DEFAULT_TOMORROW_ENTITY),
            ): selector.EntitySelector(),
            vol.Required(
                CONF_PRICES_ATTRIBUTE,
                default=defaults.get(
                    CONF_PRICES_ATTRIBUTE, DEFAULT_PRICES_ATTRIBUTE
                ),
            ): selector.TextSelector(),
            vol.Required(
                CONF_WINDOWS,
                default=_windows_to_str(
                    defaults.get(CONF_WINDOWS, DEFAULT_WINDOWS)
                ),
            ): selector.TextSelector(),
            vol.Required(
                CONF_DEFAULT_WINDOW,
                default=defaults.get(CONF_DEFAULT_WINDOW, DEFAULT_DEFAULT_WINDOW),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=12, step=1, mode="box")
            ),
            vol.Required(
                CONF_HEATMAP_HOURS,
                default=defaults.get(CONF_HEATMAP_HOURS, DEFAULT_HEATMAP_HOURS),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=48, step=1, mode="box")
            ),
        }
    )


def _normalise(user_input: dict) -> dict:
    data = dict(user_input)
    data[CONF_WINDOWS] = _str_to_windows(data[CONF_WINDOWS])
    data[CONF_DEFAULT_WINDOW] = int(data[CONF_DEFAULT_WINDOW])
    data[CONF_HEATMAP_HOURS] = int(data[CONF_HEATMAP_HOURS])
    return data


class SmartEnergyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ):
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=DEFAULT_NAME, data=_normalise(user_input)
            )

        return self.async_show_form(step_id="user", data_schema=_schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return SmartEnergyOptionsFlow(config_entry)


class SmartEnergyOptionsFlow(OptionsFlow):
    """Allow reconfiguring after setup."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ):
        if user_input is not None:
            return self.async_create_entry(title="", data=_normalise(user_input))

        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(step_id="init", data_schema=_schema(current))
