import sys
import os
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import data_processing


class TestGetData(unittest.TestCase):

    def test_get_data_valid(self):
        path = data_processing.get_data("test.csv")
        self.assertTrue(path.endswith("test.csv"))

    def test_get_data_empty_string(self):
        path = data_processing.get_data("")
        self.assertIsInstance(path, str)

    def test_get_data_invalid_type(self):
        with self.assertRaises(TypeError):
            data_processing.get_data(None)


if __name__ == '__main__':
    unittest.main()