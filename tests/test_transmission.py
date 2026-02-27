import struct
import pytest
from unittest.mock import MagicMock, call, patch

import crcmod
import pandas as pd

from transmission import (PAYLOAD_LENGTH, SYNC_BYTE_1, SYNC_BYTE_2,
                          df_to_packet, packet_to_df, receive, transmit,
                          validate_packet)

# helper function with creation of mock packet

crc8 = crcmod.predefined.mkCrcFun("crc-8")

SAMPLE_ROW = {"delta": 41, "theta": 86, "alpha": 31, "beta": 12}


def build_valid_packet(delta=41, theta=86, alpha=31, beta=12) -> bytes:
    """Build a packet using the same logic as df_to_packet for use in tests."""
    header = bytes([SYNC_BYTE_1, SYNC_BYTE_2, PAYLOAD_LENGTH])
    payload = struct.pack("HHHH", delta, theta, alpha, beta)
    checksum = crc8(payload)
    return header + payload + bytes([checksum])


# test cases


class TestValidatePacket:
    def test_valid_packet_returns_true(self):
        header = bytes([SYNC_BYTE_1, SYNC_BYTE_2, PAYLOAD_LENGTH])
        payload = struct.pack("HHHH", 41, 86, 31, 12)
        checksum = crc8(payload)
        packet = header + payload + bytes([checksum])

        assert validate_packet(packet) is True

    def test_invalid_checksum_returns_false(self):
        header = bytes([SYNC_BYTE_1, SYNC_BYTE_2, PAYLOAD_LENGTH])
        payload = struct.pack("HHHH", 41, 86, 31, 12)
        checksum = crc8(payload)
        invalid_checksum = (checksum + 1) % 256
        packet = header + payload + bytes([invalid_checksum])

        assert validate_packet(packet) is False

    def test_invalid_payload_returns_false(self):
        header = bytes([SYNC_BYTE_1, SYNC_BYTE_2, PAYLOAD_LENGTH])
        payload = struct.pack("HHHH", 41, 86, 31, 12)
        invalid_payload = bytearray(payload)
        invalid_payload[0] ^= 0xFF
        checksum = crc8(payload)
        packet = header + invalid_payload + bytes([checksum])

        assert validate_packet(packet) is False

    def test_single_byte_payload_returns_true(self):
        header = bytes([SYNC_BYTE_1, SYNC_BYTE_2, PAYLOAD_LENGTH])
        payload = bytes([0x4A])
        checksum = crc8(payload)
        packet = header + payload + bytes([checksum])

        assert validate_packet(packet) is True

    def test_zero_payload_returns_true(self):
        header = bytes([SYNC_BYTE_1, SYNC_BYTE_2, PAYLOAD_LENGTH])
        payload = struct.pack("HHHH", 0, 0, 0, 0)
        checksum = crc8(payload)
        packet = header + payload + bytes([checksum])

        assert validate_packet(packet) is True

    def test_max_value_payload_returns_true(self):
        header = bytes([SYNC_BYTE_1, SYNC_BYTE_2, PAYLOAD_LENGTH])
        payload = struct.pack("HHHH", 65535, 65535, 65535, 65535)
        checksum = crc8(payload)
        packet = header + payload + bytes([checksum])

        assert validate_packet(packet) is True


class TestDfToPacket:
    def test_packet_length_equals_twelve(self):
        packet = df_to_packet(SAMPLE_ROW)

        # 3 header bytes + 8 payload bytes + 1 checksum byte = 12
        assert len(packet) == 12

    def test_header_bytes_contain_correct_values(self):
        packet = df_to_packet(SAMPLE_ROW)

        assert packet[0] == SYNC_BYTE_1
        assert packet[1] == SYNC_BYTE_2
        assert packet[2] == PAYLOAD_LENGTH

    def test_payload_encodes_correct_values(self):
        packet = df_to_packet(SAMPLE_ROW)
        payload = packet[3:-1]
        delta, theta, alpha, beta = struct.unpack("HHHH", payload)

        assert delta == SAMPLE_ROW["delta"]
        assert theta == SAMPLE_ROW["theta"]
        assert alpha == SAMPLE_ROW["alpha"]
        assert beta == SAMPLE_ROW["beta"]

    def test_checksum_comparison_is_accurate(self):
        packet = df_to_packet(SAMPLE_ROW)
        payload = packet[3:-1]

        assert packet[-1] == crc8(payload)

    def test_zero_payload_returns_true(self):
        row = {"delta": 0, "theta": 0, "alpha": 0, "beta": 0}
        packet = df_to_packet(row)

        assert len(packet) == 12
        assert validate_packet(packet) is True

    def test_max_value_payload_returns_true(self):
        row = {"delta": 65535, "theta": 65535, "alpha": 65535, "beta": 65535}
        packet = df_to_packet(row)

        assert len(packet) == 12
        assert validate_packet(packet) is True


class TestPacketToDf:
    def _mock_serial(self, data: bytes) -> MagicMock:
        """Create a mock serial connection and return the object."""
        mock_ser = MagicMock()
        mock_ser.read.return_value = data  # defines return value of mock.read

        return mock_ser

    def test_valid_packet_returns_correct_dataframe(self):
        packet = build_valid_packet()
        mock_ser = self._mock_serial(packet)

        result = packet_to_df(mock_ser)
        assert result == {"delta": 41, "theta": 86, "alpha": 31, "beta": 12}

    def test_invalid_checksum_returns_none(self):
        payload = struct.pack("HHHH", 41, 86, 31, 12)
        checksum = crc8(payload)
        invalid_checksum = (checksum + 1) % 256
        packet = payload + bytes([invalid_checksum])
        mock_ser = self._mock_serial(packet)

        result = packet_to_df(mock_ser)
        assert result is None

    def test_packet_length_equals_twelve(self):
        packet = build_valid_packet()
        mock_ser = self._mock_serial(packet)

        packet_to_df(mock_ser)
        mock_ser.read.assert_called_once_with(12)

class TestTransmit:
    def _convert_to_df(self, rows: dict) -> pd.DataFrame:
        """Convert a dictionary into a pandas DataFrame."""
        return pd.DataFrame(rows, columns=["delta", "theta", "alpha", "beta"])
    
    def _mock_serial(self, data: bytes) -> MagicMock:
        """Create a mock serial connection and return the object."""
        mock_ser = MagicMock()
        mock_ser.read.return_value = data  # defines return value of mock.read

        return mock_ser

    def test_zero_rows_calls_write_zero_times(self):
        packet = build_valid_packet()
        mock_ser = self._mock_serial(packet)
        df = self._convert_to_df([])
        transmit(df, mock_ser)

        mock_ser.write.assert_not_called()
    
    def test_one_row_calls_write_one_time(self):
        packet = build_valid_packet()
        mock_ser = self._mock_serial(packet)
        df = self._convert_to_df(
            [{"delta": 41, "theta": 86, "alpha": 31, "beta": 12}]
        )
        transmit(df, mock_ser)

        mock_ser.write.assert_called_once()
    
    def test_multiple_rows_calls_write_once_per_row(self):
        packet = build_valid_packet()
        mock_ser = self._mock_serial(packet)
        df = self._convert_to_df([
            {"delta": 41, "theta": 86, "alpha": 31, "beta": 12},
            {"delta": 22, "theta": 18, "alpha": 2, "beta": 61},
            {"delta": 61, "theta": 88, "alpha": 90, "beta": 5},
            {"delta": 26, "theta": 45, "alpha": 12, "beta": 2},
            {"delta": 8, "theta": 72, "alpha": 33, "beta": 15}
        ])
        transmit(df, mock_ser)

        mock_ser.write.call_count == 4

    def test_writes_correct_bytes(self):
        packet = build_valid_packet()
        mock_ser = self._mock_serial(packet)
        df = self._convert_to_df([
            {"delta": 41, "theta": 86, "alpha": 31, "beta": 12},
        ])
        transmit(df, mock_ser)

        expected_packet = df_to_packet(df.iloc[0])
        mock_ser.write.assert_called_once_with(expected_packet)

    def test_correct_data_order(self):
        packet = build_valid_packet()
        mock_ser = self._mock_serial(packet)
        rows = [
            {"delta": 41, "theta": 86, "alpha": 31, "beta": 12},
            {"delta": 22, "theta": 18, "alpha": 2, "beta": 61},
            {"delta": 61, "theta": 88, "alpha": 90, "beta": 5},
            {"delta": 26, "theta": 45, "alpha": 12, "beta": 2},
            {"delta": 8, "theta": 72, "alpha": 33, "beta": 15}
        ]
        df = self._convert_to_df(rows)
        transmit(df, mock_ser)

        expected_calls = [call(df_to_packet(x)) for x in rows]
        mock_ser.write.assert_has_calls(expected_calls, any_order=False)


class TestReceive:
    def _mock_serial(self, data: bytes) -> MagicMock:
        """Create a mock serial connection and return the object."""
        mock_ser = MagicMock()
        mock_ser.read.return_value = data  # defines return value of mock.read

        return mock_ser
    
    def test_receive_returns_df(self):
        packet = build_valid_packet()
        mock_ser = self._mock_serial(packet)
        result = receive(mock_ser, 1)

        assert isinstance(result, pd.DataFrame)

    def test_correct_columns(self):
        packet = build_valid_packet()
        mock_ser = self._mock_serial(packet)
        result = receive(mock_ser, 1)

        assert list(result.columns) == ["delta", "theta", "alpha", "beta"]

    def test_row_correct_values(self):
        packet = build_valid_packet()
        mock_ser = self._mock_serial(packet)
        result = receive(mock_ser, 1)

        assert result.iloc[0]["delta"] == 41
        assert result.iloc[0]["theta"] == 86
        assert result.iloc[0]["alpha"] == 31
        assert result.iloc[0]["beta"] == 12

    def test_multiple_row_df_returns_correct_length(self):
        packet = build_valid_packet()
        mock_ser = self._mock_serial(packet)
        result = receive(mock_ser, 3)

        assert len(result) == 3

    def test_read_called_once_per_expected_row(self):
        packet = build_valid_packet()
        mock_ser = self._mock_serial(packet)
        result = receive(mock_ser, 3)

        mock_ser.read.call_count == 3

    def test_zero_expected_rows_returns_empty_df(self):
        packet = build_valid_packet()
        mock_ser = self._mock_serial(packet)
        result = receive(mock_ser, 0)

        assert len(result) == 0
        mock_ser.read.assert_not_called()   # check that packet_to_df not called
    
    def test_invalid_packet_skipped(self):
        packet = bytearray(build_valid_packet())
        packet[-1] ^= 0xFF  # flip the checksum byte to make it invalid
        mock_ser = self._mock_serial(bytes(packet))
        result = receive(mock_ser, 1)
        assert len(result) == 0