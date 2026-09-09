"""Pre-configured OBD commands for Skoda vehicles."""

from .decoders import (
    decode_ambient_temp,
    decode_bat_12v,
    decode_battery_soc,
    decode_battery_temp,
    decode_charge_power,
    decode_coolant_temp,
    decode_distance,
    decode_engine_load,
    decode_fuel_level,
    decode_hv_voltage,
    decode_hybrid_battery_soc,
    decode_intake_temp,
    decode_oil_temp,
    decode_odometer,
    decode_rpm,
    decode_run_time,
    decode_speed,
)
from .OBDCommand import OBDCommand

# Standard OBD-II Mode 01 commands (Functional broadcast 7DF or ECU 7E0)
skoda_ice_commands: dict[str, OBDCommand] = {
    "rpm": OBDCommand(
        "rpm",
        "Engine RPM",
        b"010C",
        2,
        decode_rpm,
        b"7DF",
        fast=True,
    ),
    "speed": OBDCommand(
        "speed",
        "Vehicle Speed",
        b"010D",
        1,
        decode_speed,
        b"7DF",
        fast=True,
    ),
    "coolant_temp": OBDCommand(
        "coolant_temp",
        "Engine Coolant Temperature",
        b"0105",
        1,
        decode_coolant_temp,
        b"7DF",
        fast=True,
    ),
    "oil_temp": OBDCommand(
        "oil_temp",
        "Engine Oil Temperature",
        b"015C",
        1,
        decode_oil_temp,
        b"7DF",
        fast=True,
    ),
    "fuel_level": OBDCommand(
        "fuel_level",
        "Fuel Tank Level",
        b"012F",
        1,
        decode_fuel_level,
        b"7DF",
        fast=True,
    ),
    "bat_12v_voltage": OBDCommand(
        "bat_12v_voltage",
        "Control Module 12V Voltage",
        b"0142",
        2,
        decode_bat_12v,
        b"7DF",
        fast=True,
    ),
    "ambient_temp": OBDCommand(
        "ambient_temp",
        "Ambient Air Temperature",
        b"0146",
        1,
        decode_ambient_temp,
        b"7DF",
        fast=True,
    ),
    "intake_temp": OBDCommand(
        "intake_temp",
        "Intake Air Temperature",
        b"010F",
        1,
        decode_intake_temp,
        b"7DF",
        fast=True,
    ),
    "engine_load": OBDCommand(
        "engine_load",
        "Calculated Engine Load",
        b"0104",
        1,
        decode_engine_load,
        b"7DF",
        fast=True,
    ),
    "run_time": OBDCommand(
        "run_time",
        "Engine Run Time",
        b"011F",
        2,
        decode_run_time,
        b"7DF",
        fast=True,
    ),
    "distance_since_cleared": OBDCommand(
        "distance_since_cleared",
        "Distance Since Codes Cleared",
        b"0131",
        2,
        decode_distance,
        b"7DF",
        fast=True,
    ),
}

# Standard SAE PIDs applicable to plug-in hybrids. Vehicle support varies, so
# an unsupported PID is left unknown instead of being decoded as zero.
skoda_phev_commands: dict[str, OBDCommand] = {
    "fuel_level": skoda_ice_commands["fuel_level"],
    # Some VAG ECUs do not expose fuel level through Mode 01 PID 2F but
    # provide the equivalent standardized datum through UDS DID F42F.
    "fuel_level_uds": OBDCommand(
        "fuel_level_uds",
        "Fuel Tank Level (UDS fallback)",
        b"22F42F",
        1,
        decode_fuel_level,
        b"7E0",
        fast=False,
    ),
    "battery_soc": OBDCommand(
        "battery_soc",
        "Hybrid Battery Remaining Life",
        b"015B",
        1,
        decode_hybrid_battery_soc,
        b"7DF",
        fast=True,
    ),
    "odometer": OBDCommand(
        "odometer",
        "Vehicle Odometer",
        b"01A6",
        4,
        decode_odometer,
        b"7DF",
        fast=True,
    ),
}

# Skoda EV / VAG MEB platform commands (ECU 7E5 / 714 UDS Service 22)
skoda_ev_commands: dict[str, OBDCommand] = {
    "battery_soc": OBDCommand(
        "battery_soc",
        "Traction Battery State of Charge",
        b"22028C",
        2,
        decode_battery_soc,
        b"7E5",
        fast=True,
    ),
    "battery_temp": OBDCommand(
        "battery_temp",
        "Traction Battery Temperature",
        b"22028E",
        1,
        decode_battery_temp,
        b"7E5",
        fast=True,
    ),
    "hv_voltage": OBDCommand(
        "hv_voltage",
        "High Voltage Battery Pack Voltage",
        b"221E3B",
        2,
        decode_hv_voltage,
        b"7E5",
        fast=True,
    ),
    "charge_power": OBDCommand(
        "charge_power",
        "Traction Battery Charge Power",
        b"221E38",
        2,
        decode_charge_power,
        b"7E5",
        fast=True,
    ),
    "bat_12v_voltage": OBDCommand(
        "bat_12v_voltage",
        "Control Module 12V Voltage",
        b"0142",
        2,
        decode_bat_12v,
        b"7DF",
        fast=True,
    ),
}

# Default full dictionary containing all base commands
skoda_commands: dict[str, OBDCommand] = {
    **skoda_ice_commands,
    **skoda_ev_commands,
}
