"""test_lsl_to_uart_e2e.py

End-to-end tests for the LSL streaming → buffer → FFT → UART packet pipeline.
No real LSL or serial hardware required.
"""

import unittest.mock as mock

import numpy as np

import main
import transmission


class _FakeLSLInlet:
    def __init__(self, samples):
        self._iter = iter(samples)

    def pull_sample(self):
        try:
            return next(self._iter), None
        except StopIteration:
            raise KeyboardInterrupt


def _fake_eeg_samples(n, seed=0):
    rng = np.random.default_rng(seed)
    channels = rng.uniform(-100, 100, size=(n, 4))
    return channels.tolist()


def _run_lsl_mode(samples):
    written = []
    ser = mock.MagicMock()
    ser.write.side_effect = lambda p: written.append(p)

    with (
        mock.patch("main.resolve_byprop", return_value=[mock.MagicMock()]),
        mock.patch(
            "main.StreamInlet", side_effect=lambda _: _FakeLSLInlet(samples)
        ),
        mock.patch("data_processing.graphing.run"),
    ):
        main.connect_and_process(ser)

    return written


class TestLSLToUARTPipelineE2E:

    def test_256_samples_produce_at_least_one_packet(self):
        written = _run_lsl_mode(_fake_eeg_samples(256))
        assert len(written) >= 1

    def test_all_packets_are_12_bytes(self):
        written = _run_lsl_mode(_fake_eeg_samples(256))
        for pkt in written:
            assert len(pkt) == 12

    def test_all_packets_have_correct_sync_header(self):
        written = _run_lsl_mode(_fake_eeg_samples(256))
        for pkt in written:
            assert pkt[0] == 0xAA
            assert pkt[1] == 0x55
            assert pkt[2] == 0x08

    def test_all_packets_pass_crc_validation(self):
        written = _run_lsl_mode(_fake_eeg_samples(256))
        for pkt in written:
            assert transmission.validate_packet(pkt)

    def test_384_samples_produce_at_least_as_many_packets_as_256(self):
        written_256 = _run_lsl_mode(_fake_eeg_samples(256))
        written_384 = _run_lsl_mode(_fake_eeg_samples(384))
        assert len(written_384) >= len(written_256)

    def test_keyboard_interrupt_exits_cleanly(self):
        ser = mock.MagicMock()
        with (
            mock.patch(
                "main.resolve_byprop", return_value=[mock.MagicMock()]
            ),
            mock.patch(
                "main.StreamInlet", side_effect=lambda _: _FakeLSLInlet([])
            ),
        ):
            main.connect_and_process(ser)
