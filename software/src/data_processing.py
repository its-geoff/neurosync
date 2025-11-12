import os
import pandas as pd
from tabulate import tabulate
from scipy.fft import fft
import matplotlib

"""
[x] extract data from csv
[x] print data from four channels and combine data
[ ] convert from mV to Hz
[ ] split data based on wave frequency
[ ] put each frequency into separate data structure
[ ] run preliminary tests on each frequency, checking for min, max, and variance
[x] create alternative output format that is human readable (ex: table)
[ ] output data structures in desired output format
"""

def get_data(file_name):
    """
    Extracts file from data folder for processing. Ensures compatibility across platforms.

    Arguments:
        file_name (String): The full file name of the file to be processed.

    Returns:
        String: The platform-specific path to the file.
    """
    folder_name = os.path.abspath("..\data")
    return os.path.join(folder_name, file_name)

def transform_to_hz(data):
    """
    Converts EEG input in mV to frequency in Hz.

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

    Arguments:
        data (pandas DataFrame): The CSV file data in mV to be converted to Hz.
    
    Returns:

    """

def main():
    # change to get_data(file) later with file being an arg in main
    file_path = get_data("muse2_eeg_data.csv");

    # check file existence
    if not os.path.exists(file_path):
        print(f"file does not exist at: {file_path}")
        return

    # prints first five rows of readings, split by channel; sanity check
    df = pd.read_csv(file_path)
    df_channels = df[["ch1", "ch2", "ch3", "ch4"]]
    print(tabulate(df_channels.head(), headers='keys', tablefmt='grid', showindex=False))



if __name__ == '__main__':
    main()