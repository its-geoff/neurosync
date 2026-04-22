"""main.py

Streams EEG data from Muse 2 via LSL, computes band power features per window,
and transmits each result over UART in real time.
"""

import os  # standard library

import pandas as pd  # third-party
import serial
from pylsl import StreamInlet, resolve_byprop

import data_processing  # local
import transmission
from graphing import LiveGrapher


def connect_and_process(ser: serial.Serial) -> None:
    """Streams EEG data from the Muse 2 via LSL, computes band power features
    per window, and transmits each result over UART in real time.

    Arguments:
        ser (serial.Serial): Open UART serial connection to transmit on.

    Returns:
        None.
    """
    print("Resolving Muse 2 EEG stream...")
    streams = resolve_byprop("type", "EEG")
    inlet = StreamInlet(streams[0])
    print("Stream acquired. Beginning transmission. Press Ctrl+C to stop.")

    grapher = LiveGrapher()

    buffer = []

    try:
        while True:
            sample, _ = inlet.pull_sample()
            if sample is None:
                continue
            buffer.append(sample[:5])

            if len(buffer) >= 256:
                window_df = pd.DataFrame(
                    buffer[:256],
                    columns=["timestamp", "ch1", "ch2", "ch3", "ch4"],
                )
                result = data_processing.process_pipeline(window_df)
                band_power_df = result["frequency_data"]
                transmission.transmit(band_power_df, ser)
                grapher.put(band_power_df)
                buffer = buffer[128:]

            grapher.pump()

    except KeyboardInterrupt:
        print("Stream interrupted. Closing.")
    finally:
        del inlet


def main():
    """Opens a UART serial connection and starts streaming and processing EEG
    data."""
    mode = input("Select mode (lsl / csv): ").strip().lower()

    if mode == "lsl":
        # NOTE: change port if needed for Windows (e.g., COM5)
        with serial.Serial(port="COM8", baudrate=115200, timeout=1) as ser:
            connect_and_process(ser)

    elif mode == "csv":
        file = input("Enter CSV file name (inside /data): ")

        path = data_processing.get_data(file)

        if not os.path.exists(path):
            print("File not found")
            return

        try:
            df = pd.read_csv(path)
        except IsADirectoryError:
            print("Invalid file name")
            return

        result = data_processing.process_pipeline(df)

        print("\n--- STATS ---")
        for key, value in result["stats"].items():
            print(f"\n{key}:\n{value}")

    else:
        print("Invalid mode")


if __name__ == "__main__":
    main()
