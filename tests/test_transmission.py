import struct
from unittest.mock import MagicMock, call, patch

import crcmod
import pandas as pd
import serial

import data_processing
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
    def test_valid_packet(self):
        payload = struct.pack("HHHH", 41, 86, 31, 12)
        checksum = crc8(payload)
        packet = payload + bytes([checksum])

        assert validate_packet(packet) is True

    def test_invalid_checksum(self):
        payload = struct.pack("HHHH", 41, 86, 31, 12)
        checksum = crc8(payload)
        invalid_checksum = (checksum + 1) % 256
        packet = payload + bytes([invalid_checksum])

        # False due to invalid checksum
        assert validate_packet(packet) is False

    def test_invalid_payload(self):
        payload = struct.pack("HHHH", 41, 86, 31, 12)
        invalid_payload = bytearray(payload)
        invalid_payload[0] ^= 0xFF
        checksum = crc8(payload)
        packet = bytes(invalid_payload) + bytes([checksum])

        # False due to invalid payload
        assert validate_packet(packet) is False

    def test_single_byte_payload(self):
        payload = bytes([0x4A])
        checksum = crc8(payload)
        packet = payload + bytes([checksum])

        assert validate_packet(packet) is True

    def test_zero_payload(self):
        payload = struct.pack("HHHH", 0, 0, 0, 0)
        checksum = crc8(payload)
        packet = payload + bytes([checksum])

        assert validate_packet(packet) is True

    def test_max_value_payload(self):
        payload = struct.pack("HHHH", 65535, 65535, 65535, 65535)
        checksum = crc8(payload)
        packet = payload + bytes([checksum])

        assert validate_packet(packet) is True


class TestDfToPacket:
    def test_packet_length(self):
        packet = df_to_packet(SAMPLE_ROW)

        # 3 header bytes + 8 payload bytes + 1 checksum byte = 12
        assert len(packet) == 12

    def test_header_bytes(self):
        packet = df_to_packet(SAMPLE_ROW)

        assert packet[0] == SYNC_BYTE_1
        assert packet[1] == SYNC_BYTE_2
        assert packet[2] == PAYLOAD_LENGTH

    def test_payload_encoding(self):
        packet = df_to_packet(SAMPLE_ROW)
        payload = packet[3:-1]
        delta, theta, alpha, beta = struct.unpack("HHHH", payload)

        assert delta == SAMPLE_ROW["delta"]
        assert theta == SAMPLE_ROW["theta"]
        assert alpha == SAMPLE_ROW["alpha"]
        assert beta == SAMPLE_ROW["beta"]

    def test_checksum_validity(self):
        packet = df_to_packet(SAMPLE_ROW)
        payload = packet[3:-1]

        # checksum checks payload values
        assert packet[-1] == crc8(payload)

    def test_zero_payload(self):
        row = {"delta": 0, "theta": 0, "alpha": 0, "beta": 0}
        packet = df_to_packet(row)

        assert len(packet) == 12
        assert validate_packet(packet[3:]) is True

    def test_max_value_payload(self):
        row = {"delta": 65535, "theta": 65535, "alpha": 65535, "beta": 65535}
        packet = df_to_packet(row)

        assert len(packet) == 12
        assert validate_packet(packet[3:]) is True
