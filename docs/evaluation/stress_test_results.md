## Stress Test Results

### Test Configuration
- Tool: pytest (custom stress test suite), `test_eeg_sender_stress.py`
- Test Files: `test_fft_pipeline_stress.py`, `test_packet_encode_stress.py`, `test_serial_write_stress.py`, `test_queue_buffer_stress.py`, `test_data_integrity_stress.py`, `test_windowing_stress.py`, `test_eeg_sender_stress.py`
- Target: FFT pipeline, UART packet encoding/validation, queue buffer, serial write simulation, FPGA UART parser and fractal rendering pipeline
- Input Sizes: 256 to 2048 EEG samples, up to 10,000 packets, 4 concurrent threads
- Hardware Tests: 100 packets/second sustained and random load against FPGA target

---

### Results

#### FFT Pipeline
| Metric | Value |
|--------|-------|
| 256-sample FFT | < 500 ms |
| 2048-sample FFT | < 2 s |
| Pipeline throughput | > 2 runs/s |
| Stats on 1000-row DataFrame | < 500 ms |

#### Packet Encoding / Validation
| Metric | Value |
|--------|-------|
| Encode throughput | > 5,000 packets/s |
| Validate throughput | > 5,000 packets/s |
| Round-trip (encode + validate) | > 2,000 ops/s |
| CRC failures across 10,000 packets | 0 |
| CRC collisions across 500 diverse payloads | 0 |

#### Serial Write Simulation
| Metric | Value |
|--------|-------|
| 1,000 simulated writes | < 1 s (> 1,000 writes/s) |
| 50 Hz packet rate accuracy | within 20% of ideal timing + 100 ms margin |
| Concurrent encode/validate (4 threads x 2,000 ops) | 0 errors |

#### Queue Buffer
| Metric | Value |
|--------|-------|
| 200-frame producer (single-slot queue) | < 2 s |
| Slow consumer deadlock test | producer exits cleanly |
| Final frame present after write | passes for n = 10, 50, 100, 200 |

#### Data Integrity
| Metric | Value |
|--------|-------|
| FFT finite value check (2048 samples) | no inf/nan across all bands |
| Stats determinism across 100 runs | fully deterministic |
| Windowing correctness (1024 samples) | expected window count matches |
| FFT determinism on same input | output identical across calls |

#### FPGA UART / Fractal Pipeline - Sustained Static Load
| Metric | Value |
|--------|-------|
| Test duration | 30 minutes |
| Packet rate | 100 pkt/s |
| Mode | static |
| Error rate | 0% |
| Visual artifacts observed | none |
| Flickering / tearing | none |
| Packet loss | none |

#### FPGA UART / Fractal Pipeline - Random High-Variation Load
| Metric | Value |
|--------|-------|
| Test duration | 5 minutes |
| Packet rate | 100 pkt/s |
| Mode | random |
| Error rate | 0% |
| System crashes / resets | none |
| Loss of synchronization | none |
| Visual artifacts (extreme transitions) | minor expected distortion only |

---

### Observations

- The FFT pipeline handles both real-time window sizes (256 samples) and larger batch inputs (2048 samples) well within the time budgets we set. At 256 samples it is fast enough to keep up with the Muse 2's 256 Hz sampling rate without falling behind.
- Packet encoding and CRC validation are both well above the 5,000 ops/s floor, which gives us enough headroom for real-time UART transmission at 50 Hz without the encode step becoming a bottleneck.
- The single-slot queue design in the graphing module holds up under producer pressure. The producer never blocks or deadlocks even when the consumer is slower, which is the behavior we wanted since we drop stale frames instead of queuing them up.
- No CRC collisions showed up across 500 random payloads, and all 10,000 encoded packets passed validation. That gives us confidence the transmission layer is stable.
- The 50 Hz serial timing test has a loose tolerance (20% + 100 ms) because we are simulating on a general-purpose OS with no real-time guarantees. On actual hardware the jitter could be different and would need to be validated with a logic analyzer or oscilloscope.
- The sustained static load test ran for 30 minutes at 100 packets/second with no errors, packet loss, or visual artifacts. The fractal image remained stable for the full duration and LED activity stayed consistent throughout, confirming the UART parser and framebuffer can hold up under constant load without degrading.
- The random high-variation load test pushed worst-case input variability into the FPGA pipeline for 5 minutes. The display stayed responsive with smooth transitions and no crashes, resets, or synchronization loss. Some minor visual distortion appeared during extreme input transitions, but this is expected behavior from the fixed-point fractal computation hitting edge-case parameter combinations rather than any instability in the pipeline itself.
- Taken together, the static and random hardware tests confirm that the FPGA-side UART parser, fixed-point computation, and rendering pipeline are stable across both steady-state and high-variability conditions. The software-side stress results and the hardware results are consistent with each other, which is a good sign that the boundary between the Python host and the FPGA is not a hidden failure point.
- If we were to optimize anything, the FFT windowing loop in `data_processing.py` is the most likely bottleneck at scale since it uses a Python-level for loop with `pd.concat` inside. Switching to a pre-allocated NumPy array and computing all windows in one vectorized pass would improve throughput significantly.