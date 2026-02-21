"""transmission.py.

Calculates the checksum for input data using the CRC8 algorithm. Converts from
pandas DataFrame to UART packet and vice versa.
"""

import struct

import crcmod
import pandas as pd
import serial

# global variables
crc8 = crcmod.predefined.mkCrcFun("crc-8")
SYNC_BYTE_1 = 0xAA
SYNC_BYTE_2 = 0x55
PAYLOAD_LENGTH = 8  # 4 bands * 2 bytes each


def validate_packet(packet: bytes) -> bool:
    """Returns True if the packet checksum is valid.

    Arguments:
        packet (bytes): Raw bytes where the last byte is the CRC-8 checksum.

    Returns:
        True if checksum is valid, False otherwise.
    """
    payload = packet[:-1]
    received_checksum = packet[-1]
    expected_checksum = crc8(payload)

    return received_checksum == expected_checksum


def df_to_packet(row: dict) -> bytes:
    """Packs a row of EEG band power values to a UART packet.

    Arguments:
        row (dict): A dict of EEG band power values.

    Returns:
        bytes: A set of bytes in the form of a UART packet.
            [header][delta(u16)][theta(u16)][alpha(u16)][beta(u16)][crc8]
    """
    # define header, payload, and checksum
    header = bytes([SYNC_BYTE_1, SYNC_BYTE_2, PAYLOAD_LENGTH])
    payload = struct.pack(
        "HHHH", row["delta"], row["theta"], row["alpha"], row["beta"]
    )
    checksum = crc8(payload)

    return header + payload + bytes([checksum])


def packet_to_df(ser: serial.Serial) -> dict | None:
    """Unpacks a UART packet into EEG band power values.

    Arguments:
        packet (bytes): A set of bytes in the form of a UART packet.

    Returns:
        dict: A dict of EEG band power values.
    """
    packet_size = 12
    packet = ser.read(packet_size)

    # validate checksum
    if not validate_packet(packet):
        return None

    delta, theta, alpha, beta = struct.unpack("ffff", packet[:-1])
    return {"delta": delta, "theta": theta, "alpha": alpha, "beta": beta}


def transmit(df: pd.DataFrame, ser: serial.Serial) -> None:
    """Converts all EEG band power data to UART packets then transmits them to
    the UART.

    Arguments:
        df (DataFrame): EEG power band data for the delta, theta, alpha, and
            beta bands.
        ser (Serial): Open UART serial connection to transmit on.

    Returns:
        None.
    """
    for _, row in df.iterrows():
        packet = df_to_packet(row)
        ser.write(packet)


def receive(ser: serial.Serial, expected_rows: int) -> pd.DataFrame:
    """Receives all UART packets and converts them back to a pandas DataFrame.

    Arguments:
        ser (Serial): Open UART serial connection to transmit on.
        expected_rows (int): Number of expected rows.

    Returns:
        DataFrame: EEG power band data for the delta, theta, alpha, and beta
            bands.
    """
    rows = []
    for _ in range(expected_rows):
        row = packet_to_df(ser)

        if row:
            rows.append(row)

        return pd.DataFrame(rows, columns=["delta", "theta", "alpha", "beta"])
