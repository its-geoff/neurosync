"""test_windowing_stress.py

Stress tests for windowing and overlap buffer correctness under rapid calls.
"""

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


class TestWindowingUnderLoad:

    def test_50_consecutive_fft_calls_all_return_nonempty(self):
        df = make_raw_eeg(256)
        for i in range(50):
            result = data_processing.transform_to_hz(df)
            assert not result.empty, f"run {i} returned empty DataFrame"

    def test_overlap_buffer_produces_correct_window_count(self):
        rng = np.random.default_rng(3)
        total_samples = 1024
        window_size = 256
        step_size = 128
        buffer = []
        windows_processed = 0

        samples = rng.uniform(-100, 100, size=(total_samples, 5)).tolist()
        for sample in samples:
            buffer.append(sample[:5])
            if len(buffer) >= window_size:
                window_df = pd.DataFrame(
                    buffer[:window_size],
                    columns=["timestamp", "ch1", "ch2", "ch3", "ch4"],
                )
                data_processing.transform_to_hz(window_df)
                windows_processed += 1
                buffer = buffer[step_size:]

        expected_windows = (total_samples - window_size) // step_size + 1
        assert windows_processed == expected_windows

    def test_fft_is_deterministic_on_same_input(self):
        df = make_raw_eeg(256, seed=42)
        r1 = data_processing.transform_to_hz(df)
        r2 = data_processing.transform_to_hz(df)
        pd.testing.assert_frame_equal(r1, r2)
