"""test_csv_pipeline_integration.py

Integration tests for the CSV file → read → process pipeline.
"""

import os
import unittest.mock as mock

import numpy as np
import pandas as pd

import data_processing


class TestCSVFilePipelineIntegration:

    def _write_temp_csv(self, n_rows, dir_path, seed=0):
        rng = np.random.default_rng(seed)
        df = pd.DataFrame(
            {
                "timestamp": np.arange(n_rows, dtype=float),
                "ch1": rng.uniform(-50, 50, n_rows),
                "ch2": rng.uniform(-50, 50, n_rows),
                "ch3": rng.uniform(-50, 50, n_rows),
                "ch4": rng.uniform(-50, 50, n_rows),
            }
        )
        path = os.path.join(dir_path, "test_eeg.csv")
        df.to_csv(path, index=False)
        return path

    def test_temp_csv_loads_and_pipelines_correctly(self, tmp_path):
        csv_path = self._write_temp_csv(256, str(tmp_path))
        df = pd.read_csv(csv_path)
        assert len(df) == 256
        assert list(df.columns) == ["timestamp", "ch1", "ch2", "ch3", "ch4"]

        with mock.patch("data_processing.graphing.run"):
            result = data_processing.process_pipeline(df)

        assert result["frequency_data"] is not None
        assert not result["frequency_data"].empty

    def test_pipeline_on_256_rows_produces_one_window(self, tmp_path):
        rng = np.random.default_rng(1)
        df = pd.DataFrame(
            {
                "timestamp": np.arange(256, dtype=float),
                "ch1": rng.uniform(-50, 50, 256),
                "ch2": rng.uniform(-50, 50, 256),
                "ch3": rng.uniform(-50, 50, 256),
                "ch4": rng.uniform(-50, 50, 256),
            }
        )

        with mock.patch("data_processing.graphing.run"):
            result = data_processing.process_pipeline(df)

        assert len(result["frequency_data"]) == 1
