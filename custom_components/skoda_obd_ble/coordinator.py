"""Advertisement-triggered coordinator for Skoda OBD BLE."""

import asyncio
from datetime import datetime, timezone
import logging
from time import monotonic
from typing import Any

from bleak.exc import BleakError
from homeassistant.components.bluetooth.api import async_ble_device_from_address
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import SkodaObdBleApiClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
DEFAULT_CACHE_VALUES = True
DEFAULT_FETCH_TIMEOUT = 90
LIVE_DATA_TTL = 60
ADVERTISEMENT_COOLDOWN = 30


class SkodaObdBleDataUpdateCoordinator(DataUpdateCoordinator):
    """Read only after fresh advertisements or explicit manual refreshes."""

    def __init__(self, hass: HomeAssistant, address: str,
                 api: SkodaObdBleApiClient, options, extra_commands=None,
                 extra_sensor_descriptions=None, disabled_commands=None) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN,
                         update_interval=None, always_update=False)
        self._address = address
        self.api = api
        self._cache_data: dict[str, Any] = {}
        self.extra_commands = extra_commands or {}
        self.extra_sensor_descriptions = extra_sensor_descriptions or {}
        self.disabled_commands = disabled_commands or set()
        self.options = options
        self.live_data = {}
        self.value_last_success = {}
        self._live_updated = {}
        self.last_success = None
        self.connection_status = "waiting_for_advertisement"
        self._next_attempt = 0.0
        self._reading = False
        self._refresh_pending = False
        self._advertisement_task = None
        self._expiry_handle = None
        self._stopped = False

    def advertisement_refresh_due(self):
        """Reserve one immediate read; a cooldown expiry never starts a read."""
        if (self._stopped or self._reading or self._refresh_pending
                or monotonic() < self._next_attempt):
            return False
        self._refresh_pending = True
        return True

    def async_handle_advertisement(self, service_info):
        """Handle all real packets, coalescing duplicates from nearby scanners."""
        if not service_info.connectable or not self.advertisement_refresh_due():
            return
        # Bypass the request-refresh debouncer: it can defer a read until after
        # this advertisement's opportunity. Our reservation prevents duplicates.
        self._advertisement_task = self.hass.async_create_task(self.async_refresh())

    def async_stop(self):
        """Cancel local expiry and any pending advertisement read on unload."""
        self._stopped = True
        if self._expiry_handle is not None:
            self._expiry_handle.cancel()
            self._expiry_handle = None
        if self._advertisement_task is not None:
            self._advertisement_task.cancel()
            self._advertisement_task = None

    def _snapshot(self):
        """Publish immutable snapshots so repeated missed reads stay quiet."""
        return {
            **self._cache_data,
            "_live_data": dict(self.live_data),
            "_connection_status": self.connection_status,
            "_last_success": self.last_success,
            "_value_last_success": dict(self.value_last_success),
        }

    def _expire_live_data(self):
        """Expire binary evidence locally, without connecting to the vehicle."""
        self._expiry_handle = None
        now = monotonic()
        expired = [key for key, updated in self._live_updated.items()
                   if now - updated >= LIVE_DATA_TTL]
        for key in expired:
            self._live_updated.pop(key, None)
            self.live_data.pop(key, None)
        if expired and not self._stopped:
            self.async_set_updated_data(self._snapshot())
        self._schedule_expiry()

    def _schedule_expiry(self):
        if self._expiry_handle is not None:
            self._expiry_handle.cancel()
            self._expiry_handle = None
        if self._live_updated and not self._stopped:
            delay = max(0.01, min(self._live_updated.values()) + LIVE_DATA_TTL - monotonic())
            self._expiry_handle = self.hass.loop.call_later(delay, self._expire_live_data)

    def _missed_read(self, status):
        self.connection_status = status
        if not self._cache_values:
            self._cache_data = {}
        return self._snapshot()

    async def _async_update_data(self) -> dict[str, Any]:
        """Make one bounded read. No outcome enables scheduled polling."""
        self._reading = True
        try:
            ble_device = async_ble_device_from_address(self.hass, self._address.upper(), True)
            if ble_device is None:
                return self._missed_read("out_of_range")
            self.api.update_ble_device(ble_device)
            try:
                new_data = await asyncio.wait_for(
                    self.api.async_get_data(
                        self.options, extra_commands=self.extra_commands or None,
                        disabled_commands=self.disabled_commands or None),
                    timeout=self._fetch_timeout,
                )
            except (TimeoutError, OSError, BleakError) as err:
                _LOGGER.debug("OBD connection unavailable: %s", err)
                return self._missed_read("disconnected")
            except Exception:
                _LOGGER.exception("Unexpected OBD polling failure")
                return self._missed_read("disconnected")
            if not new_data:
                return self._missed_read("no_data")
            self.connection_status = "connected"
            self.last_success = datetime.now(timezone.utc).isoformat()
            now = monotonic()
            for key, value in new_data.items():
                self.value_last_success[key] = self.last_success
                self.live_data[key] = value
                self._live_updated[key] = now
            self._schedule_expiry()
            if self._cache_values:
                self._cache_data.update(new_data)
            else:
                self._cache_data = dict(new_data)
            return self._snapshot()
        finally:
            self._reading = False
            self._refresh_pending = False
            self._next_attempt = monotonic() + ADVERTISEMENT_COOLDOWN

    @property
    def options(self):
        return self._options

    @options.setter
    def options(self, options):
        self._options = options
        self._cache_values = options.get("cache_values", DEFAULT_CACHE_VALUES)
        self._fetch_timeout = float(options.get("fetch_timeout", DEFAULT_FETCH_TIMEOUT))
