# CCSDS X-Band Telemetry Transceiver in GNU Radio

<p align="center">
  <img src="docs/figures/flowgraph_transceiver_demo.gif" alt="GNU Radio transceiver flowgraph" width="85%">
</p>

[![CCSDS 131.0-B-5](https://img.shields.io/badge/CCSDS-131.0--B--5-00529B.svg)](https://public.ccsds.org/Pubs/131x0b5.pdf)
[![GNU Radio](https://img.shields.io/badge/GNU%20Radio-3.10%2B-darkgreen.svg)](https://www.gnuradio.org/)
[![License](https://img.shields.io/badge/License-GPL--3.0-purple.svg)](LICENSE)

Software-defined transmitter, LEO channel model and receiver for an X-band (8.4 GHz) telemetry downlink, following the concatenated coding scheme of CCSDS 131.0-B-5 (Reed-Solomon + convolutional code, QPSK). The receiver handles Doppler shifts and QPSK phase ambiguity without orbital predictions (TLEs).

This is my bachelor's thesis (TFG), developed for the CHESS CubeSat mission (Pathfinder 0) with the EPFL Spacecraft Team and the Telecommunications Circuits Laboratory (TCL). The GNU Radio blocks written for it live in a separate module, [gr-chess](https://github.com/DANIEL-PEREIRA-RIQUELME/gr-chess).

**Status:** all results come from simulation, with synthetic CCSDS frames going through the modelled channel. The receiver has not been tested on a real satellite signal.

## What is implemented

- **Transmitter:** RS(255,223) with interleaving depth I=8, CCSDS pseudo-randomizer, 32-bit ASM, convolutional encoder (rate 1/2, K=7), Gray QPSK, root-raised-cosine pulse shaping (α=0.5, 2 samples/symbol).
- **Channel:** LEO Doppler model (475 km orbit, ±250 kHz, up to 2.5 kHz/s) and AWGN calibrated per Eb/N0.
- **Receiver:** AGC, polyphase timing recovery, Costas loop, soft-decision Viterbi decoding, frame synchronizer, descrambler and RS decoder.
- **Blind Doppler estimator:** 4th-power non-linearity plus FFT with parabolic peak interpolation. Details in [docs/Blind_Doppler_Estimation_Mth_Power_FFT_CCSDS.md](docs/Blind_Doppler_Estimation_Mth_Power_FFT_CCSDS.md).
- **Dual-branch frame synchronizer:** the Costas output is decoded twice, directly and rotated by +j. The synchronizer (`chess.fast_sync`) searches the ASM (`0x1ACFFC1D`) and its inverse (`0xE53003E2`) in both branches and locks to the first match, which covers the four QPSK phase ambiguities. Once locked it stays on that branch until several consecutive ASMs fail. It resolves the ambiguity; it does not prevent Costas cycle slips.
- **Diagnostic tool (C++20):** compares decoded frames with the reference, computing BER, FER and CRC-16 (`scripts/diagnostic.cpp`).

## Architecture

<p align="center">
  <img src="docs/figures/ccsds_pipeline_architecture.png" alt="Transceiver architecture" width="90%">
</p>

The transmitter and receiver are GNU Radio hierarchical blocks (`flowgraphs/hier_blocks/`). The sync stage is shown below.

<p align="center">
  <img src="docs/figures/page_1_dual_branch_sync.png" alt="Dual-branch synchronizer flowgraph" width="90%">
</p>

## Link parameters

| Parameter | Value |
| :--- | :--- |
| Carrier | 8.4 GHz (X-band) |
| Modulation | QPSK, Gray-coded, RRC α=0.5 |
| Sample rate / symbol rate | 25 MS/s / 12.5 MBd |
| Raw channel rate | 25 Mbps |
| Net telemetry rate | ≈ 10.9 Mbps |
| Outer code | RS(255,223), t=16, I=8 (1,784 bytes per frame) |
| Inner code | Convolutional r=1/2, K=7, (171, 133) octal |
| Randomizer | h(x) = x⁸ + x⁷ + x⁵ + x³ + 1 |
| Attached sync marker | `0x1ACFFC1D` |

## Results

### Bit error rate

<p align="center">
  <img src="docs/figures/BER.png" alt="BER versus Eb/N0" width="85%">
</p>

The plot compares uncoded QPSK, the CCSDS reference curve for this concatenated code, and two simulations: static AWGN, and AWGN with the Doppler profile above using the blind estimator and the Costas loop.

- Static AWGN follows the CCSDS curve, with BER ≈ 2.4·10⁻⁷ at Eb/N0 = 3.2 dB.
- With Doppler, the curve is shifted by about 0.8 dB in the waterfall region and reaches BER < 10⁻⁶ at 4.0 dB.

### CPU load

Real-time throughput is limited by the CPU, not by the algorithms. On an Intel Core i5-1335U the flowgraph sustains **14.5 Mbps**, below the 25 Mbps channel rate. The two heaviest blocks are the soft QPSK demapper (≈ 123 % of one core) and the polyphase clock synchronizer (≈ 99 %). The same bottleneck shows up on Azure VMs (AMD EPYC 7763). See [docs/CPU_BREAKDOWN_METRICS.md](docs/CPU_BREAKDOWN_METRICS.md).

<p align="center">
  <img src="docs/figures/cpu_breakdown_local.png" alt="CPU load per block" width="85%">
</p>

## Installation

Developed and run on Ubuntu 24.04 (GNU Radio 3.10, GCC 13). Requires GNU Radio 3.10+ and a C++20 compiler (GCC 11+).

```bash
sudo apt update
sudo apt install -y gnuradio gnuradio-dev cmake g++ git \
                    python3-numpy python3-scipy python3-matplotlib \
                    pybind11-dev libfmt-dev libspdlog-dev libvolk-dev
```

Three out-of-tree modules are needed. Build each one with the usual `mkdir build && cd build && cmake .. && make -j$(nproc) && sudo make install && sudo ldconfig`:

| Module | Used for |
| :--- | :--- |
| [gr-chess](https://github.com/DANIEL-PEREIRA-RIQUELME/gr-chess) | Doppler estimator, channel model, frame synchronizer |
| [gr-HighDataRate_Modem](https://github.com/DavidToddMiller/gr-HighDataRate_Modem) | Soft demapper, Viterbi decoder, timing recovery |
| [gr-satellites](https://github.com/daniestevez/gr-satellites) | Scrambler and Reed-Solomon blocks |

Then compile the hierarchical blocks:

```bash
cd flowgraphs/hier_blocks
grcc -u ccsds_concatenated_tx.grc
grcc -u ccsds_concatenated_rx.grc
```

## Usage

Use the system Python, not a Conda one, so that GNU Radio and the installed modules are found.

```bash
# One simulation at Eb/N0 = 3.5 dB on the 60,000-frame vector (generated if missing)
python3 main_transceiver_simulation.py --ebn0 3.50

# Quick run on the 1,000-frame vector included in the repository
python3 main_transceiver_simulation.py --ebn0 4.0 --signal 0.001Ms

# Several Eb/N0 points, one after another
python3 scripts/batch_runner_local.py
```

Each run writes `output/results/test/result_point_<Eb/N0>.json` and a text report with FER and BER. FER counts frames that were lost or failed the CRC. "System BER" adds a 50 % bit error penalty for every such frame; "Sync BER" only counts bit errors inside frames received with a valid CRC. Frames lost while the receiver is acquiring at the start of the file are included, so short vectors show a higher FER than long ones.

Other tools:

```bash
python3 scripts/generate_test_frames.py --frames 10000 --output data/custom_test_frames.bin
g++ -O3 -std=c++20 scripts/diagnostic.cpp -o scripts/diagnostic    # frame analyzer, built automatically when needed
```

## Repository layout

```
main_transceiver_simulation.py   simulation entry point
flowgraphs/                      GRC flowgraph (GUI) and hierarchical blocks
scripts/                         run_point.py (headless runner), diagnostic.cpp, batch runners,
                                 plotting and CPU profiling
data/                            ASM file and the 1,000-frame test vector
docs/                            Doppler estimator note, CPU profiling and figures
```

## License and acknowledgements

GPL-3.0, see [LICENSE](LICENSE). Developed with the EPFL Spacecraft Team and the TCL at EPFL for the CHESS CubeSat mission.
