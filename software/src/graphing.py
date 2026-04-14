"""graphing.py.

Graphs brainwave band data dynamically. Utilizes threading for parallel
processing and visualization.
"""

import queue
import threading
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.lines import Line2D

# module level constants
BANDS = ["delta", "theta", "alpha", "beta"]
WINDOW_SIZE = 50


def create_figure():
    """Creates a graph to display the frequency of each brainwave type.

    Arguments:
        None.

    Returns:
        tuple [Line2D, ...]: Line objects that represent a brainwave frequency.
    """
    print("Opening matplotlib...")
    plt.ion()  # turn on interactive mode
    fig, ax = plt.subplots(4, 1)
    (line_delta,) = ax[0].plot([], [], color="green")
    (line_theta,) = ax[1].plot([], [], color="red")
    (line_alpha,) = ax[2].plot([], [], color="blue")
    (line_beta,) = ax[3].plot([], [], color="purple")

    plt.tight_layout()
    plt.show()
    return line_delta, line_theta, line_alpha, line_beta


def update_delta(line: Line2D, fft_df: pd.DataFrame):
    """Updates the current line on the graph.

    Arguments:
        line (Line2D): The line object for the delta wave graph.
        fft_df (pandas.DataFrame): The existing data.

    Returns:
        None.
    """
    line.set_xdata(fft_df["timestamp"].values)
    line.set_ydata(fft_df[band].values)
    ax.relim()
    ax.autoscale_view()
    line.figure.canvas.draw()
    line.figure.canvas.flush_events()


def write_data(fft_df: pd.DataFrame, buffer: queue.Queue):
    """Writes FFT data into a shared buffer using threads for the render loop.

    Arguments:
        fft_df (pd.DataFrame): The formatted FFT data.
        buffer (queue.Queue): Shared buffer between this thread and the render
            loop.

    Returns:
        None.
    """
    for i in range(1, len(fft_df) + 1):
        if not buffer.empty():
            try:
                buffer.get_nowait()  # discard stale frame
            except queue.Empty:
                pass
        buffer.put(fft_df.iloc[:i])
        time.sleep(0.1)


def run(fft_df: pd.DataFrame):
    """Creates a graph and constantly updates the graph when new data is added.

    Arguments:
        fft_df (pandas.DataFrame): The formatted FFT data.

    Returns:
        None.
    """
    fig, ax, line_delta, line_theta, line_alpha, line_beta = create_figure()
    lines = [line_delta, line_theta, line_alpha, line_beta]

    buffer = queue.Queue(maxsize=1)

    thread = threading.Thread(
        target=write_data, args=(fft_df, buffer), daemon=True
    )
    thread.start()

    while thread.is_alive():
        try:
            current_df = buffer.get_nowait()
            windowed_df = current_df.iloc[-WINDOW_SIZE:]
            for line, band, axis in zip(lines, BANDS, ax):
                update_line(line, axis, windowed_df, band)
            fig.canvas.draw()
            fig.canvas.flush_events()
        except queue.Empty:
            pass

        plt.pause(0.01)

    plt.ioff()  # turn off interactive mode
    plt.show()  # blocking commands until window closed


if __name__ == "__main__":
    fft_df = pd.DataFrame(
        {
            "timestamp": np.arange(100),
            "delta": np.random.uniform(1, 100, 100),
            "theta": np.random.uniform(1, 100, 100),
            "alpha": np.random.uniform(1, 100, 100),
            "beta": np.random.uniform(1, 100, 100),
        }
    )

    run(fft_df)
