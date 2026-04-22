"""test_packet_round_trip_integration.py

Integration tests for the packet encode → validate → decode round-trip.
"""

import unittest.mock as mock

import numpy as np
import pandas as pd

import transmission


def make_band_power_row(delta=1000, theta=2000, alpha=3000, beta=4000):
    return pd.Series(
        {"alpha": alpha, "beta": beta, "theta": theta, "delta": delta}
    )


def make_band_power_df(n_rows=4, seed=0):
    rng = np.random.default_rng(seed)
    data = rng.integers(0, 60000, size=(n_rows, 4))
    return pd.DataFrame(data, columns=["alpha", "beta", "theta", "delta"])


class TestPacketRoundTripIntegration:

    def test_round_trip_single_row(self):
        row = make_band_power_row(delta=100, theta=200, alpha=300, beta=400)
        packet = transmission.df_to_packet(row)
        assert transmission.validate_packet(packet)

        mock_ser = mock.MagicMock()
        mock_ser.read.return_value = packet
        recovered = transmission.packet_to_df(mock_ser)

        assert recovered is not None
        assert recovered["delta"] == 100
        assert recovered["theta"] == 200
        assert recovered["alpha"] == 300
        assert recovered["beta"] == 400

    def test_round_trip_boundary_values(self):
        for val in [0, 1, 127, 128, 255, 256, 32767, 32768, 65534, 65535]:
            row = make_band_power_row(
                delta=val, theta=val, alpha=val, beta=val
            )
            packet = transmission.df_to_packet(row)
            assert transmission.validate_packet(
                packet
            ), f"validate failed for val={val}"

            mock_ser = mock.MagicMock()
            mock_ser.read.return_value = packet
            recovered = transmission.packet_to_df(mock_ser)
            assert recovered is not None
            assert recovered["delta"] == val

    def test_round_trip_full_dataframe(self):
        df = make_band_power_df(n_rows=5)
        packets = [transmission.df_to_packet(row) for _, row in df.iterrows()]

        for i, (packet, (_, original_row)) in enumerate(
            zip(packets, df.iterrows())
        ):
            assert transmission.validate_packet(
                packet
            ), f"invalid packet at row {i}"
            mock_ser = mock.MagicMock()
            mock_ser.read.return_value = packet
            recovered = transmission.packet_to_df(mock_ser)
            assert recovered is not None
            assert recovered["delta"] == int(original_row["delta"])

    def test_bit_flip_in_payload_invalidates_packet(self):
        row = make_band_power_row()
        packet = bytearray(transmission.df_to_packet(row))
        packet[4] ^= 0x01
        assert not transmission.validate_packet(bytes(packet))

    def test_header_bytes_preserved_across_round_trip(self):
        row = make_band_power_row()
        packet = transmission.df_to_packet(row)
        assert packet[0] == transmission.SYNC_BYTE_1
        assert packet[1] == transmission.SYNC_BYTE_2
        assert packet[2] == transmission.PAYLOAD_LENGTH

    def test_packet_length_is_always_12(self):
        rng = np.random.default_rng(0)
        for vals in rng.integers(0, 65535, size=(20, 4)):
            row = make_band_power_row(*vals)
            assert len(transmission.df_to_packet(row)) == 12
