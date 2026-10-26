"""Binary sensor platform for Vehicle OBD BLE."""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_PROFILE,
    DEFAULT_PROFILE,
    DOMAIN,
    NAME,
)
from .entity import SkodaObdBleEntity
from .profiles import get_profile

BINARY_SENSOR_TYPES: dict[str, BinarySensorEntityDescription] = {
    "engine_running": BinarySensorEntityDescription(
        key="engine_running",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:engine",
        name="Engine / Vehicle active",
    ),
    "check_engine": BinarySensorEntityDescription(
        key="check_engine",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:engine-outline",
        name="Check engine light (MIL)",
    ),
    "charging": BinarySensorEntityDescription(
        key="charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        icon="mdi:ev-station",
        name="Traction battery charging",
    ),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_devices
) -> bool:
    """Set up binary_sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    profile = entry.options.get(CONF_PROFILE, DEFAULT_PROFILE)
    selected_keys = get_profile(profile).binary_sensor_keys
    entities = [
        SkodaObdBleBinarySensor(coordinator, entry, sensor_desc)
        for sensor_desc in BINARY_SENSOR_TYPES
        if sensor_desc in selected_keys
    ]
    async_add_devices(entities)
    return True


class SkodaObdBleBinarySensor(SkodaObdBleEntity, BinarySensorEntity):
    """Binary sensor entity for Skoda OBD BLE."""

    def __init__(
        self,
        coordinator,
        config_entry,
        sensor: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, config_entry)
        self._sensor = sensor
        self._attr_name = f"{NAME} {BINARY_SENSOR_TYPES[sensor].name}"
        self._attr_device_class = BINARY_SENSOR_TYPES[sensor].device_class

    @property
    def is_on(self):
        """Return true if the binary_sensor is on."""
        data = self.coordinator.live_data
        val = data.get(self._sensor)
        if val is not None:
            return bool(val)
        # Infer engine running if RPM > 0 or Speed > 0
        if self._sensor == "engine_running":
            rpm = data.get("rpm")
            if rpm is not None:
                return rpm > 0
            speed = data.get("speed")
            if speed is not None and speed > 0:
                return True
        elif self._sensor == "charging":
            power = data.get("charge_power")
            if power is not None:
                return power > 0.1
        return None

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return BINARY_SENSOR_TYPES[self._sensor].icon
