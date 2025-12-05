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
[x] calculate band power and add to new df
[x] normalize band power
[x] add function for stats tests on each band, checking for min, max, variance, etc.
[x] create alternative output format that is human readable (ex: table)
[ ] output data structures in desired output format

Gamma - >32 Hz (Not needed for emotions; filter out)
----------------
Beta - 13-32 Hz
Alpha - 8-13 Hz
Theta - 4-8 Hz
Delta - 0.5-4 Hz

Notes:
    - identify frequency of band powers in relation to total -> is this a way we can identify emotions?
    - compare this to control (neutral) brainwaves and other distinct emotional brainwaves (use existing dataset)
    - figure out conversion to UART (8 bit individual integers)
"""

# global variables
folder_name = os.path.abspath(os.path.join("..", "data"))

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
    Converts EEG output in mV to frequency in Hz.

    Arguments:
        data (pandas DataFrame): The CSV file data in mV to be converted to Hz.
    
    Returns:
        DataFrame: The output set of normalized frequencies after an FFT.
    """
    window_size = 256                                   # sampling rate of Muse 2 headband
    step_size = 128                                     # 50% overlap between windows
    columns = ['delta', 'theta', 'alpha', 'beta']       # FFT DataFrame columns
    fft_df = pd.DataFrame(columns=columns)              # define FFT DataFrame

    # FFT for all channels
    for start in range(0, len(data) - window_size, step_size):
        window = data[start:start + window_size]
        fft_vals = fft(window, axis=0) / window_size        # normalize by dividing by window size
        freqs = fftfreq(window_size, 1 / window_size)
    
        # compute bands; square for band power
        delta_band = np.sum(abs(fft_vals[(freqs >= 0.5) & (freqs < 4)]) ** 2)
        theta_band = np.sum(abs(fft_vals[(freqs >= 4) & (freqs < 8)]) ** 2)
        alpha_band = np.sum(abs(fft_vals[(freqs >= 8) & (freqs < 13)]) ** 2)
        beta_band = np.sum(abs(fft_vals[(freqs >= 13) & (freqs < 32)]) ** 2)

        new_row = pd.DataFrame([{
            'delta': float(delta_band), 
            'theta': float(theta_band), 
            'alpha': float(alpha_band), 
            'beta': float(beta_band)}], 
            columns=columns)

        # initialize DataFrame if empty, otherwise concatenate
        if fft_df.empty:
            fft_df = new_row
        elif not new_row.empty and not new_row.isna().all().all():
            fft_df = pd.concat([fft_df, new_row], ignore_index=True)
    
    path = os.path.join(folder_name, "processed.csv")
    fft_df.to_csv(path, index=False)

    return fft_df

def get_stats(data):
    """
    Gets measures of central tendency and measures of dispersion for a set of data.

    Arguments:
        data (pandas DataFrame): The post-FFT data in Hz to be analyzed.
    
    Returns:
        None.
    """
    # measures of central tendency
    mean = data.mean()
    median = data.median()
    mode = data.mode()

    # measures of dispersion
    rnge = data.max() - data.min()
    variance = data.var()
    std_dev = data.std()
    iqr = data.quantile(0.75) - data.quantile(0.25)
    

    # output
    print("\n--- Measures of Central Tendency ---\n")
    print(f"Column means:\n{mean.to_string()}\n")
    print(f"Column medians:\n{median.to_string()}\n")
    print(f"Column modes:\n{mode.to_string()}\n")
    print("\n--- Measures of Dispersion ---\n")
    print(f"Column ranges:\n{rnge.to_string()}\n")
    print(f"Column variance:\n{variance.to_string()}\n")
    print(f"Column standard deviation:\n{std_dev.to_string()}\n")
    print(f"Column interquartile range:\n{iqr.to_string()}\n")

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
    data = transform_to_hz(df_channels)

    print(tabulate(data.head(), headers='keys', tablefmt='grid', showindex=False))
    get_stats(data)

if __name__ == '__main__':
    main()