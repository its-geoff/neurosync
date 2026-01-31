import argparse
import time
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.signal import welch

CSV_FILE = Path("muse2_eeg_data.csv")


def read_csv():
    if not CSV_FILE.exists():
        raise FileNotFoundError(f"CSV file not found: {CSV_FILE.resolve()}")
    df = pd.read_csv(CSV_FILE)
    return df


def band_definitions():
    return {
        "delta": (0.5, 4),
        "theta": (4, 8),
        "alpha": (8, 13),
        "beta": (13, 30),
        "gamma": (30, 80),
    }


def compute_band_power(signal, sf, band, nperseg=256):
    """Compute band power for a 1D signal using Welch's method.

    Returns the power (area) within the requested band.
    """
    f, Pxx = welch(signal, fs=sf, nperseg=min(nperseg, len(signal)))
    low, high = band
    mask = (f >= low) & (f <= high)
    # integrate PSD over the band
    power = np.trapz(Pxx[mask], f[mask]) if np.any(mask) else 0.0
    return power


def plot_static(band=None, sf=256.0):
    df = read_csv()
    if df.empty:
        print("No data in CSV.")
        return

    timestamps = df["timestamp"]
    channels = [c for c in df.columns if c.startswith("ch")]

    if band is None:
        plt.figure(figsize=(12, 6))
        for ch in channels:
            plt.plot(timestamps, df[ch], label=ch)

        plt.xlabel("Time (s)")
        plt.ylabel("Amplitude")
        plt.title("Muse EEG channels")
        plt.legend(loc="upper right")
        plt.tight_layout()
        plt.show()
        return

    bands = band_definitions()
    if band not in bands:
        raise ValueError(
            f"Unknown band: {band}. Choose from {list(bands.keys())}"
        )

    lowhigh = bands[band]

    # compute band power per channel over the whole recording
    powers = {}
    for ch in channels:
        sig = df[ch].to_numpy()
        p = compute_band_power(sig, sf, lowhigh)
        powers[ch] = p

    # plot
    plt.figure(figsize=(8, 4))
    plt.bar(powers.keys(), powers.values())
    plt.ylabel("Band power")
    plt.title(f"{band.capitalize()} band power ({lowhigh[0]}-{lowhigh[1]} Hz)")
    plt.tight_layout()
    plt.show()


def plot_live(poll_interval=1.0, window=10.0, band=None, sf=256.0):
    plt.ion()
    fig, ax = plt.subplots(figsize=(12, 6))

    channels = None
    lines = {}

    start_time = None

    try:
        bands = band_definitions()
        while True:
            df = read_csv()
            if df.empty:
                time.sleep(poll_interval)
                continue

            if start_time is None:
                start_time = df["timestamp"].iloc[0]

            timestamps = df["timestamp"] - start_time
            if channels is None:
                channels = [c for c in df.columns if c.startswith("ch")]

            if band is None:
                # time-series plotting (same as before)
                if not lines:
                    for ch in channels:
                        (line,) = ax.plot(timestamps, df[ch], label=ch)
                        lines[ch] = line
                    ax.set_xlabel("Time (s)")
                    ax.set_ylabel("Amplitude")
                    ax.set_title("Live Muse EEG")
                    ax.legend(loc="upper right")
                else:
                    for ch in channels:
                        lines[ch].set_xdata(timestamps)
                        lines[ch].set_ydata(df[ch])

                now = timestamps.iloc[-1]
                ax.set_xlim(max(0, now - window), now)
                ax.relim()
                ax.autoscale_view(True, True, True)

            else:
                # compute band power per channel and display as bar chart
                if band not in bands:
                    raise ValueError(f"Unknown band: {band}")
                lowhigh = bands[band]
                powers = []
                for ch in channels:
                    sig = df[ch].to_numpy()
                    p = compute_band_power(sig, sf, lowhigh)
                    powers.append(p)

                ax.clear()
                ax.bar(channels, powers)
                ax.set_ylabel("Band power")
                ax.set_title(f"Live {band.capitalize()} band power")

            fig.canvas.draw()
            fig.canvas.flush_events()
            time.sleep(poll_interval)

    except KeyboardInterrupt:
        print("\nStopped live plotting.")


def main():
    parser = argparse.ArgumentParser(description="Visualize Muse EEG CSV data")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run live-updating plot (tails CSV)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Polling interval for live mode (seconds)",
    )
    parser.add_argument(
        "--window",
        type=float,
        default=10.0,
        help="Time window (seconds) for live plot",
    )
    parser.add_argument(
        "--band",
        type=str,
        default=None,
        help="Band to plot (delta, theta, alpha, beta, gamma)",
    )
    parser.add_argument(
        "--sf",
        type=float,
        default=256.0,
        help="Sampling frequency (Hz) of the EEG data",
    )

    args = parser.parse_args()

    if args.live:
        plot_live(
            poll_interval=args.interval,
            window=args.window,
            band=args.band,
            sf=args.sf,
        )
    else:
        plot_static(band=args.band, sf=args.sf)


if __name__ == "__main__":
    main()
