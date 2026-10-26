"""Custom integration for BLE ELM327 vehicle data in Home Assistant."""

import logging

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.typing import ConfigType

from .api import SkodaObdBleApiClient
from .const import CONF_PROFILE, DEFAULT_PROFILE, DOMAIN, PLATFORMS, STARTUP_MESSAGE
from .coordinator import SkodaObdBleDataUpdateCoordinator
from .overrides import load_overrides

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    address: str = entry.data[CONF_ADDRESS]
    ble_device = bluetooth.async_ble_device_from_address(hass, address.upper(), True)
    api = SkodaObdBleApiClient(ble_device)

    extra_commands, extra_sensor_descriptions, disabled_commands = (
        await hass.async_add_executor_job(
            load_overrides,
            hass,
            address,
            entry.options.get(CONF_PROFILE, DEFAULT_PROFILE),
        )
    )

    coordinator = SkodaObdBleDataUpdateCoordinator(
        hass,
        address=address,
        api=api,
        options=entry.options or {},
        extra_commands=extra_commands,
        extra_sensor_descriptions=extra_sensor_descriptions,
        disabled_commands=disabled_commands,
    )

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Start available with an empty cache; cached discovery must not cause a read.
    coordinator.async_set_updated_data(coordinator._snapshot())
    entry.async_on_unload(coordinator.async_stop)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Unlike discovery callbacks, this receives unchanged packets too. It has
    # no replay of cached advertisements and never schedules a polling timer.
    entry.async_on_unload(
        bluetooth.async_register_advertisement_callback(
            hass, coordinator.async_handle_advertisement, address.upper()
        )
    )

    async def update_options_listener(hass: HomeAssistant, entry: ConfigEntry):
        """Handle options update."""
        await async_reload_entry(hass, entry)

    entry.async_on_unload(
        entry.add_update_listener(update_options_listener)
    )  # add the listener for when the user changes options

    # entry.add_update_listener(async_reload_entry)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if not hass.data.get(DOMAIN):
        hass.data.pop(DOMAIN, None)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
