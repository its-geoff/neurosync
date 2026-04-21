"""test_transmit_receive_integration.py

Integration tests for transmission.transmit and transmission.receive working
together over a mock serial connection.
"""

import unittest.mock as mock

import numpy as np
import pandas as pd

import transmission


def make_band_power_row(delta=1000, theta=2000, alpha=3000, beta=4000):
    return pd.Series(
        {"delta": delta, "theta": theta, "alpha": alpha, "beta": beta}
    )


def make_band_power_df(n_rows=4, seed=0):
    rng = np.random.default_rng(seed)
    data = rng.integers(0, 60000, size=(n_rows, 4))
    return pd.DataFrame(data, columns=["delta", "theta", "alpha", "beta"])


class TestTransmitReceiveIntegration:

    def test_transmit_then_receive_single_row(self):
        df = make_band_power_df(n_rows=1)
        expected_packet = transmission.df_to_packet(df.iloc[0])

        written = []
        mock_ser = mock.MagicMock()
        mock_ser.write.side_effect = lambda p: written.append(p)
        transmission.transmit(df, mock_ser)

        assert len(written) == 1
        assert written[0] == expected_packet

    def test_transmit_produces_valid_packets_for_all_rows(self):
        df = make_band_power_df(n_rows=10)
        written = []
        mock_ser = mock.MagicMock()
        mock_ser.write.side_effect = lambda p: written.append(p)
        transmission.transmit(df, mock_ser)

        assert len(written) == 10
        for packet in written:
            assert transmission.validate_packet(packet)

    def test_receive_reconstructs_all_rows(self):
        df = make_band_power_df(n_rows=3)
        packets = [transmission.df_to_packet(row) for _, row in df.iterrows()]

        mock_ser = mock.MagicMock()
        mock_ser.read.side_effect = packets
        result = transmission.receive(mock_ser, 3)

        assert len(result) == 3
        for i, (_, original) in enumerate(df.iterrows()):
            assert result.iloc[i]["delta"] == int(original["delta"])

    def test_receive_skips_corrupted_packets(self):
        good = transmission.df_to_packet(
            make_band_power_row(100, 200, 300, 400)
        )
        bad = bytearray(good)
        bad[-1] ^= 0xFF

        mock_ser = mock.MagicMock()
        mock_ser.read.side_effect = [bytes(bad), good]
        result = transmission.receive(mock_ser, 2)

        assert len(result) == 1
        assert result.iloc[0]["delta"] == 100
