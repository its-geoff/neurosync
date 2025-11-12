import os
import numpy as np
import pandas as pd
from tabulate import tabulate
from scipy.fft import fft, fftfreq
import matplotlib

"""
[x] extract data from csv
[x] print data from four channels and combine data
[x] convert from mV to Hz
[ ] split data based on wave frequency
[ ] put each frequency into separate data structure
[ ] run preliminary tests on each frequency, checking for min, max, and variance
[x] create alternative output format that is human readable (ex: table)
[ ] output data structures in desired output format

Gamma - >32 Hz (Not needed for emotions; filter out)
----------------
Beta - 13-32 Hz
Alpha - 8-13 Hz
Theta - 4-8 Hz
Delta - 0.5-4 Hz

Notes:
    - keep rows intact to show emotional state at a point in time
    - channels do matter; frontal channels more important in emotional detection
    - don't remove or combine channels arbitrarily
"""

# global variables
folder_name = os.path.abspath("..\data")

def get_data(file_name):
    """
    Extracts file from data folder for processing. Ensures compatibility across platforms.

    Arguments:
        file_name (String): The full file name of the file to be processed.

    Returns:
        String: The platform-specific path to the file.
    """
    path = os.path.join(folder_name, file_name)
    return path

def transform_to_hz(data):
    """
    Converts EEG input in mV to frequency in Hz.

    Arguments:
        data (pandas DataFrame): The CSV file data in mV to be converted to Hz.
    
    Returns:

    """
    samp_rate = 256             # sampling rate of Muse 2 headband
    n = len(data)               # number of tests
    channels = data.columns     # get column headers

    # FFT for all channels
    fft_data = {}               # dictionary to hold FFT values

    for ch in channels:
        signal = data[ch].to_numpy()
        fft_out = fft(signal)
        fft_data[ch] = np.abs(fft_out[:n // 2])   # take positive output and only consider first half since second half is negative
    
    freqs = fftfreq(n, 1 / samp_rate)[:n // 2]           # convert FFT values to usable frequencies
    fft_data['freq'] = freqs
    fft_df = pd.DataFrame(fft_data)
    path = os.path.join(folder_name, "processed.csv")
    fft_df.to_csv(path, index=False)

    return fft_df

def main():
    # change to get_data(file) later with file being an arg in main
    file_path = get_data("muse2_eeg_data.csv");  # path to data file

    # check file existence
    if not os.path.exists(file_path):
        print(f"file does not exist at: {file_path}")
        return

    # prints first five rows of readings, split by channel; sanity check
    df = pd.read_csv(file_path)  # CSV reading to pandas DataFrame
    df_channels = df[["ch1", "ch2", "ch3", "ch4"]]
    print(tabulate(df_channels.head(), headers='keys', tablefmt='grid', showindex=False))
    transform_to_hz(df_channels)

    print(tabulate(transform_to_hz(df_channels).head(), headers='keys', tablefmt='grid', showindex=False))

if __name__ == '__main__':
    main()