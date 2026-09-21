#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Single-Point Simulation and Diagnostic Runner for the CCSDS X-Band Transceiver
==============================================================================
Runs the transmitter, channel and receiver headless for one Eb/N0 value and
passes the decoded frames to the C++ diagnostic tool.

Signals: 0.001Ms (1,000 frames, included in the repository), 0.06Ms
(60,000 frames), 0.3Ms and 1Ms (generate them with generate_test_frames.py).

Author: Daniel Pereira Riquelme
Institution: EPFL Spacecraft Team / Telecommunications Circuits Laboratory (TCL)
License: GPL-3.0
"""
import os
import re
import sys
import math
import time
import json
import argparse
import subprocess
from pathlib import Path

# Paths configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
SAMPLES_DIR = OUTPUT_DIR / "samples/test"
RESULTS_DIR = OUTPUT_DIR / "results/test"

# Hierarchical blocks compiled with `grcc -u` are installed here.
sys.path.insert(0, os.path.join(os.getenv("XDG_STATE_HOME", os.path.expanduser("~/.local/state")), "gnuradio"))
sys.path.insert(0, str(PROJECT_ROOT / 'flowgraphs'))

os.chdir(str(SCRIPTS_DIR))

from gnuradio import gr, blocks, chess
import pmt
from ccsds_concatenated_rx import ccsds_concatenated_rx
from ccsds_concatenated_tx import ccsds_concatenated_tx


class PointTransceiver(gr.top_block):
    def __init__(self, input_file, output_file, ebn0_db=4.0, costas_bw=0.001):
        super().__init__('PointTransceiver', catch_exceptions=False)

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

        input_asm_path = str(DATA_DIR / "32bitASM_CCSDS_only")
        self.src_data = blocks.file_source(gr.sizeof_char, str(input_file), False, 0, 0)
        self.src_data.set_begin_tag(pmt.PMT_NIL)

        self.src_asm = blocks.file_source(gr.sizeof_char, input_asm_path, True, 0, 0)
        self.src_asm.set_begin_tag(pmt.PMT_NIL)

        self.sink = blocks.file_sink(gr.sizeof_char, str(output_file), False)
        self.sink.set_unbuffered(True)

        self.null_sink = blocks.null_sink(gr.sizeof_gr_complex)

        # Bypass throttle for maximum execution speed
        self.connect((self.src_asm, 0), (self.tx, 1))
        self.connect((self.src_data, 0), (self.tx, 0))
        self.connect((self.tx, 0), (self.channel, 0))
        self.connect((self.channel, 0), (self.coarse_doppler, 0))
        self.connect((self.coarse_doppler, 0), (self.rx, 0))
        self.connect((self.rx, 0), (self.sink, 0))
        self.connect((self.rx, 1), (self.null_sink, 0))


def run_point(ebn0: float, signal_tag: str, keep_samples: bool = False):
    signal_map = {
        "0.001Ms": DATA_DIR / "test_signal_0.001Ms_CCSDS_I_8",
        "0.06Ms": DATA_DIR / "test_signal_0.06Ms_CCSDS_I_8",
        "0.3Ms": DATA_DIR / "test_signal_0.3Ms_CCSDS_I_8",
        "1Ms": DATA_DIR / "test_signal_1Ms_CCSDS_I_8",
    }

    if signal_tag not in signal_map:
        raise ValueError(f"Unknown signal tag: {signal_tag}. Must be one of {list(signal_map.keys())}")

    input_file = signal_map[signal_tag]
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    formatted_ebn0 = f"{ebn0:.2f}"
    output_sample_file = SAMPLES_DIR / f"output_ebn0_{formatted_ebn0}"

    print("=" * 60)
    print(f"[*] RUNNING POINT: Eb/N0 = {ebn0:.2f} dB | Signal: {signal_tag}")
    print(f"[*] Input file: {input_file.name}")
    print(f"[*] Output sample: {output_sample_file.name}")
    print("=" * 60)

    t0 = time.time()
    tb = PointTransceiver(input_file, output_sample_file, ebn0_db=ebn0, costas_bw=0.001)
    tb.start()
    tb.wait()
    t1 = time.time()

    duration = t1 - t0
    print(f"[+] Simulation completed in {duration:.2f}s ({duration/60:.2f} min)")

    # Run C++ diagnostic
    diag_bin = SCRIPTS_DIR / "diagnostic"
    cmd = [str(diag_bin), str(output_sample_file), str(input_file)]
    diag_proc = subprocess.run(cmd, cwd=str(SCRIPTS_DIR), capture_output=True, text=True)

    print("--- DIAGNOSTIC SUMMARY ---")
    diag_report = RESULTS_DIR / f"diagnostic_results_ebn0.{formatted_ebn0}.txt"
    report = diag_report.read_text() if diag_report.exists() else ""
    if not report:
        print(f"[-] Diagnostic produced no report ({diag_proc.stderr.strip() or 'no error output'})")

    def field(label, cast):
        """Reads the number after `label :` in the diagnostic report."""
        m = re.search(rf"{re.escape(label)}\s*:\s*([0-9.eE+-]+)", report)
        return cast(m.group(1)) if m else None

    total_eval = field("Total Frames Evaluated", int)
    valid_frames = field("Frames Rx (Valid CRC)", int)
    lost_frames = field("Frames Lost (Sync Fail)", int)
    fer = field("Frame Error Rate (FER)", float)
    sync_ber = field("Sync BER (Valid only)", float)
    sys_ber = field("Global System BER", float)

    result = {
        "ebn0_db": ebn0,
        "signal": signal_tag,
        "duration_s": round(duration, 2),
        "total_frames_eval": total_eval,
        "valid_frames": valid_frames,
        "lost_frames": lost_frames,
        "fer": fer,
        "sync_ber": sync_ber,
        "global_system_ber": sys_ber
    }

    result_json_path = RESULTS_DIR / f"result_point_{formatted_ebn0}.json"
    with open(result_json_path, "w") as f:
        json.dump(result, f, indent=4)

    print(f"[+] Saved point result to {result_json_path}")
    print(f"    FER: {fer} | System BER: {sys_ber}")

    # Remove huge binary sample file if requested to keep disk clean
    if not keep_samples and output_sample_file.exists():
        try:
            output_sample_file.unlink()
            print(f"[*] Cleaned up intermediate sample file ({output_sample_file.name})")
        except Exception as e:
            print(f"[-] Warning deleting sample file: {e}")

    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run single-point CCSDS transceiver simulation")
    parser.add_argument("--ebn0", type=float, required=True, help="Eb/N0 in dB")
    parser.add_argument("--signal", type=str, required=True, choices=["0.001Ms", "0.06Ms", "0.3Ms", "1Ms"], help="Signal tag")
    parser.add_argument("--keep-samples", action="store_true", help="Do not delete output sample file after diagnostic")
    args = parser.parse_args()

    run_point(args.ebn0, args.signal, args.keep_samples)
