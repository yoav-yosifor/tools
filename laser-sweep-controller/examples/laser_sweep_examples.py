"""
Simple example script for using the laser sweep module.

This script demonstrates how to perform wavelength sweeps with various configurations.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from laser_sweep import LaserController, perform_laser_sweep

# BASIC USAGE - Simple sweep


def basic_sweep_example():
    """Perform a basic single sweep."""
    print("BASIC SWEEP EXAMPLE")

    results, folder = perform_laser_sweep(
        wavelength_min=1540.0,  # Start wavelength in nm
        wavelength_max=1560.0,  # End wavelength in nm
        power=10.0,  # Output power in dBm
        sweep_speed=5.0,  # Sweep speed in nm/s
        repetitions=1,  # Do it once
    )

    print(f"\nSweep completed in {results[0]['duration']:.2f} seconds")
    print(f"Output folder: {folder}/")
    return results, folder


# MULTIPLE REPETITIONS - Repeat the same sweep


def repeated_sweep_example():
    """Perform multiple sweep repetitions."""
    print("\nREPEATED SWEEP EXAMPLE")

    results, folder = perform_laser_sweep(
        wavelength_min=1545.0,
        wavelength_max=1555.0,
        power=8.0,
        sweep_speed=10.0,  # Faster sweep: 10 nm/s
        repetitions=5,  # Repeat 5 times
        wait_between_sweeps=2.0,  # Wait 2 seconds between each sweep
        output_prefix="repeated",
    )

    print(f"\nCompleted {len(results)} sweeps")
    print(f"Output folder: {folder}/")
    for i, result in enumerate(results, 1):
        print(f"  Sweep {i}: {result['duration']:.2f} seconds")

    return results, folder


# HIGH RESOLUTION - Many samples for detailed measurements


def high_resolution_sweep_example():
    """Perform a high-resolution sweep with many samples."""
    print("\nHIGH RESOLUTION SWEEP EXAMPLE")

    results, folder = perform_laser_sweep(
        wavelength_min=1550.0,
        wavelength_max=1560.0,
        power=12.0,
        sweep_speed=2.0,  # Slow sweep for better resolution
        repetitions=1,
        num_samples=50000,  # High number of samples
        output_prefix="high_res",
    )

    print(f"\nHigh-resolution sweep with {len(results[0]['wavelengths'])} samples")
    print(f"Output folder: {folder}/")
    return results, folder


# DIFFERENT LASER - Use 1400nm or 1300nm laser


def different_laser_example():
    """Example using a different laser (1400nm)."""
    print("\nDIFFERENT LASER EXAMPLE (1400nm)")

    results, folder = perform_laser_sweep(
        wavelength_min=1380.0,  # Within 1400nm laser range
        wavelength_max=1420.0,
        power=10.0,
        sweep_speed=5.0,
        repetitions=2,
        laser_name="1400nm Laser",  # Specify which laser to use
        output_prefix="1400nm_sweep",
    )

    print(f"\nCompleted {len(results)} sweeps with 1400nm laser")
    print(f"Output folder: {folder}/")
    return results, folder


# ADVANCED USAGE - Using the controller class directly


def advanced_controller_example():
    """Advanced usage with direct controller access."""
    print("\nADVANCED CONTROLLER EXAMPLE")

    # Create controller instance
    controller = LaserController(laser_name="1550nm Laser", use_picoscope=True)

    try:
        # Connect to instruments
        controller.connect()
        print("Connected to instruments")

        # Configure once
        controller.configure_sweep(
            wavelength_min=1540.0,
            wavelength_max=1560.0,
            power=10.0,
            sweep_speed=5.0,
            num_samples=10000,
        )

        # Perform multiple sweeps with custom logic
        for i in range(3):
            print(f"\nCustom sweep {i + 1}/3")
            data = controller.perform_single_sweep(acquire_data=True)

            if data:
                print(
                    f"  Channel A: {len(data[0])} samples, "
                    f"range: {data[0].min():.3f} to {data[0].max():.3f} V"
                )
                print(
                    f"  Channel B: {len(data[1])} samples, "
                    f"range: {data[1].min():.3f} to {data[1].max():.3f} V"
                )

            # Custom wait time or other logic
            if i < 2:
                import time

                time.sleep(1.5)

    finally:
        # Always disconnect
        controller.disconnect()
        print("\nDisconnected from instruments")


# WITHOUT PICOSCOPE - Just sweep the laser without data acquisition


def laser_only_example():
    """Sweep the laser without PicoScope data acquisition."""
    print("\nLASER ONLY EXAMPLE (No PicoScope)")

    results, folder = perform_laser_sweep(
        wavelength_min=1540.0,
        wavelength_max=1560.0,
        power=10.0,
        sweep_speed=5.0,
        repetitions=3,
        use_picoscope=False,  # Don't use PicoScope
        save_data=False,  # No data to save
        wait_between_sweeps=1.0,
    )

    print(f"\nCompleted {len(results)} laser sweeps without data acquisition")
    print(f"Output folder: {folder}/")
    return results, folder


# Run

if __name__ == "__main__":
    print("\n")
    print("*" * 70)
    print("LASER SWEEP EXAMPLES")
    print("*" * 70)

    # Uncomment the examples you want to run:

    # Example 1: Basic single sweep
    # basic_sweep_example()

    # Example 2: Multiple repetitions
    # repeated_sweep_example()

    # Example 3: High resolution sweep
    # high_resolution_sweep_example()

    # Example 4: Different laser
    # different_laser_example()

    # Example 5: Advanced controller usage
    # advanced_controller_example()

    # Example 6: Laser only (no PicoScope)
    # laser_only_example()

    print("\n" + "*" * 70)
    print("Uncomment the examples you want to run in the __main__ section")
    print("*" * 70 + "\n")


# QUICK START TEMPLATE

"""
QUICK START:

from laser_sweep import perform_laser_sweep

# Perform a sweep
results, folder = perform_laser_sweep(
    wavelength_min=1540.0,      # nm
    wavelength_max=1560.0,      # nm
    power=10.0,                  # dBm
    sweep_speed=5.0,            # nm/s
    repetitions=3,              # how many times
    wait_between_sweeps=1.0,    # seconds
    num_samples=10000,          # optional: auto-calculated if not specified
    laser_name='1550nm Laser',  # or '1400nm Laser' or '1300nm Laser'
    save_data=True,             # save CSV files and plots
    output_prefix="my_sweep"    # folder name prefix
)

# Access results
print(f"Output folder: {folder}/")
for i, result in enumerate(results, 1):
    print(f"Sweep {i}: {result['duration']:.2f} seconds")
    if 'channel_a' in result:
        print(f"  Samples: {len(result['channel_a'])}")

# Files created in folder:
#   - sweep_log.txt (all parameters and execution log)
#   - rep001_data.csv, rep001_plot.png
#   - rep002_data.csv, rep002_plot.png
#   - etc.
"""
