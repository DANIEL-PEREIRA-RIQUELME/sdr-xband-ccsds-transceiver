# Changelog

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
