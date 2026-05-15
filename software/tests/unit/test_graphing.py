import queue
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

import graphing
from graphing import BANDS, WINDOW_SIZE


@pytest.fixture
def sample_df():
    n = 10
    return pd.DataFrame(
        {
            "timestamp": np.arange(n, dtype=float),
            "delta": np.ones(n),
            "theta": np.ones(n) * 2,
            "alpha": np.ones(n) * 3,
            "beta": np.ones(n) * 4,
        }
    )


@pytest.fixture
def large_df():
    n = WINDOW_SIZE + 20
    return pd.DataFrame(
        {
            "timestamp": np.arange(n, dtype=float),
            "delta": np.random.uniform(0, 1, n),
            "theta": np.random.uniform(0, 1, n),
            "alpha": np.random.uniform(0, 1, n),
            "beta": np.random.uniform(0, 1, n),
        }
    )


@pytest.fixture
def mock_grapher():
    with patch("graphing.plt") as mock_plt:
        mock_fig = MagicMock()
        mock_axes = [MagicMock() for _ in range(4)]
        for ax in mock_axes:
            ax.plot.return_value = (MagicMock(),)
        mock_plt.subplots.return_value = (mock_fig, mock_axes)
        mock_fig.canvas.new_timer.return_value = MagicMock()
        grapher = graphing.LiveGrapher()
        yield grapher


class TestConstants:
    def test_bands_contains_four_entries(self):
        assert len(BANDS) == 4

    def test_bands_expected_names(self):
        assert set(BANDS) == {"alpha", "beta", "theta", "delta"}

    def test_window_size_is_positive(self):
        assert WINDOW_SIZE > 0

    def test_window_size_is_int(self):
        assert isinstance(WINDOW_SIZE, int)


class TestLiveGrapherPut:
    def test_put_adds_frame_to_queue(self, mock_grapher, sample_df):
        mock_grapher.put(sample_df.iloc[0:1])
        assert not mock_grapher._queue.empty()

    def test_put_evicts_stale_frame(self, mock_grapher, sample_df):
        mock_grapher.put(sample_df.iloc[0:1])
        mock_grapher.put(sample_df.iloc[1:2])
        assert mock_grapher._queue.qsize() == 1

    def test_put_increments_sample_count(self, mock_grapher, sample_df):
        initial = mock_grapher._sample_count
        mock_grapher.put(sample_df.iloc[0:3])
        assert mock_grapher._sample_count == initial + 3

    def test_put_assigns_timestamp(self, mock_grapher, sample_df):
        mock_grapher.put(sample_df.iloc[0:1])
        frame = mock_grapher._queue.get_nowait()
        assert "timestamp" in frame.columns

    @pytest.mark.parametrize("band", BANDS)
    def test_put_preserves_band_columns(self, mock_grapher, sample_df, band):
        mock_grapher.put(sample_df.iloc[0:1])
        frame = mock_grapher._queue.get_nowait()
        assert band in frame.columns

    def test_put_empty_dataframe_increments_by_zero(self, mock_grapher):
        empty = pd.DataFrame(
            {
                "timestamp": [],
                "delta": [],
                "theta": [],
                "alpha": [],
                "beta": [],
            }
        )
        initial = mock_grapher._sample_count
        mock_grapher.put(empty)
        assert mock_grapher._sample_count == initial


class TestLiveGrapherUpdate:
    def test_update_consumes_frame_from_queue(self, mock_grapher, sample_df):
        mock_grapher.put(sample_df.iloc[0:1])
        mock_grapher._update()
        assert mock_grapher._queue.empty()

    def test_update_appends_to_history(self, mock_grapher, sample_df):
        mock_grapher.put(sample_df.iloc[0:1])
        mock_grapher._update()
        assert len(mock_grapher._history) == 1

    def test_update_clips_history_to_window_size(
        self, mock_grapher, sample_df
    ):
        large = pd.DataFrame(
            {
                "timestamp": np.arange(WINDOW_SIZE + 10, dtype=float),
                "delta": np.ones(WINDOW_SIZE + 10),
                "theta": np.ones(WINDOW_SIZE + 10),
                "alpha": np.ones(WINDOW_SIZE + 10),
                "beta": np.ones(WINDOW_SIZE + 10),
            }
        )
        mock_grapher.put(large)
        mock_grapher._update()
        assert len(mock_grapher._history) <= WINDOW_SIZE

    def test_update_on_empty_queue_does_not_raise(self, mock_grapher):
        mock_grapher._update()

    def test_update_calls_draw(self, mock_grapher, sample_df):
        mock_grapher.put(sample_df.iloc[0:1])
        mock_grapher._update()
        mock_grapher._fig.canvas.draw.assert_called()


class TestLiveGrapherReset:
    def test_reset_clears_history(self, mock_grapher, sample_df):
        mock_grapher.put(sample_df.iloc[0:1])
        mock_grapher._update()
        mock_grapher.reset()
        assert mock_grapher._history.empty

    def test_reset_zeroes_sample_count(self, mock_grapher, sample_df):
        mock_grapher.put(sample_df.iloc[0:3])
        mock_grapher.reset()
        assert mock_grapher._sample_count == 0


class TestLiveGrapherInit:
    @patch("graphing.plt")
    def test_creates_four_subplots(self, mock_plt):
        mock_fig = MagicMock()
        mock_axes = [MagicMock() for _ in range(4)]
        for ax in mock_axes:
            ax.plot.return_value = (MagicMock(),)
        mock_plt.subplots.return_value = (mock_fig, mock_axes)
        mock_fig.canvas.new_timer.return_value = MagicMock()

        graphing.LiveGrapher()
        mock_plt.subplots.assert_called_once_with(4, 1, figsize=(10, 8))

    @patch("graphing.plt")
    def test_interactive_mode_enabled(self, mock_plt):
        mock_fig = MagicMock()
        mock_axes = [MagicMock() for _ in range(4)]
        for ax in mock_axes:
            ax.plot.return_value = (MagicMock(),)
        mock_plt.subplots.return_value = (mock_fig, mock_axes)
        mock_fig.canvas.new_timer.return_value = MagicMock()

        graphing.LiveGrapher()
        mock_plt.ion.assert_called_once()

    @patch("graphing.plt")
    def test_timer_started(self, mock_plt):
        mock_fig = MagicMock()
        mock_axes = [MagicMock() for _ in range(4)]
        for ax in mock_axes:
            ax.plot.return_value = (MagicMock(),)
        mock_plt.subplots.return_value = (mock_fig, mock_axes)
        mock_timer = MagicMock()
        mock_fig.canvas.new_timer.return_value = mock_timer

        graphing.LiveGrapher()
        mock_timer.start.assert_called_once()


class TestWindowingBehavior:
    def test_window_clips_to_window_size(self, large_df):
        windowed = large_df.iloc[-WINDOW_SIZE:]
        assert len(windowed) == WINDOW_SIZE

    def test_window_contains_most_recent_rows(self, large_df):
        windowed = large_df.iloc[-WINDOW_SIZE:]
        pd.testing.assert_frame_equal(
            windowed.reset_index(drop=True),
            large_df.tail(WINDOW_SIZE).reset_index(drop=True),
        )

    def test_window_on_short_df_returns_full_df(self, sample_df):
        assert len(sample_df) < WINDOW_SIZE
        windowed = sample_df.iloc[-WINDOW_SIZE:]
        assert len(windowed) == len(sample_df)
