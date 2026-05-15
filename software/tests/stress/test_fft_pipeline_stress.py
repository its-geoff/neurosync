"""test_fft_pipeline_stress.py

Stress tests for FFT pipeline throughput and latency.
"""

import time

import numpy as np
import pandas as pd

import data_processing


def make_raw_eeg(n_samples=256, seed=0):
    rng = np.random.default_rng(seed)
    ts = np.arange(n_samples, dtype=float)
    ch = rng.uniform(-100, 100, size=(n_samples, 4))
    return pd.DataFrame(
        np.hstack([ts.reshape(-1, 1), ch]),
        columns=["timestamp", "ch1", "ch2", "ch3", "ch4"],
    )


class TestFFTPipelineThroughput:

    def test_fft_on_256_samples_completes_under_500ms(self):
        df = make_raw_eeg(256)
        start = time.perf_counter()
        result = data_processing.transform_to_hz(df)
        elapsed = time.perf_counter() - start
        print(f"\n[fft 256] {elapsed*1000:.1f} ms")
        assert elapsed < 0.5
        assert not result.empty

    def test_fft_on_2048_samples_completes_under_2s(self):
        df = make_raw_eeg(2048)
        start = time.perf_counter()
        result = data_processing.transform_to_hz(df)
        elapsed = time.perf_counter() - start
        print(f"[fft 2048] {elapsed*1000:.1f} ms  ({len(result)} windows)")
        assert elapsed < 2.0

    def test_fft_throughput_runs_per_second(self):
        n_runs = 10
        df = make_raw_eeg(256)
        start = time.perf_counter()
        for _ in range(n_runs):
            data_processing.transform_to_hz(df)
        elapsed = time.perf_counter() - start
        rate = n_runs / elapsed
        print(
            f"[fft throughput] {rate:.1f} pipeline-runs/s over {n_runs} runs"
        )
        assert rate > 2.0

    def test_get_stats_on_1000_row_dataframe(self):
        rng = np.random.default_rng(2)
        df = pd.DataFrame(
            rng.uniform(0, 1000, size=(1000, 4)),
            columns=["beta", "alpha", "theta", "delta"],
        )
        start = time.perf_counter()
        result = data_processing.get_stats(df)
        elapsed = time.perf_counter() - start
        print(f"[stats 1000 rows] {elapsed*1000:.2f} ms")
        assert elapsed < 0.5
        assert result is not None
