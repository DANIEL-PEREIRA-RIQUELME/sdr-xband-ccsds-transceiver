# Software-Defined CCSDS X-Band Satellite Telemetry Transceiver

[![Standard](https://img.shields.io/badge/Standard-CCSDS%20131.0--B--5-00529B.svg)](https://public.ccsds.org/Pubs/131x0b5.pdf)
[![GNU Radio](https://img.shields.io/badge/GNU%20Radio-3.10%2B-darkgreen.svg)](https://www.gnuradio.org/)
[![RF Band](https://img.shields.io/badge/RF%20Band-X--Band%20(8.4%20GHz)-blue.svg)]()
[![Throughput](https://img.shields.io/badge/Throughput-25%20Mbps-orange.svg)]()
[![Institution](https://img.shields.io/badge/Institution-EPFL%20Spacecraft%20Team%20%2F%20TCL-red.svg)](https://www.epflspacecraftteam.ch/)
[![License](https://img.shields.io/badge/License-GPL--3.0-purple.svg)](LICENSE)

An end-to-end, high-data-rate Software-Defined Radio (SDR) transceiver pipeline for X-band Low Earth Orbit (LEO) satellite downlinks in strict compliance with the **CCSDS 131.0-B-5 (TM Synchronization and Channel Coding)** standard.

Developed for the **CHESS CubeSat mission (Pathfinder 0)** at the **EPFL Spacecraft Team** and the **Telecommunications Circuits Laboratory (TCL)**, this system integrates concatenated Forward Error Correction (Reed-Solomon + Convolutional Coding), dynamic LEO orbital Doppler channel emulation, modular hierarchical transmitter/receiver blocks, and a **Dual-Branch Flywheel Frame Synchronizer** resolving all four QPSK phase ambiguities ($0^\circ, 90^\circ, 180^\circ, 270^\circ$).

---

## Table of Contents
- [Executive Summary](#executive-summary)
- [System Architecture](#system-architecture)
- [Physical Layer Specifications](#physical-layer-specifications)
- [Repository Structure](#repository-structure)
- [Prerequisites & Dependencies](#prerequisites--dependencies)
- [Quickstart & Execution](#quickstart--execution)
- [Experimental Results](#experimental-results)
- [Autonomous Doppler Estimation Research](#autonomous-doppler-estimation-research)
- [Academic Documentation & Thesis](#academic-documentation--thesis)
- [License](#license)

---

## Executive Summary

LEO nanosatellites equipped with high-yield scientific instruments—such as the mass spectrometer on EPFL's Pathfinder 0—generate gigabits of telemetry that must be retrieved during short 5-to-10 minute visibility windows. At X-band ($8.400\text{ GHz} - 10.475\text{ GHz}$), the terrestrial ground station encounters extreme channel impairments:
- **Severe Doppler Frequency Shifts:** up to $\pm 250\text{ kHz}$ with drift rates exceeding $|\dot{f}_D| \ge 2.5\text{ kHz/s}$ at pass zenith.
- **Hardware Local Oscillator (LO) Drifts:** $\pm 30\text{ to }50\text{ kHz}$ from LNB and satellite thermal cycles.
- **Costas Loop Cycle Slipping:** inducing abrupt $\pi/2$ phase jumps on QPSK symbols.

This project delivers a completely software-defined, modular base station receiver capable of sustaining **25 Mbps** telemetry demodulation, acquiring and tracking the signal under orbital dynamics, and achieving **zero frame loss (FER = 0.0)** and **zero bit errors (BER = 0.0)**.

### Key Engineering Contributions
1. **Modular Hierarchical Architecture:** Complete encapsulation of the baseband chain into clean GNU Radio hierarchical blocks:
   - `ccsds_concatenated_tx`: Reed-Solomon encoder, interleaver ($I=8$), pseudo-randomizer, ASM multiplexer, rate 1/2 convolutional encoder, and RRC filter.
   - `ccsds_concatenated_rx`: AGC, polyphase symbol timing (PFB Clock Sync), Costas loop, soft-decision Viterbi decoders, dual-branch flywheel sync, descrambler, and RS decoder.
2. **Dual-Branch Feed-Forward Flywheel Synchronizer:** Resolves QPSK $\pi/2$ phase ambiguities by concurrently running direct ($0^\circ$) and orthogonal ($+j$, $90^\circ$) branches with flywheel state tracking (`SEARCH` $\to$ `LOCK`).
3. **Rigorous High-Performance C++20 Diagnostics:** Automated bit-level and frame-level verification tool (`diagnostic`) evaluating over 60,000 frames ($>107\text{ MB}$) in seconds with CRC-16 validation and FER/BER metrics.
4. **Autonomous Blind Doppler Estimation:** Research and implementation formulation for 4th-power non-linearity and FFT ($M$-th Power + FFT) eliminating third-party tracking software dependencies.

---

## System Architecture

```mermaid
graph TD
    subgraph Spacecraft Transmitter ["1. Spacecraft Transmitter (Hier Block: ccsds_concatenated_tx)"]
        TF[CCSDS Transfer Frame<br/>1784 Bytes] --> RS_ENC[Outer Reed-Solomon<br/>RS 255, 223 Encoder]
        RS_ENC --> INTL[Convolutional Interleaver<br/>Depth I = 8, 2040 Bytes]
        INTL --> SCRAM[CCSDS Pseudo-Randomizer<br/>LFSR h(x) Scrambler]
        SCRAM --> MUX[ASM Mux<br/>32-bit Sync Word 0x1ACFFC1D]
        MUX --> CC_ENC[Inner Convolutional Encoder<br/>Rate 1/2, K=7, 171/133]
        CC_ENC --> MAP[Gray QPSK Mapper<br/>16352 Symbols / CADU]
        MAP --> RRC_TX[Root-Raised Cosine Filter<br/>alpha = 0.5, sps = 2]
    end

    subgraph Channel ["2. Dynamic LEO Channel"]
        RRC_TX --> DOP_SIM[LEO Orbital Doppler Model<br/>Altitude 475 km, 8.4 GHz]
        DOP_SIM --> AWGN_SIM[Calibrated AWGN Noise Engine<br/>Eb/N0 Parameterized]
    end

    subgraph Ground Station Receiver ["3. Ground Station Receiver (Hier Block: ccsds_concatenated_rx)"]
        AWGN_SIM --> AGC_RX[Automatic Gain Control<br/>Fast Attack / Slow Decay]
        AGC_RX --> PFB_RX[Polyphase Clock Sync<br/>Symbol Timing Recovery sps=2]
        PFB_RX --> COSTAS[Costas Carrier Recovery<br/>4th-Power Closed-Loop]
        
        COSTAS --> SOFT0[Direct Soft Demap<br/>Branch 0: 0 deg]
        COSTAS --> ROT90[Multiply by +j<br/>Branch 1: 90 deg]
        ROT90 --> SOFT1[Rotated Soft Demap]
        
        SOFT0 --> VIT0[Viterbi Decoder 0<br/>Rate 1/2, K=7 Capillary]
        SOFT1 --> VIT1[Viterbi Decoder 1<br/>Rate 1/2, K=7 Capillary]
        
        VIT0 --> FLYWHEEL[Dual-Branch Flywheel Sync<br/>0x1ACFFC1D / 0xE53003E2 Lock]
        VIT1 --> FLYWHEEL
        
        FLYWHEEL --> DESCRAM[CCSDS Descrambler<br/>LFSR Derandomizer]
        DESCRAM --> RS_DEC[Outer RS(255, 223) Decoder<br/>I = 8 Deinterleave, t=16]
        RS_DEC --> OUT_DATA[Decoded Telemetry<br/>1784 Bytes Transfer Frames]
    end

    subgraph Diagnostics ["4. Quality Assurance"]
        OUT_DATA --> DIAG[C++20 Diagnostic Analyzer<br/>CRC-16, Sync Loss, FER, BER]
    end
```

---

## Physical Layer Specifications

| Parameter | Value | Reference / Standard |
| :--- | :--- | :--- |
| **Downlink Center Frequency ($f_c$)** | $8.400\text{ GHz} - 10.475\text{ GHz}$ | Space Research (Deep Space / Earth Exploration) |
| **Modulation & Constellation** | QPSK (Gray Coded), $\alpha = 0.5$ RRC | CCSDS 131.0-B-5 Section 2 |
| **Sampling Rate ($f_s$)** | $25.0\text{ MSps}$ ($sps = 2$) | Baseband SDR Engine |
| **Baud Rate ($R_s$)** | $12.5\text{ MBaud}$ | $25.0\text{ Mbps}$ Raw Channel Rate |
| **Net Information Throughput** | $\approx 25.0\text{ Mbps}$ | Sustained Real-Time Execution |
| **Outer Forward Error Correction** | Reed-Solomon $RS(255, 223)$, $t=16$ bytes | CCSDS 131.0-B-5 Section 4 |
| **Interleaving Depth ($I$)** | $I = 8$ ($8 \times 223 = 1784\text{ bytes/frame}$) | CCSDS 131.0-B-5 Section 5 |
| **Pseudo-Randomization** | Synchronous LFSR: $h(x) = x^8 + x^7 + x^5 + x^3 + 1$ | CCSDS 131.0-B-5 Section 8 |
| **Attached Sync Marker (ASM)** | $32\text{ bits}$: `0x1ACFFC1D` (Orthogonal: `0xE53003E2`) | CCSDS 131.0-B-5 Section 7 |
| **Inner Forward Error Correction** | Convolutional Code Rate $1/2$, $K=7$, $[171_8, 133_8]$ | CCSDS 131.0-B-5 Section 3 |
| **Nominal LEO Orbit** | $475\text{ km}$ Sun-Synchronous Orbit ($i = 98^\circ$) | EPFL CHESS Mission |
| **Doppler Dynamic Range** | $\pm 250\text{ kHz}$ ($\pm 29.7\text{ ppm}$ at $8.4\text{ GHz}$) | Orbital Dynamics Model |

---

## Repository Structure

The repository is organized following clean, industry-standard modular software engineering practices:

```
.
├── README.md                      # Comprehensive project documentation
├── LICENSE                        # GNU General Public License v3.0
├── .gitignore                     # Optimized rules for build artifacts and large data
├── main_transceiver_simulation.py # Main end-to-end Python simulation runner
│
├── flowgraphs/                    # GNU Radio Companion flowgraphs and compiled scripts
│   ├── ccsds_xband_transceiver.grc# Main transceiver flowgraph
│   ├── RS_CC_TX_RCV.py            # Compiled Python top block
│   └── hier_blocks/               # Reusable hierarchical block definitions
│       ├── ccsds_concatenated_tx.grc # Encapsulated CCSDS transmitter
│       └── ccsds_concatenated_rx.grc # Encapsulated dual-branch receiver
│
├── data/                          # Critical test vectors and sync markers
│   ├── 32bitASM_CCSDS_only        # 32-bit CCSDS ASM marker (9 KB)
│   ├── test_signal_0.001Ms_CCSDS_I_8 # Lightweight 1,000-frame test vector (1.8 MB)
│   └── test_signal_0.06Ms_CCSDS_I_8  # Full 60,000-frame test vector (107 MB)
│
├── output/                        # Simulation and diagnostic outputs (gitignored)
│   ├── samples/test/              # Decoded output binary files (output_2m_3_50)
│   └── results/test/              # Detailed frame logs and BER/FER reports
│
├── scripts/                       # High-performance utility and diagnostic scripts
│   ├── diagnostic.cpp             # Hardware-accelerated C++20 BER/FER analyzer
│   ├── diagnostic                 # Compiled diagnostic binary
│   ├── generate_test_frames.py    # Synthetic CCSDS CADU frame generator
│   └── dump_performance.py       # ControlPort CPU and throughput benchmark logger
│
└── docs/                          # Academic documentation, papers, and thesis
    ├── Algoritmo_Doppler_Mth_Power_FFT_CCSDS.md # 4th-power FFT Doppler theory
    ├── thesis.pdf                 # Full undergraduate thesis manuscript
    ├── Page 1.pdf                 # Mission cover document
    ├── figures/                   # Vector architecture and performance figures
    ├── references/                # Reference literature, standards, and textbooks
    └── latex/                     # Complete LaTeX source code of the thesis
```

---

## Prerequisites & Dependencies

### System Requirements
- **OS:** Linux (Ubuntu 22.04 LTS / 24.04 LTS recommended)
- **Compiler:** `g++` with C++20 support (GCC 11+)
- **Python:** Python 3.10, 3.11, or 3.12 (System environment)
- **SDR Framework:** GNU Radio 3.10.x

### Required Out-of-Tree (OOT) Modules
1. **`gr-chess`**: Custom EPFL space communication blocks (`chess.doppler_channel`, `chess.fast_sync`, `chess.encode_rs`, `chess.ccsds_scrambler_tx`, `chess.ccsds_descrambler_rx`).
2. **`gr-satellites`**: Satellite telemetry decoding framework (`satellites.decode_rs`).

---

## Quickstart & Execution

### 1. Compile Hierarchical Blocks
Before running the main flowgraph, register the hierarchical blocks into GNU Radio's state directory:

```bash
cd flowgraphs/hier_blocks
grcc -u ccsds_concatenated_tx.grc
grcc -u ccsds_concatenated_rx.grc
```

### 2. Run the Full Transceiver Simulation
Execute the top-level runner to simulate the complete 60,000-frame transmission and automatic diagnostic evaluation:

```bash
# Execute simulation at nominal Eb/N0 = 3.50 dB
python3 main_transceiver_simulation.py --ebn0 3.50
```

### 3. Run Diagnostic Analysis Manually
You can re-run the C++ diagnostic analyzer on existing decoded outputs at any time:

```bash
cd scripts
# Compile if needed: g++ -O3 -std=c++20 diagnostic.cpp -o diagnostic
./diagnostic
```

### 4. Synthesize Custom Test Frames
Generate synthetic CCSDS CADU transfer frames with valid headers, sequence counters, pseudo-random payload, and CRC-16:

```bash
# Generate 5,000 test frames (1784 bytes each)
python3 scripts/generate_test_frames.py --frames 5000 --output data/test_signal_custom.bin
```

---

## Experimental Results

The receiver performance has been characterized with the full 60,000-frame ($107.05\text{ MB}$) test vector at $E_b/N_0 = 3.50\text{ dB}$ with interleaving depth $I=8$ under dynamic orbital Doppler shift:

```
========================================
             FINAL SUMMARY
========================================
=== FRAME METRICS ===
Total Frames Evaluated : 60000
Frames Rx (Valid CRC)  : 60000 (100.00%)
Frames Lost (Sync Fail): 0
Frames Rx (CRC Fail)   : 0
Frame Error Rate (FER) : 0.0000e+00

=== BIT ERROR RATES (BER) ===
Sync BER (Valid only)  : 0.0000e+00  <- Errors inside successfully received frames
Global System BER      : 0.0000e+00  <- Includes 50% penalty for useless frames
========================================
```

### Result Highlights
- **100.00% Frame Reception:** Zero sync slip events and zero lost frames across the entire transmission.
- **Flawless CRC Verification:** Every single transfer frame passed the CRC-16-CCITT check ($60,000 / 60,000$).
- **Strict Error Free Performance:** $\text{FER} = 0.0$ and $\text{BER} = 0.0$.

---

## Autonomous Doppler Estimation Research

For applications in commercial ground stations (NewSpace / GSaaS) where external ephemeris tools (such as Gpredict) are avoided, this project includes a comprehensive theoretical formulation of **Blind Coarse Doppler Estimation via 4th-Power Non-Linearity and FFT ($M$-th Power + FFT)**:
- Complete mathematical derivation proving the wipe-off of QPSK modulations ($s_k^4 = -1$).
- FFT processing gain ($G_{FFT} \approx 36.1\text{ dB}$) overcoming the 4th-power squaring loss ($S_L$).
- Sub-bin quadratic and Jacobsen interpolation achieving sub-Hertz accuracy ($\sigma_{\Delta f} < 15\text{ Hz}$).

Read the complete technical specification in:  
📖 **[`docs/Algoritmo_Doppler_Mth_Power_FFT_CCSDS.md`](docs/Algoritmo_Doppler_Mth_Power_FFT_CCSDS.md)**

---

## Academic Documentation & Thesis

The complete undergraduate thesis manuscript and LaTeX source code are preserved in the `docs/` folder:
- **Full Thesis PDF:** [`docs/thesis.pdf`](docs/thesis.pdf)
- **LaTeX Source Code:** [`docs/latex/`](docs/latex/)
- **Mission Reference Literature:** [`docs/references/`](docs/references/)

---

## License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)** - see the [LICENSE](LICENSE) file for details.
