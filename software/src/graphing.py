"""graphing.py

Graphs brainwave band data dynamically.
"""

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D


def create_figure():
    """Creates a graph to display the frequency of each brainwave type.

    Arguments:
        None.

    Returns:
        tuple [Line2D, ...]: Line objects that represent a brainwave frequency.
    """
    fig, ax = plt.subplots(4, 1)
    line_delta = ax[0].plot([], [])
    line_theta = ax[1].plot([], [])
    line_alpha = ax[2].plot([], [])
    line_beta = ax[3].plot([], [])
    
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
    line.set_ydata(fft_df["delta"].values)
    plt.draw()


def run(fft_df: pd.DataFrame):
    """Creates a graph and constantly updates the graph when new data is
    added."""
    line_delta, line_theta, line_alpha, line_beta = create_figure()
    update_delta(line_delta, fft_df)


if __name__ == "__main__":
    run()
