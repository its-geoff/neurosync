import queue
import threading
from unittest.mock import MagicMock, call, patch

import numpy as np
import pandas as pd
import pytest

import graphing
from graphing import BANDS, WINDOW_SIZE, update_line, write_data


@pytest.fixture
def sample_df():
    """Minimal DataFrame that mirrors the shape write_data and update_line
    expect."""
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
def mock_line():
    """A mock matplotlib Line2D object."""
    line = MagicMock()
    line.figure = MagicMock()
    line.figure.canvas = MagicMock()
    return line


@pytest.fixture
def mock_ax():
    """A mock matplotlib Axes object."""
    return MagicMock()


class TestConstants:
    def test_bands_contains_four_entries(self):
        assert len(BANDS) == 4

    def test_bands_expected_names(self):
        assert BANDS == ["alpha", "beta", "theta", "delta"]

    def test_window_size_is_positive(self):
        assert WINDOW_SIZE > 0

    def test_window_size_is_int(self):
        assert isinstance(WINDOW_SIZE, int)


class TestUpdateLine:
    """update_line sets x/y data on the Line2D and triggers canvas refresh."""

    def test_sets_xdata_to_timestamp_column(
        self, mock_line, mock_ax, sample_df
    ):
        update_line(mock_line, mock_ax, sample_df, "delta")
        np.testing.assert_array_equal(
            mock_line.set_xdata.call_args[0][0],
            sample_df["timestamp"].values,
        )

    def test_sets_ydata_to_band_column(self, mock_line, mock_ax, sample_df):
        update_line(mock_line, mock_ax, sample_df, "alpha")
        np.testing.assert_array_equal(
            mock_line.set_ydata.call_args[0][0],
            sample_df["alpha"].values,
        )

    def test_calls_relim_and_autoscale(self, mock_line, mock_ax, sample_df):
        update_line(mock_line, mock_ax, sample_df, "beta")
        mock_ax.relim.assert_called_once()
        mock_ax.autoscale_view.assert_called_once()

    @pytest.mark.parametrize("band", BANDS)
    def test_all_bands_are_accepted(self, mock_line, mock_ax, sample_df, band):
        """update_line must not raise for any valid band name."""
        update_line(mock_line, mock_ax, sample_df, band)
        mock_line.set_ydata.assert_called_once()

    def test_missing_band_raises_key_error(
        self, mock_line, mock_ax, sample_df
    ):
        """Passing an invalid band column should surface immediately as
        KeyError."""
        with pytest.raises(KeyError):
            update_line(mock_line, mock_ax, sample_df, "gamma")


class TestWriteData:
    """write_data populates a queue with incrementally growing DataFrame
    slices."""

    @patch("graphing.time.sleep")
    def test_final_frame_is_complete(self, mock_sleep, sample_df):
        """After write_data finishes, the queue must hold the final full-length
        frame.

        The stale-frame-discard design means intermediate frames may be dropped
        when the consumer is slower than the producer (or sleep is mocked to
        0). The only guarantee is that the last frame survives and is complete.
        """
        buf = queue.Queue(maxsize=1)
        write_data(sample_df, buf)

        assert (
            not buf.empty()
        ), "Queue must hold the final frame after write_data completes"
        final_frame = buf.get_nowait()
        assert len(final_frame) == len(
            sample_df
        ), f"Final frame should have {len(sample_df)} rows, got \
            {len(final_frame)}"

    @patch("graphing.time.sleep")
    def test_surviving_frame_is_cumulative_slice(self, mock_sleep, sample_df):
        """The frame that survives is fft_df.iloc[:n], a cumulative head
        slice.

        write_data intentionally discards stale frames, so with sleep mocked
        to 0 only the last frame is guaranteed to survive. What matters is that
        this frame is the correct cumulative head of the original DataFrame,
        not a tail or a random subset.
        """
        buf = queue.Queue(maxsize=1)
        write_data(sample_df, buf)

        final_frame = buf.get_nowait()
        n = len(final_frame)
        expected = sample_df.iloc[:n]
        pd.testing.assert_frame_equal(
            final_frame.reset_index(drop=True),
            expected.reset_index(drop=True),
            check_like=False,
        )

    @patch("graphing.time.sleep")
    def test_stale_frame_is_discarded(self, mock_sleep):
        """If the queue is already full, write_data must discard before
        putting."""
        buf = queue.Queue(maxsize=1)
        stale = pd.DataFrame(
            {
                "timestamp": [0],
                "delta": [99],
                "theta": [99],
                "alpha": [99],
                "beta": [99],
            }
        )
        buf.put(stale)  # pre-fill so the first put triggers discard logic

        fft_df = pd.DataFrame(
            {
                "timestamp": [0.0, 1.0],
                "delta": [1.0, 2.0],
                "theta": [1.0, 2.0],
                "alpha": [1.0, 2.0],
                "beta": [1.0, 2.0],
            }
        )

        write_data(fft_df, buf)

        # after completion, the queue should hold the last frame, not the stale
        # one.
        final = buf.get_nowait()
        assert (
            len(final) == 2
        ), "Queue should hold the final 2-row frame, not stale data"

    @patch("graphing.time.sleep")
    def test_sleep_called_once_per_row(self, mock_sleep, sample_df):
        buf = queue.Queue(maxsize=1)

        # drain in background so write_data never blocks
        def drain():
            for _ in range(len(sample_df)):
                try:
                    buf.get(timeout=2)
                except queue.Empty:
                    pass

        drain_thread = threading.Thread(target=drain)
        drain_thread.start()
        write_data(sample_df, buf)
        drain_thread.join(timeout=5)

        assert mock_sleep.call_count == len(sample_df)

    @patch("graphing.time.sleep")
    def test_sleep_interval_is_01(self, mock_sleep, sample_df):
        buf = queue.Queue(maxsize=1)

        def drain():
            for _ in range(len(sample_df)):
                try:
                    buf.get(timeout=2)
                except queue.Empty:
                    pass

        drain_thread = threading.Thread(target=drain)
        drain_thread.start()
        write_data(sample_df, buf)
        drain_thread.join(timeout=5)

        for c in mock_sleep.call_args_list:
            assert c == call(0.1)

    @patch("graphing.time.sleep")
    def test_empty_dataframe_puts_nothing(self, mock_sleep):
        empty_df = pd.DataFrame(
            {
                "timestamp": [],
                "delta": [],
                "theta": [],
                "alpha": [],
                "beta": [],
            }
        )
        buf = queue.Queue(maxsize=1)
        write_data(empty_df, buf)
        assert buf.empty()


class TestCreateFigure:
    """create_figure is tested with the matplotlib pyplot interface fully
    mocked."""

    @patch("graphing.plt")
    def test_returns_six_objects(self, mock_plt):
        mock_fig = MagicMock()
        mock_axes = [MagicMock() for _ in range(4)]

        # ax[i].plot([], []) must return a tuple with one element.
        for ax in mock_axes:
            ax.plot.return_value = (MagicMock(),)

        mock_plt.subplots.return_value = (mock_fig, mock_axes)

        result = graphing.create_figure()
        assert (
            len(result) == 6
        ), "create_figure must return (fig, ax, l_d, l_t, l_a, l_b)"

    @patch("graphing.plt")
    def test_interactive_mode_enabled(self, mock_plt):
        mock_fig = MagicMock()
        mock_axes = [MagicMock() for _ in range(4)]
        for ax in mock_axes:
            ax.plot.return_value = (MagicMock(),)
        mock_plt.subplots.return_value = (mock_fig, mock_axes)

        graphing.create_figure()
        mock_plt.ion.assert_called_once()

    @patch("graphing.plt")
    def test_subplots_called_with_4_rows(self, mock_plt):
        mock_fig = MagicMock()
        mock_axes = [MagicMock() for _ in range(4)]
        for ax in mock_axes:
            ax.plot.return_value = (MagicMock(),)
        mock_plt.subplots.return_value = (mock_fig, mock_axes)

        graphing.create_figure()
        mock_plt.subplots.assert_called_once_with(4, 1)


class TestWindowingBehavior:
    """Verify the windowing slice applied inside run() produces the correct
    shape.

    run() itself is not unit-tested here because it owns the full render loop,
    but the windowing logic `current_df.iloc[-WINDOW_SIZE:]` is trivially
    extracted and verified independently.
    """

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
        """If df is shorter than WINDOW_SIZE, the window must not truncate
        it."""
        assert len(sample_df) < WINDOW_SIZE
        windowed = sample_df.iloc[-WINDOW_SIZE:]
        assert len(windowed) == len(sample_df)
