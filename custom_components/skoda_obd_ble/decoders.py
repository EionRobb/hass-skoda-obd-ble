"""Decoder functions for decoding Skoda OBD responses."""

import logging
import struct

_LOGGER = logging.getLogger(__name__)


def decode_linear(messages, key: str, byte_offset: int = 0, scale: float = 1.0, offset: float = 0.0) -> dict:
    """Decode a simple linear scaled byte."""
    if not messages or not messages[0].data or len(messages[0].data) <= byte_offset:
        return {}
    val = messages[0].data[byte_offset] * scale + offset
    return {key: val}


def decode_voltage_atrv(messages) -> dict:
    """Decode ELM327 'AT RV' voltage response."""
    if not messages:
        return {}
    try:
        raw_str = messages[0].raw().upper().replace("V", "").strip()
        return {"bat_12v_voltage": float(raw_str)}
    except Exception as err:
        _LOGGER.debug("Failed to decode AT RV voltage: %s", err)
        return {}


def decode_bat_12v(messages) -> dict:
    """Decode Control Module 12V Voltage (Mode 01 42)."""
    if not messages or len(messages[0].data) < 2:
        return {}
    # Formula: ((A * 256) + B) / 1000 = Volts
    raw = (messages[0].data[0] * 256) + messages[0].data[1]
    return {"bat_12v_voltage": round(raw / 1000.0, 2)}


def decode_rpm(messages) -> dict:
    """Decode Engine RPM (Mode 01 0C)."""
    if not messages or len(messages[0].data) < 2:
        return {}
    # Formula: ((A * 256) + B) / 4
    raw = (messages[0].data[0] * 256) + messages[0].data[1]
    return {"rpm": int(raw / 4)}


def decode_speed(messages) -> dict:
    """Decode Vehicle Speed in km/h (Mode 01 0D)."""
    if not messages or len(messages[0].data) < 1:
        return {}
    return {"speed": int(messages[0].data[0])}


def decode_coolant_temp(messages) -> dict:
    """Decode Engine Coolant Temperature in °C (Mode 01 05)."""
    if not messages or len(messages[0].data) < 1:
        return {}
    return {"coolant_temp": int(messages[0].data[0]) - 40}


def decode_oil_temp(messages) -> dict:
    """Decode Engine Oil Temperature in °C (Mode 01 5C)."""
    if not messages or len(messages[0].data) < 1:
        return {}
    return {"oil_temp": int(messages[0].data[0]) - 40}


def decode_intake_temp(messages) -> dict:
    """Decode Intake Air Temperature in °C (Mode 01 0F)."""
    if not messages or len(messages[0].data) < 1:
        return {}
    return {"intake_temp": int(messages[0].data[0]) - 40}


def decode_ambient_temp(messages) -> dict:
    """Decode Ambient Air Temperature in °C (Mode 01 46)."""
    if not messages or len(messages[0].data) < 1:
        return {}
    return {"ambient_temp": int(messages[0].data[0]) - 40}


def decode_fuel_level(messages) -> dict:
    """Decode Fuel Tank Level Input % (Mode 01 2F)."""
    if not messages or len(messages[0].data) < 1:
        return {}
    # Formula: (A * 100) / 255
    return {"fuel_level": round((messages[0].data[0] * 100.0) / 255.0, 1)}


def decode_engine_load(messages) -> dict:
    """Decode Calculated Engine Load % (Mode 01 04)."""
    if not messages or len(messages[0].data) < 1:
        return {}
    return {"engine_load": round((messages[0].data[0] * 100.0) / 255.0, 1)}


def decode_run_time(messages) -> dict:
    """Decode Run Time Since Engine Start in seconds (Mode 01 1F)."""
    if not messages or len(messages[0].data) < 2:
        return {}
    return {"run_time": (messages[0].data[0] * 256) + messages[0].data[1]}


def decode_distance(messages) -> dict:
    """Decode Distance Traveled Since Codes Cleared in km (Mode 01 31)."""
    if not messages or len(messages[0].data) < 2:
        return {}
    return {"distance_since_cleared": (messages[0].data[0] * 256) + messages[0].data[1]}


def decode_odometer(messages) -> dict:
    """Decode standardized Mode 01 PID A6 odometer in kilometres."""
    if not messages or len(messages[0].data) < 4:
        return {}
    raw = int.from_bytes(messages[0].data[:4], byteorder="big")
    return {"odometer": round(raw / 10.0, 1)}


def decode_hybrid_battery_soc(messages) -> dict:
    """Decode standardized Mode 01 PID 5B hybrid battery remaining life."""
    if not messages or len(messages[0].data) < 1:
        return {}
    return {"battery_soc": round(messages[0].data[0] * 100.0 / 255.0, 1)}


def decode_battery_soc(messages) -> dict:
    """Decode Traction Battery State of Charge % (VAG UDS DID 028C / F40D)."""
    if not messages or not messages[0].data:
        return {}
    data = messages[0].data
    if len(data) >= 2:
        val = ((data[0] * 256) + data[1]) * 0.1
        if 0.0 <= val <= 100.0:
            return {"battery_soc": round(val, 1)}
    val = data[0] * 0.5
    return {"battery_soc": round(val, 1)}


def decode_battery_temp(messages) -> dict:
    """Decode Traction Battery Average Temperature in °C (VAG UDS DID 028E)."""
    if not messages or not messages[0].data:
        return {}
    return {"battery_temp": round(messages[0].data[0] * 0.5 - 40.0, 1)}


def decode_hv_voltage(messages) -> dict:
    """Decode High-Voltage Traction Battery Voltage (VAG UDS DID 1E3B)."""
    if not messages or len(messages[0].data) < 2:
        return {}
    raw = (messages[0].data[0] * 256) + messages[0].data[1]
    return {"hv_voltage": round(raw * 0.1, 1)}


def decode_charge_power(messages) -> dict:
    """Decode HV Charging/Discharging Power in kW (VAG UDS DID 1E38)."""
    if not messages or len(messages[0].data) < 2:
        return {}
    try:
        raw_int = struct.unpack(">h", messages[0].data[:2])[0]
        return {"charge_power": round(raw_int * 0.1, 2)}
    except Exception:
        return {}
