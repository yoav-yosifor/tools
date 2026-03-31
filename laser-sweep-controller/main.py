"""
Main script for running laser wavelength sweeps.

Modify the parameters in this file and run it to perform sweeps.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from laser_sweep import perform_laser_sweep

# CONFIGURATION - Edit these parameters for your sweep

# Wavelength range
WAVELENGTH_MIN = 1549.00  # nm
WAVELENGTH_MAX = 1549.15  # nm

# Laser settings
POWER = 12.0  # dBm
SWEEP_SPEED = 0.8  # nm/s

# Sweep control
REPETITIONS = 5  # Number of sweeps to perform
WAIT_BETWEEN_SWEEPS = 0.5  # seconds

# Optional: Number of samples (None = auto-calculate)
NUM_SAMPLES = 1000000  # or specify like: 10000

# Laser selection
LASER_NAME = "1550nm Laser"  # Options: '1550nm Laser', '1400nm Laser', '1300nm Laser'

# Data acquisition
USE_PICOSCOPE = True  # Set to False if you don't want to acquire data
SAVE_DATA = True  # Set to False if you don't want to save CSV files

# MAIN FUNCTION


def main():
    """Run the laser sweep with configured parameters."""

    print("LASER WAVELENGTH SWEEP")
    print(f"\nConfiguration:")
    print(f"  Laser: {LASER_NAME}")
    print(f"  Wavelength: {WAVELENGTH_MIN} - {WAVELENGTH_MAX} nm")
    print(f"  Power: {POWER} dBm")
    print(f"  Sweep Speed: {SWEEP_SPEED} nm/s")
    print(f"  Repetitions: {REPETITIONS}")
    print(f"  Wait Between Sweeps: {WAIT_BETWEEN_SWEEPS} s")
    print(f"  Use PicoScope: {USE_PICOSCOPE}")
    print(f"  Save Data: {SAVE_DATA}")
    print(f"  Output: /results/{WAVELENGTH_MIN}_{WAVELENGTH_MAX}-DD_MM_YYYY/")

    # Calculate expected sweep time
    sweep_time = (WAVELENGTH_MAX - WAVELENGTH_MIN) / SWEEP_SPEED
    total_time = sweep_time * REPETITIONS + WAIT_BETWEEN_SWEEPS * (REPETITIONS - 1)
    print(f"\nEstimated sweep time: {sweep_time:.2f} s per sweep")
    print(f"Estimated total time: {total_time:.2f} s")

    # Confirm before starting
    response = input("\nProceed with sweep? (y/n): ")
    if response.lower() != "y":
        print("Sweep cancelled.")
        return

    print("\nStarting sweep...\n")

    try:
        # Perform the sweep
        results, output_folder = perform_laser_sweep(
            wavelength_min=WAVELENGTH_MIN,
            wavelength_max=WAVELENGTH_MAX,
            power=POWER,
            sweep_speed=SWEEP_SPEED,
            repetitions=REPETITIONS,
            num_samples=NUM_SAMPLES,
            laser_name=LASER_NAME,
            use_picoscope=USE_PICOSCOPE,
            wait_between_sweeps=WAIT_BETWEEN_SWEEPS,
            save_data=SAVE_DATA,
        )

        # Display results summary
        print("SWEEP COMPLETED SUCCESSFULLY")
        print(f"\nOutput Folder: {output_folder}/")
        print(f"Total sweeps completed: {len(results)}")

        for i, result in enumerate(results, 1):
            print(f"\nSweep {i}:")
            print(f"  Timestamp: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Duration: {result['duration']:.2f} seconds")

            if "spectrum" in result:
                print(f"  Samples acquired: {len(result['spectrum'])}")
                print(
                    f"  Amplitude range: {result['spectrum'].min():.4f} to {result['spectrum'].max():.4f} V"
                )

        print(f"\nFiles created in {output_folder}/:")
        print(f"  - sweep_log.txt")
        for i in range(REPETITIONS):
            print(f"  - {i + 1:03d}.csv, {i + 1:03d}.png")

    except Exception as e:
        print("ERROR OCCURRED")
        print(f"\n{str(e)}")
        print("\nPlease check:")
        print("  - Instruments are connected and powered on")
        print("  - GPIB/LAN addresses are correct")
        print("  - Wavelength range is within laser specifications")
        print("  - All required packages are installed")
        return 1

    return 0


# ALTERNATIVE: Simple one-liner


def quick_sweep():
    """Quick sweep without confirmation - for testing."""
    results, output_folder = perform_laser_sweep(
        wavelength_min=WAVELENGTH_MIN,
        wavelength_max=WAVELENGTH_MAX,
        power=POWER,
        sweep_speed=SWEEP_SPEED,
        repetitions=REPETITIONS,
        laser_name=LASER_NAME,
        use_picoscope=USE_PICOSCOPE,
    )
    print(f"\nOutput folder: {output_folder}/")
    return results, output_folder


# Run

if __name__ == "__main__":
    # Run the main function with confirmation
    exit_code = main()

    # Or for quick testing without confirmation, use:
    # results = quick_sweep()

    # Exit with appropriate code
    if exit_code:
        exit(exit_code)
