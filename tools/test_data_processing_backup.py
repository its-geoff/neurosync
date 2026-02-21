import sys
import os
import unittest
import pandas as pd
import numpy as np

# Allow import from src directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import data_processing


class TestDataProcessing(unittest.TestCase):

    # ---------- get_data() ----------

    def test_get_data_valid(self):
        path = data_processing.get_data("test.csv")
        self.assertTrue(path.endswith("test.csv"))

    def test_get_data_empty_string(self):
        path = data_processing.get_data("")
        self.assertIsInstance(path, str)

    # ---------- transform_to_hz() ----------

    def test_transform_to_hz_valid(self):
        # Create fake EEG data (256 rows, 4 channels)
        fake_data = pd.DataFrame(
            np.random.rand(256, 4),
            columns=["ch1", "ch2", "ch3", "ch4"]
        )

        result = data_processing.transform_to_hz(fake_data)

        self.assertIsInstance(result, pd.DataFrame)
        self.assertListEqual(
            list(result.columns),
            ["delta", "theta", "alpha", "beta"]
        )

    def test_transform_to_hz_small_input(self):
        # Less than 256 rows → should return empty DataFrame
        small_data = pd.DataFrame(
            np.random.rand(100, 4),
            columns=["ch1", "ch2", "ch3", "ch4"]
        )

        result = data_processing.transform_to_hz(small_data)
        self.assertTrue(result.empty)

    def test_transform_to_hz_invalid_input(self):
        with self.assertRaises(Exception):
            data_processing.transform_to_hz("not a dataframe")

    # ---------- get_stats() ----------

    def test_get_stats_valid(self):
        fake_data = pd.DataFrame({
            "delta": [1, 2, 3],
            "theta": [2, 3, 4],
            "alpha": [3, 4, 5],
            "beta": [4, 5, 6]
        })

        # Check it returns a dictionary with expected keys
        result = data_processing.get_stats(fake_data)
        self.assertIsInstance(result, dict)
        self.assertIn("mean", result)
        self.assertIn("median", result)
        self.assertIn("mode", result)
        self.assertIn("range", result)
        self.assertIn("variance", result)
        self.assertIn("std_dev", result)
        self.assertIn("iqr", result)

    def test_get_stats_empty(self):
        empty_df = pd.DataFrame(columns=["delta", "theta", "alpha", "beta"])
        result = data_processing.get_stats(empty_df)
        self.assertIsNone(result)

    def test_get_stats_invalid_input(self):
        with self.assertRaises(TypeError):
            data_processing.get_stats("not a dataframe")


if __name__ == '__main__':
    unittest.main()