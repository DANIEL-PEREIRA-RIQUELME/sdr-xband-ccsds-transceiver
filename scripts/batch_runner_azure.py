#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Azure Cloud Batch Runner for BER/FER Characterization
====================================================
Orchestrates parameterized simulations on Azure virtual machines across specified Eb/N0 values.

Author: Daniel Pereira Riquelme
Institution: EPFL Spacecraft Team / Telecommunications Circuits Laboratory (TCL)
License: GPL-3.0
"""
import sys
import time
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from run_point import run_point

AZURE_POINTS = [
    (3.00, "0.3Ms"),
    (3.25, "0.3Ms"),
    (3.75, "1Ms"),
]

if __name__ == "__main__":
    print("================================================================")
    print("  AZURE BATCH EXECUTION STARTED (3 points)")
    print("================================================================")
    overall_start = time.time()

    completed = []
    for idx, (ebn0, sig) in enumerate(AZURE_POINTS, 1):
        print(f"\n>>> [AZURE {idx}/{len(AZURE_POINTS)}] Launching Eb/N0 = {ebn0:.2f} dB ({sig})...")
        t_start = time.time()
        res = run_point(ebn0, sig, keep_samples=False)
        t_elapsed = time.time() - t_start
        completed.append(res)
        print(f">>> [AZURE {idx}/{len(AZURE_POINTS)}] FINISHED {ebn0:.2f} dB in {t_elapsed:.1f}s | FER={res.get('fer')} | BER={res.get('global_system_ber')}")

    total_time = time.time() - overall_start
    print("\n================================================================")
    print(f"  AZURE BATCH COMPLETED in {total_time:.2f}s ({total_time/60:.2f} min)")
    print("================================================================")
