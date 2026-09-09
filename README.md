# Skoda OBD BLE — Home Assistant Custom Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![License](https://img.shields.io/github/license/pbutterworth/nissan-leaf-obd-ble.svg)](LICENSE)

A [Home Assistant](https://www.home-assistant.io/) custom integration for monitoring **Skoda / VAG** vehicles via a Bluetooth Low Energy (BLE) ELM327 OBD-II adapter (such as the LeLink2 or vLinker MC+).

The communication engine and Skoda diagnostic command sets are self-contained and embedded directly within the integration, requiring no external PyPI library dependencies.

When your Skoda pulls into the garage or driveway, this integration automatically connects over BLE and reads live vehicle diagnostics (Engine RPM, Coolant & Oil Temp, Fuel Level, 12V Battery Voltage, or EV High-Voltage Battery SoC & Power) into native Home Assistant sensors for dashboards, automations, and history tracking.

---

## Features

- **No external library dependencies** — Self-contained pure-Python BLE ELM327 / CAN communication engine
- **Powertrain Profile Support**:
  - **Skoda ICE / Hybrid** (Octavia, Superb, Kodiaq, Karoq, Fabia, Scala, Kamiq): Standard OBD-II Mode 01 sensors (RPM, Speed, Coolant Temperature, Oil Temperature, Fuel Level, 12V Voltage, Run Time, Engine Load, Ambient Temp)
  - **Skoda EV / MEB Platform** (Enyaq iV, Citigo-e iV): VAG UDS Service `22` sensors (Traction Battery SoC, Battery Temperature, High-Voltage Pack Voltage, Charging Power)
- Communicates over **Bluetooth Low Energy** — no Wi-Fi or cloud dependency
- Compatible with **ESPHome Bluetooth proxy** (e.g. GL-iNet GL-S10)
- Configurable **command override system** via `overrides.yaml` for adding custom PIDs or decoders

---

## Requirements

### Hardware

| Item | Details |
|---|---|
| **BLE ELM327 OBD-II adapter** | LeLink2, vLinker MC+, Viecar BLE, or compatible ELM327 Bluetooth Low Energy adapter. |
| **Bluetooth radio** | Either the Home Assistant host's built-in Bluetooth, or an [ESPHome Bluetooth proxy](https://esphome.io/components/bluetooth_proxy.html) in the garage. |

### Software

- Home Assistant **2023.6** or later
- [HACS](https://hacs.xyz/) (optional for easy installation)

---

## Installation

### Option 1 — Manual Installation
1. Copy the `custom_components/skoda_obd_ble` folder into your Home Assistant `config/custom_components/` directory:
   ```
   config/
   └── custom_components/
       └── skoda_obd_ble/
           ├── __init__.py
           ├── manifest.json
           ├── config_flow.py
           ├── sensor.py
           ├── commands.py
           ├── decoders.py
           └── ...
   ```
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration**, search for **Skoda OBD BLE**, and follow the setup wizard.

---

## Configuration

During setup, select:
1. **Discovered BLE OBD Adapter** (e.g. LeLink / vLinker).
2. **Vehicle Profile**:
   - `Skoda ICE / Hybrid (Standard OBD-II)`
   - `Skoda EV (Enyaq / Citigo-e / MEB UDS)`
   - `All Supported Skoda Sensors`
3. Optional: Customize GATT service / characteristic UUIDs if using a non-standard adapter.

---

## Entities

| Entity | Unit | Powertrain | Description |
|---|---|---|---|
| `sensor.skoda_obd_ble_engine_rpm` | `RPM` | ICE / Hybrid | Current Engine RPM |
| `sensor.skoda_obd_ble_vehicle_speed` | `km/h` | All | Current Vehicle Speed |
| `sensor.skoda_obd_ble_engine_coolant_temperature` | `°C` | ICE / Hybrid | Engine Coolant Temperature |
| `sensor.skoda_obd_ble_engine_oil_temperature` | `°C` | ICE / Hybrid | Engine Oil Temperature |
| `sensor.skoda_obd_ble_fuel_level` | `%` | ICE / Hybrid | Fuel Tank Level |
| `sensor.skoda_obd_ble_12v_battery_voltage` | `V` | All | 12V Control Module Battery Voltage |
| `sensor.skoda_obd_ble_ambient_temperature` | `°C` | All | Ambient Air Temperature |
| `sensor.skoda_obd_ble_state_of_charge` | `%` | EV | High-Voltage Traction Battery SoC |
| `sensor.skoda_obd_ble_traction_battery_temperature` | `°C` | EV | High-Voltage Battery Pack Temperature |
| `sensor.skoda_obd_ble_hv_battery_voltage` | `V` | EV | High-Voltage Traction Battery Voltage |
| `sensor.skoda_obd_ble_traction_battery_charge_power` | `kW` | EV | High-Voltage Charging Power |

---

## Customizing PIDs via `overrides.yaml`

You can add custom PIDs, modify scaling formulas, or disable commands by placing an `overrides.yaml` file in `config/custom_components/skoda_obd_ble/overrides.yaml`:

```yaml
_all_:
  commands:
    custom_intake_temp:
      command: "010F"
      header: "7DF"
      bytes: 1
      description: "Intake Air Temperature"
      decoder:
        type: "linear_scale"
        byte_offset: 0
        scale: 1.0
        offset: -40.0
      sensor:
        name: "Intake Air Temperature"
        unit: "°C"
        device_class: "temperature"
        state_class: "measurement"
```
