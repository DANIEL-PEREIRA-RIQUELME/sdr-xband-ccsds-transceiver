#!/usr/bin/env python3
"""
CCSDS Simulation Results and Doppler Convergence Plotter
========================================================
Parses diagnostic output files and ControlPort performance metrics to generate
Bit Error Rate (BER), Frame Error Rate (FER), and Doppler tracking convergence plots.

Author: Daniel Pereira Riquelme
Institution: EPFL Spacecraft Team / Telecommunications Circuits Laboratory (TCL)
License: GPL-3.0
"""

import os
import re
import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "output/results/test"
DOCS_FIGS_DIR = PROJECT_ROOT / "docs/figures"
DOCS_FIGS_DIR.mkdir(parents=True, exist_ok=True)

ebn0s = [2.0, 2.8, 3.6, 4.4, 5.2, 6.0]

# --- 1. BER & FER Curve ---
bers = []
for eb in ebn0s:
    diag_file = RESULTS_DIR / f"diagnostic_results_{eb}.txt"
    sys_ber = 1.0
    if diag_file.exists():
        with open(diag_file, 'r') as f:
            for line in f:
                if "FER:" in line:
                    match = re.search(r'FER:\s+([0-9\.eE+-]+)', line)
                    if match:
                        sys_ber = float(match.group(1))
    bers.append(sys_ber)

plt.figure(figsize=(8, 5))
plt.semilogy(ebn0s, bers, 'bo-', linewidth=2, markersize=7)
plt.grid(True, which="both", ls="-", alpha=0.5)
plt.xlabel("Eb/N0 (dB)", fontsize=11, fontweight='bold')
plt.ylabel("Frame Error Rate (FER)", fontsize=11, fontweight='bold')
plt.title("CCSDS Transceiver FER vs Eb/N0", fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig(DOCS_FIGS_DIR / "ber_curve_summary.png", dpi=150)
plt.close()

# --- 2. Doppler Curves ---
plt.figure(figsize=(10, 6))
curves_plotted = False
for eb in ebn0s:
    freq_file = RESULTS_DIR / f"freqs_{eb}.json"
    if freq_file.exists():
        try:
            with open(freq_file, 'r') as f:
                freqs = json.load(f)
            time_ms = np.arange(len(freqs)) * 5.24
            plt.plot(time_ms, freqs, label=f"Eb/N0 = {eb} dB")
            curves_plotted = True
        except Exception:
            pass

if curves_plotted:
    plt.xlabel("Time (ms)", fontsize=11, fontweight='bold')
    plt.ylabel("Estimated Doppler (Hz)", fontsize=11, fontweight='bold')
    plt.title("Coarse Doppler Sync Frequency Acquisition Convergence", fontsize=12, fontweight='bold')
    plt.legend(loc="upper right")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(DOCS_FIGS_DIR / "doppler_convergence.png", dpi=150)
plt.close()

# --- 3. CPU Performance Breakdown ---
perf_file = PROJECT_ROOT / "scripts/perf_metrics_average_10s.json"
if not perf_file.exists():
    perf_file = PROJECT_ROOT / "scripts/perf_metrics_promedio_10s.json"

if perf_file.exists():
    with open(perf_file, 'r') as f:
        perf = json.load(f)
    
    work_times = {}
    for block, metrics in perf.items():
        for k, v in metrics.items():
            if "work time" in k:
                bname = block.split('(')[0]
                work_times[bname] = v
                break

    if work_times:
        sorted_blocks = sorted(work_times.items(), key=lambda x: x[1], reverse=True)
        labels = [x[0] for x in sorted_blocks[:10]]
        sizes = [x[1] for x in sorted_blocks[:10]]
        
        if len(sorted_blocks) > 10:
            other = sum(x[1] for x in sorted_blocks[10:])
            labels.append("Other")
            sizes.append(other)

        descriptions = {
            'chess_coarse_doppler_sync': 'Coarse Doppler Sync (FFT Frequency Recovery)',
            'digital_costas_loop_cc': 'Costas Loop (Carrier Tracking & Phase Lock)',
            'chess_fast_sync': 'Fast Sync (ASM Framer & Phase Ambiguity)',
            'ccsds_concatenated_rx': 'CCSDS RX (Hierarchical Pipeline)',
            'fec_extended_decoder': 'Viterbi Decoder (Inner Convolutional Code)',
            'satellites_decode_rs_ccsds': 'Reed-Solomon Decoder (Outer RS FEC)',
            'digital_pfb_clock_sync_xxx': 'Polyphase Clock Sync (Symbol Timing Recovery)',
            'blocks_throttle2': 'Throttle (CPU Rate Limiter)',
            'blocks_file_source': 'File Source (TX Data Reader)',
            'chess_downlink_channel': 'Downlink Channel (LEO Channel Simulator)',
            'blocks_multiply_const_vxx': 'Multiply Const (90-deg Phase Rotation)',
            'digital_constellation_soft_decoder_cf': 'Soft Decoder (QPSK LLR Demapper)',
            'analog_agc_xx': 'AGC (Automatic Gain Control)'
        }
        
        mapped_labels = []
        for l in labels:
            base_name = re.sub(r'_[0-9]+$', '', l)
            base_name = re.sub(r'_[0-9]+$', '', base_name)
            desc = descriptions.get(base_name, None)
            if desc is None:
                for key, val in descriptions.items():
                    if key in l:
                        desc = val
                        break
            if desc is None:
                desc = l
            
            if "(" in desc:
                name, func = desc.split("(")
                mapped_labels.append(f"{name.strip()}\n({func}")
            else:
                mapped_labels.append(desc)

        plt.figure(figsize=(10, 10))
        plt.pie(sizes, labels=mapped_labels, autopct='%1.1f%%', startangle=140, textprops={'fontsize': 9})
        plt.title("CPU Utilization Breakdown by DSP Block (Top 10)", fontsize=13, fontweight='bold')
        plt.tight_layout()
        plt.savefig(DOCS_FIGS_DIR / "cpu_pie_chart.png", dpi=150)
        plt.close()

print("[+] Plotting completed successfully.")
