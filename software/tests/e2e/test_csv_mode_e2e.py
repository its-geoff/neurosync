"""test_csv_mode_e2e.py

End-to-end tests for the CSV mode user workflow in main.py.
"""

import os
import unittest.mock as mock

import numpy as np
import pandas as pd
import pytest

import main


def _write_temp_csv(n_rows, dir_path, seed=0):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "timestamp": np.arange(n_rows, dtype=float),
        "ch1": rng.uniform(-50, 50, n_rows),
        "ch2": rng.uniform(-50, 50, n_rows),
        "ch3": rng.uniform(-50, 50, n_rows),
        "ch4": rng.uniform(-50, 50, n_rows),
    })
    path = os.path.join(dir_path, "test_eeg.csv")
    df.to_csv(path, index=False)
    return path


class TestCSVModeE2E:

    def test_valid_file_produces_stats_output(self, capsys, tmp_path):
        csv_path = _write_temp_csv(256, str(tmp_path))
        filename = os.path.basename(csv_path)

        with (
            mock.patch("data_processing.FOLDER_NAME", str(tmp_path)),
            mock.patch("data_processing.graphing.run"),
            mock.patch("builtins.input", side_effect=["csv", filename]),
        ):
            main.main()

        captured = capsys.readouterr()
        assert "STATS" in captured.out
        assert "mean" in captured.out

    def test_missing_file_prints_error(self, capsys, tmp_path):
        with (
            mock.patch("data_processing.FOLDER_NAME", str(tmp_path)),
            mock.patch("builtins.input", side_effect=["csv", "nonexistent.csv"]),
        ):
            main.main()

        captured = capsys.readouterr()
        assert "not found" in captured.out.lower() or "invalid" in captured.out.lower()

    def test_all_stat_keys_appear_in_output(self, capsys, tmp_path):
        csv_path = _write_temp_csv(256, str(tmp_path))
        filename = os.path.basename(csv_path)
        expected_keys = ["mean", "median", "std_dev", "variance", "iqr", "range"]

        with (
            mock.patch("data_processing.FOLDER_NAME", str(tmp_path)),
            mock.patch("data_processing.graphing.run"),
            mock.patch("builtins.input", side_effect=["csv", filename]),
        ):
            main.main()

        captured = capsys.readouterr()
        for key in expected_keys:
            assert key in captured.out, f"'{key}' missing from output"

    def test_512_rows_processes_multiple_windows(self, tmp_path):
        csv_path = _write_temp_csv(512, str(tmp_path))
        df = pd.read_csv(csv_path)

        with mock.patch("data_processing.graphing.run"):
            result = data_processing.process_pipeline(df)

        assert len(result["frequency_data"]) > 1

    def test_invalid_mode_prints_error(self, capsys):
        with mock.patch("builtins.input", side_effect=["badmode"]):
            main.main()
        captured = capsys.readouterr()
        assert "invalid" in captured.out.lower()


import data_processing
