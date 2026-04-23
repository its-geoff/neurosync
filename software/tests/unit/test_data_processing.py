import numpy as np
import pandas as pd
import pytest

from data_processing import get_data, get_stats, transform_to_hz

# get_data()
# Unit tests for the data_processing module.
# These tests validate:
# - get_data(): file path resolution
# - transform_to_hz(): conversion of raw EEG signals into frequency bands
# - get_stats(): statistical analysis of EEG frequency band data


def test_get_data_valid():
    path = get_data("test.csv")
    assert path.endswith("test.csv")


def test_get_data_empty_string():
    path = get_data("")
    assert isinstance(path, str)


# transform_to_hz()


def test_transform_to_hz_valid():
    # Create fake EEG data (256 rows, 4 channels)
    fake_data = pd.DataFrame(
        {
            "timestamp": np.arange(256, dtype=float),
            "ch1": np.random.rand(256),
            "ch2": np.random.rand(256),
            "ch3": np.random.rand(256),
            "ch4": np.random.rand(256),
        }
    )

    result = transform_to_hz(fake_data)

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == [
        "timestamp",
        "alpha",
        "beta",
        "theta",
        "delta",
    ]


def test_transform_to_hz_small_input():
    # Less than 256 rows → should return empty DataFrame
    small_data = pd.DataFrame(
        {
            "timestamp": np.arange(100, dtype=float),
            "ch1": np.random.rand(100),
            "ch2": np.random.rand(100),
            "ch3": np.random.rand(100),
            "ch4": np.random.rand(100),
        }
    )

    result = transform_to_hz(small_data)
    assert result.empty


def test_transform_to_hz_invalid_input():
    with pytest.raises(Exception):
        transform_to_hz("not a dataframe")


# get_stats()


def test_get_stats_valid():
    fake_data = pd.DataFrame(
        {
            "timestamp": [1, 2, 3],
            "delta": [1, 2, 3],
            "theta": [2, 3, 4],
            "alpha": [3, 4, 5],
            "beta": [4, 5, 6],
        }
    )

    result = get_stats(fake_data)
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
    empty_df = pd.DataFrame(columns=["beta", "alpha", "theta", "delta"])
    result = get_stats(empty_df)
    assert result is None


def test_get_stats_invalid_input():
    with pytest.raises(TypeError):
        get_stats("not a dataframe")
