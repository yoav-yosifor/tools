# Installation Instructions

## Prerequisites

### Python Version
- Python 3.7 or higher
- Check your version: `python --version` or `python3 --version`

### Operating System
- Windows 10/11
- Linux (Ubuntu, Debian, etc.)
- macOS

## Installation Steps

### 1. Install Python Packages

#### Option A: Using pip with requirements.txt (Recommended)
```bash
pip install -r requirements.txt
```

#### Option B: Manual installation
```bash
pip install numpy pandas matplotlib pyvisa pyvisa-py picosdk
```

### 2. Install VISA Backend

You need a VISA backend for instrument communication. Choose ONE:

#### Option A: NI-VISA (Recommended for Windows)
1. Download from: https://www.ni.com/en-us/support/downloads/drivers/download.ni-visa.html
2. Install the full package
3. Restart your computer
4. Test with: `python -c "import pyvisa; print(pyvisa.ResourceManager().list_resources())"`

#### Option B: PyVISA-py (Pure Python, no installation needed)
- Already installed if you used requirements.txt
- No additional software needed
- Works on all platforms
- May have limited functionality compared to NI-VISA

### 3. Install PicoScope Drivers (If using PicoScope)

#### Windows:
1. Download PicoScope software from: https://www.picotech.com/downloads
2. Install PicoScope 6 or 7 (includes drivers)
3. Restart computer

#### Linux:
```bash
# Add Pico repository
sudo bash -c 'echo "deb https://labs.picotech.com/debian/ picoscope main" > /etc/apt/sources.list.d/picoscope.list'

# Import public key
wget -O - https://labs.picotech.com/debian/dists/picoscope/Release.gpg.key | sudo apt-key add -

# Update and install
sudo apt-get update
sudo apt-get install libps5000a

# Install Python bindings
pip install picosdk
```

#### macOS:
1. Download from: https://www.picotech.com/downloads
2. Install the PicoScope application (includes drivers)

### 4. Install GPIB Drivers (If using GPIB laser)

#### Windows:
1. Install NI-VISA (includes GPIB support)
2. OR install NI-488.2 driver separately from National Instruments

#### Linux:
```bash
# Install linux-gpib
sudo apt-get install linux-gpib libgpib-dev

# Configure GPIB board
sudo gpib_config
```

#### macOS:
- Install NI-VISA from National Instruments
- OR use a USB-GPIB adapter with its specific drivers

## Verification

### Test Python Packages
```bash
python -c "import numpy, pandas, matplotlib, pyvisa, picosdk; print('All packages imported successfully!')"
```

### Test VISA Connection
```python
import pyvisa

rm = pyvisa.ResourceManager()
print("Available resources:")
print(rm.list_resources())
```

Expected output might look like:
```
Available resources:
('GPIB0::10::INSTR', 'TCPIP::192.168.31.12::5000::SOCKET')
```

### Test PicoScope
```python
from picoscope import ps5000a

try:
    ps = ps5000a.PS5000a()
    print("PicoScope connected successfully!")
    ps.close()
except:
    print("PicoScope not found or drivers not installed")
```

## Common Issues

### Issue: "No module named 'pyvisa'"
**Solution:** Install pyvisa: `pip install pyvisa`

### Issue: "Could not find VISA library"
**Solution:** 
- Install NI-VISA (Windows/Mac)
- OR use PyVISA-py: `pip install pyvisa-py`
- Set backend: `rm = pyvisa.ResourceManager('@py')`

### Issue: "PicoScope not found"
**Solution:**
1. Check USB connection
2. Install PicoScope drivers
3. Verify device works in PicoScope software first
4. On Linux, check permissions: `sudo usermod -a -G pico $USER`

### Issue: "GPIB device not found"
**Solution:**
1. Check GPIB cable connections
2. Verify GPIB address matches (e.g., address 10)
3. Install GPIB drivers
4. Test with NI MAX (Windows) or `ibtest` (Linux)

### Issue: Import errors on Linux
**Solution:**
```bash
# Make sure you have Python development headers
sudo apt-get install python3-dev

# Install build tools
sudo apt-get install build-essential
```

### Issue: Permission denied on Linux
**Solution:**
```bash
# For USB devices (PicoScope)
sudo usermod -a -G plugdev $USER
sudo usermod -a -G pico $USER

# For GPIB
sudo usermod -a -G gpib $USER

# Log out and back in for changes to take effect
```

## Network Configuration for LAN Lasers

If using LAN-connected lasers (`192.168.31.12`, `192.168.31.11`):

### 1. Check Network Connectivity
```bash
ping 192.168.31.12
ping 192.168.31.11
```

### 2. Verify Port Access
```bash
# Windows
telnet 192.168.31.12 5000

# Linux/Mac
nc -zv 192.168.31.12 5000
```

### 3. Firewall Settings
- Ensure your firewall allows connections to port 5000
- Add exceptions for Python/PyVISA if needed

### 4. Static IP Configuration (if needed)
If your computer needs to be on the same subnet:
- Set your computer's IP to `192.168.31.xxx` (e.g., `192.168.31.100`)
- Subnet mask: `255.255.255.0`

## Testing the Installation

Run the test script:

```python
from laser_sweep import LaserController

# This will attempt to connect and show any errors
try:
    controller = LaserController(laser_name='1550nm Laser', use_picoscope=True)
    controller.connect()
    print("✓ Connection successful!")
    controller.disconnect()
except Exception as e:
    print(f"✗ Connection failed: {e}")
```

## Minimal Installation (No PicoScope)

If you only want to control the laser without data acquisition:

```bash
# Install only these
pip install numpy pandas matplotlib pyvisa pyvisa-py
```

Then use:
```python
from laser_sweep import perform_laser_sweep

results, folder = perform_laser_sweep(
    wavelength_min=1540.0,
    wavelength_max=1560.0,
    power=10.0,
    sweep_speed=5.0,
    repetitions=1,
    use_picoscope=False  # No PicoScope needed
)
```

## Getting Help

1. Check error messages carefully
2. Verify all hardware connections
3. Test instruments with manufacturer software first
4. Check instrument manuals for network/GPIB configuration
5. Consult PyVISA documentation: https://pyvisa.readthedocs.io/
6. PicoScope SDK documentation: https://www.picotech.com/downloads

## Version Information

Tested with:
- Python 3.8+
- NumPy 1.21+
- Pandas 1.3+
- Matplotlib 3.4+
- PyVISA 1.12+
- PicoSDK 1.1+

Last updated: February 2024
