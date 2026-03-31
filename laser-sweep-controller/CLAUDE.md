# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python module for automated wavelength sweeps on tunable lasers (Santec TSL-570) with optional PicoScope 5000 Series data acquisition. Extracted from a legacy GUI into a clean programmatic API.

## Running

```bash
# Install dependencies
pip install -r requirements.txt

# Interactive CLI
python main.py

# Run tests
pytest src/tests/ -v

# Programmatic usage
from src.laser_sweep import perform_laser_sweep
results, folder = perform_laser_sweep(wavelength_min=1540.0, wavelength_max=1560.0, power=10.0)
```

No build step. `examples/laser_sweep_examples.py` contains usage demonstrations.

## Architecture

**Entry points:**
- `main.py` — CLI with interactive parameter prompts and confirmation before sweep
- `src/laser_sweep.py` — Core module; import `perform_laser_sweep()` or use `LaserController` directly
- `examples/laser_sweep_examples.py` — Example functions demonstrating all major features
- `src/tests/test_laser_sweep.py` — Unit tests (no hardware required, fully mocked)

**Core flow:**
1. `perform_laser_sweep()` is a convenience wrapper around `LaserController`
2. `LaserController.validate_parameters()` checks wavelength/power against hardware limits
3. `configure_sweep()` sends SCPI commands to the laser and configures PicoScope sampling
4. `perform_single_sweep()` triggers the laser and acquires oscilloscope data
5. Results saved per-repetition: `{timestamp}/rep00X_data.csv`, `rep00X_plot.png`, plus a `sweep_log.txt`

**Hardware connections:**

| Laser | Connection | Address |
|-------|-----------|---------|
| 1550nm | GPIB | `GPIB0::10::INSTR` |
| 1400nm | LAN | `TCPIP::192.168.31.12::5000::SOCKET` |
| 1300nm | LAN | `TCPIP::192.168.31.11::5000::SOCKET` |

Laser configs are hard-coded in `LASER_CONFIGS` dict at the top of `src/laser_sweep.py` (lines 28–47). Modify there to add new lasers or update IP addresses.

**PicoScope defaults:** 12-bit resolution, Channel A 5V DC, Channel B 2V DC, triggered on Channel A rising edge at 1V. Sampling interval is auto-calculated from sweep speed.

**Output CSV columns:** `Wavelength_nm`, `Channel_A_V`, `Channel_B_V`

## Key Files

- `src/laser_sweep.py` — All instrument logic; `LaserController` class + `perform_laser_sweep()` function
- `main.py` — Interactive CLI entry point
- `src/tests/test_laser_sweep.py` — Unit tests; run with `pytest src/tests/ -v`
- `examples/laser_sweep_examples.py` — Usage demonstrations
- `docs/installation.md` — VISA backend, PicoScope drivers, GPIB driver setup per OS
