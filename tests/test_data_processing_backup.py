import sys
import os
import unittest
import pandas as pd
import numpy as np

# Allow import from src directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import data_processing


class TestDataProcessing(unittest.TestCase):

    #  get_data() 

    def test_get_data_valid(self):
        path = data_processing.get_data("test.csv")
        self.assertTrue(path.endswith("test.csv"))

    def test_get_data_empty_string(self):
        path = data_processing.get_data("")
        self.assertIsInstance(path, str)

    #  get_stats() 

    def test_get_stats_valid(self):
        fake_data = pd.DataFrame({
            "delta": [1, 2, 3],
            "theta": [2, 3, 4],
            "alpha": [3, 4, 5],
            "beta": [4, 5, 6]
        })

        stats = data_processing.get_stats(fake_data)
        self.assertIsInstance(stats, dict)
        self.assertIn("mean", stats)
        self.assertIn("median", stats)
        self.assertIn("mode", stats)
        self.assertIn("range", stats)
        self.assertIn("variance", stats)
        self.assertIn("std_dev", stats)
        self.assertIn("iqr", stats)

    def test_get_stats_empty(self):
        empty_df = pd.DataFrame(columns=["delta", "theta", "alpha", "beta"])
        stats = data_processing.get_stats(empty_df)
        self.assertIsNone(stats)

    def test_get_stats_invalid_input(self):
        with self.assertRaises(TypeError):
            data_processing.get_stats("not a dataframe")


if __name__ == '__main__':
    unittest.main()