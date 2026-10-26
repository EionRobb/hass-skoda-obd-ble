"""Constants for Vehicle OBD BLE."""

# Base component constants
from homeassistant.const import Platform

NAME = "Vehicle OBD BLE"
DOMAIN = "skoda_obd_ble"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "1.1.0"

ATTRIBUTION = "Data retrieved locally from the vehicle via OBD-II BLE"
ISSUE_URL = "https://github.com/EionRobb/hass-skoda-obd-ble/issues"

# Platforms
PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SENSOR]

# Configuration and options
CONF_ENABLED = "enabled"
CONF_PROFILE = "profile"
CONF_SERVICE_UUID = "service_uuid"
CONF_CHARACTERISTIC_UUID_READ = "characteristic_uuid_read"
CONF_CHARACTERISTIC_UUID_WRITE = "characteristic_uuid_write"

# Profiles
PROFILE_ICE = "skoda_ice"
PROFILE_PHEV = "skoda_phev"
PROFILE_EV = "skoda_ev"
PROFILE_ALL = "all"
PROFILE_GENERIC = "generic_obd"
PROFILE_CUSTOM = "custom"

# Defaults
DEFAULT_NAME = DOMAIN
DEFAULT_PROFILE = PROFILE_GENERIC
DEFAULT_SERVICE_UUID = "0000ffe0-0000-1000-8000-00805f9b34fb"
DEFAULT_CHARACTERISTIC_UUID_READ = "0000ffe1-0000-1000-8000-00805f9b34fb"
DEFAULT_CHARACTERISTIC_UUID_WRITE = "0000ffe1-0000-1000-8000-00805f9b34fb"

OVERRIDES_FILE = "custom_components/skoda_obd_ble/overrides.yaml"
DECODERS_MODULE_FILE = "custom_components/skoda_obd_ble/decoders.py"

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration for ELM327 BLE vehicle diagnostics!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
