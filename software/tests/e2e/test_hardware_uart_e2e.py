"""test_hardware_uart_e2e.py

End-to-end hardware loopback tests against the Nexys A7 FPGA over USB-UART.
These tests are skipped automatically unless NEUROSYNC_SERIAL_PORT is set.

Usage:
    NEUROSYNC_SERIAL_PORT=COM3 pytest test_hardware_uart_e2e.py -v
    NEUROSYNC_SERIAL_PORT=/dev/ttyUSB0 pytest test_hardware_uart_e2e.py -v
"""

import os
import time

import pandas as pd
import pytest

import transmission

SERIAL_PORT = os.environ.get("NEUROSYNC_SERIAL_PORT", None)
requires_hardware = pytest.mark.skipif(
    SERIAL_PORT is None,
    reason="Set NEUROSYNC_SERIAL_PORT to run hardware E2E tests",
)


class TestHardwareUARTLoopbackE2E:

    @requires_hardware
    def test_single_packet_loopback(self):
        import serial

        row = pd.Series(
            {"delta": 1000, "theta": 2000, "alpha": 3000, "beta": 4000}
        )
        packet = transmission.df_to_packet(row)

        with serial.Serial(SERIAL_PORT, baudrate=115200, timeout=2) as ser:
            ser.write(packet)
            time.sleep(0.1)
            echoed = ser.read(12)

        assert len(echoed) == 12
        assert echoed[0] == 0xAA
        assert echoed[1] == 0x55

    @requires_hardware
    def test_multiple_packets_loopback_round_trip(self):
        import serial

        df = pd.DataFrame(
            [
                {"delta": 100, "theta": 200, "alpha": 300, "beta": 400},
                {"delta": 500, "theta": 600, "alpha": 700, "beta": 800},
            ]
        )
        packets = [transmission.df_to_packet(row) for _, row in df.iterrows()]

        with serial.Serial(SERIAL_PORT, baudrate=115200, timeout=2) as ser:
            for pkt in packets:
                ser.write(pkt)
            time.sleep(0.2)
            responses = [ser.read(12) for _ in packets]

        for resp in responses:
            assert len(resp) == 12

    @requires_hardware
    def test_hardware_packet_rate_at_50hz(self):
        import serial

        n_packets = 50
        interval = 1.0 / 50
        row = pd.Series(
            {"delta": 1000, "theta": 2000, "alpha": 3000, "beta": 4000}
        )
        packet = transmission.df_to_packet(row)

        start = time.monotonic()
        with serial.Serial(SERIAL_PORT, baudrate=115200, timeout=2) as ser:
            for _ in range(n_packets):
                ser.write(packet)
                time.sleep(interval)
        elapsed = time.monotonic() - start

        assert (
            elapsed < 2.5
        ), f"50-packet burst took {elapsed:.2f}s, expected ~1s"
