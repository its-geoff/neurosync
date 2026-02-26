import os
import sys

import numpy as np
import pandas as pd
import pytest

# Allow import from src directory
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

import data_processing

# get_data()


def test_get_data_valid():
    path = data_processing.get_data("test.csv")
    assert path.endswith("test.csv")


def test_get_data_empty_string():
    path = data_processing.get_data("")
    assert isinstance(path, str)


# transform_to_hz()


def test_transform_to_hz_valid():
    # Create fake EEG data (256 rows, 4 channels)
    fake_data = pd.DataFrame(
        np.random.rand(256, 4), columns=["ch1", "ch2", "ch3", "ch4"]
    )

    result = data_processing.transform_to_hz(fake_data)

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["delta", "theta", "alpha", "beta"]


def test_transform_to_hz_small_input():
    # Less than 256 rows → should return empty DataFrame
    small_data = pd.DataFrame(
        np.random.rand(100, 4), columns=["ch1", "ch2", "ch3", "ch4"]
    )

    result = data_processing.transform_to_hz(small_data)
    assert result.empty


def test_transform_to_hz_invalid_input():
    with pytest.raises(Exception):
        data_processing.transform_to_hz("not a dataframe")


# get_stats()


def test_get_stats_valid():
    fake_data = pd.DataFrame(
        {
            "delta": [1, 2, 3],
            "theta": [2, 3, 4],
            "alpha": [3, 4, 5],
            "beta": [4, 5, 6],
        }
    )

    result = data_processing.get_stats(fake_data)
    assert isinstance(result, dict)
    expected_keys = [
        "mean",
        "median",
        "mode",
        "range",
        "variance",
        "std_dev",
        "iqr",
    ]
    for key in expected_keys:
        assert key in result


def test_get_stats_empty():
    empty_df = pd.DataFrame(columns=["delta", "theta", "alpha", "beta"])
    result = data_processing.get_stats(empty_df)
    assert result is None


def test_get_stats_invalid_input():
    with pytest.raises(TypeError):
        data_processing.get_stats("not a dataframe")
