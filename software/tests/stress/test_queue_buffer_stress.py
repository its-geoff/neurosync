"""test_queue_buffer_stress.py

Stress tests for the graphing queue buffer under producer/consumer pressure.
"""

import queue
import threading
import time
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

import graphing


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


def make_df(n):
    return pd.DataFrame(
        {
            "timestamp": np.arange(n, dtype=float),
            "delta": np.ones(n),
            "theta": np.ones(n) * 2,
            "alpha": np.ones(n) * 3,
            "beta": np.ones(n) * 4,
        }
    )


class TestQueueBufferStress:

    def test_single_slot_queue_does_not_block_producer(self, mock_grapher):
        n = 200
        fft_df = make_df(n)
        start = time.perf_counter()
        for i in range(len(fft_df)):
            mock_grapher.put(fft_df.iloc[i : i + 1])
        elapsed = time.perf_counter() - start
        print(f"\n[queue stress n={n}] {elapsed:.3f}s")
        assert elapsed < 2.0

    def test_slow_consumer_does_not_deadlock_producer(self, mock_grapher):
        n = 100
        fft_df = pd.DataFrame(
            {
                "timestamp": np.arange(n, dtype=float),
                "delta": np.random.rand(n),
                "theta": np.random.rand(n),
                "alpha": np.random.rand(n),
                "beta": np.random.rand(n),
            }
        )
        consumed = []

        def slow_consumer():
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                try:
                    item = mock_grapher._queue.get(timeout=0.3)
                    consumed.append(item)
                    time.sleep(0.05)
                except queue.Empty:
                    break

        def producer():
            for i in range(len(fft_df)):
                mock_grapher.put(fft_df.iloc[i : i + 1])

        producer_thread = threading.Thread(target=producer)
        consumer_thread = threading.Thread(target=slow_consumer)
        producer_thread.start()
        consumer_thread.start()
        producer_thread.join(timeout=10)
        consumer_thread.join(timeout=10)

        assert (
            not producer_thread.is_alive()
        ), "producer thread still running (deadlock?)"

    def test_final_frame_always_present_after_put(self, mock_grapher):
        for n in [10, 50, 100, 200]:
            mock_grapher.reset()
            fft_df = make_df(n)
            for i in range(len(fft_df)):
                mock_grapher.put(fft_df.iloc[i : i + 1])
            assert (
                not mock_grapher._queue.empty()
            ), f"queue empty after put with n={n}"
