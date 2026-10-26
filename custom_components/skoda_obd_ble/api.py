"""API client for Skoda OBD BLE communication."""

import logging
import random
from typing import Any

from bleak.backends.device import BLEDevice

from .const import (
    CONF_CHARACTERISTIC_UUID_READ,
    CONF_CHARACTERISTIC_UUID_WRITE,
    CONF_PROFILE,
    CONF_SERVICE_UUID,
    DEFAULT_CHARACTERISTIC_UUID_READ,
    DEFAULT_CHARACTERISTIC_UUID_WRITE,
    DEFAULT_PROFILE,
    DEFAULT_SERVICE_UUID,
)
from .OBDCommand import OBDCommand
from .obd import OBD
from .profiles import get_profile

_LOGGER: logging.Logger = logging.getLogger(__package__)


class SkodaObdBleApiClient:
    """API for connecting to the Skoda OBD BLE dongle."""

    def __init__(self, ble_device: BLEDevice) -> None:
        """Initialize API client."""
        self._ble_device = ble_device
        self._command_bag = []
        self._command_signature = None
        self._variant_index = {}

    def update_ble_device(self, ble_device):
        """Use Home Assistant's current connectable route to the adapter."""
        self._ble_device = ble_device

    def _select_command(self, commands):
        """Shuffle values without starvation; alternate fallback PID variants."""
        groups = {}
        for key, command in commands.items():
            value = "fuel_level" if key == "fuel_level_uds" else key
            groups.setdefault(value, []).append(command)
        signature = tuple((key, tuple(id(cmd) for cmd in variants)) for key, variants in groups.items())
        if signature != self._command_signature:
            self._command_bag = []
            self._variant_index = {}
            self._command_signature = signature
        if not groups:
            return None
        if not self._command_bag:
            self._command_bag = list(groups)
            random.shuffle(self._command_bag)
        value = self._command_bag.pop()
        variants = groups[value]
        index = self._variant_index.get(value, 0)
        self._variant_index[value] = index + 1
        return variants[index % len(variants)]

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

        base_commands = dict(get_profile(profile).commands)

        # Merge in any user extra/override commands
        if extra_commands:
            base_commands.update(extra_commands)

        # Filter out disabled commands
        active_commands = {
            key: cmd for key, cmd in base_commands.items() if key not in disabled
        }
        if not active_commands:
            return {}

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
            check_voltage=False,
            service_uuid=service_uuid,
            characteristic_uuid_read=char_read,
            characteristic_uuid_write=char_write,
        )

        if api is None:
            return None
        if not api.is_connected():
            _LOGGER.debug("ELM327 initialization did not reach CAR_CONNECTED")
            await api.close()
            return None

        data: dict[str, Any] = {}
        try:
            # Advance only after connecting. BLE failures don't consume a turn;
            # unsupported/quiet PIDs do, so they cannot starve the other values.
            command = self._select_command(active_commands)
            _LOGGER.debug("Querying single wake-window command: %s", command.name)
            response = await api.query(command, force=True)
            if response and response.value is not None:
                data.update(response.value)
        finally:
            await api.close()

        _LOGGER.debug("Decoded OBD data: %s", data)
        return data
