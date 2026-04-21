"""test_queue_buffer_stress.py

Stress tests for the graphing queue buffer under producer/consumer pressure.
"""

import queue
import threading
import time
import unittest.mock as mock

import numpy as np
import pandas as pd

import graphing


class TestQueueBufferStress:

    def test_single_slot_queue_does_not_block_producer(self):
        n = 200
        fft_df = pd.DataFrame(
            {
                "timestamp": np.arange(n, dtype=float),
                "delta": np.ones(n),
                "theta": np.ones(n),
                "alpha": np.ones(n),
                "beta": np.ones(n),
            }
        )
        buf = queue.Queue(maxsize=1)
        with mock.patch("graphing.time.sleep"):
            start = time.perf_counter()
            graphing.write_data(fft_df, buf)
            elapsed = time.perf_counter() - start
        print(f"\n[queue stress n={n}] {elapsed:.3f}s")
        assert elapsed < 2.0

    def test_slow_consumer_does_not_deadlock_producer(self):
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
        buf = queue.Queue(maxsize=1)
        consumed = []

        def slow_consumer():
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                try:
                    item = buf.get(timeout=0.3)
                    consumed.append(item)
                    time.sleep(0.05)
                except queue.Empty:
                    break

        with mock.patch("graphing.time.sleep"):
            producer = threading.Thread(
                target=graphing.write_data, args=(fft_df, buf)
            )
            consumer = threading.Thread(target=slow_consumer)
            producer.start()
            consumer.start()
            producer.join(timeout=10)
            consumer.join(timeout=10)

        assert (
            not producer.is_alive()
        ), "producer thread still running (deadlock?)"

    def test_final_frame_always_present_after_write(self):
        for n in [10, 50, 100, 200]:
            fft_df = pd.DataFrame(
                {
                    "timestamp": np.arange(n, dtype=float),
                    "delta": np.ones(n),
                    "theta": np.ones(n) * 2,
                    "alpha": np.ones(n) * 3,
                    "beta": np.ones(n) * 4,
                }
            )
            buf = queue.Queue(maxsize=1)
            with mock.patch("graphing.time.sleep"):
                graphing.write_data(fft_df, buf)
            assert not buf.empty(), f"queue empty after write_data with n={n}"
            frame = buf.get_nowait()
            assert (
                len(frame) == n
            ), f"n={n}: expected {n} rows, got {len(frame)}"
