"""test_fft_pipeline_integration.py

Integration tests for the FFT → stats pipeline.
"""

import unittest.mock as mock

import numpy as np
import pandas as pd

import data_processing


def make_raw_eeg(n_samples=256, seed=42):
    rng = np.random.default_rng(seed)
    timestamps = np.arange(n_samples, dtype=float)
    channels = rng.uniform(-100, 100, size=(n_samples, 4))
    return pd.DataFrame(
        np.hstack([timestamps.reshape(-1, 1), channels]),
        columns=["timestamp", "ch1", "ch2", "ch3", "ch4"],
    )


class TestFFTPipelineIntegration:

    def test_transform_then_stats_shape_agreement(self):
        df = make_raw_eeg(256)
        freq_df = data_processing.transform_to_hz(df)
        assert not freq_df.empty

        numeric = freq_df.drop(columns=["timestamp"])
        stats = data_processing.get_stats(numeric)

        assert stats is not None
        for key in ["mean", "median", "std_dev", "variance", "iqr", "range"]:
            assert key in stats
            assert len(stats[key]) == 4

    def test_band_power_values_are_non_negative(self):
        df = make_raw_eeg(512)
        freq_df = data_processing.transform_to_hz(df)
        for band in ["beta", "alpha", "theta", "delta"]:
            assert (freq_df[band] >= 0).all(), f"{band} contains negatives"

    def test_multiple_windows_produce_monotone_timestamps(self):
        df = make_raw_eeg(512)
        freq_df = data_processing.transform_to_hz(df)
        timestamps = freq_df["timestamp"].values
        assert (np.diff(timestamps) > 0).all()

    def test_stats_mean_within_plausible_range(self):
        df = make_raw_eeg(256)
        freq_df = data_processing.transform_to_hz(df)
        numeric = freq_df.drop(columns=["timestamp"])
        stats = data_processing.get_stats(numeric)
        for band in ["beta", "alpha", "theta", "delta"]:
            assert np.isfinite(stats["mean"][band])
            assert stats["mean"][band] >= 0

    def test_process_pipeline_returns_expected_keys(self):
        df = make_raw_eeg(256)
        with mock.patch("data_processing.graphing.run"):
            result = data_processing.process_pipeline(df)
        assert "frequency_data" in result
        assert "stats" in result
        assert isinstance(result["frequency_data"], pd.DataFrame)
        assert isinstance(result["stats"], dict)

    def test_process_pipeline_frequency_data_has_band_columns(self):
        df = make_raw_eeg(256)
        with mock.patch("data_processing.graphing.run"):
            result = data_processing.process_pipeline(df)
        for band in ["beta", "alpha", "theta", "delta"]:
            assert band in result["frequency_data"].columns

    def test_larger_input_produces_more_windows(self):
        df_small = make_raw_eeg(256)
        df_large = make_raw_eeg(512)
        with mock.patch("data_processing.graphing.run"):
            r_small = data_processing.process_pipeline(df_small)
            r_large = data_processing.process_pipeline(df_large)
        assert len(r_large["frequency_data"]) > len(r_small["frequency_data"])
