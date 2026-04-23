"""data_processing.py

Processes EEG data for Muse 2, including:
- Reading CSV
- FFT transformation
- Statistical calculations
"""

import os

import numpy as np
import pandas as pd
from scipy.fft import fft, fftfreq

import graphing

# global variables
FOLDER_NAME = os.path.abspath(os.path.join("..", "data"))


def get_data(file_name):
    """Extracts file from the data folder for processing. Ensures compatibility
    across platforms.

    Arguments:
        file_name (str): The full file name of the file to be processed.

    Returns:
        str: The platform-specific path to the file.

    """
    if not isinstance(file_name, str):
        raise TypeError("file_name must be a string")

    path = os.path.join(FOLDER_NAME, file_name)
    return path


def transform_to_hz(data: pd.DataFrame) -> pd.DataFrame:
    """Converts EEG band power features from time domain samples using FFT.

    Arguments:
        data (pd.DataFrame): The CSV file data in mV to be converted to Hz.

    Returns:
        pd.DataFrame: The output set of normalized frequencies after an FFT.
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")

    window_size = 256  # sampling rate of Muse 2 headband
    step_size = 128  # 50% overlap between windows
    columns = ["timestamp", "beta", "alpha", "theta", "delta"]
    signal_cols = ["ch1", "ch2", "ch3", "ch4"]
    fft_df = pd.DataFrame(columns=columns)  # define FFT DataFrame

    # FFT for all channels
    for start in range(0, len(data) - window_size + 1, step_size):
        window = data.iloc[start : start + window_size]
        signal_window = window[signal_cols].values
        fft_vals = (
            fft(signal_window, axis=0) / window_size
        )  # normalize by dividing by window size
        freqs = fftfreq(window_size, 1 / window_size)

        # compute bands; square for band power
        beta_band = np.sum(abs(fft_vals[(freqs >= 13) & (freqs < 32)]) ** 2)
        alpha_band = np.sum(abs(fft_vals[(freqs >= 8) & (freqs < 13)]) ** 2)
        theta_band = np.sum(abs(fft_vals[(freqs >= 4) & (freqs < 8)]) ** 2)
        delta_band = np.sum(abs(fft_vals[(freqs >= 0.5) & (freqs < 4)]) ** 2)

        new_row = pd.DataFrame(
            [
                {
                    "timestamp": data["timestamp"].iloc[start],
                    "beta": float(beta_band),
                    "alpha": float(alpha_band),
                    "theta": float(theta_band),
                    "delta": float(delta_band),
                }
            ],
            columns=columns,
        )

        # initialize DataFrame if empty, otherwise concatenate
        if fft_df.empty:
            fft_df = new_row
        elif not new_row.empty and not new_row.isna().all().all():
            fft_df = pd.concat([fft_df, new_row], ignore_index=True)

    return fft_df


def get_stats(data):
    """Returns statistical measures for a pandas DataFrame.

    Arguments:
        data (pd.DataFrame): Input DataFrame containing numeric columns.

    Returns:
        dict: Dictionary containing mean, median, mode, range, variance,
              standard deviation, and interquartile range of the columns.
              Returns None if DataFrame is empty.

    Raises:
        TypeError: If input is not a pandas DataFrame.
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")

    if data.empty:
        return None

    stats = {
        "mean": data.mean(),
        "median": data.median(),
        "mode": data.mode(),
        "range": data.max() - data.min(),
        "variance": data.var(),
        "std_dev": data.std(),
        "iqr": data.quantile(0.75) - data.quantile(0.25),
    }

    return stats


def process_pipeline(df: pd.DataFrame):
    """
    Full dynamic processing pipeline:
    raw EEG → FFT → stats
    """
    freq_data = transform_to_hz(df)
    stats_data = freq_data.drop(columns=["timestamp"], errors="ignore")
    stats = get_stats(stats_data)

    return {
        "frequency_data": freq_data,
        "stats": stats,
    }


def run():
    """Reads CSV EEG data, transforms it to frequency bands, prints sample
    data, and calculates statistics.

    Arguments:
        None.

    Returns:
        None.
    """
    file_path = get_data("muse2_eeg_data.csv")

    # check file existence
    if not os.path.exists(file_path):
        print(f"file does not exist at: {file_path}")
        return

    # prints first five rows of readings, split by channel; sanity check
    df = pd.read_csv(file_path)  # CSV reading to pandas DataFrame
    result = process_pipeline(df)

    print("\n--- STATS ---")
    for key, value in result["stats"].items():
        print(f"\n{key}:\n{value}")


if __name__ == "__main__":
    run()
