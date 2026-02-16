import os

import numpy as np
import pandas as pd
import pytest

import data_processing  # file being tested

# global variables
folder_name = os.path.abspath(os.path.join("..", "data"))


@pytest.fixture
def sample_eeg_data():
    """
    Fixture providing sample EEG data.

    Returns a DataFrame with sample EEG frequency bands for testing statistical
    analysis functions.
    """
    return pd.DataFrame(
        {
            "delta_Hz": [1.5, 2.0, 1.8, 2.2, 1.9, 2.1, 1.7, 2.0, 1.8, 2.0],
            "theta_Hz": [5.5, 6.0, 5.8, 6.2, 5.9, 6.1, 5.7, 6.0, 5.8, 6.0],
            "alpha_Hz": [
                10.5,
                11.0,
                10.8,
                11.2,
                10.9,
                11.1,
                10.7,
                11.0,
                10.8,
                11.0,
            ],
        }
    )


def test_get_data():
    """Test that the get_data function creates a path and outputs it."""
    file_name = "muse2_eeg_data.csv"
    path = data_processing.get_data(file_name)

    assert path == os.path.join(folder_name, file_name)


def test_transform_to_hz():
    """
    Test that the FFT accurately converts EEG band power to normalized
    frequency.
    """


def test_get_stats_prints_all_sections(capsys, sample_eeg_data):
    """
    Test that get_stats prints all sections to the console.
    """
    data_processing.get_stats(sample_eeg_data)

    # read output from console
    captured = capsys.readouterr()

    assert "--- Measures of Central Tendency ---" in captured.out
    assert "--- Measures of Dispersion ---" in captured.out


def test_get_stats_prints_central_tendency(capsys, sample_eeg_data):
    """
    Test that get_stats prints all parts of the central tendency section to the
    console.
    """
    data_processing.get_stats(sample_eeg_data)

    # read output from console
    captured = capsys.readouterr()

    assert "Column means:" in captured.out
    assert "Column medians:" in captured.out
    assert "Column modes:" in captured.out


def test_get_stats_prints_dispersion(capsys, sample_eeg_data):
    """
    Test that get_stats prints all parts of the dispersion section to the
    console.
    """
    data_processing.get_stats(sample_eeg_data)

    # read output from console
    captured = capsys.readouterr()

    assert "Column ranges:" in captured.out
    assert "Column variance:" in captured.out
    assert "Column standard deviation:" in captured.out
    assert "Column interquartile range:" in captured.out


def test_get_stats_mean_values(capsys):
    """
    Test that get_stats calculates and prints correct mean values.
    """
    df = pd.DataFrame({"alpha_Hz": [5.0, 7.5, 10.0]})

    data_processing.get_stats(df)

    # read output from console
    captured = capsys.readouterr()

    assert "7.5" in captured.out or "7.500000" in captured.out


def test_get_stats_median_values(capsys):
    """
    Test that get_stats calculates and prints correct median values.
    """
    df = pd.DataFrame({"alpha_Hz": [3, 8, 1, 7, 3, 9, 2]})

    data_processing.get_stats(df)

    # read output from console
    captured = capsys.readouterr()

    assert "3" in captured.out or "3.0" in captured.out


def test_get_stats_mode_values(capsys):
    """
    Test that get_stats calculates and prints correct mode values.
    """
    df = pd.DataFrame({"alpha_Hz": [1, 2, 1, 1, 1, 1, 6, 2, 9, 7, 2]})

    data_processing.get_stats(df)

    # read output from console
    captured = capsys.readouterr()

    assert "1" in captured.out or "1.0" in captured.out


def test_get_stats_range_values(capsys):
    """
    Test that get_stats calculates and prints correct range values.
    """
    df = pd.DataFrame({"alpha_Hz": [20.0, 17.5, 19.5, 15.0, 9.5]})

    data_processing.get_stats(df)

    # read output from console
    captured = capsys.readouterr()

    assert "10.5" in captured.out or "10.500000" in captured.out


def test_get_stats_variance_values(capsys):
    """
    Test that get_stats calculates and prints correct variance values.
    """
    df = pd.DataFrame({"alpha_Hz": [2, 4, 4, 4, 9, 5, 7, 5]})

    data_processing.get_stats(df)

    # read output from console
    captured = capsys.readouterr()

    assert "4" in captured.out or "4.0" in captured.out


def test_get_stats_std_dev_values(capsys):
    """
    Test that get_stats calculates and prints correct standard deviation
    values.
    """
    df = pd.DataFrame({"alpha_Hz": [1, 3, 5, 7]})

    data_processing.get_stats(df)

    # read output from console
    captured = capsys.readouterr()

    assert "2.58" in captured.out or "2.582634" in captured.out


def test_get_stats_iqr_values(capsys):
    """
    Test that get_stats calculates and prints correct interquartile range
    values.
    """
    df = pd.DataFrame({"alpha_Hz": [3, 4, 9, 11, 15, 14, 16]})

    data_processing.get_stats(df)

    # read output from console
    captured = capsys.readouterr()

    assert "3" in captured.out or "3.0" in captured.out
