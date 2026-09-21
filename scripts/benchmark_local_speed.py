#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local Speed Benchmark for CCSDS X-Band Transceiver
==================================================
Runs at maximum CPU capability without throttle to measure real-time throughput,
sample processing rates, and execution time per frame.

Author: Daniel Pereira Riquelme
Institution: EPFL Spacecraft Team / Telecommunications Circuits Laboratory (TCL)
License: GPL-3.0
"""
import os
import sys
import math
import time
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output/samples/test"

# Paths to ensure GNU Radio and hierarchical blocks load properly
sys.path.insert(0, '/usr/lib/python3/dist-packages')
sys.path.insert(0, os.path.expanduser('~/.local/state/gnuradio'))
sys.path.insert(0, str(PROJECT_ROOT / 'flowgraphs'))

os.chdir(str(SCRIPTS_DIR))

from gnuradio import gr, blocks, chess
import pmt
from ccsds_concatenated_rx import ccsds_concatenated_rx
from ccsds_concatenated_tx import ccsds_concatenated_tx


class BenchmarkTransceiver(gr.top_block):
    def __init__(self, ebn0_db=4.0, costas_bw=0.001):
        super().__init__('BenchmarkTransceiver', catch_exceptions=False)

        sps = 2
        samp_rate = 25000000

        noise_volts = math.sqrt(sps / (10**(ebn0_db / 10.0) * (223.0 / 259.0)))
        self.channel = chess.downlink_channel(samp_rate, 8.4e9, 475, 90.0, 53.0, noise_volts, -150.0)
        self.coarse_doppler = chess.coarse_doppler_sync(samp_rate, 16384, 131072, 4, True, 0.7, 1.0, 8)

        self.tx = ccsds_concatenated_tx(interleave=8, rolloff=0.5, samp_rate=samp_rate, sps=sps)
        self.rx = ccsds_concatenated_rx(
            interleave=8,
            loop_bw=costas_bw,
            max_missed=1,
            rolloff=0.5,
            samp_rate=samp_rate,
            sps=sps,
            sync_threshold=0
        )

        input_data_path = str(DATA_DIR / "test_signal_0.06Ms_CCSDS_I_8")
        input_asm_path = str(DATA_DIR / "32bitASM_CCSDS_only")
        output_data_path = str(OUTPUT_DIR / "output_local_speed_test")

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        self.src_data = blocks.file_source(gr.sizeof_char, input_data_path, False, 0, 0)
        self.src_data.set_begin_tag(pmt.PMT_NIL)

        self.src_asm = blocks.file_source(gr.sizeof_char, input_asm_path, True, 0, 0)
        self.src_asm.set_begin_tag(pmt.PMT_NIL)

        self.sink = blocks.file_sink(gr.sizeof_char, output_data_path, False)
        self.sink.set_unbuffered(True)

        self.null_sink = blocks.null_sink(gr.sizeof_gr_complex)

        # Connect blocks bypassing throttle
        self.connect((self.src_asm, 0), (self.tx, 1))
        self.connect((self.src_data, 0), (self.tx, 0))
        self.connect((self.tx, 0), (self.channel, 0))
        self.connect((self.channel, 0), (self.coarse_doppler, 0))
        self.connect((self.coarse_doppler, 0), (self.rx, 0))
        self.connect((self.rx, 0), (self.sink, 0))
        self.connect((self.rx, 1), (self.null_sink, 0))


def main():
    print("=" * 65)
    print("  CCSDS X-Band Transceiver Speed Benchmark (Local PC)")
    print("=" * 65)
    print("  CPU Target       : Intel Core i5-1335U (10 cores / 12 threads)")
    print("  Test Vector      : 60,000 frames (107.05 MB)")
    print("  Channel Model    : LEO Doppler (475km, 8.4 GHz) + AWGN (Eb/N0 = 4.0 dB)")
    print("  Costas Loop BW   : 0.001 (1m)")
    print("  Throttle Mode    : BYPASSED (Maximum CPU throughput)")
    print("  Throughput Target: 15.00 Mbps Encoded Data")
    print("-" * 65)
    print("Starting simulation...")

    t0 = time.time()
    tb = BenchmarkTransceiver(ebn0_db=4.0, costas_bw=0.001)
    tb.start()
    tb.wait()
    t1 = time.time()

    duration = t1 - t0
    num_frames = 60000
    useful_bits = num_frames * 1784 * 8
    encoded_bits = num_frames * 32704  # 2044 bytes * 8 * 2 = 32704 bits / frame

    useful_mbps = (useful_bits / 1e6) / duration
    encoded_mbps = (encoded_bits / 1e6) / duration
    sample_rate_msps = (encoded_bits / 1e6) / duration
    fps = num_frames / duration

    print("\n" + "=" * 65)
    print("                 BENCHMARK RESULTS")
    print("=" * 65)
    print(f"  Total Duration       : {duration:.2f} seconds ({duration/60:.2f} min)")
    print(f"  Frames Processed     : {num_frames} frames ({fps:.2f} frames/sec)")
    print(f"  Useful Data Rate     : {useful_mbps:.2f} Mbps ({useful_mbps/8:.2f} MB/s)")
    print(f"  Encoded Data Rate    : {encoded_mbps:.2f} Mbps")
    print(f"  Sample Rate Achieved : {sample_rate_msps:.2f} MSps")
    print("-" * 65)

    reaches_15mbps = encoded_mbps >= 15.0
    status_str = "ALCANZADO / SUPERADO" if reaches_15mbps else "NO ALCANZADO"
    print(f"  Reaches 15 Mbps?: [{status_str}] ({encoded_mbps:.2f} Mbps / 15.00 Mbps -> {encoded_mbps/15.0*100:.1f}%)")
    print("=" * 65)

    # Run diagnostic
    diag_bin = SCRIPTS_DIR / "diagnostic"
    output_sample = OUTPUT_DIR / "output_local_speed_test"
    if diag_bin.exists() and output_sample.exists():
        print("\nEjecutando verificador de BER/FER (diagnostic)...")
        subprocess.run([str(diag_bin), str(output_sample)], cwd=str(SCRIPTS_DIR))


if __name__ == "__main__":
    main()
