import os

import numpy as np
import pandas as pd
from scipy.fft import fft, fftfreq
from tabulate import tabulate

# global variables
FOLDER_NAME = os.path.abspath(os.path.join("..", "data"))


# --
# get_data
# Original version is commented nehehehe
# def get_data(file_name):
#     Extracts file from data folder for processing. Ensures compatibility
#     across platforms.
#
#     Arguments:
#         file_name (String): The full file name of the file to be processed.
#
#     Returns:
#         String: The platform-specific path to the file.
#     original: path = os.path.join(folder_name, file_name)
#     return path
#     # 2/20/26 returns stats instead of printing
# --


# Updated version for tests & usage:
def get_data(file_name):
    """Extracts file from the data folder for processing. Ensures compatibility
    across platforms.

    Arguments:
        file_name (str): The full file name of the file to be processed.

    Returns:
        str: The platform-specific path to the file.

    Change note: 2/20/26 — uncommented and fixed indentation so that function
    works.
    """
    if not isinstance(file_name, str):
        raise TypeError("file_name must be a string")

    folder_name = "data"
    path = os.path.join(folder_name, file_name)
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
    # 2/20/26 added input check to make sure it only runs on a pandas DataFrame
    window_size = 256  # sampling rate of Muse 2 headband
    step_size = 128  # 50% overlap between windows
    columns = ["delta", "theta", "alpha", "beta"]  # FFT DataFrame columns
    fft_df = pd.DataFrame(columns=columns)  # define FFT DataFrame

    # FFT for all channels
    for start in range(0, len(data) - window_size + 1, step_size):
        window = data[start : start + window_size]
        fft_vals = (
            fft(window, axis=0) / window_size
        )  # normalize by dividing by window size
        freqs = fftfreq(window_size, 1 / window_size)

        # compute bands; square for band power
        delta_band = np.sum(abs(fft_vals[(freqs >= 0.5) & (freqs < 4)]) ** 2)
        theta_band = np.sum(abs(fft_vals[(freqs >= 4) & (freqs < 8)]) ** 2)
        alpha_band = np.sum(abs(fft_vals[(freqs >= 8) & (freqs < 13)]) ** 2)
        beta_band = np.sum(abs(fft_vals[(freqs >= 13) & (freqs < 32)]) ** 2)

        new_row = pd.DataFrame(
            [
                {
                    "delta": float(delta_band),
                    "theta": float(theta_band),
                    "alpha": float(alpha_band),
                    "beta": float(beta_band),
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


# --
# get_stats
# Returns statistical measures for a pandas DataFrame.
# --
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


def run():
    # change to get_data(file) later with file being an arg in main
    file_path = get_data("muse2_eeg_data.csv")
    # path to data file

    # check file existence
    if not os.path.exists(file_path):
        print(f"file does not exist at: {file_path}")
        return

    # prints first five rows of readings, split by channel; sanity check
    df = pd.read_csv(file_path)  # CSV reading to pandas DataFrame
    df_channels = df[["ch1", "ch2", "ch3", "ch4"]]
    print(
        tabulate(
            df_channels.head(),
            headers="keys",
            tablefmt="grid",
            showindex=False,
        )
    )
    data = transform_to_hz(df_channels)

    print(
        tabulate(data.head(), headers="keys", tablefmt="grid", showindex=False)
    )
    get_stats(data)


if __name__ == "__main__":
    run()
