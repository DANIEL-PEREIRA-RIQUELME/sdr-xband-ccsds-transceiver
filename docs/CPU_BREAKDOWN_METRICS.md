# DSP Block CPU Utilization Breakdown: Azure VM vs. Local Workstation

This technical document details the empirical performance benchmarks and block-by-block computational load breakdown for the Software-Defined CCSDS X-Band satellite telemetry transceiver evaluated across two distinct computing platforms:
1. **Azure Cloud Virtual Machine:** `Standard_B4as_v2` (4 vCPUs AMD EPYC 7763 @ 2.45 GHz, 16 GB RAM, Ubuntu 24.04).
2. **Local Multi-Core Workstation:** Intel Core i5-1335U (10 cores: 2 Performance + 8 Efficient, 12 threads @ up to 4.6 GHz, 16 GB RAM, Linux).

---

## 1. Remote Cloud Server: Microsoft Azure (AMD EPYC 7763 - 4 vCPUs)

![CPU Utilization Breakdown - Azure VM](figures/cpu_breakdown_azure.png)

### 1.1 Global Performance Metrics (Azure VM)
- **Test Vector:** 60,000 CCSDS CADU transfer frames ($107,057,840\text{ bytes}$ useful telemetry).
- **Total Processed Complex Samples:** 1,962,240,000 samples ($1.96\text{ Gsamples}$).
- **Channel Conditions:** $E_b/N_0 = 4.00\text{ dB}$, dynamic LEO Doppler ($475\text{ km}$ orbit, $8.4\text{ GHz}$), Costas loop bandwidth $= 0.001$ ($1\text{m}$).
- **Total Execution Time:** 219.08 seconds (3 minutes, 39 seconds).
- **Cumulative CPU Load:** 366.38% out of 400.00% available (91.60% machine saturation).
- **Encoded Channel Throughput:** 8.96 Mbps.
- **Decoded Useful Telemetry Throughput:** 3.91 Mbps (0.488 MB/s).
- **Sample Processing Rate:** 8.96 MSps.
- **Frame Processing Rate:** 273.87 frames/second.
- **Real-Time Baseline Percentage (25.00 Mbps):** 35.84% ($2.79\times$ slower than real time).
- **Link Verification (C++20 Diagnostic Tool):**
  - Evaluated Frames: 60,000 frames.
  - Received Frames with Valid CRC: 59,983 frames (99.97%).
  - Lost Frames (Initial Acquisition Transient): 17 frames (0.03%).
  - Corrupted Received Frames: 0 frames (0.00%).
  - Frame Error Rate (FER): $2.8333 \times 10^{-4}$.
  - Sync Bit Error Rate (Valid Frames): $0.0000 \times 10^{0}$ (strictly zero bit errors post-RS).
  - Global System BER (50% Lost Frame Penalty): $1.4167 \times 10^{-4}$.

### 1.2 Block-Level Load Breakdown (Azure VM)
- **`constellation_decoder_cb` (Dual Branch Soft QPSK LLR Demapper - Bottleneck #1):**
  - Relative Load: **21.05%**
  - Average CPU Consumption: **77.12%** of a core
- **`pfb_clock_sync_ccf` (Polyphase Clock Sync, 1,704 taps - Bottleneck #2):**
  - Relative Load: **18.51%**
  - Average CPU Consumption: **67.83%** of a core
- **`chess_downlink_channel` (LEO Dynamic Doppler + AWGN Channel Simulation):**
  - Relative Load: **12.93%**
  - Average CPU Consumption: **47.37%** of a core
- **`costas_loop_cc` (4th-Power Costas Carrier Tracking Loop):**
  - Relative Load: **7.69%**
  - Average CPU Consumption: **28.18%** of a core
- **`interp_fir_filter_ccf` (TX RRC Pulse Shaping Filter):**
  - Relative Load: **6.42%**
  - Average CPU Consumption: **23.51%** of a core
- **`chess_coarse_doppler_sync` (Autonomous Blind 4th-Power FFT Estimator):**
  - Relative Load: **5.49%**
  - Average CPU Consumption: **20.12%** of a core
- **`fec_decoder` Dual Branch (Rate 1/2, K=7 Viterbi Decoders, 2 branches):**
  - Combined Relative Load: **5.51%** (2.76% branch 1 + 2.75% branch 0)
  - Average CPU Consumption: **20.18%** of a core (10.10% branch 1 + 10.08% branch 0)
- **`agc_cc` (Automatic Gain Control):**
  - Relative Load: **4.05%**
  - Average CPU Consumption: **14.83%** of a core
- **Bit Repacking Blocks (`repack_bits_bb` + `pack_k_bits_bb`):**
  - Combined Relative Load: **2.83%**
  - Average CPU Consumption: **11.36%** of a core
- **Transmitter Encoders (`fec_encoder` CC + `chess_encode_rs`):**
  - Combined Relative Load: **2.53%**
  - Average CPU Consumption: **9.25%** of a core (5.27% CC + 3.98% RS)
- **Soft Metric Formatting (`float_to_uchar` branches 0 & 1):**
  - Combined Relative Load: **2.29%**
  - Average CPU Consumption: **8.39%** of a core
- **Phase Rotators (`multiply_const` $0^\circ$ and $90^\circ$):**
  - Combined Relative Load: **2.29%**
  - Average CPU Consumption: **8.38%** of a core
- **`decode_rs` (Reed-Solomon RS(255, 223) Decoder with I=8):**
  - Relative Load: **1.27%**
  - Average CPU Consumption: **4.66%** of a core
- **Pseudo-Randomizer / Descrambler (`additive_scrambler` TX & RX):**
  - Combined Relative Load: **1.28%**
  - Average CPU Consumption: **4.69%** of a core
- **TX Symbol Mapping (`chunks_to_symbols`):**
  - Relative Load: **0.88%**
  - Average CPU Consumption: **3.22%** of a core
- **`chess_fast_sync` (Frame Synchronizer & Ambiguity Resolver):**
  - Relative Load: **0.32%**
  - Average CPU Consumption: **1.17%** of a core
- **File I/O, Tagged Streams, Python Runtime, and OS Scheduling Overhead:**
  - Combined Relative Load: **6.99%**
  - Average CPU Consumption: **25.59%** of a core

---

## 2. Local Workstation: Intel Core i5-1335U (10 Cores / 12 Threads)

![CPU Utilization Breakdown - Local Workstation](figures/cpu_breakdown_local.png)

### 2.1 Global Performance Metrics (Local Workstation)
- **Test Vector:** 60,000 CCSDS CADU transfer frames ($107,057,840\text{ bytes}$ useful telemetry).
- **Total Processed Complex Samples:** 1,962,240,000 samples ($1.96\text{ Gsamples}$).
- **Channel Conditions:** $E_b/N_0 = 4.00\text{ dB}$, dynamic LEO Doppler ($475\text{ km}$, $8.4\text{ GHz}$), Costas loop bandwidth $= 0.001$ ($1\text{m}$).
- **Total Execution Time:** 135.02 seconds (2 minutes, 15 seconds).
- **Cumulative CPU Load:** 532.43% out of 1200.00% available (Performance cores fully utilized).
- **Encoded Channel Throughput:** 14.53 Mbps.
- **Decoded Useful Telemetry Throughput:** 6.34 Mbps (0.792 MB/s).
- **Sample Processing Rate:** 14.53 MSps.
- **Frame Processing Rate:** 444.39 frames/second.
- **Progress towards 15.00 Mbps Target:** 96.87% (within 0.47 Mbps of objective).
- **Real-Time Baseline Percentage (25.00 Mbps):** 58.12% ($1.72\times$ slower than real time).
- **Link Verification (C++20 Diagnostic Tool):**
  - Evaluated Frames: 60,000 frames.
  - Received Frames with Valid CRC: 59,983 frames (99.97%).
  - Lost Frames: 17 frames (0.03%).
  - Corrupted Frames: 0 frames (0.00%).
  - Frame Error Rate (FER): $2.8333 \times 10^{-4}$.
  - Sync Bit Error Rate: $0.0000 \times 10^{0}$ (strictly zero bit errors post-RS).
  - Global System BER: $1.4167 \times 10^{-4}$.

### 2.2 Block-Level Load Breakdown (Local Workstation)
- **`constellation_decoder_cb` Dual Branch (Soft Demod QPSK LLR - Bottleneck #1):**
  - Combined Relative Load: **23.03%**
  - Average CPU Consumption: **122.62%** of a core (62.70% branch 1 + 59.92% branch 0)
  - *Diagnosis:* Consumes more than one full physical core computing Euclidean distances concurrently for two orthogonal branches.
- **`pfb_clock_sync_ccf` (Polyphase Clock Sync, 1,704 taps - Bottleneck #2):**
  - Relative Load: **18.49%**
  - Average CPU Consumption: **98.45%** of a core
  - *Diagnosis:* **Saturates a single physical core at 98.45%**, representing the definitive single-threaded architectural bottleneck.
- **`chess_downlink_channel` (LEO Dynamic Doppler + AWGN Channel Simulation):**
  - Relative Load: **10.75%**
  - Average CPU Consumption: **57.25%** of a core
- **`costas_loop_cc` (4th-Power Costas Carrier Tracking Loop):**
  - Relative Load: **9.61%**
  - Average CPU Consumption: **51.19%** of a core
- **`interp_fir_filter_ccf` (TX RRC Pulse Shaping Filter):**
  - Relative Load: **5.69%**
  - Average CPU Consumption: **30.32%** of a core
- **`fec_decoder` Dual Branch (Rate 1/2, K=7 Viterbi Decoders, 2 branches):**
  - Combined Relative Load: **5.12%** (2.56% branch 1 + 2.56% branch 0)
  - Average CPU Consumption: **27.27%** of a core (13.65% branch 1 + 13.62% branch 0)
- **`chess_coarse_doppler_sync` (Autonomous Blind 4th-Power FFT Estimator):**
  - Relative Load: **5.09%**
  - Average CPU Consumption: **27.09%** of a core
- **`agc_cc` (Automatic Gain Control):**
  - Relative Load: **4.68%**
  - Average CPU Consumption: **24.94%** of a core
- **Bit Repacking Blocks (`repack_bits_bb` + `pack_k_bits_bb`):**
  - Combined Relative Load: **3.73%**
  - Average CPU Consumption: **19.86%** of a core
- **Transmitter Encoders (`fec_encoder` CC + `chess_encode_rs`):**
  - Combined Relative Load: **2.24%**
  - Average CPU Consumption: **11.92%** of a core
- **Soft Metric Formatting (`float_to_uchar` branches 0 & 1):**
  - Combined Relative Load: **2.04%**
  - Average CPU Consumption: **10.85%** of a core
- **`decode_rs` (Reed-Solomon RS(255, 223) Decoder with I=8):**
  - Relative Load: **1.33%**
  - Average CPU Consumption: **7.06%** of a core
- **Pseudo-Randomizer / Descrambler (`additive_scrambler` TX & RX):**
  - Combined Relative Load: **1.30%**
  - Average CPU Consumption: **6.92%** of a core
- **Phase Rotators (`multiply_const` $90^\circ$):**
  - Relative Load: **1.01%**
  - Average CPU Consumption: **5.37%** of a core
- **TX Symbol Mapping (`chunks_to_symbols`):**
  - Relative Load: **0.87%**
  - Average CPU Consumption: **4.61%** of a core
- **`chess_fast_sync` (Frame Synchronizer & Ambiguity Resolver):**
  - Relative Load: **0.26%**
  - Average CPU Consumption: **1.37%** of a core
- **File I/O, Tagged Streams, Python Runtime, and OS Scheduling Overhead:**
  - Combined Relative Load: **4.78%**
  - Average CPU Consumption: **25.46%** of a core

---

## 3. Platform Comparison Summary

| Metric | Azure VM (AMD EPYC 7763) | Local PC (Intel Core i5-1335U) | Target Requirement |
| :--- | :--- | :--- | :--- |
| **Execution Time (60,000 frames)** | 219.08 s | **135.02 s** (+62.2% faster) | Real-time pass |
| **Encoded Throughput** | 8.96 Mbps | **14.53 Mbps** | 25.00 Mbps |
| **Useful Decoded Telemetry** | 3.91 Mbps (0.488 MB/s) | **6.34 Mbps** (0.792 MB/s) | 10.91 Mbps |
| **Primary Bottleneck #1** | Soft QPSK Demapper (21.05%) | Soft QPSK Demapper (23.03%) | SIMD AVX2 acceleration |
| **Primary Bottleneck #2** | PFB Clock Sync (18.51%) | PFB Clock Sync (**98.45% single-core**) | Filter tap reduction |

### Operational Deployment Note
In a live ground station receiver connected directly to an RF frontend (e.g., USRP or SDR hardware):
- The software channel emulator (`chess_downlink_channel`) is omitted, saving **10.75% to 12.93%** CPU load.
- The software transmitter blocks (`interp_fir_filter_ccf`, `fec_encoder`, etc.) are omitted, saving an additional **~9%** CPU load.
- **Estimated Live SDR Throughput:** Disconnecting software simulation blocks instantly elevates receiver throughput from **14.53 Mbps to ~17.5 Mbps** on the local workstation without algorithmic changes.
