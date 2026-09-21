#!/usr/bin/env python3
"""
CCSDS X-Band Transceiver Simulation
===================================
Runs one end-to-end simulation (transmitter, LEO Doppler channel, receiver) at
a given Eb/N0 and reports FER/BER with the C++ diagnostic tool.

Requires the hierarchical blocks to be compiled first:
    cd flowgraphs/hier_blocks && grcc -u ccsds_concatenated_tx.grc ccsds_concatenated_rx.grc

Author: Daniel Pereira Riquelme
Institution: EPFL Spacecraft Team / Telecommunications Circuits Laboratory (TCL)
License: GPL-3.0
"""

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Number of frames per signal tag; the 1,000-frame vector is shipped in the repository.
SIGNAL_FRAMES = {"0.001Ms": 1_000, "0.06Ms": 60_000}


def ensure_inputs(signal: str) -> None:
    """Builds the diagnostic tool and the test vector if they are missing."""
    if not (DATA_DIR / "32bitASM_CCSDS_only").exists():
        sys.exit(f"Missing {DATA_DIR / '32bitASM_CCSDS_only'}")

    vector = DATA_DIR / f"test_signal_{signal}_CCSDS_I_8"
    if not vector.exists():
        print(f"[*] Generating {vector.name} ({SIGNAL_FRAMES[signal]} frames)...")
        subprocess.check_call([sys.executable, str(SCRIPTS_DIR / "generate_test_frames.py"),
                               "--frames", str(SIGNAL_FRAMES[signal]), "--output", str(vector)])

    diagnostic = SCRIPTS_DIR / "diagnostic"
    if not diagnostic.exists():
        print("[*] Compiling scripts/diagnostic.cpp...")
        subprocess.check_call(["g++", "-O3", "-std=c++20", str(SCRIPTS_DIR / "diagnostic.cpp"),
                               "-o", str(diagnostic)])


def main() -> None:
    parser = argparse.ArgumentParser(description="CCSDS X-band transceiver simulation")
    parser.add_argument("--ebn0", type=float, default=3.50, help="Eb/N0 in dB (default: 3.50)")
    parser.add_argument("--signal", choices=sorted(SIGNAL_FRAMES), default="0.06Ms",
                        help="test vector: 0.001Ms (1,000 frames) or 0.06Ms (60,000 frames, default)")
    parser.add_argument("--keep-samples", action="store_true",
                        help="keep the decoded output file after the diagnostic")
    args = parser.parse_args()

    ensure_inputs(args.signal)

    # Imported here because it loads GNU Radio and the compiled hierarchical blocks.
    sys.path.insert(0, str(SCRIPTS_DIR))
    from run_point import run_point
    run_point(args.ebn0, args.signal, args.keep_samples)


if __name__ == "__main__":
    main()
