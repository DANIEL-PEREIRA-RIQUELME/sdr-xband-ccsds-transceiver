#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local CPU Bottleneck Breakdown Visualizer (Intel Core i5-1335U)
==============================================================
Generates high-resolution dual charts (Horizontal Ranking Bars + Doughnut Chart)
illustrating the per-block computational load across multi-threaded SDR blocks.

Author: Daniel Pereira Riquelme
Institution: EPFL Spacecraft Team / Telecommunications Circuits Laboratory (TCL)
License: GPL-3.0
"""
import os
import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
DOCS_FIGS = PROJECT_ROOT / "docs/figures"

with open(SCRIPTS_DIR / "local_block_profile.json", "r") as f:
    data = json.load(f)

avg_cores = data["avg_cpu_cores"]
total_cpu = data["total_cpu_percent"]

# Aggregate logical functional blocks
# Soft Demod (Dual branch 35 + 36)
soft_demod_cores = avg_cores.get("constellation35", 0.0) + avg_cores.get("constellation36", 0.0)
soft_demod_pct = round((soft_demod_cores / total_cpu) * 100.0, 2)

# PFB Clock Sync
pfb_cores = avg_cores.get("pfb_clock_syn33", 0.0)
pfb_pct = round((pfb_cores / total_cpu) * 100.0, 2)

# Downlink Channel Sim
channel_cores = avg_cores.get("chess_downlink2", 0.0)
channel_pct = round((channel_cores / total_cpu) * 100.0, 2)

# Costas Loop
costas_cores = avg_cores.get("costas_loop_c34", 0.0)
costas_pct = round((costas_cores / total_cpu) * 100.0, 2)

# TX Pulse Shaping
tx_rrc_cores = avg_cores.get("interp_fir_fil5", 0.0)
tx_rrc_pct = round((tx_rrc_cores / total_cpu) * 100.0, 2)

# Coarse Doppler Sync
doppler_cores = avg_cores.get("chess_coarse_d3", 0.0)
doppler_pct = round((doppler_cores / total_cpu) * 100.0, 2)

# Viterbi Decoder (Dual branch 28 + 32)
viterbi_cores = avg_cores.get("fec_decoder28", 0.0) + avg_cores.get("fec_decoder32", 0.0)
viterbi_pct = round((viterbi_cores / total_cpu) * 100.0, 2)

# AGC
agc_cores = avg_cores.get("agc_cc46", 0.0)
agc_pct = round((agc_cores / total_cpu) * 100.0, 2)

# Repack / Packing Bits
repack_cores = avg_cores.get("repack_bits_b19", 0.0) + avg_cores.get("pack_k_bits_b20", 0.0) + avg_cores.get("pack_k_bits_b44", 0.0)
repack_pct = round((repack_cores / total_cpu) * 100.0, 2)

# TX Encoders (RS + CC)
tx_enc_cores = avg_cores.get("chess_encode_10", 0.0) + avg_cores.get("fec_encoder8", 0.0)
tx_enc_pct = round((tx_enc_cores / total_cpu) * 100.0, 2)

# Reed-Solomon Decoder
rs_dec_cores = avg_cores.get("decode_rs22", 0.0)
rs_dec_pct = round((rs_dec_cores / total_cpu) * 100.0, 2)

# Grouped categories for visualization
categories = [
    ("Soft Demod (Dual Branch QPSK LLR)", soft_demod_pct, soft_demod_cores, "#e74c3c"),
    ("PFB Clock Sync (1704 taps)", pfb_pct, pfb_cores, "#e67e22"),
    ("Downlink Channel Sim", channel_pct, channel_cores, "#f1c40f"),
    ("Costas Loop (Carrier Lock)", costas_pct, costas_cores, "#3498db"),
    ("TX Pulse Shaping (RRC FIR)", tx_rrc_pct, tx_rrc_cores, "#9b59b6"),
    ("Viterbi Decoder (Dual Branch)", viterbi_pct, viterbi_cores, "#2ecc71"),
    ("Coarse Doppler Sync (4th FFT)", doppler_pct, doppler_cores, "#1abc9c"),
    ("Automatic Gain Control (AGC)", agc_pct, agc_cores, "#34495e"),
    ("Reed-Solomon Decoder (I=8)", rs_dec_pct, rs_dec_cores, "#27ae60"),
    ("Bit Packing / Repack", repack_pct, repack_cores, "#95a5a6"),
    ("TX RS + CC Encoders", tx_enc_pct, tx_enc_cores, "#7f8c8d"),
]

accounted_pct = sum(c[1] for c in categories)
other_pct = round(100.0 - accounted_pct, 2)
other_cores = round(total_cpu * (other_pct / 100.0), 2)
categories.append(("File I/O, Descrambler & Others", other_pct, other_cores, "#bdc3c7"))

# Reverse order for horizontal bar chart (highest at top)
bar_cats = list(reversed(categories))

labels = [c[0] for c in bar_cats]
pcts = [c[1] for c in bar_cats]
cores = [c[2] for c in bar_cats]
colors = [c[3] for c in bar_cats]

# Setup plot style
plt.style.use('default')
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8.5), gridspec_kw={'width_ratios': [1.2, 1]})

# --- 1. Horizontal Bar Chart ---
y_pos = np.arange(len(labels))
bars = ax1.barh(y_pos, pcts, color=colors, edgecolor='black', linewidth=0.8, height=0.7)

ax1.set_yticks(y_pos)
ax1.set_yticklabels(labels, fontsize=11, fontweight='bold')
ax1.set_xlabel('Consumo de CPU Relativo (%)', fontsize=13, fontweight='bold', labelpad=10)
ax1.set_xlim(0, 33)
ax1.set_ylim(-0.8, len(labels) + 0.6)
ax1.grid(axis='x', linestyle='--', alpha=0.6)
ax1.set_title(
    "Desglose de Consumo de CPU por Bloque DSP\n(Local PC - Intel Core i5-1335U [10 cores / 12 hilos])",
    fontsize=14,
    fontweight='bold',
    pad=15
)

# Annotate percentages on bars
for bar, pct, core in zip(bars, pcts, cores):
    w = bar.get_width()
    ax1.text(
        w + 0.3,
        bar.get_y() + bar.get_height() / 2,
        f"{pct:.1f}% ({core:.1f}% core)",
        va='center',
        ha='left',
        fontsize=10.5,
        fontweight='bold'
    )

# Cuello de botella #1 Callout (Soft Demod)
idx_top1 = len(labels) - 1
ax1.annotate(
    "BOTTLENECK #1\n(Soft Demod Dual: 122.6% CPU core)",
    xy=(pcts[idx_top1], idx_top1),
    xytext=(13.5, idx_top1 - 1.0),
    bbox=dict(boxstyle="round,pad=0.4", fc="#fadbd8", ec="#c0392b", lw=1.5),
    arrowprops=dict(facecolor="#c0392b", shrink=0.08, width=2, headwidth=8),
    fontsize=9.5,
    fontweight='bold',
    color="#922b21"
)

# Cuello de botella #2 Callout (PFB Clock Sync)
idx_top2 = len(labels) - 2
ax1.annotate(
    "BOTTLENECK #2\n(saturates one core at 98.5% - 1704 taps)",
    xy=(pcts[idx_top2], idx_top2),
    xytext=(11.5, idx_top2 - 1.7),
    bbox=dict(boxstyle="round,pad=0.4", fc="#fdebd0", ec="#d35400", lw=1.5),
    arrowprops=dict(facecolor="#d35400", shrink=0.08, width=2, headwidth=8),
    fontsize=9.5,
    fontweight='bold',
    color="#a04000"
)

# --- 2. Doughnut Chart ---
pie_labels = [f"{c[0]}: {c[1]}%" for c in categories]
pie_pcts = [c[1] for c in categories]
pie_colors = [c[3] for c in categories]

wedges, texts, autotexts = ax2.pie(
    pie_pcts,
    colors=pie_colors,
    autopct=lambda p: f"{p:.1f}%" if p >= 4.0 else "",
    pctdistance=0.78,
    startangle=140,
    wedgeprops=dict(width=0.45, edgecolor='white', linewidth=2)
)

for autotext in autotexts:
    autotext.set_fontsize(10)
    autotext.set_fontweight('bold')

# Center doughnut circle label
ax2.text(
    0, 0,
    f"CPU TOTAL\n{total_cpu:.0f}% / 1200%\n(12 hilos)",
    ha='center', va='center',
    fontsize=13, fontweight='bold',
    color='#2c3e50'
)

ax2.set_title("Overall CPU Load Distribution", fontsize=14, fontweight='bold', pad=15)
ax2.legend(
    wedges,
    pie_labels,
    title="Bloques DSP",
    loc="center left",
    bbox_to_anchor=(1.0, 0.5),
    fontsize=9.5,
    title_fontsize=11
)

plt.tight_layout()

# Save figure
out_docs = DOCS_FIGS / "cpu_breakdown_local.png"
plt.savefig(out_docs, dpi=180, bbox_inches='tight')
plt.close()

print(f"[+] Saved CPU breakdown chart to: {out_docs}")
