"""test_fft_to_packet_integration.py

Integration tests verifying that FFT band power output can be encoded into
UART packets without data loss or struct errors.
"""

import struct
import unittest.mock as mock

import numpy as np
import pandas as pd

import data_processing
import transmission


def make_raw_eeg(n_samples=256, seed=42):
    rng = np.random.default_rng(seed)
    timestamps = np.arange(n_samples, dtype=float)
    channels = rng.uniform(-100, 100, size=(n_samples, 4))
    return pd.DataFrame(
        np.hstack([timestamps.reshape(-1, 1), channels]),
        columns=["timestamp", "ch1", "ch2", "ch3", "ch4"],
    )


class TestFFTToPacketIntegration:

    def test_fft_output_band_powers_fit_in_uint16(self):
        df = make_raw_eeg(256)
        freq_df = data_processing.transform_to_hz(df)
        for band in ["delta", "theta", "alpha", "beta"]:
            max_val = freq_df[band].max()
            assert max_val <= 65535, (
                f"{band} max={max_val:.2f} exceeds uint16 range. "
                "Normalization or scaling required before transmission."
            )

    def test_fft_row_encodes_to_valid_packet(self):
        df = make_raw_eeg(256)
        freq_df = data_processing.transform_to_hz(df)

        row = freq_df.iloc[0].copy()
        for band in ["delta", "theta", "alpha", "beta"]:
            row[band] = min(int(row[band]), 65535)

        packet = transmission.df_to_packet(row)
        assert len(packet) == 12
        assert transmission.validate_packet(packet)

    def test_pipeline_output_encodes_without_struct_error(self):
        df = make_raw_eeg(256)
        with mock.patch("data_processing.graphing.run"):
            result = data_processing.process_pipeline(df)

        freq_df = result["frequency_data"]
        errors = []
        for _, row in freq_df.iterrows():
            clamped = row.copy()
            for band in ["delta", "theta", "alpha", "beta"]:
                clamped[band] = min(int(clamped[band]), 65535)
            try:
                transmission.df_to_packet(clamped)
            except struct.error as e:
                errors.append(str(e))

        assert len(errors) == 0, f"Encoding errors: {errors}"
