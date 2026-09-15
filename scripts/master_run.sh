#!/bin/bash
set -e

cd "/home/dan/Documents/PROJECTS/X-band TFG/scripts"

echo "[1/3] Generating 0.3Ms test signal (300,000 frames)..."
python3 generate_test_frames.py --frames 300000 --output ../data/test_signal_0.3Ms_CCSDS_I_8

echo "[2/2] Running batch Eb/N0 simulations..."
python3 run_batch_ebn0.py

echo "=== ALL DONE ==="
