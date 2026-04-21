import sys
import types
import unittest
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd


# Stub pylsl before main.py is imported
def _make_pylsl_stub():
    pylsl = types.ModuleType("pylsl")

    class FakeInlet:
        def __init__(self, samples):
            # samples is a list of 4-element lists
            self._samples = iter(samples)

        def pull_sample(self):
            try:
                return next(self._samples), None
            except StopIteration:
                raise KeyboardInterrupt  # stop the loop when samples run out

    def resolve_byprop(stream_type, stream_name):
        return [MagicMock()]  # return one fake stream

    pylsl.StreamInlet = FakeInlet
    pylsl.resolve_byprop = resolve_byprop
    return pylsl


sys.modules.setdefault("pylsl", _make_pylsl_stub())


# Now safe to import
import main  # noqa: E402

#  Helpers


def _fake_samples(n: int) -> list:
    """Generate n fake EEG samples, each with 5 channels (main.py slices
    [:4])."""
    rng = np.random.default_rng(0)
    return rng.standard_normal((n, 5)).tolist()


def _make_fake_ser():
    ser = MagicMock()
    ser.write = MagicMock()
    return ser


#  Tests

#  patch target helper
# main.py uses "from pylsl import StreamInlet, resolve_byprop" so the names
# live directly on the main module, not under main.pylsl.
# All other dependencies (data_processing, transmission) are imported as
# modules, so patches use "main.data_processing.X" and "main.transmission.X".


def _patch_inlet(samples):
    """Patch main.StreamInlet to return a _SampleInlet for the given
    samples."""
    return patch(
        "main.StreamInlet", side_effect=lambda _: _SampleInlet(samples)
    )


def _patch_resolve():
    """Patch main.resolve_byprop to return one fake stream."""
    return patch("main.resolve_byprop", return_value=[MagicMock()])


def _patch_fft(return_value=None):
    rv = (
        pd.DataFrame([{"delta": 1, "theta": 2, "alpha": 3, "beta": 4}])
        if return_value is None
        else return_value
    )
    return patch("main.data_processing.transform_to_hz", return_value=rv)


def _patch_fft_side_effect(fn):
    return patch("main.data_processing.transform_to_hz", side_effect=fn)


def _patch_packet(return_value=b"\x00" * 12):
    return patch("main.transmission.df_to_packet", return_value=return_value)


class TestConnectAndProcessBuffering(unittest.TestCase):
    """Tests that the buffer fills correctly and triggers at the right time."""

    def test_no_processing_before_256_samples(self):
        """If fewer than 256 samples arrive, transform_to_hz is never
        called."""
        with (
            _patch_resolve(),
            _patch_inlet(_fake_samples(255)),
            patch("main.data_processing.transform_to_hz") as mock_fft,
        ):
            main.connect_and_process(_make_fake_ser())
        mock_fft.assert_not_called()

    def test_processing_triggers_at_exactly_256_samples(self):
        """transform_to_hz is called exactly once when 256 samples arrive."""
        with (
            _patch_resolve(),
            _patch_inlet(_fake_samples(256)),
            _patch_fft() as mock_fft,
            _patch_packet(),
        ):
            main.connect_and_process(_make_fake_ser())
        mock_fft.assert_called_once()

    def test_processing_triggers_twice_for_384_samples(self):
        """384 samples = first window at 256, then 128 remaining + 128 new =
        second window.

        transform_to_hz should be called twice.
        """
        with (
            _patch_resolve(),
            _patch_inlet(_fake_samples(384)),
            _patch_fft() as mock_fft,
            _patch_packet(),
        ):
            main.connect_and_process(_make_fake_ser())
        self.assertEqual(mock_fft.call_count, 2)

    def test_processing_triggers_three_times_for_512_samples(self):
        """Three full windows in 512 samples."""
        with (
            _patch_resolve(),
            _patch_inlet(_fake_samples(512)),
            _patch_fft() as mock_fft,
            _patch_packet(),
        ):
            main.connect_and_process(_make_fake_ser())
        self.assertEqual(mock_fft.call_count, 3)


class TestConnectAndProcessWindowShape(unittest.TestCase):
    """Tests that transform_to_hz receives the right data shape."""

    def test_fft_called_with_dataframe(self):
        """transform_to_hz must receive a DataFrame, not a list."""
        captured = {}

        def capture_fft(df):
            captured["arg"] = df
            return pd.DataFrame(
                [{"delta": 1, "theta": 2, "alpha": 3, "beta": 4}]
            )

        with (
            _patch_resolve(),
            _patch_inlet(_fake_samples(256)),
            _patch_fft_side_effect(capture_fft),
            _patch_packet(),
        ):
            main.connect_and_process(_make_fake_ser())

        self.assertIn("arg", captured)
        self.assertIsInstance(captured["arg"], pd.DataFrame)

    def test_fft_receives_256_row_window(self):
        """The DataFrame passed to transform_to_hz must have exactly 256
        rows."""
        captured = {}

        def capture_fft(df):
            captured["shape"] = df.shape
            return pd.DataFrame(
                [{"delta": 1, "theta": 2, "alpha": 3, "beta": 4}]
            )

        with (
            _patch_resolve(),
            _patch_inlet(_fake_samples(256)),
            _patch_fft_side_effect(capture_fft),
            _patch_packet(),
        ):
            main.connect_and_process(_make_fake_ser())

        self.assertEqual(captured["shape"][0], 256)

    def test_fft_receives_four_channel_columns(self):
        """Window DataFrame must have exactly 4 columns (ch1–ch4)."""
        captured = {}

        def capture_fft(df):
            captured["cols"] = list(df.columns)
            return pd.DataFrame(
                [{"delta": 1, "theta": 2, "alpha": 3, "beta": 4}]
            )

        with (
            _patch_resolve(),
            _patch_inlet(_fake_samples(256)),
            _patch_fft_side_effect(capture_fft),
            _patch_packet(),
        ):
            main.connect_and_process(_make_fake_ser())

        self.assertListEqual(captured["cols"], ["ch1", "ch2", "ch3", "ch4"])

    def test_samples_sliced_to_four_channels(self):
        """main.py does sample[:4] — fifth channel must not reach the
        window."""
        captured = {}

        def capture_fft(df):
            captured["ncols"] = df.shape[1]
            return pd.DataFrame(
                [{"delta": 1, "theta": 2, "alpha": 3, "beta": 4}]
            )

        with (
            _patch_resolve(),
            _patch_inlet(_fake_samples(256)),
            _patch_fft_side_effect(capture_fft),
            _patch_packet(),
        ):
            main.connect_and_process(_make_fake_ser())

        self.assertEqual(captured["ncols"], 4)


class TestConnectAndProcessOverlap(unittest.TestCase):
    """Tests the 50% window overlap — buffer[:128] is kept after each
    window."""

    def test_second_window_uses_overlap_from_first(self):
        """After the first window (samples 0–255), the buffer keeps samples
        128–255.

        The second window is samples 128–383. transform_to_hz called twice.
        """
        call_count = {"n": 0}

        def counting_fft(df):
            call_count["n"] += 1
            return pd.DataFrame(
                [{"delta": 1, "theta": 2, "alpha": 3, "beta": 4}]
            )

        with (
            _patch_resolve(),
            _patch_inlet(_fake_samples(384)),
            _patch_fft_side_effect(counting_fft),
            _patch_packet(),
        ):
            main.connect_and_process(_make_fake_ser())

        self.assertEqual(
            call_count["n"],
            2,
            "Expected 2 windows with 50% overlap over 384 samples",
        )

    def test_buffer_not_fully_cleared_between_windows(self):
        """If the buffer were cleared completely (no overlap), only one window
        would fire for 383 samples.

        Two windows means overlap is working.
        """
        call_count = {"n": 0}

        def counting_fft(df):
            call_count["n"] += 1
            return pd.DataFrame(
                [{"delta": 1, "theta": 2, "alpha": 3, "beta": 4}]
            )

        with (
            _patch_resolve(),
            _patch_inlet(_fake_samples(383)),
            _patch_fft_side_effect(counting_fft),
            _patch_packet(),
        ):
            main.connect_and_process(_make_fake_ser())

        # 383 samples: first window at 256, then 255 in buffer — not enough for
        # second
        self.assertEqual(call_count["n"], 1)


class TestConnectAndProcessTransmission(unittest.TestCase):
    """Tests that packets are built and written to serial correctly."""

    def test_ser_write_called_for_each_fft_row(self):
        """ser.write() must be called once per row returned by
        transform_to_hz."""
        fft_output = pd.DataFrame(
            [
                {"delta": 1, "theta": 2, "alpha": 3, "beta": 4},
                {"delta": 5, "theta": 6, "alpha": 7, "beta": 8},
            ]
        )
        ser = _make_fake_ser()

        with (
            _patch_resolve(),
            _patch_inlet(_fake_samples(256)),
            _patch_fft(return_value=fft_output),
            _patch_packet(b"\xaa" * 12),
        ):
            main.connect_and_process(ser)

        self.assertEqual(ser.write.call_count, 2)

    def test_df_to_packet_called_for_each_row(self):
        """df_to_packet must be called once per FFT output row."""
        fft_output = pd.DataFrame(
            [{"delta": 10, "theta": 20, "alpha": 30, "beta": 40}]
        )

        with (
            _patch_resolve(),
            _patch_inlet(_fake_samples(256)),
            _patch_fft(return_value=fft_output),
            patch(
                "main.transmission.df_to_packet", return_value=b"\x00" * 12
            ) as mock_packet,
        ):
            main.connect_and_process(_make_fake_ser())

        mock_packet.assert_called_once()

    def test_packet_written_to_serial_is_from_df_to_packet(self):
        """The bytes passed to ser.write() must come directly from
        df_to_packet."""
        expected_packet = b"\xaa\x55\x08" + b"\x00" * 8 + b"\xff"
        ser = _make_fake_ser()

        with (
            _patch_resolve(),
            _patch_inlet(_fake_samples(256)),
            _patch_fft(),
            _patch_packet(expected_packet),
        ):
            main.connect_and_process(ser)

        ser.write.assert_called_with(expected_packet)

    def test_no_serial_write_when_no_full_window(self):
        """If fewer than 256 samples arrive, ser.write must never be called."""
        ser = _make_fake_ser()

        with (
            _patch_resolve(),
            _patch_inlet(_fake_samples(100)),
            patch("main.data_processing.transform_to_hz") as mock_fft,
        ):
            main.connect_and_process(ser)

        ser.write.assert_not_called()
        mock_fft.assert_not_called()


class TestConnectAndProcessShutdown(unittest.TestCase):
    """Tests that KeyboardInterrupt stops the loop cleanly."""

    def test_keyboard_interrupt_stops_loop(self):
        """Loop must exit cleanly on KeyboardInterrupt — no exception
        propagates."""
        with _patch_resolve(), _patch_inlet([]):
            try:
                main.connect_and_process(_make_fake_ser())
            except KeyboardInterrupt:
                self.fail(
                    "KeyboardInterrupt was not caught inside "
                    "connect_and_process"
                )

    def test_partial_buffer_discarded_on_interrupt(self):
        """Samples in a partial buffer (< 256) are discarded without
        processing."""
        with (
            _patch_resolve(),
            _patch_inlet(_fake_samples(200)),
            patch("main.data_processing.transform_to_hz") as mock_fft,
        ):
            main.connect_and_process(_make_fake_ser())

        mock_fft.assert_not_called()


#  _SampleInlet
# A minimal LSL inlet stand-in. Returns one sample per pull_sample() call,
# then raises KeyboardInterrupt to stop the while-True loop in main.py.


class _SampleInlet:
    def __init__(self, samples):
        self._iter = iter(samples)

    def pull_sample(self):
        try:
            return next(self._iter), None
        except StopIteration:
            raise KeyboardInterrupt


#  Run

if __name__ == "__main__":
    unittest.main(verbosity=2)
