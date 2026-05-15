"""test_graphing_buffer_integration.py

Integration tests for the LiveGrapher put/consume flow.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from graphing import BANDS, WINDOW_SIZE, LiveGrapher


@pytest.fixture
def mock_plt():
    with patch("graphing.plt") as m:
        mock_fig = MagicMock()
        mock_axes = [MagicMock() for _ in range(4)]
        for ax in mock_axes:
            ax.plot.return_value = (MagicMock(),)
        mock_fig.canvas.new_timer.return_value = MagicMock()
        m.subplots.return_value = (mock_fig, mock_axes)
        yield m


@pytest.fixture
def grapher(mock_plt):
    return LiveGrapher()


@pytest.fixture
def sample_df():
    n = 20
    return pd.DataFrame(
        {
            "timestamp": np.arange(n, dtype=float),
            "alpha": np.ones(n) * 10,
            "beta": np.ones(n) * 20,
            "theta": np.ones(n) * 30,
            "delta": np.ones(n) * 40,
        }
    )


@pytest.fixture
def large_df():
    n = WINDOW_SIZE + 30
    return pd.DataFrame(
        {
            "timestamp": np.arange(n, dtype=float),
            "alpha": np.random.uniform(0, 100, n),
            "beta": np.random.uniform(0, 100, n),
            "theta": np.random.uniform(0, 100, n),
            "delta": np.random.uniform(0, 100, n),
        }
    )


class TestGraphingBufferIntegration:

    def test_put_and_update_produce_correct_columns(self, grapher, sample_df):
        grapher.put(sample_df)
        grapher._update()
        assert set(grapher._history.columns) == {"timestamp"} | set(BANDS)

    def test_put_and_update_preserve_band_values(self, grapher, sample_df):
        expected = {"alpha": 10, "beta": 20, "theta": 30, "delta": 40}
        grapher.put(sample_df)
        grapher._update()
        for band, value in expected.items():
            assert (grapher._history[band] == value).all()

    def test_windowing_clips_history_to_window_size(self, grapher, large_df):
        grapher.put(large_df)
        grapher._update()
        assert len(grapher._history) <= WINDOW_SIZE

    def test_windowing_retains_most_recent_rows(self, grapher, large_df):
        grapher.put(large_df)
        grapher._update()
        actual = grapher._history.drop(columns=["timestamp"]).reset_index(
            drop=True
        )
        expected = (
            large_df.tail(WINDOW_SIZE)
            .drop(columns=["timestamp"])[actual.columns]
            .reset_index(drop=True)
        )
        pd.testing.assert_frame_equal(actual, expected)

    def test_multiple_puts_accumulate_in_history(self, grapher, sample_df):
        for i in range(3):
            grapher.put(sample_df.iloc[i : i + 1])
            grapher._update()
        assert len(grapher._history) == 3

    def test_queue_empty_after_update(self, grapher, sample_df):
        grapher.put(sample_df)
        grapher._update()
        assert grapher._queue.empty()

    def test_canvas_draw_called_after_update(self, grapher, sample_df):
        grapher.put(sample_df)
        grapher._update()
        grapher._fig.canvas.draw.assert_called()

    def test_reset_between_sessions_clears_history(self, grapher, sample_df):
        grapher.put(sample_df)
        grapher._update()
        grapher.reset()
        grapher.put(sample_df.iloc[0:1])
        grapher._update()
        assert len(grapher._history) == 1

    def test_timestamps_are_monotonic_across_puts(self, grapher, sample_df):
        grapher.put(sample_df.iloc[:5])
        grapher._update()
        first_end = grapher._history["timestamp"].iloc[-1]
        grapher.put(sample_df.iloc[:5])
        grapher._update()
        second_start = grapher._history["timestamp"].iloc[
            len(grapher._history) - 5
        ]
        assert second_start > first_end
