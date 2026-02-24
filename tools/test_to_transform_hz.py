import sys
import os
import unittest
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import data_processing


class TestTransformToHz(unittest.TestCase):

    def test_valid_input(self):
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

    def test_small_input(self):
        small_data = pd.DataFrame(
            np.random.rand(100, 4),
            columns=["ch1", "ch2", "ch3", "ch4"]
        )

        result = data_processing.transform_to_hz(small_data)
        self.assertTrue(result.empty)

    def test_invalid_input(self):
        with self.assertRaises(Exception):
            data_processing.transform_to_hz("not a dataframe")


if __name__ == '__main__':
    unittest.main()