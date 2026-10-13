#!/usr/bin/env python3
"""
Coarse Doppler estimator versus Eb/N0 and sampling phase
========================================================
Feeds the real `chess.coarse_doppler_sync` block (same parameters as the
flowgraph) with QPSK shaped by the transmitter's RRC taps, a constant carrier
offset and AWGN set with the flowgraph's noise formula. It runs two cases:
the 1-in-8 decimation landing on the symbol centre, and half a symbol later.

Each trial is 14 estimator buffers (14 x 131,072 samples), so the alpha = 0.7
smoothing, which starts from 0 Hz, has settled (0.3^14 of the offset is left).
An estimate counts as correct if it is within 200 Hz of the true offset.

Author: Daniel Pereira Riquelme
License: GPL-3.0
Usage: python3 scripts/doppler_phase_test.py [--trials 20]
"""
import argparse
import numpy as np
from gnuradio import gr, blocks, chess
from gnuradio.filter import firdes

FS = 25e6
N_FFT = 16384
DECIM = 8
SPS = 2
TRUE_OFFSET = 150e3
TAPS = np.array(firdes.root_raised_cosine(SPS, FS, FS / SPS, 0.5, 32))
DELAY = (len(TAPS) - 1) // 2


def shaped_qpsk(nsamp, phase, rng):
    nsym = nsamp // SPS + len(TAPS)
    sym = (rng.choice([1, -1], nsym) + 1j * rng.choice([1, -1], nsym)) / np.sqrt(2)
    up = np.zeros(nsym * SPS, complex)
    up[::SPS] = sym
    start = DELAY + 2 * SPS + phase      # phase 0: sample 0 at a symbol centre; 1: half a symbol later
    return np.convolve(up, TAPS)[start:start + nsamp]


def run_trial(ebn0_db, phase, seed, nbuf=14):
    rng = np.random.default_rng(seed)
    nsamp = N_FFT * DECIM * nbuf
    x = shaped_qpsk(nsamp, phase, rng)
    sigma2 = SPS / (10 ** (ebn0_db / 10) * (223 / 259))     # same formula as the flowgraph
    n = np.arange(nsamp)
    y = x * np.exp(1j * (2 * np.pi * TRUE_OFFSET * n / FS + rng.uniform(0, 2 * np.pi)))
    y += np.sqrt(sigma2 / 2) * (rng.standard_normal(nsamp) + 1j * rng.standard_normal(nsamp))

    tb = gr.top_block()
    src = blocks.vector_source_c(y.astype(np.complex64).tolist(), False)
    est = chess.coarse_doppler_sync(FS, N_FFT, N_FFT * DECIM, 4, True, 0.7, 1.0, DECIM)
    tb.connect(src, est, blocks.null_sink(gr.sizeof_gr_complex))
    tb.run()
    return est.get_doppler_freq()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=20)
    args = ap.parse_args()

    print(f"True offset {TRUE_OFFSET / 1e3:.0f} kHz, {args.trials} trials per point\n")
    print(f"{'phase':<14}{'Eb/N0 [dB]':>11}{'correct':>10}{'RMS error [Hz]':>16}")
    for phase, name in ((0, "symbol centre"), (1, "mid-symbol")):
        for ebn0 in (0.0, 1.0, 2.0, 3.2, 4.0, 6.0, 7.0, 8.0, 10.0):
            est = np.array([run_trial(ebn0, phase, s) for s in range(args.trials)])
            err = est - TRUE_OFFSET
            ok = np.abs(err) < 200
            rms = np.sqrt(np.mean(err[ok] ** 2)) if ok.any() else float("nan")
            print(f"{name:<14}{ebn0:>11.1f}{ok.mean():>10.0%}{rms:>16.1f}")
        print()


if __name__ == "__main__":
    main()
