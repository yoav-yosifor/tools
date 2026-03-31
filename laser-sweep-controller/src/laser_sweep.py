"""
Laser Wavelength Sweep Module

This module provides functionality to perform repeated wavelength sweeps on a tunable laser
with configurable parameters including wavelength range, power, sweep speed, and repetitions.

Based on the laser configuration from GUI_V4_3lasers_.py
"""

import time
from datetime import datetime
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
import pyvisa
from picoscope import ps5000a


class LaserController:
    """
    Controller for performing wavelength sweeps on tunable lasers.

    Supports multiple laser types with different wavelength ranges and connection types.
    """

    # Laser configurations from original GUI
    LASER_CONFIGS = {
        "1550nm Laser": {
            "address": "GPIB0::10::INSTR",
            "wavelength_range": (1480.0, 1640.0),
            "default_wavelength": 1550.0,
            "connection_type": "GPIB",
        },
        "1400nm Laser": {
            "address": "TCPIP::192.168.31.12::5000::SOCKET",
            "wavelength_range": (1355.0, 1485.0),
            "default_wavelength": 1400.0,
            "connection_type": "LAN",
        },
        "1300nm Laser": {
            "address": "TCPIP::192.168.31.11::5000::SOCKET",
            "wavelength_range": (1260.0, 1360.0),
            "default_wavelength": 1300.0,
            "connection_type": "LAN",
        },
    }

    def __init__(self, laser_name: str = "1550nm Laser", use_picoscope: bool = True):
        """
        Initialize the laser sweep controller.

        Args:
            laser_name: Name of the laser to use (must be in LASER_CONFIGS)
            use_picoscope: Whether to use PicoScope for data acquisition
        """
        if laser_name not in self.LASER_CONFIGS:
            raise ValueError(
                f"Unknown laser: {laser_name}. Available: {list(self.LASER_CONFIGS.keys())}"
            )

        self.laser_name = laser_name
        self.config = self.LASER_CONFIGS[laser_name]
        self.use_picoscope = use_picoscope

        self.laser = None
        self.ps = None
        self.rm = None

    def connect(self):
        """Connect to the laser and optionally PicoScope."""
        try:
            # Connect to laser
            self.rm = pyvisa.ResourceManager()
            self.laser = self.rm.open_resource(self.config["address"])

            # Configure connection based on type
            if self.config["connection_type"] == "LAN":
                self.laser.timeout = 5000  # 5 second timeout
                self.laser.write_termination = "\n"
                self.laser.read_termination = "\n"

                # Test connection
                try:
                    idn = self.laser.query("*IDN?")
                    print(f"Connected to laser: {idn.strip()}")
                except:
                    print(f"Connected to {self.laser_name} (IDN query failed)")
            else:
                print(f"Connected to {self.laser_name} via GPIB")

            # Connect to PicoScope if requested
            if self.use_picoscope:
                self.ps = ps5000a.PS5000a()
                time.sleep(0.2)
                self.ps.setResolution("12")
                self.ps.setChannel(
                    "A",
                    coupling="DC",
                    VRange=5,
                    VOffset=0.0,
                    enabled=True,
                    BWLimited=False,
                )
                self.ps.setChannel(
                    "B",
                    coupling="DC",
                    VRange=5,
                    VOffset=0.0,
                    enabled=True,
                    BWLimited=False,
                )
                print("PicoScope connected and configured")

            return True

        except Exception as e:
            self.disconnect()
            raise Exception(f"Failed to connect: {str(e)}")

    def disconnect(self):
        """Disconnect from all instruments."""
        try:
            if self.laser:
                self.laser.write(":POW:STAT 0")  # Turn off laser
                time.sleep(0.2)
                self.laser.close()
                self.laser = None
        except:
            pass

        try:
            if self.ps:
                self.ps.close()
                self.ps = None
        except:
            pass

        if self.rm:
            self.rm.close()
            self.rm = None

    def validate_parameters(
        self,
        wavelength_min: float,
        wavelength_max: float,
        power: float,
        sweep_speed: float,
    ):
        """
        Validate sweep parameters against laser specifications.

        Args:
            wavelength_min: Minimum wavelength in nm
            wavelength_max: Maximum wavelength in nm
            power: Output power in dBm
            sweep_speed: Sweep speed in nm/s

        Raises:
            ValueError: If parameters are out of range
        """
        wl_range = self.config["wavelength_range"]

        if wavelength_min < wl_range[0] or wavelength_min > wl_range[1]:
            raise ValueError(
                f"wavelength_min {wavelength_min} nm is out of range "
                f"{wl_range[0]}-{wl_range[1]} nm for {self.laser_name}"
            )

        if wavelength_max < wl_range[0] or wavelength_max > wl_range[1]:
            raise ValueError(
                f"wavelength_max {wavelength_max} nm is out of range "
                f"{wl_range[0]}-{wl_range[1]} nm for {self.laser_name}"
            )

        if wavelength_min >= wavelength_max:
            raise ValueError(
                f"wavelength_min ({wavelength_min}) must be less than "
                f"wavelength_max ({wavelength_max})"
            )

        if sweep_speed <= 0:
            raise ValueError(f"sweep_speed must be positive, got {sweep_speed}")

        # Power validation (typical range, adjust as needed)
        if power < -20 or power > 20:
            print(
                f"Warning: Power {power} dBm may be out of typical range (-20 to +20 dBm)"
            )

    def configure_sweep(
        self,
        wavelength_min: float,
        wavelength_max: float,
        power: float,
        sweep_speed: float,
        num_samples: Optional[int] = None,
    ):
        """
        Configure the laser and PicoScope for a sweep.

        Args:
            wavelength_min: Starting wavelength in nm
            wavelength_max: Ending wavelength in nm
            power: Output power in dBm
            sweep_speed: Sweep speed in nm/s
            num_samples: Number of samples to acquire (if using PicoScope)

        Returns:
            Tuple of (actual_sampling_interval, actual_num_samples) if using PicoScope,
            otherwise None
        """
        if not self.laser:
            raise Exception("Laser not connected. Call connect() first.")

        # Validate parameters
        self.validate_parameters(wavelength_min, wavelength_max, power, sweep_speed)

        # Configure laser
        self.laser.write(f":WAV:SWE:START {wavelength_min}nm")
        self.laser.write(f":WAV:SWE:STOP {wavelength_max}nm")
        self.laser.write(f":POW {power}dBm")
        self.laser.write(":WAV:SWE:MOD 1")  # Enable sweep mode
        self.laser.write(f":WAV:SWE:SPE {sweep_speed}")
        self.laser.write(":TRIG:OUTP 2")  # Configure trigger output

        print(
            f"Laser configured: {wavelength_min}-{wavelength_max} nm at {power} dBm, "
            f"sweep speed {sweep_speed} nm/s"
        )

        # Configure PicoScope if available
        if self.use_picoscope and self.ps:
            # Calculate time window for the sweep
            time_window = (wavelength_max - wavelength_min) / sweep_speed

            # If num_samples not specified, use a reasonable default
            if num_samples is None:
                num_samples = int(time_window * 1000)  # 1 kHz default sampling

            sampling_interval = time_window / num_samples

            (actual_interval, actual_samples, _) = self.ps.setSamplingInterval(
                sampling_interval, time_window
            )

            # Configure trigger
            self.ps.setSimpleTrigger(
                trigSrc="A",
                threshold_V=1,
                direction="Rising",
                timeout_ms=int(10000),  # Add 10s margin
                enabled=True,
            )

            print(
                f"PicoScope configured: {actual_samples} samples at "
                f"{actual_interval * 1e6:.2f} µs interval"
            )

            return actual_interval, actual_samples

        return None

    def perform_single_sweep(
        self, acquire_data: bool = True, wavelength_min: float = None,
        wavelength_max: float = None, sweep_speed: float = None,
        num_samples: Optional[int] = None,
    ) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Perform a single wavelength sweep.

        Args:
            acquire_data: Whether to acquire data from PicoScope
            wavelength_min: Minimum wavelength (used to calculate sweep time if PicoScope disabled)
            wavelength_max: Maximum wavelength (used to calculate sweep time if PicoScope disabled)
            sweep_speed: Sweep speed in nm/s (used to calculate sweep time if PicoScope disabled)
            num_samples: Number of samples to request from PicoScope

        Returns:
            Tuple of (data_channel_a, data_channel_b) if acquire_data is True and
            PicoScope is being used, otherwise None
        """
        if not self.laser:
            raise Exception("Laser not connected")

        # Start laser output
        self.laser.write(":POW:STAT 1")
        time.sleep(0.5)

        # Start the wavelength sweep
        self.laser.write(":WAV:SWE 1")

        # If using PicoScope, acquire data
        if self.use_picoscope and self.ps and acquire_data:
            self.ps.runBlock()
            self.ps.waitReady()

            # Get data from both channels (pass num_samples like the GUI does)
            data_a = self.ps.getDataV("A", num_samples)
            data_b = self.ps.getDataV("B", num_samples)

            return data_a, data_b

        # If NOT using PicoScope but have sweep parameters, wait for sweep to complete
        elif wavelength_min is not None and wavelength_max is not None and sweep_speed is not None:
            sweep_time = (wavelength_max - wavelength_min) / sweep_speed
            time.sleep(sweep_time)

        return None

    def perform_sweep(
        self,
        wavelength_min: float,
        wavelength_max: float,
        power: float,
        sweep_speed: float,
        repetitions: int = 1,
        num_samples: Optional[int] = None,
        wait_between_sweeps: float = 1.0,
        save_data: bool = True,
    ) -> Tuple[list, str]:
        """
        Perform multiple wavelength sweeps with specified parameters.

        Args:
            wavelength_min: Starting wavelength in nm
            wavelength_max: Ending wavelength in nm
            power: Output power in dBm
            sweep_speed: Sweep speed in nm/s
            repetitions: Number of times to repeat the sweep
            num_samples: Number of samples per sweep (if using PicoScope)
            wait_between_sweeps: Time to wait between sweeps in seconds
            save_data: Whether to save data to CSV files

        Returns:
            Tuple of (list of dictionaries containing sweep results, output folder path)
        """
        import os

        import matplotlib.pyplot as plt

        if repetitions < 1:
            raise ValueError("repetitions must be at least 1")

        results = []

        # Create output folder: results/{min}_{max}-DD_MM_YYYY (relative to this module)
        date_str = datetime.now().strftime("%d_%m_%Y")
        folder_name = f"{wavelength_min}_{wavelength_max}-{date_str}"
        results_root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
        output_folder = os.path.join(results_root, folder_name)
        data_folder = os.path.join(output_folder, "data")
        plots_folder = os.path.join(output_folder, "plots")
        os.makedirs(data_folder, exist_ok=True)
        os.makedirs(plots_folder, exist_ok=True)

        print(f"\nCreated output folder: {output_folder}/")
        print(f"  Data folder: {data_folder}/")
        print(f"  Plots folder: {plots_folder}/")

        # Create log file with all parameters
        log_filename = os.path.join(output_folder, "sweep_log.txt")
        with open(log_filename, "w") as log_file:
            log_file.write("# LASER SWEEP LOG\n\n")
            log_file.write(
                f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )

            log_file.write("LASER CONFIGURATION:\n")
            log_file.write(f"  Laser Name: {self.laser_name}\n")
            log_file.write(f"  Connection Type: {self.config['connection_type']}\n")
            log_file.write(f"  Address: {self.config['address']}\n")
            log_file.write(
                f"  Wavelength Range: {self.config['wavelength_range'][0]} - {self.config['wavelength_range'][1]} nm\n\n"
            )

            log_file.write("SWEEP PARAMETERS:\n")
            log_file.write(f"  Wavelength Min: {wavelength_min} nm\n")
            log_file.write(f"  Wavelength Max: {wavelength_max} nm\n")
            log_file.write(
                f"  Wavelength Range: {wavelength_max - wavelength_min} nm\n"
            )
            log_file.write(f"  Power: {power} dBm\n")
            log_file.write(f"  Sweep Speed: {sweep_speed} nm/s\n")
            log_file.write(f"  Repetitions: {repetitions}\n")
            log_file.write(f"  Wait Between Sweeps: {wait_between_sweeps} s\n")
            log_file.write(
                f"  Number of Samples: {num_samples if num_samples else 'Auto-calculated'}\n\n"
            )

            log_file.write("DATA ACQUISITION:\n")
            log_file.write(f"  Use PicoScope: {self.use_picoscope}\n")
            log_file.write(f"  Save Data: {save_data}\n")
            log_file.write(f"  Output Folder: {output_folder}/\n\n")

            expected_sweep_time = (wavelength_max - wavelength_min) / sweep_speed
            expected_total_time = (
                expected_sweep_time * repetitions
                + wait_between_sweeps * (repetitions - 1)
            )
            log_file.write("TIMING ESTIMATES:\n")
            log_file.write(f"  Expected Sweep Time: {expected_sweep_time:.2f} s\n")
            log_file.write(f"  Expected Total Time: {expected_total_time:.2f} s\n\n")

        print(f"Log file created: {log_filename}")

        try:
            # Configure instruments
            scope_params = self.configure_sweep(
                wavelength_min, wavelength_max, power, sweep_speed, num_samples
            )

            if scope_params:
                actual_interval, actual_samples = scope_params
                # Update log with actual parameters
                with open(log_filename, "a") as log_file:
                    log_file.write("ACTUAL PICOSCOPE PARAMETERS:\n")
                    log_file.write(f"  Actual Samples: {actual_samples}\n")
                    log_file.write(
                        f"  Sampling Interval: {actual_interval * 1e6:.2f} micro s\n"
                    )
                    log_file.write(f"  Sampling Rate: {1 / actual_interval:.2f} Hz\n\n")
            else:
                actual_interval = None
                actual_samples = num_samples if num_samples else 0

            # Log sweep start
            with open(log_filename, "a") as log_file:
                log_file.write("# SWEEP EXECUTION LOG\n\n")

            # Perform sweeps
            for rep in range(repetitions):
                print(f"\nStarting sweep {rep + 1}/{repetitions}")

                sweep_start_time = time.time()

                # Perform single sweep
                data = self.perform_single_sweep(
                    acquire_data=self.use_picoscope,
                    wavelength_min=wavelength_min,
                    wavelength_max=wavelength_max,
                    sweep_speed=sweep_speed,
                    num_samples=actual_samples if actual_samples else None,
                )

                sweep_duration = time.time() - sweep_start_time

                # Compute wavelengths from time axis (matching GUI behaviour)
                if data and actual_interval is not None:
                    data_b = data[1]
                    time_axis = np.arange(len(data_b)) * actual_interval
                    wavelengths = wavelength_min + time_axis * sweep_speed
                    mask = wavelengths <= wavelength_max
                    wavelengths = wavelengths[mask]
                    spectrum = data_b[: len(wavelengths)]
                else:
                    wavelengths = np.linspace(wavelength_min, wavelength_max, actual_samples if actual_samples > 0 else 1000)
                    spectrum = data[1] if data else None

                # Store results
                result = {
                    "repetition": rep + 1,
                    "timestamp": datetime.now(),
                    "wavelength_min": wavelength_min,
                    "wavelength_max": wavelength_max,
                    "power": power,
                    "sweep_speed": sweep_speed,
                    "duration": sweep_duration,
                    "wavelengths": wavelengths,
                }

                if data:
                    result["channel_a"] = data[0]
                    result["channel_b"] = data[1]
                    result["spectrum"] = spectrum

                results.append(result)

                print(f"Sweep {rep + 1} completed in {sweep_duration:.2f} seconds")

                # Log this sweep
                with open(log_filename, "a") as log_file:
                    log_file.write(f"Repetition {rep + 1}:\n")
                    log_file.write(
                        f"  Timestamp: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                    )
                    log_file.write(f"  Duration: {sweep_duration:.2f} s\n")
                    if data:
                        log_file.write(f"  Samples Acquired: {len(spectrum)}\n")
                        log_file.write(
                            f"  Channel A Range: {data[0].min():.6f} to {data[0].max():.6f} V\n"
                        )
                        log_file.write(
                            f"  Amplitude (Ch B) Range: {spectrum.min():.6f} to {spectrum.max():.6f} V\n"
                        )
                    log_file.write("\n")

                # Save data if requested
                if save_data and data is not None and spectrum is not None:
                    # Save CSV — same format as GUI: Wavelength_nm, Amplitude_V (Channel B)
                    csv_filename = os.path.join(
                        data_folder, f"{rep + 1:03d}.csv"
                    )
                    df = pd.DataFrame(
                        {
                            "Wavelength_nm": wavelengths,
                            "Amplitude_V": spectrum,
                        }
                    )
                    df.to_csv(csv_filename, index=False)
                    print(f"Data saved to: {csv_filename}")

                    # Create plot — matching GUI style (single axes)
                    plot_filename = os.path.join(
                        plots_folder, f"{rep + 1:03d}.png"
                    )
                    fig, ax = plt.subplots(1, 1, figsize=(8, 6))
                    ax.plot(wavelengths, spectrum)
                    ax.set_xlabel("Wavelength [nm]")
                    ax.set_ylabel("Amplitude [V]")
                    ax.grid(True)
                    plt.tight_layout()
                    plt.savefig(plot_filename, dpi=150, bbox_inches="tight")
                    plt.close(fig)
                    print(f"Plot saved to: {plot_filename}")

                # Wait before next sweep (except after last one)
                if rep < repetitions - 1:
                    print(f"Waiting {wait_between_sweeps} seconds before next sweep...")
                    time.sleep(wait_between_sweeps)

            # Final log summary
            with open(log_filename, "a") as log_file:
                log_file.write("# SWEEP SUMMARY\n\n")
                log_file.write(f"Total Sweeps Completed: {len(results)}\n")
                total_duration = sum(r["duration"] for r in results)
                log_file.write(f"Total Acquisition Time: {total_duration:.2f} s\n")
                avg_duration = total_duration / len(results) if results else 0
                log_file.write(f"Average Sweep Time: {avg_duration:.2f} s\n\n")

                if results and "spectrum" in results[0]:
                    log_file.write("DATA STATISTICS:\n")
                    all_spectrum = np.concatenate([r["spectrum"] for r in results])
                    log_file.write(
                        f"  Amplitude (Ch B) - Overall Range: {all_spectrum.min():.6f} to {all_spectrum.max():.6f} V\n"
                    )
                    log_file.write(
                        f"  Amplitude (Ch B) - Mean: {all_spectrum.mean():.6f} V, Std: {all_spectrum.std():.6f} V\n\n"
                    )

                log_file.write(f"Files Created:\n")
                log_file.write(f"  Log file: sweep_log.txt\n")
                for rep in range(repetitions):
                    log_file.write(
                        f"  Repetition {rep + 1}: data/{rep + 1:03d}.csv, plots/{rep + 1:03d}.png\n"
                    )
                log_file.write("\n")
                log_file.write(
                    f"Sweep completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )

            print(f"\nAll {repetitions} sweeps completed successfully!")
            print(f"Output folder: {output_folder}/\n")

        except Exception as e:
            # Log error
            with open(log_filename, "a") as log_file:
                log_file.write("\n# ERROR OCCURRED\n\n")
                log_file.write(f"Error: {str(e)}\n")
                log_file.write(
                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )

            print(f"Error during sweep: {str(e)}")
            raise

        finally:
            # Turn off laser
            try:
                if self.laser:
                    self.laser.write(":POW:STAT 0")
            except:
                pass

        return results, output_folder


def perform_laser_sweep(
    wavelength_min: float,
    wavelength_max: float,
    power: float,
    sweep_speed: float,
    repetitions: int = 1,
    num_samples: Optional[int] = None,
    laser_name: str = "1550nm Laser",
    use_picoscope: bool = True,
    wait_between_sweeps: float = 1.0,
    save_data: bool = True,
) -> Tuple[list, str]:
    """
    Convenience function to perform laser wavelength sweeps.

    Results are saved to results/{wavelength_min}_{wavelength_max}-DD_MM_YYYY/ (inside the module directory)
    with files saved into data/ and plots/ subfolders, e.g. data/001.csv and plots/001.png.

    Args:
        wavelength_min: Minimum wavelength in nm
        wavelength_max: Maximum wavelength in nm
        power: Output power in dBm
        sweep_speed: Sweep speed in nm/s
        repetitions: Number of times to repeat the sweep (default: 1)
        num_samples: Number of samples to acquire per sweep (optional, auto-calculated if None)
        laser_name: Name of laser to use (default: '1550nm Laser')
        use_picoscope: Whether to use PicoScope for data acquisition (default: True)
        wait_between_sweeps: Time to wait between sweeps in seconds (default: 1.0)
        save_data: Whether to save data to CSV files (default: True)

    Returns:
        Tuple of (list of dictionaries containing sweep results, output folder path)

    Example:
        >>> results, folder = perform_laser_sweep(
        ...     wavelength_min=1540.0,
        ...     wavelength_max=1560.0,
        ...     power=10.0,
        ...     sweep_speed=5.0,
        ...     repetitions=3,
        ...     num_samples=10000
        ... )
    """
    controller = LaserController(laser_name=laser_name, use_picoscope=use_picoscope)

    try:
        controller.connect()

        results, output_folder = controller.perform_sweep(
            wavelength_min=wavelength_min,
            wavelength_max=wavelength_max,
            power=power,
            sweep_speed=sweep_speed,
            repetitions=repetitions,
            num_samples=num_samples,
            wait_between_sweeps=wait_between_sweeps,
            save_data=save_data,
        )

        return results, output_folder

    finally:
        controller.disconnect()
