#!/usr/bin/env python3
"""
CCSDS Transceiver Performance Sweep Plotter (9 Points)
======================================================
Plots high-resolution Frame Error Rate (FER) and Bit Error Rate (BER) curves
across parameterized Eb/N0 values (2.0 dB to 4.0 dB) for the CCSDS concatenated pipeline.

Author: Daniel Pereira Riquelme
Institution: EPFL Spacecraft Team / Telecommunications Circuits Laboratory (TCL)
License: GPL-3.0
"""

import os
import re
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import scipy.special as sp

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "output/results/test"
DOCS_FIG_DIR = PROJECT_ROOT / "docs/figures"

points = [
    {"ebn0": 2.00, "file_ebn0": "2.00", "signal": "0.06Ms", "node": "Local PC"},
    {"ebn0": 2.25, "file_ebn0": "2.25", "signal": "0.06Ms", "node": "Local PC"},
    {"ebn0": 2.50, "file_ebn0": "2.50", "signal": "0.06Ms", "node": "Local PC"},
    {"ebn0": 2.75, "file_ebn0": "2.75", "signal": "0.3Ms",  "node": "Local PC"},
    {"ebn0": 3.00, "file_ebn0": "3.00", "signal": "0.3Ms",  "node": "Azure VM"},
    {"ebn0": 3.25, "file_ebn0": "3.25", "signal": "0.3Ms",  "node": "Azure VM"},
    {"ebn0": 3.50, "file_ebn0": "3.50", "signal": "1Ms",    "node": "Local PC"},
    {"ebn0": 3.75, "file_ebn0": "3.75", "signal": "1Ms",    "node": "Azure VM"},
    {"ebn0": 4.00, "file_ebn0": "4.00", "signal": "1Ms",    "node": "Local PC"},
]

data = []

for p in points:
    fn = os.path.join(RESULTS_DIR, f"diagnostic_results_ebn0.{p['file_ebn0']}.txt")
    if not os.path.exists(fn):
        print(f"Warning: File {fn} does not exist!")
        continue
    
    with open(fn, "r") as f:
        content = f.read()

    total_m = re.search(r"Total Frames Evaluated\s*:\s*(\d+)", content)
    rx_valid_m = re.search(r"Frames Rx \(Valid CRC\)\s*:\s*(\d+)", content)
    lost_m = re.search(r"Frames Lost \(Sync Fail\)\s*:\s*(\d+)", content)
    crc_fail_m = re.search(r"Frames Rx \(CRC Fail\)\s*:\s*(\d+)", content)
    fer_m = re.search(r"Frame Error Rate \(FER\)\s*:\s*([0-9\.eE+-]+)", content)
    sync_ber_m = re.search(r"Sync BER \(Valid only\)\s*:\s*([0-9\.eE+-]+)", content)
    global_ber_m = re.search(r"Global System BER\s*:\s*([0-9\.eE+-]+)", content)

    row = {
        "ebn0_db": p["ebn0"],
        "signal": p["signal"],
        "node": p["node"],
        "total_frames": int(total_m.group(1)) if total_m else 0,
        "valid_frames": int(rx_valid_m.group(1)) if rx_valid_m else 0,
        "lost_frames": int(lost_m.group(1)) if lost_m else 0,
        "crc_fail_frames": int(crc_fail_m.group(1)) if crc_fail_m else 0,
        "fer": float(fer_m.group(1)) if fer_m else 0.0,
        "sync_ber": float(sync_ber_m.group(1)) if sync_ber_m else 0.0,
        "global_ber": float(global_ber_m.group(1)) if global_ber_m else 0.0,
    }
    data.append(row)

# Save JSON summary
summary_json_path = os.path.join(RESULTS_DIR, "sweep_9points_summary.json")
with open(summary_json_path, "w") as f:
    json.dump(data, f, indent=4)
print(f"Summary saved to {summary_json_path}")

ebn0_vals = [d["ebn0_db"] for d in data]
fer_vals = [d["fer"] for d in data]
global_ber_vals = [d["global_ber"] for d in data]

# --- PLOTTING ---
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
fig, ax = plt.subplots(figsize=(11, 7), dpi=300)

# Uncoded QPSK theoretical curve for reference
ebn0_lin = 10.0 ** (np.linspace(1.5, 5.0, 200) / 10.0)
uncoded_qpsk_ber = 0.5 * sp.erfc(np.sqrt(ebn0_lin))
ax.semilogy(np.linspace(1.5, 5.0, 200), uncoded_qpsk_ber, 'k--', linewidth=1.5, alpha=0.6, label="Uncoded QPSK Theory (Reference)")

# Plot FER curve
ax.semilogy(ebn0_vals, fer_vals, 's-', color='#D9381E', linewidth=2.4, markersize=8, label="Frame Error Rate (FER) - CCSDS RS+Conv (I=8)")

# Plot Global System BER curve
ax.semilogy(ebn0_vals, global_ber_vals, 'o-', color='#1E56D9', linewidth=2.4, markersize=8, label="Global System BER (w/ 50% Lost Frame Penalty)")

# Data point annotations
for d in data:
    eb = d["ebn0_db"]
    fer = d["fer"]
    ber = d["global_ber"]
    ax.annotate(f"{fer:.1e}", (eb, fer), textcoords="offset points", xytext=(-8, 10), fontsize=8, fontweight='bold', color='#B02010')

# Annotations & Regions
ax.axvspan(2.0, 2.5, color='#FFE6CC', alpha=0.4, label="Waterfall Region (Steep Drop ~2.0 - 2.5 dB)")
ax.axvspan(3.0, 4.0, color='#D4EDDA', alpha=0.35, label=r"High Reliability Floor (FER < $3\cdot 10^{-4}$)")

# Styling & Labels
ax.set_xlabel(r"$E_b / N_0$ [dB]", fontsize=13, fontweight='bold', labelpad=8)
ax.set_ylabel("Error Probability (Log Scale)", fontsize=13, fontweight='bold', labelpad=8)
ax.set_title("X-Band SDR Downlink Performance Sweep: FER & Global BER vs $E_b/N_0$\nCCSDS 131.0-B-3 Concatenated Coding (RS(255,223) + Convolutional r=1/2, K=7, I=8)", 
             fontsize=13, fontweight='bold', pad=14)

ax.set_xlim(1.85, 4.15)
ax.set_ylim(4e-6, 1.2)
ax.set_xticks(ebn0_vals)
ax.set_xticklabels([f"{x:.2f} dB" for x in ebn0_vals], fontsize=10, fontweight='bold')
ax.grid(True, which="both", linestyle="--", alpha=0.6)

# Frame distribution note box
note_text = (
    "Sample Frame Depth:\n"
    "• 2.00 - 2.50 dB: 60,000 frames (0.06Ms)\n"
    "• 2.75 - 3.25 dB: 300,000 frames (0.3Ms)\n"
    "• 3.50 - 4.00 dB: 1,000,000 frames (1Ms)\n"
    "Distributed across Local PC & Azure VM"
)
ax.text(0.03, 0.05, note_text, transform=ax.transAxes, fontsize=9,
        verticalalignment='bottom', bbox=dict(boxstyle='round,pad=0.6', facecolor='#F8F9FA', edgecolor='#CED4DA', alpha=0.9))

ax.legend(loc="upper right", frameon=True, framealpha=0.95, facecolor='white', edgecolor='#D0D0D0', fontsize=10)

plt.tight_layout()

# Save targets
out_paths = [
    RESULTS_DIR / "ber_fer_sweep_9points.png",
    DOCS_FIG_DIR / "ber_fer_sweep_9points.png",
]

for p in out_paths:
    os.makedirs(os.path.dirname(p), exist_ok=True)
    plt.savefig(str(p), dpi=300)
    print(f"Saved figure to: {p}")

plt.close()
print("All plotting completed successfully!")
