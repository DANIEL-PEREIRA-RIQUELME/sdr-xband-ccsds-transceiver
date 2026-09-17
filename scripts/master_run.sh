#!/usr/bin/env bash
# ==============================================================================
# Master Execution Pipeline for CCSDS Transceiver Verification
#
# Author: Daniel Pereira Riquelme
# Institution: EPFL Spacecraft Team / Telecommunications Circuits Laboratory (TCL)
# License: GPL-3.0
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

echo "[1/2] Generating test vectors (if required)..."
if [ ! -f "../data/test_signal_0.06Ms_CCSDS_I_8" ]; then
    python3 generate_test_frames.py --frames 60000 --output ../data/test_signal_0.06Ms_CCSDS_I_8
fi

echo "[2/2] Executing main transceiver simulation..."
python3 ../main_transceiver_simulation.py --ebn0 3.50

echo "=== ALL DONE ==="
