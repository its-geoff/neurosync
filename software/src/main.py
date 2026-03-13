import pandas as pd
import serial
from pylsl import StreamInlet, resolve_streams

import data_processing
import transmission


def connect_and_process(ser: serial.Serial) -> None:
    """Streams EEG data from the Muse 2 via LSL, computes band power features
    per window, and transmits each result over UART in real time.

    Arguments:
        ser (serial.Serial): Open UART serial connection to transmit on.

    Returns:
        None.
    """
    print("Resolving Muse 2 EEG stream...")
    streams = resolve_streams("type", "EEG")
    inlet = StreamInlet(streams[0])
    print("Stream acquired. Beginning transmission. Press Ctrl+C to stop.")

    buffer = []

    try:
        while True:
            sample, _ = inlet.pull_sample()
            buffer.append(sample[:4])

            if len(buffer) >= 256:  # window size
                window_df = pd.DataFrame(
                    buffer[:256], columns=["ch1", "ch2", "ch3", "ch4"]
                )
                band_power_df = data_processing.transform_to_hz(window_df)

                for _, row in band_power_df.iterrows():
                    packet = transmission.df_to_packet(row)
                    ser.write(packet)

                buffer = buffer[128:]  # 50% window overlap

    except KeyboardInterrupt:
        print("Stream interrupted. Closing.")


def main():
    # initializes serial and automatically cleans up after connection closed
    # NOTE: change port before running
    with serial.Serial(port="/dev/ttyUSB0", baudrate=115200, timeout=1) as ser:
        connect_and_process(ser)


if __name__ == "__main__":
    main()
