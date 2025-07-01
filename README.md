# MagnetRun

**A comprehensive Python package for analyzing magnetic measurement data from various sources.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🔬 Overview

MagnetRun provides a unified interface for reading, processing, and visualizing magnetic measurement data from multiple file formats. It was designed to handle the complexity of different measurement systems while providing a simple, consistent API for data analysis.

### 📊 Supported File Formats

- **🔧 Pupitre files**: Space-separated data with .txt extension from pupitre measurement systems
- **⚡ PigBrother files**: TDMS files from PigBrother measurement systems  
- **📈 Bprofile files**: Profile measurement data in CSV format with .txt extension
- **🔌 Extensible**: Easy to add support for new file formats

## ✨ Key Features

### 🎯 **Automatic Format Detection**
```python
# No need to specify format - automatically detected!
data = MagnetData.from_file('measurement.tdms')    # TDMS format
data = MagnetData.from_file('pupitre_data.txt')    # Space-separated
data = MagnetData.from_file('bprofile.txt')        # CSV with headers
```

### 🔧 **Unified API**
```python
# Same interface regardless of file format
keys = data.keys                           # Available columns
field_data = data.get_data(['Field'])      # Extract data
data.add_data('Power', 'Power = Field * Current')  # Add calculations
info = data.get_info()                     # Get metadata
```

### 🏗️ **Extensible Architecture**
```python
# Easy to add new formats
format_registry.register_format("custom", CustomReader, CustomData)
```

### 📏 **Unit-Aware Computing**
Built-in support for physical units using Pint:
```python
# Automatic unit inference and conversion
field_unit = data.get_unit_key('Field')    # ('B', tesla)
temperature_unit = data.get_unit_key('T1') # ('T', degree_Celsius)
```

### 🎛️ **Housing-Specific Processing**
```python
# Automatic processing based on magnet housing type
run = MagnetRun('M9', 'Lab1', data)
run.prepare_data()  # Applies M9-specific transformations
```

## 🚀 Quick Start

### Installation

```bash
pip install magnetrun
```

### Basic Usage

```python
from magnetrun import MagnetData, MagnetRun

# Load data (format auto-detected)
data = MagnetData.from_file('your_measurement_file.tdms')

# Explore the data
print(f"Format: {data.format_type}")
print(f"Available keys: {data.keys}")
print(f"Data shape: {data.get_info()['metadata']['shape']}")

# Create analysis object
run = MagnetRun('M9', 'site1', data)
run.prepare_data()  # Apply housing-specific processing

# Extract specific data
field_current_data = data.get_data(['Field', 'Current'])

# Add calculated columns
data.add_data('Power', 'Power = Field * Current')

# Get data with units
symbol, unit = data.get_unit_key('Field')
print(f"Field unit: {symbol} [{unit}]")
```

## 📋 File Format Examples

### Pupitre Files (.txt)
Space-separated values:
```
timestamp    Field    Current    Temperature
0.0          0.0      0.0        20.1
0.1          0.1      1.2        20.2
0.2          0.2      2.4        20.3
```

### PigBrother Files (.tdms)
TDMS files with grouped channels:
```
Groups: Courants_Alimentations, Champ_magnetique, Tensions
Channels: Référence_A1, Référence_A2, Field_X, Field_Y
```

### Bprofile Files (.txt)  
CSV format with specific column structure:
```csv
Index,Position (mm),Profile at Tr (%),Profile at max (%)
0,299.7,-62.54857446812466,-51.83603303013679
1,299.8,-62.515206120643384,-51.80767721498118
2,299.9,-62.48169694682428,-51.77923216656832
```

## 🔧 Advanced Usage

### Adding Calculated Data
```python
# Add new columns with formulas
data.add_data('Power', 'Power = Field * Current')
data.add_data('FieldSquared', 'FieldSquared = Field ** 2')

# Specify units for new columns
data.add_data('Energy', 'Energy = Power * time', unit='J')
```

### Housing-Specific Processing
```python
# Different housing configurations
run_m8 = MagnetRun('M8', 'site1', data)   # M8 configuration
run_m9 = MagnetRun('M9', 'site1', data)   # M9 configuration
run_m10 = MagnetRun('M10', 'site1', data) # M10 configuration

# Each applies different reference calculations and field mappings
run_m9.prepare_data()
```

### Data Export
```python
from magnetrun.io.writers import DataWriter

# Export to CSV
DataWriter.to_csv(data, 'output.csv')

# Export specific keys only
DataWriter.to_csv(data, 'field_current.csv', keys=['Field', 'Current'])

# Export to Excel
DataWriter.to_excel(data, 'data.xlsx')
```

### Working with TDMS Data
```python
# TDMS files have grouped structure
data = MagnetData.from_file('measurement.tdms')

# Access specific group/channel
field_data = data.get_data(['Champ_magnetique/Field_X'])
current_data = data.get_data(['Courants_Alimentations/Référence_A1'])

# Add cross-group calculations
data.add_data('Courants_Alimentations/Total_Current', 
              'Total_Current = Référence_A1 + Référence_A2')
```

## 🏗️ Architecture

### Core Components

```python
# Main data container
MagnetData    # Auto-detecting data loader
MagnetRun     # High-level analysis interface

# Format system
BaseReader    # Abstract reader interface
BaseData      # Abstract data handler
FormatRegistry # Plugin management
```

### Extension Points

#### Adding New File Formats
```python
from magnetrun.io.base_reader import BaseReader
from magnetrun.core.base_data import BaseData
from magnetrun.formats.registry import format_registry

# 1. Create a reader
class MyFormatReader(BaseReader):
    @property
    def format_name(self) -> str:
        return "myformat"
    
    @property  
    def supported_extensions(self) -> List[str]:
        return ['.myext']
    
    def can_read(self, filepath: Path) -> bool:
        # Detection logic
        return filepath.suffix == '.myext'
    
    def read(self, filepath: Path) -> Dict[str, Any]:
        # File reading logic
        data = pd.read_csv(filepath)  # or custom parsing
        return {
            'data': data,
            'format_type': self.format_name,
            'metadata': {'shape': data.shape}
        }

# 2. Create a data handler  
class MyFormatData(BaseData):
    def __init__(self, filename: str, data: pd.DataFrame, metadata=None):
        super().__init__(filename, "myformat", metadata)
        self.data = data
        self._keys = data.columns.tolist()
        self._setup_units()
    
    def get_data(self, key=None):
        if key is None:
            return self.data.copy()
        return self.data[key].copy()
    
    def add_data(self, key: str, formula: str, unit=None):
        self.data.eval(formula, inplace=True)
        self._keys.append(key)
    
    def _setup_units(self):
        # Set up units for your format
        pass

# 3. Register the format
format_registry.register_format("myformat", MyFormatReader, MyFormatData)

# 4. Use immediately!
data = MagnetData.from_file('data.myext')  # Works automatically!
```

#### Adding New Housing Configurations
```python
from magnetrun.config.housing_configs import HOUSING_CONFIGS, HousingConfig

# Define new housing
HOUSING_CONFIGS["M11"] = HousingConfig(
    name="M11",
    ih_ref_channels=["IH1", "IH2", "IH3", "IH4", "IH5"],
    ib_ref_channels=["IB1", "IB2", "IB3", "IB4"],
    field_mappings={"B_new": "Field"},
    remove_channels=["obsolete_channel"]
)

# Use immediately
run = MagnetRun('M11', 'site1', data)
run.prepare_data()  # Applies M11-specific processing
```

## 🔍 API Reference

### MagnetData

The main data container class:

```python
# Class methods
MagnetData.from_file(filepath)              # Auto-detect and load
MagnetData.from_pandas(filename, dataframe) # From pandas DataFrame
MagnetData.from_dict(filename, groups, keys, data) # From TDMS structure

# Properties
.filename      # Source filename
.keys         # Available data keys
.format_type  # Format name ('pupitre', 'pigbrother', 'bprofile')
.units        # Unit information for each key
.metadata     # Additional metadata

# Methods
.get_data(keys=None)              # Extract data
.add_data(key, formula, unit=None) # Add calculated column
.remove_data(keys)                # Remove columns
.rename_data(mapping)             # Rename columns
.get_info()                       # Get dataset information
.get_unit_key(key)               # Get unit info for key
```

### MagnetRun

High-level analysis interface:

```python
# Constructor
MagnetRun(housing, site, magnet_data=None)

# Properties
.housing        # Housing type ('M8', 'M9', 'M10')
.site          # Site identifier
.magnet_data   # Associated MagnetData object
.housing_config # Housing configuration

# Methods
.get_data(key=None)    # Get data from MagnetData
.get_keys()           # Get available keys
.prepare_data()       # Apply housing-specific processing
```

### DataWriter

Export utilities:

```python
DataWriter.to_csv(magnet_data, filepath, keys=None, separator='\t')
DataWriter.to_excel(magnet_data, filepath, keys=None)
```

## 💻 Command Line Interface

MagnetRun includes a comprehensive CLI for batch processing and analysis without writing Python code.

### Installation & Basic Usage

```bash
# Install MagnetRun
pip install magnetrun

# Verify installation
magnetrun --version

# Get help
magnetrun --help
```

### CLI Command Overview

```bash
magnetrun info      # File information and validation
magnetrun plot      # Data visualization  
magnetrun stats     # Statistical analysis
magnetrun add       # Data processing and formulas
magnetrun select    # Data extraction and conversion
```

### File Information & Validation

```bash
# Basic file information
magnetrun info show data.txt

# List all available data keys
magnetrun info show measurement.tdms --list-keys

# Validate multiple files
magnetrun info validate *.txt *.tdms

# Convert files to CSV
magnetrun info show data.txt --convert

# Check supported formats
magnetrun info formats
```

### Working with Multiple Files

```bash
# Process all TDMS files in current directory
magnetrun info show *.tdms --list-keys

# Process files in subdirectories
magnetrun info show data/*.tdms measurements/*.txt --housing M9

# Validate mixed file types
magnetrun info validate data/*.txt measurements/*.tdms profiles/*.csv

# Convert multiple files
magnetrun info show *.tdms --convert
```

### Data Visualization

```bash
# Basic time series plot
magnetrun plot show data.txt --keys Field Current --save

# Plot multiple files
magnetrun plot show *.tdms --keys Field --save --output-dir figures/

# X-Y scatter plots
magnetrun plot show data.txt --key-vs-key "Field-Current" --save

# Normalized plots
magnetrun plot show *.txt --keys Field Current --normalize --save

# Overview plots with templates
magnetrun plot overview *.tdms --template publication --save

# Subplot grids
magnetrun plot subplots data.txt --keys Field Current Temperature --cols 2

# Breakpoint analysis
magnetrun plot breakpoints *.tdms --keys Field --compare --save
```

### Statistical Analysis

```bash
# Basic statistical analysis
magnetrun stats analyze data.txt --keys Field Current

# Find local maxima
magnetrun stats analyze *.tdms --localmax --save

# Plateau detection
magnetrun stats analyze data.txt --plateau --threshold 1e-3

# Breakpoint detection
magnetrun stats analyze *.txt --detect-bkpts --level 95 --save

# Combined analysis on multiple files
magnetrun stats analyze *.tdms --plateau --localmax --detect-bkpts --save
```

### Data Processing

```bash
# Add calculated columns
magnetrun add formula data.txt --formula "Power = Field * Current"

# Add and plot formula
magnetrun add formula *.tdms --formula "Energy = Power * 0.1" --plot-formula --save

# Process multiple files with formulas
magnetrun add formula measurements/*.txt --formula "FieldNorm = Field / 10.0" --save
```

### Data Selection & Conversion

```bash
# Convert files to CSV
magnetrun select extract *.tdms --convert

# Extract time ranges
magnetrun select extract data.txt --output-timerange "10;50" 

# Extract specific data at times
magnetrun select extract *.txt --output-time "5;10;15"

# Extract specific keys
magnetrun select extract data.txt --output-key "Field;Current"

# Extract key pairs
magnetrun select extract *.tdms --extract-pairkeys "Field-Current;Voltage-Current"
```

### Chaining CLI Commands

MagnetRun CLI commands can be chained using shell operators for powerful batch processing:

#### Sequential Processing
```bash
# Validate → Analyze → Plot → Export
magnetrun info validate *.tdms && \
magnetrun stats analyze *.tdms --plateau --save && \
magnetrun plot overview *.tdms --template publication --save && \
magnetrun select extract *.tdms --convert
```

#### Conditional Processing
```bash
# Only process if validation passes
magnetrun info validate data.txt && magnetrun plot show data.txt --save
```

#### Parallel Processing with GNU Parallel
```bash
# Process files in parallel
ls *.tdms | parallel magnetrun plot show {} --keys Field --save

# Parallel analysis with different parameters
ls *.txt | parallel magnetrun stats analyze {} --plateau --threshold {%}e-3
```

#### Advanced Batch Processing Scripts

**Process by file type:**
```bash
#!/bin/bash
# process_measurements.sh

# Process all TDMS files
echo "Processing TDMS files..."
magnetrun info show *.tdms --list-keys > tdms_keys.txt
magnetrun plot overview *.tdms --template standard --save --output-dir tdms_plots/
magnetrun stats analyze *.tdms --plateau --localmax --save

# Process all text files  
echo "Processing text files..."
magnetrun info show *.txt --list-keys > txt_keys.txt
magnetrun plot show *.txt --keys Field Current --save --output-dir txt_plots/
magnetrun add formula *.txt --formula "Power = Field * Current" --plot-formula --save

# Convert everything to CSV
echo "Converting to CSV..."
magnetrun select extract *.tdms *.txt --convert

echo "Batch processing complete!"
```

**Quality control pipeline:**
```bash
#!/bin/bash
# quality_control.sh

DATA_DIR="measurements"
OUTPUT_DIR="analysis_results"
mkdir -p $OUTPUT_DIR

echo "=== MagnetRun Quality Control Pipeline ==="

# 1. Validate all files
echo "Step 1: Validating files..."
magnetrun info validate $DATA_DIR/*.* > $OUTPUT_DIR/validation_report.txt

# 2. Generate overview plots
echo "Step 2: Generating overview plots..."
magnetrun plot overview $DATA_DIR/*.tdms --template publication --save --output-dir $OUTPUT_DIR/overview/

# 3. Statistical analysis
echo "Step 3: Running statistical analysis..."
magnetrun stats analyze $DATA_DIR/*.* --plateau --localmax --detect-bkpts --save > $OUTPUT_DIR/stats_summary.txt

# 4. Create detailed plots for problematic files
echo "Step 4: Detailed analysis..."
magnetrun plot breakpoints $DATA_DIR/*.tdms --compare --save --output-dir $OUTPUT_DIR/breakpoints/

# 5. Export processed data
echo "Step 5: Exporting data..."
magnetrun select extract $DATA_DIR/*.* --convert
mv *.csv $OUTPUT_DIR/

echo "Quality control complete! Results in $OUTPUT_DIR/"
```

#### Using with Make
```makefile
# Makefile for MagnetRun processing

DATA_FILES := $(wildcard data/*.tdms data/*.txt)
PLOT_DIR := plots
RESULTS_DIR := results

.PHONY: all validate analyze plot export clean

all: validate analyze plot export

validate:
	magnetrun info validate $(DATA_FILES) > validation.log

analyze: validate
	magnetrun stats analyze $(DATA_FILES) --plateau --save

plot: analyze
	mkdir -p $(PLOT_DIR)
	magnetrun plot overview $(DATA_FILES) --template publication --save --output-dir $(PLOT_DIR)/

export: analyze
	mkdir -p $(RESULTS_DIR)
	magnetrun select extract $(DATA_FILES) --convert
	mv *.csv $(RESULTS_DIR)/

clean:
	rm -rf $(PLOT_DIR) $(RESULTS_DIR) *.png *.csv validation.log
```

#### Real-World Example: Daily Data Processing
```bash
#!/bin/bash
# daily_processing.sh - Process daily measurement files

DATE=$(date +%Y%m%d)
RAW_DATA="/data/measurements/$DATE"
PROCESSED="/data/processed/$DATE"
ARCHIVE="/data/archive/$DATE"

mkdir -p $PROCESSED $ARCHIVE

echo "Processing measurements for $DATE"

# 1. Quality check
echo "Validating files..."
if ! magnetrun info validate $RAW_DATA/*.tdms $RAW_DATA/*.txt; then
    echo "ERROR: File validation failed!"
    exit 1
fi

# 2. Generate daily summary plots
echo "Creating summary plots..."
magnetrun plot overview $RAW_DATA/*.tdms --template standard --save --output-dir $PROCESSED/plots/

# 3. Find interesting features
echo "Analyzing for plateaus and breakpoints..."
magnetrun stats analyze $RAW_DATA/*.* --plateau --detect-bkpts --save > $PROCESSED/analysis_summary.txt

# 4. Process each housing type separately
for housing in M8 M9 M10; do
    echo "Processing $housing data..."
    housing_files=$(ls $RAW_DATA/*$housing* 2>/dev/null || true)
    if [[ -n "$housing_files" ]]; then
        magnetrun add formula $housing_files --formula "Power = Field * Current" --save
        magnetrun plot show $housing_files --keys Field Current Power --save --output-dir $PROCESSED/$housing/
    fi
done

# 5. Export processed data
echo "Exporting to CSV..."
magnetrun select extract $RAW_DATA/*.* --convert
mv *.csv $PROCESSED/

# 6. Archive raw data
echo "Archiving raw data..."
cp $RAW_DATA/*.* $ARCHIVE/

echo "Daily processing complete for $DATE"
```

#### Integration with Other Tools

**With rsync for data synchronization:**
```bash
# Sync data from measurement computer and process
rsync -av measurement-pc:/data/today/ ./raw_data/
magnetrun info validate raw_data/*.* && magnetrun stats analyze raw_data/*.* --save
```

**With cron for automated processing:**
```bash
# Add to crontab: process measurements every hour
0 * * * * cd /home/user/magnetrun && ./hourly_processing.sh >> processing.log 2>&1
```

**With database logging:**
```bash
# Extract key metrics and log to database
magnetrun stats analyze *.tdms --plateau > stats.txt
python parse_stats.py stats.txt | sqlite3 measurements.db ".import /dev/stdin daily_stats"
```

### CLI Tips & Tricks

#### Useful Patterns
```bash
# Process only files modified today
find . -name "*.tdms" -mtime -1 -exec magnetrun plot show {} --save \;

# Process files by size (avoid very large files)
find . -name "*.txt" -size -100M -exec magnetrun stats analyze {} --plateau \;

# Create subdirectories for output
magnetrun plot show *.tdms --save --output-dir $(date +%Y%m%d)/

# Process with specific housing based on filename
for file in *M9*.tdms; do magnetrun stats analyze "$file" --housing M9; done

# Quick data exploration
magnetrun info show *.* --list-keys | grep -E "(Field|Current|Power)"
```

#### Error Handling
```bash
# Process files with error logging
for file in *.tdms; do
    if magnetrun plot show "$file" --save 2>error.log; then
        echo "✓ Processed $file"
    else
        echo "✗ Failed $file (see error.log)"
    fi
done

# Skip problematic files and continue
magnetrun plot show *.tdms --save || echo "Some files failed, continuing..."
```

#### Performance Optimization
```bash
# Process large datasets efficiently
magnetrun select extract huge_file.tdms --output-timerange "0;100" --convert  # Extract subset first
magnetrun plot show processed_subset.csv --save  # Then analyze subset

# Use specific keys to reduce memory usage
magnetrun plot show *.tdms --keys Field Current --save  # Only load needed data
```

## 🧪 Examples

### Python API Examples

#### Basic Analysis Pipeline
```python
from magnetrun import MagnetData, MagnetRun

# Load and prepare data
data = MagnetData.from_file('measurement.tdms')
run = MagnetRun('M9', 'Lab1', data)
run.prepare_data()

# Add calculated fields
data.add_data('Power', 'Power = Field * Current')
data.add_data('FieldNormalized', 'FieldNormalized = Field / Field.max()')

# Extract analysis data
analysis_data = data.get_data(['Field', 'Current', 'Power'])

# Statistical analysis
print(f"Max power: {analysis_data['Power'].max():.2f}")
print(f"Mean field: {analysis_data['Field'].mean():.3f}")

# Export results
from magnetrun.io.writers import DataWriter
DataWriter.to_csv(data, 'analysis_results.csv')
```

### Multi-File Processing
```python
from pathlib import Path
from magnetrun import MagnetData

results = []
data_dir = Path('measurements/')

for file_path in data_dir.glob('*.tdms'):
    try:
        data = MagnetData.from_file(file_path)
        
        # Extract key metrics
        if 'Field' in data.keys:
            field_data = data.get_data(['Field'])
            max_field = field_data['Field'].max()
            results.append({
                'file': file_path.name,
                'max_field': max_field,
                'format': data.format_type
            })
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

# Create summary
import pandas as pd
summary = pd.DataFrame(results)
print(summary)
```

### Format Validation
```python
from magnetrun.io.format_detector import FormatDetector
from pathlib import Path

detector = FormatDetector()

# Check multiple files
files = ['data1.txt', 'data2.tdms', 'profile.txt']

for file_path in files:
    path = Path(file_path)
    if path.exists():
        format_type = detector.detect_format(path)
        if format_type:
            print(f"✓ {file_path}: {format_type} format")
        else:
            print(f"✗ {file_path}: Unknown format")
    else:
        print(f"? {file_path}: File not found")
```

## 🤝 Contributing

Contributions are welcome! The extensible architecture makes it easy to add new features:

### Adding New Formats
1. Create a `Reader` class inheriting from `BaseReader`
2. Create a `Data` class inheriting from `BaseData`  
3. Register with `format_registry.register_format()`
4. Add tests and documentation

### Adding New Features
1. Fork the repository
2. Create a feature branch
3. Add your improvements
4. Add tests for new functionality
5. Submit a pull request

### Development Setup
```bash
git clone https://github.com/yourorg/magnetrun.git
cd magnetrun
pip install -e ".[dev]"
pytest tests/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Pint](https://pint.readthedocs.io/) for unit management
- TDMS file support via [npTDMS](https://nptdms.readthedocs.io/)
- Data manipulation with [Pandas](https://pandas.pydata.org/)

## 📞 Support

- **Documentation**: Coming soon
- **Issues**: [GitHub Issues](https://github.com/yourorg/magnetrun/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourorg/magnetrun/discussions)

---

*MagnetRun: Making magnetic measurement analysis simple, powerful, and extensible.*