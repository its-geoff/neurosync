"""test_serial_write_stress.py

Stress tests for simulated serial write throughput and timing.
"""

import threading
import time
import unittest.mock as mock

import pandas as pd

import transmission


def make_band_row(delta=1000, theta=2000, alpha=3000, beta=4000):
    return pd.Series(
        {"alpha": alpha, "beta": beta, "theta": theta, "delta": delta}
    )


class TestSerialWriteRateSimulation:

    def test_1000_packets_written_in_under_1s(self):
        n = 1000
        row = make_band_row()
        written = []
        ser = mock.MagicMock()
        ser.write.side_effect = lambda p: written.append(p)

        start = time.perf_counter()
        for _ in range(n):
            pkt = transmission.df_to_packet(row)
            ser.write(pkt)
        elapsed = time.perf_counter() - start
        rate = n / elapsed
        print(
            f"\n[serial sim] {n} writes in {elapsed:.3f}s  →  {rate:,.0f} "
            "writes/s"
        )
        assert len(written) == n
        assert rate > 1_000

    def test_50hz_packet_rate_timing_accuracy(self):
        n = 50
        interval = 1.0 / 50
        row = make_band_row()
        times = []
        next_t = time.monotonic()

        for _ in range(n):
            transmission.df_to_packet(row)
            times.append(time.monotonic())
            next_t += interval
            sleep_for = next_t - time.monotonic()
            if sleep_for > 0:
                time.sleep(sleep_for)

        elapsed = times[-1] - times[0]
        print(
            f"\n[50Hz sim] {n} packets over {elapsed:.3f}s (ideal: "
            f"{(n-1)*interval:.3f}s)"
        )
        assert elapsed < (n - 1) * interval * 1.20 + 0.1

    def test_concurrent_encode_and_validate_threads(self):
        n = 2_000
        row = make_band_row()
        errors = []

        def encode_loop():
            try:
                for _ in range(n):
                    pkt = transmission.df_to_packet(row)
                    if not transmission.validate_packet(pkt):
                        errors.append("crc_fail")
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=encode_loop) for _ in range(4)]
        start = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)
        elapsed = time.perf_counter() - start
        total = 4 * n
        rate = total / elapsed
        print(
            f"\n[concurrent encode] {total} ops across 4 threads in "
            f"{elapsed:.3f}s  →  {rate:,.0f} ops/s"
        )
        assert len(errors) == 0, f"thread errors: {errors}"
