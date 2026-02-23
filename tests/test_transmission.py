import struct
from unittest.mock import MagicMock, patch, call

import crcmod
import pandas as pd
import serial

import data_processing
from transmission import (
    PAYLOAD_LENGTH,
    SYNC_BYTE_1,
    SYNC_BYTE_2,
    df_to_packet,
    packet_to_df,
    receive,
    transmit,
    validate_packet,
)

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
        payload = struct.pack("HHHH", 41, 86, 31, 12)
        checksum = crc8(payload)
        packet = payload + bytes([checksum])

        assert validate_packet(packet) is True

    def test_invalid_checksum_returns_false(self):
        payload = struct.pack("HHHH", 41, 86, 31, 12)
        checksum = crc8(payload)
        invalid_checksum = (checksum + 1) % 256
        packet = payload + bytes([invalid_checksum])

        # False due to invalid checksum
        assert validate_packet(packet) is False

    def test_invalid_payload_returns_false(self):
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