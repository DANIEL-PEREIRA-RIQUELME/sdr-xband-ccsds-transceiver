# Changelog

## Documentation review (2026-10-13)

### Fixed
- README and Doppler note: the orbital Doppler of the simulated pass is ±191 kHz with up to 2.95 kHz/s at zenith, not ±250 kHz with 2.5 kHz/s. ±250 kHz is the budget including oscillator offsets. The channel uses i = 53°, not a 98° sun-synchronous orbit.
- README installation: gr-HighDataRate_Modem is not used by any flowgraph. Timing recovery, the Costas loop, the soft demapper and the Viterbi decoder are GNU Radio blocks. The scrambler and the Reed-Solomon encoder come from gr-chess. gr-satellites provides only the Reed-Solomon decoder.
- Coherent gain stated with the Hann window loss (≈ 40.4 dB instead of 42.1 dB).
- Frame synchronizer: it returns to search after two consecutive misses (`max_misses = 1`), not "several".
- Results: removed the unsupported claim "BER below 10⁻⁶ at 4.0 dB with Doppler".

### Added
- `scripts/doppler_phase_test.py`: runs the C++ Doppler estimator against Eb/N0 for the two sampling phases. The README and the Doppler note give its results, including the timing-phase dependence, the inactive detection threshold and the interpolation bias.
- Note on the Eb/N0 calibration: the noise uses the I = 1 rate 223/259. For I = 8 the true Eb/N0 is 0.06 dB lower.


## Pre-release review (2026-09)

### Fixed
- `scripts/run_point.py` was excluded by `.gitignore` (`scripts/run_*.py`), so `batch_runner_local.py` and `batch_runner_azure.py` failed on a clean clone. It is now tracked.
- `run_point.py` reported FER and BER as `None`: it parsed lines that the diagnostic tool no longer prints. It now reads the diagnostic report file.
- Hard-coded personal paths removed from `scripts/diagnostic.cpp` and `scripts/profile_local_blocks.py`.

### Changed
- `main_transceiver_simulation.py` is now a thin wrapper around `run_point`. It no longer patches the generated flowgraph with regular expressions or writes a temporary top block into `flowgraphs/`. New options: `--signal {0.001Ms,0.06Ms}` and `--keep-samples`. It builds the diagnostic tool and generates the test vector when they are missing.
- `run_point.py` accepts the `0.001Ms` vector (1,000 frames, included in the repository) for quick runs.
- `docs/Blind_Doppler_Estimation_Mth_Power_FFT_CCSDS.md` rewritten. It now uses the parameters of the flowgraph (FFT 16384, decimation 8, 47.7 Hz carrier-domain bin width, 42.1 dB coherent gain) instead of 4096 points. It no longer calls the parabolic interpolation "Jacobsen", describes the decimator as sample-and-hold rather than a FIR, corrects the role of the inverted ASM `0xE53003E2` (polarity inversion, not a 90 degree rotation), and lists the limitations. Unmeasured claims (sigma < 15 Hz, MCRB, 1.5 % CPU, a closed-form squaring loss) were removed.
- README rewritten: shorter, factual, states that all results come from simulation, and describes the synchronizer as it is implemented (two states). Usage section updated to the commands that work.
- `docs/CPU_BREAKDOWN_METRICS.md`: "Flywheel" removed from the synchronizer name.

### Removed
- `flowgraphs/RS_CC_TX_RCV.py` (generated file with a hard-coded Python 3.12 path; regenerate with `grcc` if needed).
- `scripts/run_transceiver_simulation.py` (copy of the flowgraph) and `scripts/patch_and_run.py` (string-patched the generated code).
- Symlinks `files`, `results` and `samples`.
All of them remain in the git history.

### Verified
- Clean clones of both repositories: `gr-chess` builds and its 3 tests pass; `python3 main_transceiver_simulation.py --ebn0 4.0 --signal 0.001Ms` runs end to end with the freshly built `gr-chess` (FER about 0.02 on 1,000 frames; the lost frames are the acquisition at the start of the file, and the noise generator is not seeded so the value varies slightly between runs).
- The 60,000-frame vector is generated in about one minute.
- Not run: the batch runners, the plotting scripts and the CPU profilers.
