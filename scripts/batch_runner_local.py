#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local Batch Runner for BER/FER Characterization
==============================================
Orchestrates parameterized simulations on local hardware across specified Eb/N0 values.

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

LOCAL_POINTS = [
    (2.00, "0.06Ms"),
    (2.25, "0.06Ms"),
    (2.50, "0.06Ms"),
    (2.75, "0.3Ms"),
    (3.50, "1Ms"),
    (4.00, "1Ms"),
]

if __name__ == "__main__":
    print("================================================================")
    print("  LOCAL BATCH EXECUTION STARTED (6 points)")
    print("================================================================")
    overall_start = time.time()

    completed = []
    for idx, (ebn0, sig) in enumerate(LOCAL_POINTS, 1):
        print(f"\n>>> [LOCAL {idx}/{len(LOCAL_POINTS)}] Launching Eb/N0 = {ebn0:.2f} dB ({sig})...")
        t_start = time.time()
        res = run_point(ebn0, sig, keep_samples=False)
        t_elapsed = time.time() - t_start
        completed.append(res)
        print(f">>> [LOCAL {idx}/{len(LOCAL_POINTS)}] FINISHED {ebn0:.2f} dB in {t_elapsed:.1f}s | FER={res.get('fer')} | BER={res.get('global_system_ber')}")

    total_time = time.time() - overall_start
    print("\n================================================================")
    print(f"  LOCAL BATCH COMPLETED in {total_time:.2f}s ({total_time/60:.2f} min)")
    print("================================================================")
