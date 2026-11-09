#!/usr/bin/env python3
"""
Battery state-of-charge (0-100%) for a 12.8 V 12 Ah LiFePO4, using an INA226.
The battery is charged OFF this circuit, then plugged back in.

Requires: sudo apt install -y python3-smbus2
Run:      python3 battery_soc.py          # normal
          python3 battery_soc.py --full   # just plugged in a fully charged battery
"""

import argparse                             # UPDATE: for the --full option
import json
import os
import sys
import time

try:
    from smbus2 import SMBus
except ImportError:
    sys.exit("smbus2 not found. Install it with: sudo apt install -y python3-smbus2")

# =====================================================================
# SETTINGS - edit these
# =====================================================================
PRINT_INTERVAL_S = 10        # seconds between percentage outputs  <-- CHANGE THIS
SAMPLE_INTERVAL_S = 1.0      # how often current is measured (keep at ~1 s)
SAVE_INTERVAL_S = 60         # how often the % is saved to the SD card

CAPACITY_AH = 12.0
SHUNT_OHMS = 0.002           # your module's shunt (R2 = 0.002R)
I2C_ADDRESS = 0x40
I2C_BUS = 1

DISCHARGE_IS_POSITIVE = True # flip to False if % rises while discharging

# UPDATE: "full" is now detected when a battery is plugged in:
FULL_REST_VOLTAGE = 13.4     # UPDATE: resting at/above this when plugged in -> 100%
RECHARGE_MARGIN = 25         # UPDATE: if voltage says >= this many points fuller than
                             #         the saved %, assume it was charged and use voltage
NO_BATTERY_VOLTAGE = 5.0     # UPDATE: below this = battery unplugged (don't count)
EMPTY_VOLTAGE = 11.0         # at/below this...
EMPTY_HOLD_S = 30            # ...for this long -> reset to 0%
REST_CURRENT_A = 0.5         # voltage is only trusted below this current

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "battery_soc.json")

# Approximate resting voltage -> SOC for 12 V LiFePO4 (Renogy / footprinthero).
VOLTAGE_SOC_TABLE = [
    (10.0, 0), (12.0, 9), (12.5, 14), (12.8, 17), (12.9, 20), (13.0, 30),
    (13.1, 40), (13.2, 70), (13.3, 90), (13.4, 99), (13.6, 100),
]
# =====================================================================

REG_CONFIG  = 0x00
REG_SHUNT_V = 0x01
REG_BUS_V   = 0x02
REG_MFG_ID  = 0xFE
REG_DIE_ID  = 0xFF

SHUNT_LSB_V = 2.5e-6
BUS_LSB_V   = 1.25e-3

CONFIG_VALUE = 0x4000 | (0b110 << 9) | (0b100 << 6) | (0b100 << 3) | 0b111   # = 0x4D27
CONFIG_RESET = 0x8000
SETTLE_S = 1.2               # one full averaged reading (~1.13 s)


def swap16(v):
    return ((v & 0xFF) << 8) | (v >> 8)


def read_reg(bus, reg):
    return swap16(bus.read_word_data(I2C_ADDRESS, reg))


def write_reg(bus, reg, value):
    bus.write_word_data(I2C_ADDRESS, reg, swap16(value & 0xFFFF))


def to_signed(v):
    return v - 0x10000 if v & 0x8000 else v


def setup(bus):
    if (read_reg(bus, REG_MFG_ID), read_reg(bus, REG_DIE_ID)) != (0x5449, 0x2260):
        sys.exit(f"Device at 0x{I2C_ADDRESS:02X} is not an INA226. Check I2C_ADDRESS.")
    write_reg(bus, REG_CONFIG, CONFIG_RESET)
    time.sleep(0.01)
    write_reg(bus, REG_CONFIG, CONFIG_VALUE)
    if read_reg(bus, REG_CONFIG) != CONFIG_VALUE:
        print("WARNING: INA226 config readback mismatch.", file=sys.stderr)


def read_battery(bus):
    """Returns (volts, amps); amps > 0 means DISCHARGING."""
    volts = read_reg(bus, REG_BUS_V) * BUS_LSB_V
    amps = to_signed(read_reg(bus, REG_SHUNT_V)) * SHUNT_LSB_V / SHUNT_OHMS
    return volts, (amps if DISCHARGE_IS_POSITIVE else -amps)


def soc_from_voltage(volts):
    table = VOLTAGE_SOC_TABLE
    if volts <= table[0][0]:
        return 0.0
    if volts >= table[-1][0]:
        return 100.0
    for (v1, s1), (v2, s2) in zip(table, table[1:]):
        if v1 <= volts <= v2:
            return s1 + (s2 - s1) * (volts - v1) / (v2 - v1)
    return 0.0


def load_state():
    try:
        with open(STATE_FILE) as f:
            return float(json.load(f)["soc_percent"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


def save_state(soc):
    try:
        tmp = STATE_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"soc_percent": round(soc, 3), "saved": time.time()}, f)
        os.replace(tmp, STATE_FILE)
    except OSError as e:
        print(f"WARNING: could not save state: {e}", file=sys.stderr)


def starting_soc(volts, amps, saved, force_full):            # UPDATE: new decision logic
    """Pick the starting % when a battery is (re)connected."""
    if force_full:
        return 100.0
    at_rest = abs(amps) <= REST_CURRENT_A
    if at_rest and volts >= FULL_REST_VOLTAGE:
        return 100.0                                          # freshly charged
    v_soc = soc_from_voltage(volts)
    if saved is None:
        if not at_rest:
            print(f"WARNING: battery not at rest ({amps:+.2f} A); starting % is rough. "
                  f"Use --full after a full charge.", file=sys.stderr)
        return v_soc
    if at_rest and v_soc >= saved + RECHARGE_MARGIN:
        return v_soc                                          # looks charged since last time
    return saved


def main():
    ap = argparse.ArgumentParser(description="Battery % from an INA226.")   # UPDATE
    ap.add_argument("--full", action="store_true",
                    help="Battery was just fully charged: start at 100%%")
    args = ap.parse_args()

    try:
        bus = SMBus(I2C_BUS)
    except (FileNotFoundError, PermissionError) as e:
        sys.exit(f"Cannot open /dev/i2c-{I2C_BUS}: {e}")

    remaining_ah = None
    try:
        try:
            setup(bus)
            time.sleep(SETTLE_S)
            read_battery(bus)                                 # check the chip responds
        except OSError as e:
            sys.exit(f"No response from 0x{I2C_ADDRESS:02X} ({e}). Check wiring / i2cdetect -y 1.")

        saved = load_state()
        connected = False                                     # UPDATE: tracks plug-in state
        force_full = args.full
        empty_timer = 0.0
        last_sample = time.monotonic()
        next_print = last_sample
        next_save = last_sample + SAVE_INTERVAL_S

        while True:
            now = time.monotonic()
            dt = now - last_sample
            last_sample = now
            volts, amps = read_battery(bus)

            if volts < NO_BATTERY_VOLTAGE:                    # UPDATE: battery unplugged
                if connected:
                    save_state(100.0 * remaining_ah / CAPACITY_AH)
                    saved = 100.0 * remaining_ah / CAPACITY_AH
                    connected = False
                empty_timer = 0.0
            else:
                if not connected:                             # UPDATE: just plugged in
                    time.sleep(SETTLE_S)                      # let the reading settle
                    volts, amps = read_battery(bus)
                    soc0 = min(max(starting_soc(volts, amps, saved, force_full), 0.0), 100.0)
                    remaining_ah = CAPACITY_AH * soc0 / 100.0
                    force_full = False                        # --full applies once
                    connected = True
                    last_sample = time.monotonic()
                    dt = 0.0

                remaining_ah -= amps * dt / 3600.0            # coulomb counting
                remaining_ah = min(max(remaining_ah, 0.0), CAPACITY_AH)

                if volts <= EMPTY_VOLTAGE:
                    empty_timer += dt
                    if empty_timer >= EMPTY_HOLD_S:
                        remaining_ah = 0.0
                else:
                    empty_timer = 0.0

            if now >= next_print:
                if connected:
                    print(f"{round(100.0 * remaining_ah / CAPACITY_AH)}%", flush=True)
                else:
                    print("No battery", flush=True)           # UPDATE
                next_print = max(next_print + PRINT_INTERVAL_S, now)
            if connected and now >= next_save:
                save_state(100.0 * remaining_ah / CAPACITY_AH)
                next_save = now + SAVE_INTERVAL_S

            time.sleep(max(0.0, SAMPLE_INTERVAL_S - (time.monotonic() - now)))

    except KeyboardInterrupt:
        pass
    except OSError as e:
        print(f"I2C error: {e}", file=sys.stderr)
    finally:
        if remaining_ah is not None:
            save_state(100.0 * remaining_ah / CAPACITY_AH)
        bus.close()


if __name__ == "__main__":
    main()