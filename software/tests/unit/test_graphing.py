import queue
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from graphing import BANDS, WINDOW_SIZE, LiveGrapher


@pytest.fixture
def sample_df():
    """Minimal DataFrame matching the shape LiveGrapher.put() expects."""
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
    """DataFrame larger than WINDOW_SIZE to test windowing behavior."""
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
def grapher(mock_plt):
    """LiveGrapher instance with matplotlib fully mocked."""
    return LiveGrapher()


@pytest.fixture
def mock_plt():
    """Patches matplotlib.pyplot for all tests that instantiate LiveGrapher."""
    with patch("graphing.plt") as m:
        mock_fig = MagicMock()
        mock_axes = [MagicMock() for _ in range(4)]
        for ax in mock_axes:
            ax.plot.return_value = (MagicMock(),)
        mock_fig.canvas.new_timer.return_value = MagicMock()
        m.subplots.return_value = (mock_fig, mock_axes)
        yield m


class TestConstants:
    def test_bands_contains_four_entries(self):
        assert len(BANDS) == 4

    def test_bands_expected_names(self):
        assert BANDS == ["beta", "alpha", "theta", "delta"]

    def test_window_size_is_positive(self):
        assert WINDOW_SIZE > 0

    def test_window_size_is_int(self):
        assert isinstance(WINDOW_SIZE, int)


class TestLiveGrapherInit:
    def test_sample_count_starts_at_zero(self, grapher):
        assert grapher._sample_count == 0

    def test_history_starts_empty(self, grapher):
        assert len(grapher._history) == 0

    def test_history_has_correct_columns(self, grapher):
        assert list(grapher._history.columns) == ["timestamp"] + BANDS

    def test_history_columns_are_float64(self, grapher):
        for col in grapher._history.columns:
            assert grapher._history[col].dtype == np.float64

    def test_queue_starts_empty(self, grapher):
        assert grapher._queue.empty()

    def test_timer_started(self, grapher):
        grapher._fig.canvas.new_timer.return_value.start.assert_called_once()


class TestLiveGrapherPut:
    def test_puts_frame_in_queue(self, grapher, sample_df):
        grapher.put(sample_df)
        assert not grapher._queue.empty()

    def test_increments_sample_count(self, grapher, sample_df):
        grapher.put(sample_df)
        assert grapher._sample_count == len(sample_df)

    def test_timestamps_are_monotonic(self, grapher, sample_df):
        grapher.put(sample_df)
        frame = grapher._queue.get_nowait()
        assert (frame["timestamp"].diff().dropna() >= 0).all()

    def test_timestamps_start_at_zero(self, grapher, sample_df):
        grapher.put(sample_df)
        frame = grapher._queue.get_nowait()
        assert frame["timestamp"].iloc[0] == 0.0

    def test_timestamps_scale_by_half_second(self, grapher, sample_df):
        grapher.put(sample_df)
        frame = grapher._queue.get_nowait()
        expected = np.arange(len(sample_df)) * 0.5
        np.testing.assert_array_almost_equal(frame["timestamp"].values, expected)

    def test_second_put_continues_sample_count(self, grapher, sample_df):
        grapher.put(sample_df)
        grapher._queue.get_nowait()
        grapher.put(sample_df)
        frame = grapher._queue.get_nowait()
        assert frame["timestamp"].iloc[0] == len(sample_df) * 0.5

    def test_evicts_stale_frame(self, grapher, sample_df):
        grapher.put(sample_df)
        grapher.put(sample_df)
        assert grapher._queue.qsize() == 1

    def test_does_not_mutate_input(self, grapher, sample_df):
        original_timestamps = sample_df["timestamp"].copy()
        grapher.put(sample_df)
        pd.testing.assert_series_equal(sample_df["timestamp"], original_timestamps)

    @pytest.mark.parametrize("band", BANDS)
    def test_all_bands_preserved(self, grapher, sample_df, band):
        grapher.put(sample_df)
        frame = grapher._queue.get_nowait()
        np.testing.assert_array_equal(frame[band].values, sample_df[band].values)


class TestLiveGrapherReset:
    def test_clears_history(self, grapher, sample_df):
        grapher.put(sample_df)
        grapher._queue.get_nowait()
        grapher._history = pd.concat(
            [grapher._history, sample_df], ignore_index=True
        )
        grapher.reset()
        assert len(grapher._history) == 0

    def test_resets_sample_count(self, grapher, sample_df):
        grapher.put(sample_df)
        grapher.reset()
        assert grapher._sample_count == 0

    def test_history_columns_preserved_after_reset(self, grapher):
        grapher.reset()
        assert list(grapher._history.columns) == ["timestamp"] + BANDS

    def test_timestamps_restart_from_zero_after_reset(self, grapher, sample_df):
        grapher.put(sample_df)
        grapher.reset()
        grapher.put(sample_df)
        frame = grapher._queue.get_nowait()
        assert frame["timestamp"].iloc[0] == 0.0


class TestLiveGrapherUpdate:
    def test_consumes_frame_from_queue(self, grapher, sample_df):
        grapher.put(sample_df)
        grapher._update()
        assert grapher._queue.empty()

    def test_appends_to_history(self, grapher, sample_df):
        grapher.put(sample_df)
        grapher._update()
        assert len(grapher._history) == len(sample_df)

    def test_history_clipped_to_window_size(self, grapher, large_df):
        for i in range(0, len(large_df), 1):
            grapher.put(large_df.iloc[i : i + 1])
            grapher._update()
        assert len(grapher._history) <= WINDOW_SIZE

    def test_empty_queue_does_not_raise(self, grapher):
        grapher._update()

    def test_calls_canvas_draw(self, grapher, sample_df):
        grapher.put(sample_df)
        grapher._update()
        grapher._fig.canvas.draw.assert_called()


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
        """If df is shorter than WINDOW_SIZE, the window must not truncate it."""
        assert len(sample_df) < WINDOW_SIZE
        windowed = sample_df.iloc[-WINDOW_SIZE:]
        assert len(windowed) == len(sample_df)