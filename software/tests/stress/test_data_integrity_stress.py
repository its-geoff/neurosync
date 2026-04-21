"""test_data_integrity_stress.py

Stress tests for data integrity and determinism under large or repeated inputs.
"""

import numpy as np
import pandas as pd
import pytest

import data_processing
import transmission


def make_raw_eeg(n_samples=256, seed=0):
    rng = np.random.default_rng(seed)
    ts = np.arange(n_samples, dtype=float)
    ch = rng.uniform(-100, 100, size=(n_samples, 4))
    return pd.DataFrame(
        np.hstack([ts.reshape(-1, 1), ch]),
        columns=["timestamp", "ch1", "ch2", "ch3", "ch4"],
    )


def make_band_row(delta=1000, theta=2000, alpha=3000, beta=4000):
    return pd.Series({"delta": delta, "theta": theta, "alpha": alpha, "beta": beta})


class TestDataIntegrityUnderLoad:

    def test_fft_produces_finite_values_for_large_input(self):
        df = make_raw_eeg(2048)
        result = data_processing.transform_to_hz(df)
        for band in ["delta", "theta", "alpha", "beta"]:
            assert np.isfinite(result[band].values).all(), f"{band} contains inf/nan"

    def test_stats_are_stable_across_100_repeated_runs(self):
        df = make_raw_eeg(256)
        freq_df = data_processing.transform_to_hz(df)
        numeric = freq_df.drop(columns=["timestamp"])

        means = []
        for _ in range(100):
            stats = data_processing.get_stats(numeric)
            means.append(stats["mean"]["delta"])

        assert len(set(round(m, 10) for m in means)) == 1, "get_stats is non-deterministic"

    def test_no_crc_collisions_across_500_diverse_payloads(self):
        """Verify no two distinct payloads produce the same encoded packet.
        CRC-8 collisions are theoretically possible but should not appear
        in a random 500-sample draw.
        """
        rng = np.random.default_rng(99)
        n = 500
        seen = set()
        collisions = 0
        for d, t, a, b in rng.integers(0, 65535, size=(n, 4)):
            row = pd.Series({"delta": int(d), "theta": int(t), "alpha": int(a), "beta": int(b)})
            pkt = transmission.df_to_packet(row)
            if pkt in seen:
                collisions += 1
            seen.add(pkt)
        assert collisions == 0, f"{collisions} CRC collisions detected in {n} packets"
