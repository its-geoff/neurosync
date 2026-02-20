"""
transmission.py

Calculates the checksum for input data using the CRC8 algorithm. Converts from
pandas DataFrame to UART packet and vice versa.
"""
import crcmod
import struct
import serial

# global variables
crc8 = crcmod.predefined.mkCrcFun('crc-8')


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


def pack_row(row: dict) -> bytes:
    """Packs a row of EEG band power values to a UART packet.

    Arguments:
        row (dict): A dict of EEG band power values.

    Returns:
        bytes: A set of bytes in the form of a UART packet.
            Format: [delta(f32)][theta(f32)][alpha(f32)][beta(f32)][crc8]
    """
    payload = struct.pack('ffff', row['delta'], row['theta'], row['alpha'],
                          row['beta'])
    checksum = crc8(payload)

    return payload + bytes([checksum])


def unpack_packet(ser: serial.Serial) -> dict | None:
    """Unpacks a UART packet into EEG band power values.

    Arguments:
        packet (bytes): A set of bytes in the form of a UART packet.

    Returns:
        dict: A dict of EEG band power values.
    """
    packet_size = 17
    packet = ser.read(packet_size)

    # validate checksum
    if not validate_packet(packet):
        return None

    delta, theta, alpha, beta = struct.unpack('ffff', packet[:-1])
    return {'delta': delta, 'theta': theta, 'alpha': alpha, 'beta': beta}


def transmit():
    """Converts all EEG band power data to UART packets then transmits them
    to the UART.

    Arguments:
        TBD.

    Returns:
        TBD.
    """


def receive():
    """Receives all UART packets and converts them back to a pandas DataFrame.

    Arguments:
        TBD.

    Returns:
        TBD.
    """
