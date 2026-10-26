"""Module to implement a serial-like interface over BLE GATT."""

import asyncio
from contextlib import suppress
import logging

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError
from bleak_retry_connector import (
    BleakAbortedError,
    BleakClientWithServiceCache,
    BleakConnectionError,
    BleakNotFoundError,
    BleakOutOfConnectionSlotsError,
    establish_connection,
)

logger = logging.getLogger(__name__)

OBD_NOTIFICATION_CHARACTERISTICS = (
    "0000ffe1-0000-1000-8000-00805f9b34fb",
    "0000ffe4-0000-1000-8000-00805f9b34fb",
)

class bleserial:
    """Encapsulates the ble connection and make it appear something like a UART port."""

    __buffer = bytearray()

    def __init__(
        self,
        ble_device: BLEDevice,
        service_uuid,
        characteristic_uuid_read,
        characteristic_uuid_write,
    ) -> None:
        """Initialise."""
        self._ble_device: BLEDevice = ble_device
        self._service_uuid = service_uuid
        self._characteristic_uuid_read = characteristic_uuid_read
        self._characteristic_uuid_write = characteristic_uuid_write
        self._client: BleakClient | None = None
        self._rx_buffer = bytearray()
        self._timeout = None
        self._closing = False
        self._close_lock = asyncio.Lock()
        self._write_timeout = None
        self._connection_stage = "idle"
        self._first_notification_logged = False
        self._notification_characteristics: list[str] = []

    async def _wait_for_data(self, size):
        while len(self._rx_buffer) < size:
            if self._client is None or not self._client.is_connected:
                raise BleakError("BLE disconnected while waiting for data")
            await asyncio.sleep(0.01)

    async def _wait_for_line(self):
        while b"\n" not in self._rx_buffer:
            if self._client is None or not self._client.is_connected:
                raise BleakError("BLE disconnected while waiting for line")
            await asyncio.sleep(0.01)

    def reset_input_buffer(self):
        """Reset the input buffer."""
        logger.debug("Resetting input buffer")
        self._rx_buffer.clear()

    def reset_output_buffer(self):
        """Reset the output buffer."""
        logger.debug("Resetting output buffer")
        # Since there's no explicit output buffer, this is a no-op.

    def flush(self):
        """Reset the input and the output buffer."""
        self.reset_input_buffer()
        self.reset_output_buffer()

    async def wait_for_unsolicited(self, timeout: float = 1.0) -> bytes:
        """Wait briefly for a device challenge or other unsolicited data."""
        try:
            await asyncio.wait_for(self._wait_for_data(1), timeout=timeout)
        except TimeoutError:
            logger.debug(
                "BLE stage=no_unsolicited_data timeout=%.1fs",
                timeout,
            )
            return b""

        data = bytes(self._rx_buffer)
        logger.debug("BLE stage=unsolicited_data data=%r", data)
        return data

    @property
    def in_waiting(self):
        """Return the number of bytes in the receive buffer."""
        return len(self._rx_buffer)

    @property
    def timeout(self):
        """Timeout duration."""
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        """Set the timeout duration."""
        self._timeout = value

    @property
    def write_timeout(self):
        """Write timeout duration."""
        return self._write_timeout

    @write_timeout.setter
    def write_timeout(self, value):
        """Set the write timeout duration."""
        self._write_timeout = value

    def _notification_handler(self, sender, data):
        """Handle when a GATT notification arrives."""
        if not self._first_notification_logged:
            logger.debug(
                "BLE stage=first_notification sender=%s data=%r", sender, bytes(data)
            )
            self._first_notification_logged = True
        logger.debug("Notification received: %s", data)
        self._rx_buffer.extend(data)

    async def open(self):
        """Open the port."""

        logger.debug("open port, ble_device: %s", self._ble_device)

        self._closing = False
        def on_disconnect(client):
            """Handle disconnection (expected or unexpected)."""
            if self._closing:
                logger.debug("BleakClient disconnected (expected)")
            else:
                logger.debug(
                    "BleakClient disconnected unexpectedly at stage=%s",
                    self._connection_stage,
                )
            self._connection_stage = "disconnected"
            self._client = None

        try:
            self._connection_stage = "connecting"
            logger.debug(
                "BLE stage=connecting device=%s address=%s",
                self._ble_device.name,
                self._ble_device.address,
            )
            logger.debug("Connecting to ble_device: %s %s", self._ble_device, self._ble_device.name)
            self._client = await establish_connection(
                BleakClientWithServiceCache,  # Use BleakClientWithServiceCache for service caching
                self._ble_device,
                self._ble_device.name or "Unknown Device",
                disconnected_callback=on_disconnect,
                max_attempts=3,  # Will retry up to 3 times with backoff
            )

            self._connection_stage = "connected"
            logger.debug("BLE stage=connected device=%s", self._ble_device.address)
            logger.debug("Connected to ble_device: %s", self._ble_device)

            services = self._client.services
            for service in services:
                logger.debug("BLE service discovered: %s", service.uuid)
                for characteristic in service.characteristics:
                    logger.debug(
                        "BLE characteristic discovered: %s properties=%s",
                        characteristic.uuid,
                        characteristic.properties,
                    )

            configured_service = services.get_service(self._service_uuid)
            if configured_service is None:
                raise BleakError(
                    f"Configured service UUID {self._service_uuid} was not discovered"
                )
            read_characteristic = services.get_characteristic(
                self._characteristic_uuid_read
            )
            write_characteristic = services.get_characteristic(
                self._characteristic_uuid_write
            )
            if read_characteristic is None:
                raise BleakError(
                    "Configured read characteristic UUID "
                    f"{self._characteristic_uuid_read} was not discovered"
                )
            if write_characteristic is None:
                raise BleakError(
                    "Configured write characteristic UUID "
                    f"{self._characteristic_uuid_write} was not discovered"
                )

            self._connection_stage = "starting_notifications"
            notification_characteristics = []
            for characteristic_uuid in (
                self._characteristic_uuid_read,
                *OBD_NOTIFICATION_CHARACTERISTICS,
            ):
                characteristic = services.get_characteristic(characteristic_uuid)
                if (
                    characteristic is not None
                    and "notify" in characteristic.properties
                    and characteristic.uuid not in notification_characteristics
                ):
                    notification_characteristics.append(characteristic.uuid)

            for characteristic_uuid in notification_characteristics:
                logger.debug(
                    "BLE stage=starting_notifications characteristic=%s",
                    characteristic_uuid,
                )
                await self._client.start_notify(
                    characteristic_uuid, self._notification_handler
                )
                self._notification_characteristics.append(characteristic_uuid)

            self._connection_stage = "notifications_started"
            logger.debug(
                "BLE stage=notifications_started characteristics=%s",
                self._notification_characteristics,
            )
            logger.debug("Notifications started")

        except BleakNotFoundError as e:
            logger.debug("Device not found - it may have moved out of range: %s", e)
            await self.close()
            raise

        except BleakOutOfConnectionSlotsError:
            logger.debug(
                "No connection slots available - try disconnecting other devices"
            )
            await self.close()
            raise

        except BleakAbortedError:
            logger.debug("Connection aborted - check for interference or move closer")
            await self.close()
            raise

        except BleakConnectionError as e:
            logger.debug("Connection failed: %s", e)
            await self.close()
            raise

        except BleakError as e:
            logger.debug("Failed to connect or start notifications: %s", e)
            await self.close()
            raise

    async def close(self):
        """Close the port (expected disconnect)."""
        async with self._close_lock:
            if not self._client:
                return

            self._closing = True
            client = self._client

            try:
                for characteristic_uuid in self._notification_characteristics:
                    logger.debug(
                        "Stopping notifications on characteristic UUID: %s",
                        characteristic_uuid,
                    )
                    with suppress(BleakError):
                        await client.stop_notify(characteristic_uuid)
                self._notification_characteristics.clear()
                logger.debug("Disconnecting from device")
                await client.disconnect()
                logger.debug("Disconnected from device")
            finally:
                self._client = None
                self._closing = False

    async def write(self, data):
        """Write bytes."""
        if isinstance(data, str):
            data = data.encode()
        try:
            if self._client is None or not self._client.is_connected:
                raise BleakError(
                    f"Cannot write while BLE is disconnected (stage={self._connection_stage})"
                )
            self._connection_stage = "writing"
            logger.debug(
                "Writing data to characteristic UUID: %s Data: %s",
                self._characteristic_uuid_write,
                data,
            )
            await self._client.write_gatt_char(
                self._characteristic_uuid_write,
                data,
                response=False,
            )
            self._connection_stage = "waiting_for_notification"
            logger.debug("Data written")
        except BleakError as e:
            logger.debug("Failed to write data: %s", e)
            raise

    async def read(self, size=1):
        """Read from the buffer."""
        try:
            logger.debug("Reading %s bytes of data", size)
            await asyncio.wait_for(self._wait_for_data(size), timeout=self._timeout)
            data = self._rx_buffer[:size]
            self._rx_buffer = self._rx_buffer[size:]
            logger.debug("Read data: %s", data)
            return bytes(data)
        except Exception as e:
            logger.debug(
                "Failed to read data (%s): %s",
                type(e).__name__,
                e,
            )
            raise

    async def readline(self):
        """Read a whole line from the buffer."""
        try:
            logger.debug("Reading line")
            await asyncio.wait_for(self._wait_for_line(), timeout=self._timeout)
            index = self._rx_buffer.index(b"\n") + 1
            data = self._rx_buffer[:index]
            self._rx_buffer = self._rx_buffer[index:]
            logger.debug("Read line: %s", data)
            return bytes(data)
        except TimeoutError as e:
            logger.debug("Readline operation timed out")
            raise BleakError("Readline operation timed out") from e
        except Exception as e:
            logger.debug(
                "Failed to read line (%s): %s",
                type(e).__name__,
                e,
            )
            raise
