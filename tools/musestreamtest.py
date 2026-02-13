import csv
import subprocess
import time

from pylsl import StreamInlet, resolve_byprop

# ---------- CONFIG ----------
CSV_FILENAME = "muse2_eeg_data.csv"
STREAM_START_DELAY = 10  # seconds to wait for Muse LSL to connect
# ----------------------------


def start_muse_stream():
    """Start the muselsl stream as a background process."""
    print("[INFO] Starting Muse LSL stream...")
    proc = subprocess.Popen(
        ["muselsl", "stream"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    print(f"[OK] Muse stream process started (PID: {proc.pid})")
    return proc


def connect_to_stream(stream_type="EEG", timeout=5):
    """Find and connect to the Muse EEG stream."""
    print(f"[INFO] Waiting {STREAM_START_DELAY}s for stream to initialize...")
    time.sleep(STREAM_START_DELAY)
    print(f"[INFO] Looking for {stream_type} stream (timeout={timeout}s)...")
    # resolve_byprop(prop, value, timeout) is the pylsl helper to find streams
    # by property
    streams = resolve_byprop("type", stream_type, timeout=timeout)
    if not streams:
        raise RuntimeError(f"No LSL stream found with type='{stream_type}'")
    inlet = StreamInlet(streams[0])
    print(f"[OK] Connected to {stream_type} stream!")
    return inlet


def collect_and_save(inlet):
    """Collect samples, print them live, and save to CSV."""
    print(f"[INFO] Collecting EEG samples... (Saving to {CSV_FILENAME})\n")
    with open(CSV_FILENAME, "w", newline="") as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(["timestamp", "ch1", "ch2", "ch3", "ch4"])

        try:
            while True:
                sample, timestamp = inlet.pull_sample(timeout=1.0)
                if sample:
                    # Print to console
                    print(f"{timestamp:.3f}, {sample}")
                    # Write to CSV
                    writer.writerow([timestamp] + sample)
        except KeyboardInterrupt:
            print("\n[INFO] Stopped by user. Data saved to", CSV_FILENAME)


def main():
    # Start Muse LSL streaming process
    muse_proc = start_muse_stream()

    try:
        # Connect to EEG LSL stream
        inlet = connect_to_stream()

        # Collect and save EEG samples
        collect_and_save(inlet)

    finally:
        print("[INFO] Terminating Muse stream process...")
        muse_proc.terminate()
        print("[DONE] Muse stream closed.")


if __name__ == "__main__":
    main()
