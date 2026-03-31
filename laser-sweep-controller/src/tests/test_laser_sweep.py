"""
Tests for laser_sweep.py — no physical hardware required.

PicoScope and laser VISA connections are fully mocked via sys.modules
injection before laser_sweep is imported.

Run with:
    pytest test_laser_sweep.py -v
"""

import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import matplotlib
matplotlib.use("Agg")  # non-interactive backend — must be set before pyplot import
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

# ── Inject hardware stubs before laser_sweep is imported ─────────────────────
_pyvisa_stub = MagicMock()
_picoscope_stub = MagicMock()
_ps5000a_stub = MagicMock()
_picoscope_stub.ps5000a = _ps5000a_stub

sys.modules["pyvisa"] = _pyvisa_stub
sys.modules["picoscope"] = _picoscope_stub
sys.modules["picoscope.ps5000a"] = _ps5000a_stub

from laser_sweep import LaserController  # noqa: E402

# ── Sweep parameters used across all tests ────────────────────────────────────
WL_MIN = 1540.0
WL_MAX = 1560.0
POWER = 10.0
SWEEP_SPEED = 20.0      # nm/s
ACTUAL_INTERVAL = 1e-4  # 100 µs/sample  →  step = interval × speed = 2e-3 nm
NUM_SAMPLES = 10_000


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def no_sleep():
    """Patch time.sleep so tests finish instantly."""
    with patch("time.sleep"):
        yield


@pytest.fixture
def fake_data():
    rng = np.random.default_rng(42)
    data_a = rng.uniform(0.0, 5.0, NUM_SAMPLES).astype(np.float32)
    data_b = rng.uniform(0.1, 0.6, NUM_SAMPLES).astype(np.float32)
    return data_a, data_b


@pytest.fixture
def ctrl(fake_data):
    """LaserController with all hardware mocked and connected."""
    data_a, data_b = fake_data

    ps = MagicMock()
    ps.setSamplingInterval.return_value = (ACTUAL_INTERVAL, NUM_SAMPLES, None)
    ps.getDataV.side_effect = lambda ch, n=None: data_a if ch == "A" else data_b

    laser = MagicMock()
    laser.query.return_value = "MockLaser IDN"

    rm = MagicMock()
    rm.open_resource.return_value = laser

    _ps5000a_stub.PS5000a.return_value = ps
    _pyvisa_stub.ResourceManager.return_value = rm

    c = LaserController(laser_name="1550nm Laser", use_picoscope=True)
    c.connect()
    return c


def _run_sweep(ctrl, tmp_path, repetitions=1):
    """Run perform_sweep, redirecting /results → tmp_path/results."""
    results_root = tmp_path / "results"
    results_root.mkdir(exist_ok=True)

    original_join = os.path.join

    def patched_join(a, *args):
        if a == "/results":
            a = str(results_root)
        return original_join(a, *args)

    with patch("os.path.join", side_effect=patched_join):
        results, folder = ctrl.perform_sweep(
            wavelength_min=WL_MIN,
            wavelength_max=WL_MAX,
            power=POWER,
            sweep_speed=SWEEP_SPEED,
            repetitions=repetitions,
            num_samples=NUM_SAMPLES,
        )

    return results, folder, str(results_root)


@pytest.fixture
def sweep1(ctrl, tmp_path):
    """Single-rep sweep with redirected output. Returns (results, folder, results_root)."""
    return _run_sweep(ctrl, tmp_path, repetitions=1)


@pytest.fixture
def captured_ax(ctrl, tmp_path):
    """Run a 1-rep sweep and capture the matplotlib Axes before plt.close() discards it."""
    results_root = tmp_path / "results"
    results_root.mkdir()

    original_subplots = plt.subplots
    original_join = os.path.join
    captured = {}

    def mock_subplots(*args, **kwargs):
        fig, ax = original_subplots(*args, **kwargs)
        captured["ax"] = ax
        return fig, ax

    def patched_join(a, *args):
        if a == "/results":
            a = str(results_root)
        return original_join(a, *args)

    with patch("os.path.join", side_effect=patched_join), \
         patch("matplotlib.pyplot.subplots", side_effect=mock_subplots):
        ctrl.perform_sweep(
            WL_MIN, WL_MAX, POWER, SWEEP_SPEED,
            repetitions=1, num_samples=NUM_SAMPLES,
        )

    return captured["ax"], str(results_root)


# ── Output structure ──────────────────────────────────────────────────────────

class TestOutputStructure:

    def test_folder_is_inside_results(self, sweep1):
        _, folder, results_root = sweep1
        assert folder.startswith(results_root)

    def test_folder_name_format(self, sweep1):
        _, folder, _ = sweep1
        name = os.path.basename(folder)
        date = datetime.now().strftime("%d_%m_%Y")
        assert name == f"{WL_MIN}_{WL_MAX}-{date}"

    def test_sweep_log_created(self, sweep1):
        _, folder, _ = sweep1
        assert os.path.isfile(os.path.join(folder, "sweep_log.txt"))

    def test_single_rep_files_exist(self, sweep1):
        _, folder, _ = sweep1
        assert os.path.isfile(os.path.join(folder, "001.csv"))
        assert os.path.isfile(os.path.join(folder, "001.png"))

    def test_multi_rep_files_exist(self, ctrl, tmp_path):
        _, folder, _ = _run_sweep(ctrl, tmp_path, repetitions=3)
        for i in ("001", "002", "003"):
            assert os.path.isfile(os.path.join(folder, f"{i}.csv")), f"{i}.csv missing"
            assert os.path.isfile(os.path.join(folder, f"{i}.png")), f"{i}.png missing"

    def test_no_extra_csv_files(self, ctrl, tmp_path):
        _, folder, _ = _run_sweep(ctrl, tmp_path, repetitions=2)
        csvs = [f for f in os.listdir(folder) if f.endswith(".csv")]
        assert len(csvs) == 2

    def test_no_extra_png_files(self, ctrl, tmp_path):
        _, folder, _ = _run_sweep(ctrl, tmp_path, repetitions=2)
        pngs = [f for f in os.listdir(folder) if f.endswith(".png")]
        assert len(pngs) == 2


# ── CSV format ────────────────────────────────────────────────────────────────

class TestCSV:

    def _df(self, sweep1, rep="001"):
        _, folder, _ = sweep1
        return pd.read_csv(os.path.join(folder, f"{rep}.csv"))

    def test_column_names_match_gui(self, sweep1):
        df = self._df(sweep1)
        assert list(df.columns) == ["Wavelength_nm", "Amplitude_V"]

    def test_exactly_two_columns(self, sweep1):
        df = self._df(sweep1)
        assert len(df.columns) == 2

    def test_wavelength_within_range(self, sweep1):
        df = self._df(sweep1)
        assert df["Wavelength_nm"].min() >= WL_MIN
        assert df["Wavelength_nm"].max() <= WL_MAX

    def test_wavelength_monotonically_increasing(self, sweep1):
        df = self._df(sweep1)
        assert df["Wavelength_nm"].is_monotonic_increasing

    def test_wavelength_from_time_axis_not_linspace(self, sweep1):
        """Wavelengths must follow interval × speed, not be evenly spaced by linspace."""
        df = self._df(sweep1)
        # Time-axis derivation (mirrors GUI and laser_sweep.py logic)
        expected = WL_MIN + np.arange(NUM_SAMPLES) * ACTUAL_INTERVAL * SWEEP_SPEED
        expected = expected[expected <= WL_MAX]
        np.testing.assert_allclose(df["Wavelength_nm"].values, expected, rtol=1e-6)

    def test_wavelength_step_equals_interval_times_speed(self, sweep1):
        df = self._df(sweep1)
        steps = np.diff(df["Wavelength_nm"].values)
        expected_step = ACTUAL_INTERVAL * SWEEP_SPEED
        np.testing.assert_allclose(steps, expected_step, rtol=1e-5)

    def test_amplitude_is_channel_b_not_channel_a(self, sweep1, fake_data):
        """Amplitude_V must be Channel B data (the spectrum), not Channel A."""
        _, data_b = fake_data
        df = self._df(sweep1)
        n = len(df)
        np.testing.assert_allclose(df["Amplitude_V"].values, data_b[:n], rtol=1e-5)

    def test_no_index_column(self, sweep1):
        """CSV must not contain a row-index column (index=False)."""
        _, folder, _ = sweep1
        with open(os.path.join(folder, "001.csv")) as f:
            header = f.readline().strip()
        assert header == "Wavelength_nm,Amplitude_V"

    def test_multiple_reps_same_structure(self, ctrl, tmp_path):
        _, folder, _ = _run_sweep(ctrl, tmp_path, repetitions=2)
        df1 = pd.read_csv(os.path.join(folder, "001.csv"))
        df2 = pd.read_csv(os.path.join(folder, "002.csv"))
        assert list(df1.columns) == list(df2.columns)
        assert len(df1) == len(df2)


# ── Plot format ───────────────────────────────────────────────────────────────

class TestPlot:

    def test_x_label(self, captured_ax):
        ax, _ = captured_ax
        assert ax.get_xlabel() == "Wavelength [nm]"

    def test_y_label(self, captured_ax):
        ax, _ = captured_ax
        assert ax.get_ylabel() == "Amplitude [V]"

    def test_single_axes_only(self, captured_ax):
        ax, _ = captured_ax
        assert len(ax.get_figure().axes) == 1

    def test_grid_is_enabled(self, captured_ax):
        ax, _ = captured_ax
        gridlines = ax.get_xgridlines() + ax.get_ygridlines()
        assert any(gl.get_visible() for gl in gridlines)

    def test_file_is_valid_png(self, sweep1):
        _, folder, _ = sweep1
        with open(os.path.join(folder, "001.png"), "rb") as f:
            header = f.read(8)
        assert header == b"\x89PNG\r\n\x1a\n"

    def test_plotted_y_matches_csv_amplitude(self, captured_ax):
        """The line drawn on the plot must match Amplitude_V in the CSV."""
        ax, results_root = captured_ax
        folder = next(
            os.path.join(results_root, d)
            for d in os.listdir(results_root)
            if os.path.isdir(os.path.join(results_root, d))
        )
        df = pd.read_csv(os.path.join(folder, "001.csv"))
        plotted_y = ax.lines[0].get_ydata()
        np.testing.assert_allclose(plotted_y, df["Amplitude_V"].values, rtol=1e-5)

    def test_plotted_x_matches_csv_wavelengths(self, captured_ax):
        """The line drawn on the plot must match Wavelength_nm in the CSV."""
        ax, results_root = captured_ax
        folder = next(
            os.path.join(results_root, d)
            for d in os.listdir(results_root)
            if os.path.isdir(os.path.join(results_root, d))
        )
        df = pd.read_csv(os.path.join(folder, "001.csv"))
        plotted_x = ax.lines[0].get_xdata()
        np.testing.assert_allclose(plotted_x, df["Wavelength_nm"].values, rtol=1e-6)
