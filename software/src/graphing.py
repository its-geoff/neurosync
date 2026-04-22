"""graphing.py

Graphs brainwave band data dynamically using a canvas timer on the main thread.
The acquisition loop feeds data via put(); the timer handles redraws.
"""

import queue

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BANDS = ["alpha", "beta", "theta", "delta"]
WINDOW_SIZE = 50


class LiveGrapher:
    """Runs a matplotlib figure updated by a canvas timer on the main thread.

    The acquisition loop calls put() with each new frequency DataFrame row.
    The canvas timer calls _update() every 50ms to redraw the figure.
    """

    def __init__(self):
        self._queue: queue.Queue[pd.DataFrame] = queue.Queue(maxsize=1)
        self._history = pd.DataFrame({
            "timestamp": pd.Series(dtype="float64"),
            **{band: pd.Series(dtype="float64") for band in BANDS}
        })
        self._sample_count = 0

        plt.ion()
        self._fig, self._axes = plt.subplots(4, 1, figsize=(10, 8))
        colors = ["green", "red", "blue", "purple"]
        self._lines = [
            ax.plot([], [], color=c)[0]
            for ax, c in zip(self._axes, colors)
        ]
        for ax, band in zip(self._axes, BANDS):
            ax.set_ylabel(f"{band} (Hz)")
        self._axes[-1].set_xlabel("elapsed time (sec)")
        plt.tight_layout()
        plt.show()

        self._timer = self._fig.canvas.new_timer(interval=50)
        self._timer.add_callback(self._update)
        self._timer.start()

    def put(self, freq_row: pd.DataFrame) -> None:
        """Feed a new frequency DataFrame into the grapher.

        Arguments:
            freq_row (pd.DataFrame): One or more rows from transform_to_hz().

        Returns:
            None.
        """
        freq_row = freq_row.copy()
        n = len(freq_row)
        freq_row["timestamp"] = (self._sample_count + np.arange(n)) * 0.5
        self._sample_count += n

        evicted = False
        try:
            stale = self._queue.get_nowait()
            evicted = True
            print(f"[QUEUE] evicted stale frame at t={stale['timestamp'].iloc[-1]:.1f}s")
        except queue.Empty:
            pass

        self._queue.put(freq_row)
        print(f"[QUEUE] put frame t={freq_row['timestamp'].iloc[-1]:.1f}s | evicted={evicted} | sample_count={self._sample_count}")

    def pump(self) -> None:
        """Pump the Tkinter event loop. Call from main thread each iteration.

        Arguments:
            None.

        Returns:
            None.
        """
        self._fig.canvas.flush_events()

    def reset(self) -> None:
        """Clears history and resets sample counter for a new session.

        Arguments:
            None.

        Returns:
            None.
        """
        self._history = pd.DataFrame({
            "timestamp": pd.Series(dtype="float64"),
            **{band: pd.Series(dtype="float64") for band in BANDS}
        })
        self._sample_count = 0

    def _update(self) -> None:
        """Called by the canvas timer on the main thread every 50ms.

        Arguments:
            None.

        Returns:
            None.
        """
        try:
            new_data = self._queue.get_nowait()
            print(f"[RENDER] consumed frame t={new_data['timestamp'].iloc[-1]:.1f}s | history_len={len(self._history)}")

            self._history = pd.concat(
                [self._history, new_data], ignore_index=True
            ).iloc[-WINDOW_SIZE:]

            for line, ax, band in zip(self._lines, self._axes, BANDS):
                line.set_xdata(self._history["timestamp"].values)
                line.set_ydata(self._history[band].values)
                ax.relim()
                ax.autoscale_view(scaley=True)
                if len(self._history) > 1:
                    ax.set_xlim(
                        self._history["timestamp"].iloc[0],
                        self._history["timestamp"].iloc[-1]
                    )
                    elapsed = self._history["timestamp"].iloc[-1]
                    tick_step = 5 if elapsed >= 50 else 1
                    ax.set_xticks(range(
                        int(self._history["timestamp"].iloc[0]),
                        int(self._history["timestamp"].iloc[-1]) + 1,
                        tick_step
                    ))

            self._fig.canvas.draw()

        except queue.Empty:
            pass


def run(fft_df: pd.DataFrame) -> None:
    """Blocking replay for standalone / CSV mode.

    Arguments:
        fft_df (pd.DataFrame): Full frequency DataFrame to replay.

    Returns:
        None.
    """
    grapher = LiveGrapher()
    grapher.start()

    for i in range(1, len(fft_df) + 1):
        grapher.put(fft_df.iloc[i - 1 : i])
        grapher.pump()
        plt.pause(0.1)

    plt.ioff()
    plt.show()