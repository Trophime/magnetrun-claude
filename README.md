"""
# MagnetRun

A Python package for analyzing magnetic measurement data from various sources including TDMS files, text files, and CSV files.

## Features

- **Multi-format support**: Read TDMS, TXT, and CSV files
- **Data cleaning**: Automatic removal of duplicates and empty columns
- **Unit management**: Comprehensive unit handling with Pint
- **Statistical analysis**: Peak detection, plateau analysis, breakpoint detection
- **Visualization**: Built-in plotting capabilities
- **Configurable**: Housing-specific configurations for different magnet types
- **CLI interface**: Command-line tools for common operations

## Installation

```bash
pip install magnetrun
```

For development:
```bash
git clone https://github.com/yourusername/magnetrun.git
cd magnetrun
pip install -e .[dev]
```

## Quick Start

### Python API

```python
from magnetrun import DataReader, DataAnalyzer, DataPlotter

# Read data file
magnet_run = DataReader.read_file('data.txt', housing='M9')

# Add time column (for pandas data)
from magnetrun.processing import TimeProcessor
TimeProcessor.add_time_column(magnet_run.magnet_data)

# Analyze data
peaks, _ = DataAnalyzer.find_peaks_in_data(magnet_run.magnet_data, 'Field')
plateaus = DataAnalyzer.detect_plateaus(magnet_run.magnet_data, 'Field')

# Plot results
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
DataPlotter.plot_time_series(magnet_run.magnet_data, ['Field'], ax=ax)
plt.show()
```

### Command Line Interface

```bash
# Get information about data files
magnetrun info data.txt --housing M9 --list-keys

# Convert to CSV
magnetrun info data.txt --convert

# Analyze data
magnetrun analyze data.txt --keys Field --plateaus --peaks

# Generate plots
magnetrun plot data.txt --keys Field Current --save
```

## Supported Housing Types

- **M8**: Housing configuration for M8 magnets
- **M9**: Housing configuration for M9 magnets  
- **M10**: Housing configuration for M10 magnets

Each housing type has specific current reference calculations and field mappings.

## Data Formats

### TDMS Files
- Supports National Instruments TDMS format
- Handles grouped data structure
- Automatic time offset correction for downsampled data

### Text Files  
- Space-separated values
- Automatic header detection
- Configurable data preparation based on housing type

### CSV Files
- Comma-separated values
- Standard pandas CSV reading

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black magnetrun/
flake8 magnetrun/
```

### Type Checking

```bash
mypy magnetrun/
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Changelog

### Version 1.0.0
- Initial restructured release
- Modular architecture
- Comprehensive test coverage
- CLI interface with Click
- Improved error handling
- Type hints throughout
"""
