"""graphing.py

Graphs brainwave band data dynamically in a background thread.
The main acquisition loop feeds data via put(); rendering is non-blocking.
"""

import queue
import threading

import matplotlib.pyplot as plt
import pandas as pd

BANDS = ["alpha", "beta", "theta", "delta"]
WINDOW_SIZE = 50


class LiveGrapher:
    """Runs a matplotlib figure in a background thread.

    The acquisition loop calls put() with each new frequency DataFrame row.
    The background thread pulls from the queue and updates the plot.
    Matplotlib must be driven from a single thread, so all draw calls
    stay inside _render_loop().
    """

    def __init__(self):
        self._queue: queue.Queue[pd.DataFrame] = queue.Queue(maxsize=1)
        self._history = pd.DataFrame(columns=["timestamp"] + BANDS)
        self._thread = threading.Thread(
            target=self._render_loop, daemon=True
        )

    def start(self) -> None:
        """Start the background render thread."""
        self._thread.start()

    def put(self, freq_row: pd.DataFrame) -> None:
        """Feed a new frequency DataFrame into the grapher.

        Drops stale frames if the render thread hasn't caught up.

        Arguments:
            freq_row (pd.DataFrame): One or more rows from transform_to_hz().

        Returns:
            None.
        """
        try:
            self._queue.get_nowait()  # evict stale frame
        except queue.Empty:
            pass
        self._queue.put(freq_row)

    def _render_loop(self) -> None:
        """Main render loop; runs entirely in the background thread.
        
        Arguments:
            None.

        Returns:
            None.
        """
        plt.ion()
        fig, axes = plt.subplots(4, 1, figsize=(10, 8))
        colors = ["green", "red", "blue", "purple"]
        lines = [
            ax.plot([], [], color=c)[0]
            for ax, c in zip(axes, colors)
        ]
        for ax, band in zip(axes, BANDS):
            ax.set_ylabel(band)
        axes[-1].set_xlabel("timestamp")
        plt.tight_layout()
        plt.show()

        while True:
            try:
                new_data = self._queue.get(timeout=0.05)
                self._history = pd.concat(
                    [self._history, new_data], ignore_index=True
                ).iloc[-WINDOW_SIZE:]

                for line, ax, band in zip(lines, axes, BANDS):
                    line.set_xdata(self._history["timestamp"].values)
                    line.set_ydata(self._history[band].values)
                    ax.relim()
                    ax.autoscale_view()

                fig.canvas.draw()
                fig.canvas.flush_events()

            except queue.Empty:
                plt.pause(0.01)


def run(fft_df: pd.DataFrame) -> None:
    """Blocking replay for standalone / CSV mode.

    Not called in LSL mode, use LiveGrapher directly.

    Arguments:
        fft_df (pd.DataFrame): Full frequency DataFrame to replay.

    Returns:
        None.
    """
    grapher = LiveGrapher()
    grapher.start()

    for i in range(1, len(fft_df) + 1):
        grapher.put(fft_df.iloc[i - 1 : i])
        plt.pause(0.1)

    plt.ioff()
    plt.show()