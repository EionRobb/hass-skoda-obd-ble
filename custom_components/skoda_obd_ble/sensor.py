"""Sensor platform for Vehicle OBD BLE."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_PROFILE, DEFAULT_PROFILE, DOMAIN, NAME
from .entity import SkodaObdBleEntity
from .profiles import get_profile

SENSOR_TYPES: dict[str, SensorEntityDescription] = {
    "rpm": SensorEntityDescription(
        key="rpm",
        icon="mdi:gauge",
        name="Engine RPM",
        native_unit_of_measurement="RPM",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "speed": SensorEntityDescription(
        key="speed",
        icon="mdi:speedometer",
        name="Vehicle speed",
        native_unit_of_measurement="km/h",
        suggested_display_precision=0,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "coolant_temp": SensorEntityDescription(
        key="coolant_temp",
        icon="mdi:coolant-temperature",
        name="Engine coolant temperature",
        native_unit_of_measurement="°C",
        suggested_display_precision=0,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "oil_temp": SensorEntityDescription(
        key="oil_temp",
        icon="mdi:oil-temperature",
        name="Engine oil temperature",
        native_unit_of_measurement="°C",
        suggested_display_precision=0,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "fuel_level": SensorEntityDescription(
        key="fuel_level",
        icon="mdi:gas-station",
        name="Fuel level",
        native_unit_of_measurement="%",
        suggested_display_precision=1,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "bat_12v_voltage": SensorEntityDescription(
        key="bat_12v_voltage",
        icon="mdi:car-battery",
        name="12V battery voltage",
        native_unit_of_measurement="V",
        suggested_display_precision=1,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "ambient_temp": SensorEntityDescription(
        key="ambient_temp",
        icon="mdi:thermometer",
        name="Ambient temperature",
        native_unit_of_measurement="°C",
        suggested_display_precision=1,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "intake_temp": SensorEntityDescription(
        key="intake_temp",
        icon="mdi:thermometer-lines",
        name="Intake air temperature",
        native_unit_of_measurement="°C",
        suggested_display_precision=0,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "engine_load": SensorEntityDescription(
        key="engine_load",
        icon="mdi:engine",
        name="Engine load",
        native_unit_of_measurement="%",
        suggested_display_precision=1,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "run_time": SensorEntityDescription(
        key="run_time",
        icon="mdi:timer-outline",
        name="Engine run time",
        native_unit_of_measurement="s",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "distance_since_cleared": SensorEntityDescription(
        key="distance_since_cleared",
        icon="mdi:map-marker-distance",
        name="Distance since codes cleared",
        native_unit_of_measurement="km",
        suggested_display_precision=0,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "odometer": SensorEntityDescription(
        key="odometer",
        icon="mdi:counter",
        name="Odometer",
        native_unit_of_measurement="km",
        suggested_display_precision=1,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    "battery_soc": SensorEntityDescription(
        key="battery_soc",
        icon="mdi:battery-high",
        name="State of charge",
        native_unit_of_measurement="%",
        suggested_display_precision=1,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "battery_temp": SensorEntityDescription(
        key="battery_temp",
        icon="mdi:battery-heart",
        name="Traction battery temperature",
        native_unit_of_measurement="°C",
        suggested_display_precision=1,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "hv_voltage": SensorEntityDescription(
        key="hv_voltage",
        icon="mdi:flash",
        name="HV battery voltage",
        native_unit_of_measurement="V",
        suggested_display_precision=1,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    "charge_power": SensorEntityDescription(
        key="charge_power",
        icon="mdi:lightning-bolt",
        name="Traction battery charge power",
        native_unit_of_measurement="kW",
        suggested_display_precision=2,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    profile = entry.options.get(CONF_PROFILE, DEFAULT_PROFILE)
    selected_keys = get_profile(profile).sensor_keys
    overridden_keys = set(coordinator.extra_sensor_descriptions)
    entities = [
        SkodaObdBleSensor(coordinator, entry, desc)
        for key, desc in SENSOR_TYPES.items()
        if key in selected_keys and key not in overridden_keys
    ]
    for desc in coordinator.extra_sensor_descriptions.values():
        entities.append(SkodaObdBleSensor(coordinator, entry, desc))
    async_add_entities(entities)


class SkodaObdBleSensor(SkodaObdBleEntity, SensorEntity):
    """Sensor entity for Skoda OBD BLE."""

    def __init__(
        self,
        coordinator,
        config_entry,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._description = description
        self._sensor = description.key
        self._attr_name = f"{NAME} {description.name}"
        self._attr_device_class = description.device_class
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_state_class = description.state_class

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(self._sensor)

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._description.icon
