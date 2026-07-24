# FIR Filter Design & SDR Signal Chain

Offline FIR filter design (windowed-sinc & Parks-McClellan) verified against theory and applied via a hand-written filter engine to live LimeSDR IQ capture — pure Python, no GNU Radio.

This project designs two FIR lowpass filters to the same spec using different methods, verifies each against theory with `freqz()`, implements the actual filtering operation by hand (no `numpy.convolve()` black box), and applies it to real IQ data captured from a LimeSDR. Results compare the hand-built filter's measured response against the theoretical design, and compare the two design methods against each other.

## Repo Structure

```
fir-filter-sdr/
├── README.md
├── .gitignore
├── requirements.txt
├── config.py
├── src/
│   ├── design.py
│   ├── fir.py
│   ├── capture.py
│   └── plotting.py
├── tests/
│   └── test_fir_impulse.py
├── scripts/
│   ├── run_design_verification.py
│   ├── run_windowing_comparison.py
│   ├── run_tap_count_comparison.py
│   ├── run_capture.py
│   └── run_capture_analysis.py
├── data/
│   ├── raw/
│   └── processed/
└── results/
    └── plots/
```

## File Descriptions

### Root

**`README.md`**
This file. Project overview, structure, and usage.

**`.gitignore`**
Excludes Python artifacts (`__pycache__/`, `*.pyc`, virtual environments), editor/OS clutter, and bulk raw IQ captures in `data/raw/` (aside from one checked-in sample buffer used as a reproducibility fixture).

**`requirements.txt`**
Pinned Python dependencies: `numpy`, `scipy`, `matplotlib`, `SoapySDR` bindings, `pytest`.

**`config.py`**
The single source of truth for every parameter shared across the project: cutoff frequency, transition width, stopband attenuation target, sample rate, center frequency, and starting tap count. Every design and capture script imports from here instead of hardcoding its own copy, so the filter design and the captured signal are always specified consistently.

### `src/` — core logic, imported by scripts, not run directly

**`src/design.py`**
Designs both FIR filters to the spec in `config.py`:
- Windowed-sinc method (via `scipy.signal.firwin`, or built directly from the sinc function and a window)
- Parks-McClellan / equiripple method (via `scipy.signal.remez`)

Runs `scipy.signal.freqz()` on each to compute the theoretical frequency response (magnitude, phase, group delay) and check it against the spec. Exposes functions to generate taps and theoretical response curves, used by the scripts in `scripts/`.

**`src/fir.py`**
The hand-written FIR filter engine — a sliding-window dot product implementation (loop or vectorized), explicitly not a call to `numpy.convolve()`. This is the actual filtering operation used everywhere in the project once taps have been designed. Also exposed here so it can be unit-tested independently in `tests/test_fir_impulse.py`.

**`src/capture.py`**
Interfaces with SoapySDR to configure and capture IQ data from the LimeSDR (sample rate, center frequency, gain, buffer length — pulled from `config.py`). Writes the captured buffer to `data/raw/`. This is the only file in the project that touches hardware.

**`src/plotting.py`**
Shared matplotlib helpers used by all the analysis scripts, so magnitude/phase plots, dB-scaled spectra, and overlay comparisons look consistent across every result in `results/plots/` rather than each script re-implementing its own styling.

### `tests/`

**`tests/test_fir_impulse.py`**
A `pytest` test, not a one-off script. Feeds an impulse through `src/fir.py`'s filter engine and asserts the output exactly matches the designed tap coefficients (within floating-point tolerance). Isolates implementation bugs in the hand-written engine from design bugs in `src/design.py`. Requires no hardware and should be run any time `fir.py` changes.

### `scripts/` — runnable entry points, one per deliverable

**`scripts/run_design_verification.py`**
Runs `src/design.py` for both filter methods, verifies each against the spec using `freqz()`, and saves:
- The designed taps for each method to `data/processed/`
- The theoretical response arrays to `data/processed/`
- A magnitude/phase/group-delay verification plot to `results/plots/`

No hardware required.

**`scripts/run_tap_count_comparison.py`**
Compares the tap count each method needed to hit the same spec (windowed-sinc vs. Parks-McClellan), using the designs already produced by `run_design_verification.py`. Produces a comparison plot/summary in `results/plots/`. No hardware required.

**`scripts/run_windowing_comparison.py`**
Designs three windowed-sinc filters at the same tap count using rectangular, Hamming, and Blackman windows, runs the same captured buffer from `data/raw/` through each via `src/fir.py`, FFTs each result, and overlays them to show the main-lobe-width vs. sidelobe-level trade-off. Requires a captured buffer to already exist.

**`scripts/run_capture.py`**
Calls `src/capture.py` to open the LimeSDR, capture a buffer of IQ samples at the parameters defined in `config.py`, and save it to `data/raw/`. The only script that requires hardware to be connected.

**`scripts/run_capture_analysis.py`**
Loads the raw IQ buffer from `data/raw/` and the taps/theoretical response saved by `run_design_verification.py`, runs the buffer through the hand-written filter in `src/fir.py`, FFTs the output, and overlays it against the theoretical `freqz()` prediction. Also produces the before/after spectrum plot showing the target signal component isolated or removed. This is where design, implementation, and live captured data are all checked against each other.

### `data/`

**`data/raw/`**
Captured IQ buffers written by `run_capture.py`. Bulk captures are gitignored; one small representative buffer is checked in so the analysis scripts can be run without hardware.

**`data/processed/`**
Intermediate artifacts from the design stage — saved tap arrays and theoretical response curves — consumed by the analysis scripts so they reuse the exact same designed filters rather than redesigning them.

### `results/`

**`results/plots/`**
All generated figures: the `freqz()` verification plot, the tap-count comparison, the windowing/spectral-leakage comparison, and the measured-vs-theoretical and before/after spectrum plots from captured data.

## Suggested Run Order

```
1. run_design_verification.py     (no hardware)
2. run_tap_count_comparison.py    (no hardware)
3. run_capture.py                 (requires LimeSDR)
4. run_capture_analysis.py        (requires step 1 + 3 outputs)
5. run_windowing_comparison.py    (requires step 3 output)
```

Run `pytest tests/` at any point after `src/fir.py` exists or changes.