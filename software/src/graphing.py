"""graphing.py

Graphs brainwave band data dynamically.
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.axes import Axes


def create_figure():
    """Creates a graph to display the frequency of each brainwave type.

    Arguments:
        None.

    Returns:
        tuple [Line2D, ...]: Line objects that represent a brainwave frequency.
    """
    plt.ion()   # turn on interactive mode
    fig, ax = plt.subplots(4, 1)
    line_delta, = ax[0].plot([], [])
    line_theta, = ax[1].plot([], [])
    line_alpha, = ax[2].plot([], [])
    line_beta, = ax[3].plot([], [])
    
    plt.show()
    return fig, ax, line_delta, line_theta, line_alpha, line_beta


def update_delta(line: Line2D, ax: Axes, fft_df: pd.DataFrame):
    """Updates the current line on the graph.

    Arguments:
        line (Line2D): The line object for the delta wave graph.
        fft_df (pandas.DataFrame): The existing data.

    Returns:
        None.
    """
    line.set_xdata(fft_df["timestamp"].values)
    line.set_ydata(fft_df["delta"].values)
    ax.relim()
    ax.autoscale_view()
    line.figure.canvas.draw()
    line.figure.canvas.flush_events()


def run(fft_df: pd.DataFrame):
    """Creates a graph and constantly updates the graph when new data is
    added."""
    fig, ax, line_delta, line_theta, line_alpha, line_beta = create_figure()
    update_delta(line_delta, ax[0], fft_df)
    
    for i in range(1, len(fft_df) + 1):
        update_delta(line_delta, ax[0], fft_df.iloc[:i])
        plt.pause(0.1)
        
    plt.ioff()  # turn off interactive mode
    plt.show()  # blocking commands until window closed


if __name__ == "__main__":
    fft_df = pd.DataFrame({
        "timestamp": np.arange(100),
        "delta": np.random.uniform(1, 100, 100),
        "theta": np.random.uniform(1, 100, 100),
        "alpha": np.random.uniform(1, 100, 100),
        "beta":  np.random.uniform(1, 100, 100),
    })
    
    run(fft_df)
