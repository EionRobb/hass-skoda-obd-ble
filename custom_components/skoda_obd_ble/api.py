"""API client for Skoda OBD BLE communication."""

import logging
from typing import Any

from bleak.backends.device import BLEDevice

from .commands import (
    skoda_commands,
    skoda_ev_commands,
    skoda_ice_commands,
    skoda_phev_commands,
)
from .const import (
    CONF_CHARACTERISTIC_UUID_READ,
    CONF_CHARACTERISTIC_UUID_WRITE,
    CONF_PROFILE,
    CONF_SERVICE_UUID,
    DEFAULT_CHARACTERISTIC_UUID_READ,
    DEFAULT_CHARACTERISTIC_UUID_WRITE,
    DEFAULT_PROFILE,
    DEFAULT_SERVICE_UUID,
    PROFILE_EV,
    PROFILE_ICE,
    PROFILE_PHEV,
)
from .OBDCommand import OBDCommand
from .obd import OBD

_LOGGER: logging.Logger = logging.getLogger(__package__)


class SkodaObdBleApiClient:
    """API for connecting to the Skoda OBD BLE dongle."""

    def __init__(self, ble_device: BLEDevice) -> None:
        """Initialize API client."""
        self._ble_device = ble_device

    async def async_get_data(
        self,
        options: dict[str, Any] | None = None,
        extra_commands: dict[str, OBDCommand] | None = None,
        disabled_commands: set[str] | None = None,
    ) -> dict[str, Any] | None:
        """Fetch and decode data from the vehicle over BLE."""
        if self._ble_device is None:
            return {}

        options = options or {}
        disabled = disabled_commands or set()
        profile = options.get(CONF_PROFILE, DEFAULT_PROFILE)

        # Select base command dictionary based on configured vehicle profile
        if profile == PROFILE_EV:
            base_commands = dict(skoda_ev_commands)
        elif profile == PROFILE_PHEV:
            base_commands = dict(skoda_phev_commands)
        elif profile == PROFILE_ICE:
            base_commands = dict(skoda_ice_commands)
        else:
            base_commands = dict(skoda_commands)

        # Merge in any user extra/override commands
        if extra_commands:
            base_commands.update(extra_commands)

        # Filter out disabled commands
        active_commands = [
            cmd for key, cmd in base_commands.items() if key not in disabled
        ]

        service_uuid = options.get(CONF_SERVICE_UUID, DEFAULT_SERVICE_UUID)
        char_read = options.get(
            CONF_CHARACTERISTIC_UUID_READ, DEFAULT_CHARACTERISTIC_UUID_READ
        )
        char_write = options.get(
            CONF_CHARACTERISTIC_UUID_WRITE, DEFAULT_CHARACTERISTIC_UUID_WRITE
        )

        api = await OBD.create(
            self._ble_device,
            protocol="6",
            service_uuid=service_uuid,
            characteristic_uuid_read=char_read,
            characteristic_uuid_write=char_write,
        )

        if api is None:
            return None
        if not api.is_connected():
            _LOGGER.error("ELM327 initialization did not reach CAR_CONNECTED")
            await api.close()
            return None

        data: dict[str, Any] = {}
        try:
            for command in active_commands:
                _LOGGER.debug("Querying command: %s", command.name)
                response = await api.query(command, force=True)
                if response and response.value is not None:
                    data.update(response.value)
        finally:
            await api.close()

        _LOGGER.debug("Decoded OBD data: %s", data)
        return data
