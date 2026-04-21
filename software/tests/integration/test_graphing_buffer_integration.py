"""test_graphing_buffer_integration.py

Integration tests for the write_data → queue → consumer threading flow.
"""

import queue
import threading
import time
import unittest.mock as mock

import numpy as np
import pandas as pd
import pytest

import graphing


class TestGraphingBufferIntegration:

    def test_write_data_and_consumer_see_correct_columns(self):
        n = 20
        fft_df = pd.DataFrame({
            "timestamp": np.arange(n, dtype=float),
            "delta":  np.ones(n) * 10,
            "theta":  np.ones(n) * 20,
            "alpha":  np.ones(n) * 30,
            "beta":   np.ones(n) * 40,
        })

        buf = queue.Queue(maxsize=1)
        consumed = []

        def consumer():
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                try:
                    frame = buf.get(timeout=0.2)
                    consumed.append(frame)
                except queue.Empty:
                    break

        with mock.patch("graphing.time.sleep"):
            t_write = threading.Thread(target=graphing.write_data, args=(fft_df, buf))
            t_consume = threading.Thread(target=consumer)
            t_write.start()
            t_consume.start()
            t_write.join(timeout=5)
            t_consume.join(timeout=5)

        assert len(consumed) > 0
        final = consumed[-1]
        assert list(final.columns) == ["timestamp", "delta", "theta", "alpha", "beta"]

    def test_windowing_applied_to_frame_larger_than_window_size(self):
        n = graphing.WINDOW_SIZE + 30
        fft_df = pd.DataFrame({
            "timestamp": np.arange(n, dtype=float),
            "delta": np.random.uniform(0, 100, n),
            "theta": np.random.uniform(0, 100, n),
            "alpha": np.random.uniform(0, 100, n),
            "beta":  np.random.uniform(0, 100, n),
        })

        buf = queue.Queue(maxsize=1)
        with mock.patch("graphing.time.sleep"):
            graphing.write_data(fft_df, buf)

        frame = buf.get_nowait()
        windowed = frame.iloc[-graphing.WINDOW_SIZE:]
        assert len(windowed) == graphing.WINDOW_SIZE
