#!/usr/bin/env python3
"""
CCSDS X-Band Satellite Transceiver Simulation Engine
====================================================
End-to-end simulation runner for the CCSDS 131.0-B-5 telemetry downlink pipeline.
Coordinates the GNU Radio transceiver flowgraph, channel dynamics, and executes
the C++ frame synchronization and BER/FER diagnostic analyzer.

Author: Daniel Pereira Riquelme
Institution: EPFL Spacecraft Team / Telecommunications Circuits Laboratory (TCL)
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Paths configuration
PROJECT_ROOT = Path(__file__).resolve().parent
FLOWGRAPHS_DIR = PROJECT_ROOT / "flowgraphs"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

SYSTEM_PYTHON = "/usr/bin/python3"


def check_prerequisites():
    """Validates that input data files and compiled hier blocks exist."""
    asm_file = DATA_DIR / "32bitASM_CCSDS_only"
    test_signal = DATA_DIR / "test_signal_0.06Ms_CCSDS_I_8"
    diag_bin = SCRIPTS_DIR / "diagnostic"

    if not asm_file.exists():
        print(f"[-] Error: Required ASM file not found at {asm_file}")
        sys.exit(1)

    if not test_signal.exists():
        print(f"[-] Warning: Standard test signal not found at {test_signal}")
        alt_signal = DATA_DIR / "test_signal_0.001Ms_CCSDS_I_8"
        if alt_signal.exists():
            print(f"[*] Found alternate test signal: {alt_signal}")

    if not diag_bin.exists():
        print("[*] Diagnostic binary not found. Compiling scripts/diagnostic.cpp...")
        cmd = ["g++", "-O3", "-std=c++20", str(SCRIPTS_DIR / "diagnostic.cpp"), "-o", str(diag_bin)]
        subprocess.check_call(cmd, cwd=str(SCRIPTS_DIR))
        print("[+] Compiled diagnostic tool successfully.")


def run_transceiver(ebn0_db: float = 3.50):
    """Executes the GNU Radio flowgraph using the system Python environment."""
    flowgraph_script = FLOWGRAPHS_DIR / "RS_CC_TX_RCV.py"
    if not flowgraph_script.exists():
        print(f"[*] Compiling flowgraph {FLOWGRAPHS_DIR / 'ccsds_xband_transceiver.grc'}...")
        subprocess.check_call(["grcc", "ccsds_xband_transceiver.grc"], cwd=str(FLOWGRAPHS_DIR))

    print(f"\n========================================================")
    print(f"  Starting CCSDS Transceiver Simulation (Eb/N0 = {ebn0_db:.2f} dB)")
    print(f"========================================================")

    env = os.environ.copy()
    user_pkg = os.path.expanduser('~/.local/lib/python3.12/dist-packages')
    user_lib = os.path.expanduser('~/.local/lib/x86_64-linux-gnu')
    env["PYTHONPATH"] = f"{user_pkg}:{FLOWGRAPHS_DIR}:{os.path.expanduser('~/.local/state/gnuradio')}:{env.get('PYTHONPATH', '')}"
    env["LD_LIBRARY_PATH"] = f"{user_lib}:{env.get('LD_LIBRARY_PATH', '')}"

    # Use system python to ensure access to system OOT modules (gr-chess, satellites)
    py_exec = SYSTEM_PYTHON if Path(SYSTEM_PYTHON).exists() else sys.executable
    cmd = [py_exec, str(flowgraph_script)]

    print(f"[*] Executing flowgraph via: {py_exec} {flowgraph_script.name}")
    ret = subprocess.run(cmd, cwd=str(PROJECT_ROOT), env=env)
    if ret.returncode != 0:
        print(f"[-] Transceiver execution exited with code {ret.returncode}")
    else:
        print(f"[+] Transceiver execution completed successfully.")


def run_diagnostic():
    """Runs the C++ diagnostic tool to calculate FER and BER metrics."""
    diag_bin = SCRIPTS_DIR / "diagnostic"
    print(f"\n========================================================")
    print(f"  Running C++ Frame & BER/FER Diagnostic Analyzer")
    print(f"========================================================")

    subprocess.run([str(diag_bin)], cwd=str(SCRIPTS_DIR))


def main():
    parser = argparse.ArgumentParser(description="CCSDS X-Band Satellite Transceiver Simulation Runner")
    parser.add_argument("--ebn0", type=float, default=3.50, help="Eb/N0 value in dB (default: 3.50)")
    parser.add_argument("--skip-sim", action="store_true", help="Skip flowgraph simulation and only run diagnostic")
    parser.add_argument("--no-diag", action="store_true", help="Do not run diagnostic tool after simulation")

    args = parser.parse_args()

    check_prerequisites()

    if not args.skip_sim:
        run_transceiver(args.ebn0)

    if not args.no_diag:
        run_diagnostic()


if __name__ == "__main__":
    main()
