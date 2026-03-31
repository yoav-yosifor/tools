# Laser Wavelength Sweep Module

A Python module for performing automated wavelength sweeps on tunable lasers with optional PicoScope data acquisition.

This project was developed and tested using:

- **Santec TSL-570 Tunable Semiconductor Laser**
- **PicoScope 5000 Series Oscilloscope**

## Hardware 

### Laser
- **Model**: Santec TSL-570  
- **Type**: Tunable Semiconductor Laser  
- **Interface**: SCPI over GPIB or LAN (TCP/IP)  
- **Typical Sweep Range**: Depends on installed module (e.g., 1260–1640 nm variants)  

The module communicates with the laser using standard SCPI commands for wavelength sweep configuration and trigger output.

### Oscilloscope
- **Model Series**: PicoScope 5000 Series  
- **Interface**: USB  
- **SDK**: PicoSDK (`picosdk` Python package)  
- **Channels Used**: Channel A and Channel B (configurable)  

The oscilloscope is used for synchronized signal acquisition during wavelength sweeps.

## Features

- **Santec TSL-570 Support**: Designed for SCPI control of Santec tunable lasers  
- **PicoScope 5000 Series Integration**: High-speed synchronized data acquisition  
- **Multiple Laser Configurations**: Works with 1550nm, 1400nm, and 1300nm configurations  
- **Flexible Connections**: Supports both GPIB and LAN (TCP/IP) connections  
- **Repeated Sweeps**: Perform multiple sweep repetitions automatically  
- **Data Acquisition**: Optional PicoScope integration for signal measurement  
- **Auto-save**: Automatically saves sweep data to CSV files  
- **Parameter Validation**: Checks that wavelength ranges are within laser specs  
- **Error Handling**: Robust error handling and instrument cleanup  



## Installation

Required packages:
```bash
pip install pyvisa
pip install picosdk
pip install numpy
pip install pandas
```

## Quick Start

```python
from laser_sweep import perform_laser_sweep

# Perform a simple sweep
results = perform_laser_sweep(
    wavelength_min=1540.0,      # Starting wavelength (nm)
    wavelength_max=1560.0,      # Ending wavelength (nm)
    power=10.0,                  # Output power (dBm)
    sweep_speed=5.0,            # Sweep speed (nm/s)
    repetitions=3                # Number of sweeps to perform
)
```

## Supported Lasers

### 1550nm Laser (GPIB)
- **Connection**: GPIB0::10::INSTR
- **Wavelength Range**: 1480.0 - 1640.0 nm
- **Connection Type**: GPIB

### 1400nm Laser (LAN)
- **Connection**: TCPIP::192.168.31.12::5000::SOCKET
- **Wavelength Range**: 1355.0 - 1485.0 nm
- **Connection Type**: LAN/TCP

### 1300nm Laser (LAN)
- **Connection**: TCPIP::192.168.31.11::5000::SOCKET
- **Wavelength Range**: 1260.0 - 1360.0 nm
- **Connection Type**: LAN/TCP

## Parameters

### Required Parameters

- **wavelength_min** (float): Starting wavelength in nanometers
- **wavelength_max** (float): Ending wavelength in nanometers
- **power** (float): Laser output power in dBm
- **sweep_speed** (float): Sweep speed in nm/s

### Optional Parameters

- **repetitions** (int): Number of times to repeat the sweep (default: 1)
- **num_samples** (int): Number of samples to acquire per sweep (default: auto-calculated)
- **laser_name** (str): Which laser to use (default: '1550nm Laser')
- **use_picoscope** (bool): Whether to use PicoScope (default: True)
- **wait_between_sweeps** (float): Delay between sweeps in seconds (default: 1.0)
- **save_data** (bool): Whether to save CSV files (default: True)
- **output_prefix** (str): Prefix for output filenames (default: "sweep")

## Usage Examples

### Example 1: Basic Single Sweep

```python
from laser_sweep import perform_laser_sweep

results = perform_laser_sweep(
    wavelength_min=1540.0,
    wavelength_max=1560.0,
    power=10.0,
    sweep_speed=5.0,
    repetitions=1
)
```

### Example 2: Multiple Repetitions

```python
# Perform 5 sweeps with 2-second delays between them
results = perform_laser_sweep(
    wavelength_min=1545.0,
    wavelength_max=1555.0,
    power=8.0,
    sweep_speed=10.0,
    repetitions=5,
    wait_between_sweeps=2.0,
    output_prefix="repeated_sweep"
)
```

### Example 3: High-Resolution Sweep

```python
# Slow sweep with many samples for high resolution
results = perform_laser_sweep(
    wavelength_min=1550.0,
    wavelength_max=1560.0,
    power=12.0,
    sweep_speed=2.0,           # Slower sweep
    repetitions=1,
    num_samples=50000,         # High resolution
    output_prefix="high_res"
)
```

### Example 4: Using Different Laser

```python
# Use the 1400nm laser instead
results = perform_laser_sweep(
    wavelength_min=1380.0,
    wavelength_max=1420.0,
    power=10.0,
    sweep_speed=5.0,
    repetitions=2,
    laser_name='1400nm Laser'
)
```

### Example 5: Laser Only (No Data Acquisition)

```python
# Just sweep the laser without acquiring data
results = perform_laser_sweep(
    wavelength_min=1540.0,
    wavelength_max=1560.0,
    power=10.0,
    sweep_speed=5.0,
    repetitions=3,
    use_picoscope=False,
    save_data=False
)
```

### Example 6: Advanced Usage with Controller Class

```python
from laser_sweep import LaserController

# Create controller
controller = LaserController(laser_name='1550nm Laser')

try:
    # Connect
    controller.connect()
    
    # Configure sweep
    controller.configure_sweep(
        wavelength_min=1540.0,
        wavelength_max=1560.0,
        power=10.0,
        sweep_speed=5.0
    )
    
    # Perform multiple sweeps with custom logic
    for i in range(3):
        print(f"Sweep {i+1}")
        data = controller.perform_single_sweep(acquire_data=True)
        
        # Your custom processing here
        # ...
        
finally:
    # Always disconnect
    controller.disconnect()
```

## Output Data

When `save_data=True`, the module automatically saves CSV files with the format:

**Filename**: `{output_prefix}_rep{N}_{timestamp}.csv`

**Columns**:
- `Wavelength_nm`: Wavelength values in nanometers
- `Channel_A_V`: PicoScope Channel A voltage data
- `Channel_B_V`: PicoScope Channel B voltage data

Example filename: `sweep_rep001_20240208_143022.csv`

## Return Value

The `perform_laser_sweep()` function returns a list of dictionaries, one for each repetition:

```python
[
    {
        'repetition': 1,
        'timestamp': datetime.datetime(...),
        'wavelength_min': 1540.0,
        'wavelength_max': 1560.0,
        'power': 10.0,
        'sweep_speed': 5.0,
        'duration': 4.23,  # seconds
        'wavelengths': array([1540.0, 1540.02, ...]),
        'channel_a': array([0.123, 0.125, ...]),
        'channel_b': array([0.456, 0.458, ...])
    },
    # ... more repetitions
]
```

## How It Works

### Sweep Process

1. **Connect** to laser and PicoScope
2. **Validate** parameters against laser specifications
3. **Configure** laser sweep parameters (start/stop wavelength, power, speed)
4. **Configure** PicoScope sampling and trigger (if used)
5. **For each repetition**:
   - Start laser output
   - Acquire data from PicoScope (if enabled)
   - Save data to CSV (if enabled)
   - Wait specified delay before next sweep
6. **Disconnect** and cleanup

### Time Calculation

The sweep duration is automatically calculated:

```
sweep_time = (wavelength_max - wavelength_min) / sweep_speed
```

For example:
- Range: 1540 to 1560 nm (20 nm)
- Speed: 5 nm/s
- Time: 20 / 5 = 4 seconds per sweep

### Sampling

If `num_samples` is not specified, it's calculated automatically:
```
num_samples = sweep_time × 1000  # 1 kHz default sampling rate
```

## Laser Commands

The module sends these SCPI commands to the laser:

```
:WAV:SWE:START {wavelength_min}nm    # Set start wavelength
:WAV:SWE:STOP {wavelength_max}nm     # Set stop wavelength
:POW {power}dBm                       # Set output power
:WAV:SWE:MOD 1                        # Enable sweep mode
:WAV:SWE:SPE {sweep_speed}            # Set sweep speed
:TRIG:OUTP 2                          # Configure trigger output
:POW:STAT 1                           # Turn laser on
:POW:STAT 0                           # Turn laser off
```

## Error Handling

The module includes comprehensive error handling:

- **Parameter validation**: Checks wavelength ranges against laser specs
- **Connection errors**: Handles GPIB/LAN connection failures
- **Instrument cleanup**: Always turns off laser and closes connections
- **Exception propagation**: Raises informative exceptions with context

## Safety Features

- Automatically turns off laser power when disconnecting
- Validates all parameters before starting sweep
- Includes timeout settings for LAN connections
- Proper cleanup in case of errors

## Troubleshooting

### "Failed to connect" errors

1. Check that laser is powered on
2. Verify GPIB/LAN addresses in `LASER_CONFIGS`
3. For LAN: Check network connectivity with `ping`
4. For GPIB: Verify GPIB interface is properly installed

### "Out of range" errors

Check that your wavelength values are within the laser's supported range:
- 1550nm laser: 1480-1640 nm
- 1400nm laser: 1355-1485 nm  
- 1300nm laser: 1260-1360 nm

### PicoScope issues

- Ensure PicoScope drivers are installed
- Check USB connection
- Try increasing timeout values
- Verify channel configuration

### Data acquisition issues

- Check trigger settings and threshold
- Verify sampling rate is appropriate for sweep speed
- Ensure sufficient memory for sample count
- Check that sweep time calculation is correct

## Limitations

- Requires PyVISA and appropriate VISA backend (NI-VISA, PyVISA-py)
- PicoScope support requires picosdk package and drivers
- LAN connections require network access to laser IP addresses
- Maximum sample count limited by PicoScope memory
- Sweep speed limited by laser capabilities

## License

This module is based on the laser control GUI (GUI_V4_3lasers_.py) and maintains
compatibility with its instrument configurations.

## Support

For issues or questions:
1. Check parameter validation errors for out-of-range values
2. Verify instrument connections and addresses
3. Review error messages for specific failure points
4. Check that all required packages are installed
