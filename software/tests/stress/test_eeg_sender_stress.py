#!/usr/bin/env python3
"""
eeg_test_sender.py
──────────────────
Sends fake EEG packets to the Nexys A7 FPGA over USB-UART at 115200 baud.
Packet format (12 bytes):
  [0xAA, 0x55, 0x08,
   alpha_hi, alpha_lo,
   beta_hi,  beta_lo,
   theta_hi, theta_lo,
   delta_hi, delta_lo,
   checksum]
Checksum = XOR of LEN(0x08) and all 8 payload bytes.

Usage:
  python eeg_test_sender.py          # interactive mode picker
  python eeg_test_sender.py --port COM3 --mode sine
  python eeg_test_sender.py --port /dev/ttyUSB0 --mode bars
"""

import argparse
import math
import random
import sys
import time

import serial
import serial.tools.list_ports


# ──────────────────────────────────────────────
#  Packet builder
# ──────────────────────────────────────────────
def build_packet(alpha: int, beta: int, theta: int, delta: int) -> bytes:
    """Build a 12-byte EEG packet. Values are uint16 (0–65535)."""
    # Clamp to uint16
    alpha = max(0, min(0xFFFF, alpha))
    beta = max(0, min(0xFFFF, beta))
    theta = max(0, min(0xFFFF, theta))
    delta = max(0, min(0xFFFF, delta))

    a_hi, a_lo = (alpha >> 8) & 0xFF, alpha & 0xFF
    b_hi, b_lo = (beta >> 8) & 0xFF, beta & 0xFF
    t_hi, t_lo = (theta >> 8) & 0xFF, theta & 0xFF
    d_hi, d_lo = (delta >> 8) & 0xFF, delta & 0xFF

    payload = [a_hi, a_lo, b_hi, b_lo, t_hi, t_lo, d_hi, d_lo]
    chk = 0x08  # XOR starts with LEN byte
    for b in payload:
        chk ^= b

    return bytes([0xAA, 0x55, 0x08] + payload + [chk])


# ──────────────────────────────────────────────
#  Animation modes  (each is a generator)
#  Yields (alpha, beta, theta, delta) tuples
# ──────────────────────────────────────────────


def mode_sine(rate_hz=50):
    """All four bands on independent sine waves — looks like a live EEG."""
    phases = [0.0, 0.9, 1.8, 2.7]  # offset each band
    freqs = [0.3, 0.5, 0.7, 0.4]  # Hz of oscillation
    dt = 1.0 / rate_hz
    t = 0.0
    while True:
        vals = []
        for ph, fr in zip(phases, freqs):
            # Map sine [-1,1] -> [2000, 60000] so bars are clearly visible
            v = int(31000 + 29000 * math.sin(2 * math.pi * fr * t + ph))
            vals.append(v)
        yield tuple(vals)
        t += dt


def mode_sweep(rate_hz=50):
    """Each bar sweeps from 0 to max one at a time so you can verify each."""
    steps = int(rate_hz * 2)  # 2 seconds per bar
    while True:
        for i in range(4):
            for s in range(steps):
                v = int((s / steps) * 0xFFFF)
                vals = [0, 0, 0, 0]
                vals[i] = v
                yield tuple(vals)
            # Hold full for half a second
            for _ in range(int(rate_hz * 0.5)):
                vals = [0, 0, 0, 0]
                vals[i] = 0xFFFF
                yield tuple(vals)


def mode_bars(rate_hz=50):
    """
    All bars fill together then drop — simple up/down ramp.
    Good for checking that scaling looks right across the full range.
    """
    steps = int(rate_hz * 3)  # 3 seconds up, 3 seconds down
    while True:
        for s in range(steps):
            v = int((s / steps) * 0xFFFF)
            yield (v, v, v, v)
        for s in range(steps, 0, -1):
            v = int((s / steps) * 0xFFFF)
            yield (v, v, v, v)


def mode_random(rate_hz=50):
    """Random walk — each band drifts up/down independently."""
    vals = [32768, 32768, 32768, 32768]
    step = 2000
    while True:
        vals = [
            max(0, min(0xFFFF, v + random.randint(-step, step))) for v in vals
        ]
        yield tuple(vals)


def mode_static(rate_hz=50):
    """All bars at 50% — useful to confirm static display isn't flickering."""
    while True:
        yield (0x8000, 0x8000, 0x8000, 0x8000)


def mode_individual(rate_hz=50):
    """
    Interactive: type a band name and value.
    Press Enter with no input to keep current values.
    """
    vals = [0x8000, 0x8000, 0x8000, 0x8000]
    names = ["alpha", "beta", "theta", "delta"]
    print("  Enter  '<band> <0-65535>'  e.g.  'alpha 50000'")
    print("  or just press Enter to keep current values.")
    print("  Ctrl+C to quit.\n")
    import threading

    user_input = [None]

    def reader():
        while True:
            try:
                line = input()
                user_input[0] = line.strip()
            except EOFError:
                break

    t = threading.Thread(target=reader, daemon=True)
    t.start()

    while True:
        if user_input[0] is not None:
            parts = user_input[0].lower().split()
            user_input[0] = None
            if len(parts) == 2 and parts[0] in names:
                try:
                    idx = names.index(parts[0])
                    vals[idx] = max(0, min(0xFFFF, int(parts[1])))
                    print(f"  → {parts[0]} = {vals[idx]}")
                except ValueError:
                    print("  Bad value, ignored.")
        yield tuple(vals)


MODES = {
    "sine": mode_sine,
    "sweep": mode_sweep,
    "bars": mode_bars,
    "random": mode_random,
    "static": mode_static,
    "individual": mode_individual,
}


# ──────────────────────────────────────────────
#  Port auto-detection helper
# ──────────────────────────────────────────────
def pick_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("No serial ports found. Connect your FPGA and try again.")
        sys.exit(1)
    if len(ports) == 1:
        print(f"Auto-selected port: {ports[0].device}")
        return ports[0].device
    print("\nAvailable serial ports:")
    for i, p in enumerate(ports):
        print(f"  [{i}] {p.device}  –  {p.description}")
    while True:
        try:
            idx = int(input("Select port number: "))
            return ports[idx].device
        except (ValueError, IndexError):
            print("Invalid selection, try again.")


# ──────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="EEG test packet sender for Nexys A7 FPGA"
    )
    parser.add_argument(
        "--port",
        default=None,
        help="Serial port (e.g. COM3 or /dev/ttyUSB0). Auto-detected if "
        "omitted.",
    )
    parser.add_argument(
        "--mode",
        default=None,
        choices=list(MODES.keys()),
        help="Animation mode",
    )
    parser.add_argument(
        "--rate", type=int, default=50, help="Packets per second (default: 50)"
    )
    args = parser.parse_args()

    # Port
    port = args.port or pick_port()

    # Mode
    if args.mode is None:
        print("\nAnimation modes:")
        descs = {
            "sine": 'Independent sine waves on each band (looks most "live")',
            "sweep": "Each bar fills one at a time – verify each bar "
            "individually",
            "bars": "All bars ramp up/down together – check scaling",
            "random": "Random walk – stress test",
            "static": "All bars fixed at 50% – check for flicker",
            "individual": "Type values manually in the terminal",
        }
        for k, v in descs.items():
            print(f"  {k:<12} {v}")
        mode_name = input("\nPick mode: ").strip().lower()
        if mode_name not in MODES:
            print("Unknown mode.")
            sys.exit(1)
    else:
        mode_name = args.mode

    rate_hz = args.rate
    interval = 1.0 / rate_hz

    print(f"\nOpening {port} at 115200 baud…")
    try:
        ser = serial.Serial(port, baudrate=115200, timeout=1)
    except serial.SerialException as e:
        print(f"Could not open port: {e}")
        sys.exit(1)

    time.sleep(0.1)  # let the FPGA UART settle

    gen = MODES[mode_name](rate_hz)

    print(
        f"Sending {rate_hz} packets/sec in '{mode_name}' mode.  Ctrl+C to "
        "stop.\n"
    )
    print(f"  {'Alpha':>7}  {'Beta':>7}  {'Theta':>7}  {'Delta':>7}")
    print(f"  {'-----':>7}  {'----':>7}  {'-----':>7}  {'-----':>7}")

    pkt_count = 0
    next_time = time.monotonic()

    try:
        while True:
            alpha, beta, theta, delta = next(gen)
            pkt = build_packet(alpha, beta, theta, delta)
            ser.write(pkt)
            pkt_count += 1

            # Print every 10 packets so terminal isn't flooded
            if pkt_count % 10 == 0:
                print(
                    f"\r  {alpha:>7}  {beta:>7}  {theta:>7}  {delta:>7}   "
                    "pkt#{pkt_count}",
                    end="",
                    flush=True,
                )

            # Rate limiter
            next_time += interval
            sleep_for = next_time - time.monotonic()
            if sleep_for > 0:
                time.sleep(sleep_for)

    except KeyboardInterrupt:
        print(f"\n\nStopped after {pkt_count} packets.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
