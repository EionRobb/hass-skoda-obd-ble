"""Vehicle profiles for the generic ELM327 BLE integration core."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .commands import (
    skoda_commands,
    skoda_ev_commands,
    skoda_ice_commands,
    skoda_phev_commands,
)
from .const import (
    PROFILE_ALL,
    PROFILE_CUSTOM,
    PROFILE_EV,
    PROFILE_GENERIC,
    PROFILE_ICE,
    PROFILE_PHEV,
)
from .OBDCommand import OBDCommand


@dataclass(frozen=True)
class VehicleProfile:
    """A command set and the entities it can populate."""

    label: str
    commands: Mapping[str, OBDCommand]
    sensor_keys: frozenset[str]
    binary_sensor_keys: frozenset[str]


STANDARD_SENSOR_KEYS = frozenset(
    {
        "rpm",
        "speed",
        "coolant_temp",
        "oil_temp",
        "fuel_level",
        "bat_12v_voltage",
        "ambient_temp",
        "intake_temp",
        "engine_load",
        "run_time",
        "distance_since_cleared",
    }
)

PROFILES: Mapping[str, VehicleProfile] = MappingProxyType(
    {
        PROFILE_GENERIC: VehicleProfile(
            "Generic vehicle (standard OBD-II)",
            MappingProxyType(skoda_ice_commands),
            STANDARD_SENSOR_KEYS,
            frozenset({"engine_running", "check_engine"}),
        ),
        PROFILE_ICE: VehicleProfile(
            "Skoda ICE (standard OBD-II)",
            MappingProxyType(skoda_ice_commands),
            STANDARD_SENSOR_KEYS,
            frozenset({"engine_running", "check_engine"}),
        ),
        PROFILE_PHEV: VehicleProfile(
            "Skoda Superb iV / VAG MQB plug-in hybrid",
            MappingProxyType(skoda_phev_commands),
            frozenset({"fuel_level", "battery_soc", "odometer"}),
            frozenset({"engine_running"}),
        ),
        PROFILE_EV: VehicleProfile(
            "Skoda Enyaq / VAG MEB electric vehicle",
            MappingProxyType(skoda_ev_commands),
            frozenset(
                {
                    "battery_soc",
                    "battery_temp",
                    "hv_voltage",
                    "charge_power",
                    "bat_12v_voltage",
                }
            ),
            frozenset({"engine_running", "charging"}),
        ),
        PROFILE_CUSTOM: VehicleProfile(
            "Custom PIDs only (overrides.yaml)",
            MappingProxyType({}),
            frozenset(),
            frozenset(),
        ),
        PROFILE_ALL: VehicleProfile(
            "Legacy: all built-in commands",
            MappingProxyType(skoda_commands),
            frozenset(
                STANDARD_SENSOR_KEYS
                | {
                    "odometer",
                    "battery_soc",
                    "battery_temp",
                    "hv_voltage",
                    "charge_power",
                }
            ),
            frozenset({"engine_running", "check_engine", "charging"}),
        ),
    }
)


def get_profile(profile_id: str) -> VehicleProfile:
    """Return a profile, falling back to generic standard OBD-II."""
    return PROFILES.get(profile_id, PROFILES[PROFILE_GENERIC])


def profile_labels() -> dict[str, str]:
    """Return labels suitable for a Home Assistant selector."""
    return {profile_id: profile.label for profile_id, profile in PROFILES.items()}
