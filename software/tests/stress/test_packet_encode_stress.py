"""test_packet_encode_stress.py

Stress tests for packet encoding and validation throughput.
"""

import time

import numpy as np
import pandas as pd

import transmission


def make_band_row(delta=1000, theta=2000, alpha=3000, beta=4000):
    return pd.Series(
        {"beta": beta, "alpha": alpha, "theta": theta, "delta": delta}
    )


class TestPacketEncodeThroughput:

    def test_encode_10k_packets(self):
        n = 10_000
        row = make_band_row()
        start = time.perf_counter()
        for _ in range(n):
            transmission.df_to_packet(row)
        elapsed = time.perf_counter() - start
        rate = n / elapsed
        print(
            f"\n[encode] {n} packets in {elapsed:.3f}s  →  {rate:,.0f} pkt/s"
        )
        assert rate > 5_000

    def test_validate_10k_packets(self):
        row = make_band_row()
        packets = [transmission.df_to_packet(row) for _ in range(10_000)]
        n = len(packets)
        start = time.perf_counter()
        for pkt in packets:
            transmission.validate_packet(pkt)
        elapsed = time.perf_counter() - start
        rate = n / elapsed
        print(
            f"[validate] {n} packets in {elapsed:.3f}s  →  {rate:,.0f} pkt/s"
        )
        assert rate > 5_000

    def test_encode_validate_round_trip_throughput(self):
        n = 5_000
        rng = np.random.default_rng(0)
        rows = [
            pd.Series(
                {
                    "delta": int(d),
                    "theta": int(t),
                    "alpha": int(a),
                    "beta": int(b),
                }
            )
            for d, t, a, b in rng.integers(0, 65535, size=(n, 4))
        ]
        start = time.perf_counter()
        for row in rows:
            pkt = transmission.df_to_packet(row)
            transmission.validate_packet(pkt)
        elapsed = time.perf_counter() - start
        rate = n / elapsed
        print(f"[round-trip] {n} ops in {elapsed:.3f}s  →  {rate:,.0f} ops/s")
        assert rate > 2_000

    def test_all_10k_packets_are_valid(self):
        rng = np.random.default_rng(1)
        n = 10_000
        failures = 0
        for d, t, a, b in rng.integers(0, 65535, size=(n, 4)):
            row = pd.Series(
                {
                    "delta": int(d),
                    "theta": int(t),
                    "alpha": int(a),
                    "beta": int(b),
                }
            )
            pkt = transmission.df_to_packet(row)
            if not transmission.validate_packet(pkt):
                failures += 1
        assert failures == 0, f"{failures}/{n} packets failed CRC validation"
