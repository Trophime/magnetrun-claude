# MagnetRun

**A comprehensive Python package for analyzing magnetic measurement data with JSON-based field management.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🔬 Overview

MagnetRun provides a unified interface for reading, processing, and visualizing magnetic measurement data from multiple file formats. It features a modern JSON-based field management system that makes it easy to define, validate, and work with measurement data from LNCMI facilities.

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

### 📏 **JSON-Based Field Management**
Modern field definitions using easy-to-edit JSON configuration files:
```python
# Automatic field information from JSON definitions
field_label = data.get_field_label('Field')  # "B_res [T]"
symbol, unit_obj, unit_str = data.get_field_info('Current')  # ('I', <ampere>, 'A')
compatible_units = data.get_compatible_units('Field')  # ['tesla', 'gauss', 'millitesla']
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

# Explore the data with field information
print(f"Format: {data.format_type}")
print(f"Available keys: {data.keys}")
print(f"Field coverage: {data._get_field_coverage():.1f}%")

# Create analysis object
run = MagnetRun('M9', 'site1', data)
run.prepare_data()  # Apply housing-specific processing

# Extract specific data with proper field labels
field_current_data = data.get_data(['Field', 'Current'])

# Add calculated columns with field metadata
data.add_data('Power', 'Power = Field * Current', 
              field_type='power', unit='watt', symbol='P')

# Get field information with units
field_label = data.get_field_label('Field')  # "B_res [T]"
symbol, unit_obj, unit_str = data.get_field_info('Field')
```

## 🆕 JSON-Based Field Management

MagnetRun now uses JSON configuration files for field definitions, making it much easier to manage and extend:

### Built-in Format Definitions
- **pupitre.json**: Complete field definitions for Pupitre control system
- **pigbrother.json**: TDMS data acquisition format definitions  
- **bprofile.json**: Magnetic field profile measurement format

### Field Definition Structure
```json
{
  "format_name": "pupitre",
  "metadata": {
    "description": "Pupitre control system data format",
    "file_extension": ".txt"
  },
  "fields": [
    {
      "name": "Field",
      "field_type": "magnetic_field",
      "unit": "tesla",
      "symbol": "B_z",
      "description": "Resistive magnet field z component at the center",
    },
    {
      "name": "Current",
      "field_type": "current", 
      "unit": "ampere",
      "symbol": "I",
      "description": "Magnet current"
    }
  ]
}
```

### Working with Field Definitions
```python
# Access format definition
format_def = data.field_registry  # or data.format_definition

# Get field information
field = format_def.get_field('Field')
print(f"Symbol: {field.symbol}, Unit: {field.unit}")

# Field validation
validation = data.get_field_validation_summary()
print(f"Coverage: {validation['summary']['coverage_percent']:.1f}%")

# Unit conversion
converted_values = data.convert_field_values('Field', values, 'gauss')
compatible_units = data.get_compatible_units('Field')
```

## 📋 File Format Examples

### Pupitre Files (.txt)
Space-separated values with comprehensive field definitions:
```
Date        Time     Field    Current    Temperature
2024.01.15  10:30:00 0.0      0.0        20.1
2024.01.15  10:30:01 0.1      1.2        20.2
2024.01.15  10:30:02 0.2      2.4        20.3
```

### PigBrother Files (.tdms)
TDMS files with grouped channels and detailed field mapping:
```
Groups: Courants_Alimentations, Tensions_Aimant, Puissances
Channels: Courant_A1, Courant_A2, Tension_A1, Puissance_A1
Field definitions: 180+ predefined fields with proper units and symbols
```

### Bprofile Files (.txt)  
CSV format with field profile definitions:
```csv
Index,Position (mm),Profile at Tr (%),Profile at max (%)
0,299.7,-62.54857446812466,-51.83603303013679
1,299.8,-62.515206120643384,-51.80767721498118
2,299.9,-62.48169694682428,-51.77923216656832
```

## 🔧 Advanced Usage

### Adding Calculated Data with Field Information
```python
# Add new columns with proper field metadata
data.add_data('Power', 'Power = Field * Current', 
              field_type='power', unit='watt', symbol='P')
data.add_data('FieldSquared', 'FieldSquared = Field ** 2',
              field_type='magnetic_field', unit='tesla**2', symbol='B²')

# Field information is automatically preserved
power_label = data.get_field_label('Power')  # "P [W]"
```

### Housing-Specific Processing with M9 Configuration
```python
# Housing configurations now use JSON with field mapping
run_m9 = MagnetRun('M9', 'site1', data)   # Loads M9.json configuration
run_m9.prepare_data()

# M9 configuration includes:
# - Insert magnet: 14 coils with voltage tap locations
# - Bitters magnet: 2 coils  
# - Field mappings and reference calculations
```

### Field Validation and Quality Control
```python
# Comprehensive field validation
validation = data.get_field_validation_summary()
print(f"Valid fields: {validation['summary']['valid_fields']}")
print(f"Coverage: {validation['summary']['coverage_percent']:.1f}%")

# Individual field validation
field_result = data.validate_field_data('Field')
print(f"Field status: {field_result['status']}")
print(f"Valid values: {field_result['valid_values']}")
```

### Data Export with Field Information
```python
from magnetrun.io.writers import DataWriter

# Export to CSV with field metadata preserved
DataWriter.to_csv(data, 'output.csv')

# Export specific keys with field labels
field_labels = {key: data.get_field_label(key) for key in ['Field', 'Current']}
DataWriter.to_csv(data, 'field_current.csv', keys=['Field', 'Current'])

# Export to Excel with field information sheet
DataWriter.to_excel(data, 'data.xlsx')  # Includes field metadata
```

### Working with TDMS Data and Field Mappings
```python
# TDMS files have grouped structure with comprehensive field definitions
data = MagnetData.from_file('measurement.tdms')

# Access specific group/channel with field information
field_data = data.get_data(['Courants_Alimentations/Courant_A1'])
field_label = data.get_field_label('Courants_Alimentations/Courant_A1')  # "I_A1 [A]"

# Add cross-group calculations with proper field metadata
data.add_data('Total_Power', 
              'Total_Power = Puissances/Puissance_A1 + Puissances/Puissance_A2',
              field_type='power', unit='watt', symbol='P_total')
```

## 🏗️ Architecture

### Core Components

```python
# Main data container with integrated field management
MagnetData    # Auto-detecting data loader with JSON field definitions
MagnetRun     # High-level analysis interface with housing configurations

# JSON-based field system
FormatDefinition    # JSON-based format definitions
FormatRegistry      # Manages all format components and definitions
Field              # Individual field with type, unit, symbol
FieldType          # Enumeration of supported field types

# Format system
BaseReader         # Abstract reader interface
BaseData          # Abstract data handler with field integration
```

### Extension Points

#### Adding New File Formats with Field Support
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

# 2. Create a data handler with field integration  
class MyFormatData(BaseData):
    def __init__(self, filename: str, data: pd.DataFrame, metadata=None):
        super().__init__(filename, "myformat", metadata)
        self.data = data
        self._keys = data.columns.tolist()
        
        # Integrated field definition loading
        self.definition = self._load_format_definition()
    
    def _load_format_definition(self):
        """Load field definition from JSON."""
        from magnetrun.formats.format_definition import FormatDefinition
        config_path = Path(__file__).parent / "configs" / "myformat.json"
        return FormatDefinition.load_from_file(config_path)
    
    # Implement required methods with field support
    def get_field_info(self, key: str) -> tuple:
        field = self.definition.get_field(key)
        if field:
            return field.symbol, field.get_unit_object(self.definition.ureg), field.unit
        return key, None, ""

# 3. Create JSON field definition
# Save to magnetrun/formats/configs/myformat.json:
{
  "format_name": "myformat",
  "metadata": {"description": "My custom format"},
  "fields": [
    {
      "name": "MyField",
      "field_type": "magnetic_field", 
      "unit": "tesla",
      "symbol": "B_my",
      "description": "My magnetic field measurement"
    }
  ]
}

# 4. Register the format
format_registry.register_format("myformat", MyFormatReader, MyFormatData)

# 5. Use immediately with full field support!
data = MagnetData.from_file('data.myext')
field_label = data.get_field_label('MyField')  # "B_my [T]"
```

#### Adding New Housing Configurations
```python
# Housing configurations now use JSON files in magnetrun/config/
# Create magnetrun/config/m11.json:
{
  "metadata": {
    "description": "M11 housing configuration",
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "Insert": {
    "pupitre": {
      "current": {
        "fields": ["Idcct1", "Idcct2", "Idcct3"],
        "field_type": "current",
        "symbol": "I_insert",
        "unit": "ampere",
        "formula": "Idcct1 + Idcct2 + Idcct3"
      },
      "coil_voltage": {
        "fields": ["Ucoil1", "Ucoil2", "Ucoil3"],
        "field_type": "voltage",
        "symbol": "U_coil",
        "unit": "volt"
      }
    }
  },
  "voltage_tap_locations": {
    "Ucoil1": [0.12, 0.0, -0.45],
    "Ucoil2": [0.12, 0.0, -0.35],
    "Ucoil3": [0.12, 0.0, -0.25]
  }
}

# Use immediately
run = MagnetRun('M11', 'site1', data)
run.prepare_data()  # Applies M11-specific processing with field management
```

## 💻 Command Line Interface

MagnetRun includes a comprehensive CLI with enhanced field management capabilities.

### Field Management Commands

```bash
# List available format definitions
magnetrun formats list --detailed

# Show specific format with field information
magnetrun formats show pupitre

# Edit format configuration files
magnetrun formats edit pupitre

# Validate field definitions
magnetrun formats validate pupitre

# Show field information
magnetrun formats fields pupitre --field-type current


### Enhanced Data Processing with Field Awareness

```bash
# File information with field validation
magnetrun info show data.txt --list-keys --validate-fields

# Plotting with proper field labels
magnetrun plot show data.txt --keys Field Current --save
magnetrun plot field-validation data.txt --save  # New field validation plots
magnetrun plot field-types data.txt --save       # Field type distribution

# Analysis with field context
magnetrun stats analyze data.txt --keys Field Current --field-info

# ETL operations with field preservation
magnetrun etl transform data.txt --add-field-info --normalize-units
magnetrun etl validate data.txt --check-field-definitions --check-units
```

### Field-Aware Batch Processing

```bash
# Process with field validation
magnetrun formats validate *.json --check-fields
magnetrun etl validate *.dat --check-field-definitions --export-report

# Enhanced conversion preserving field information
magnetrun select extract *.tdms --convert --preserve-field-info
```

## 🔍 API Reference

### MagnetData (Enhanced)

Enhanced data container with integrated field management:

```python
# Class methods
MagnetData.from_file(filepath)              # Auto-detect with field loading
MagnetData.from_pandas(filename, dataframe) # With field definition creation

# Properties  
.filename           # Source filename
.keys              # Available data keys
.format_type       # Format name ('pupitre', 'pigbrother', 'bprofile')
.field_registry    # FormatDefinition with field information
.format_definition # Same as field_registry

# Enhanced methods with field support
.get_data(keys=None)                    # Extract data
.get_field_info(key)                    # Get (symbol, unit_obj, unit_string)
.get_field_label(key, show_unit=True)   # Get formatted label "Symbol [unit]"
.convert_field_values(key, values, target_unit)  # Unit conversion
.get_compatible_units(key)              # List compatible units
.get_field_validation_summary()         # Comprehensive validation
.validate_field_data(key)              # Individual field validation
.get_data_summary()                     # Statistics with field information

# Field management
.save_format_definition(filepath)       # Export field definitions
.load_format_definition(filepath)       # Import field definitions
```

### FormatDefinition (New)

JSON-based format definitions:

```python
# Loading and saving
FormatDefinition.load_from_file(filepath, ureg)
.save_to_file(filepath)

# Field access
.get_field(name)                        # Get field by name
.list_fields()                          # Get all field names
.get_fields_by_type(field_type)        # Filter by type
.add_field(field)                       # Add new field

# Unit operations
.convert_field_values(field_name, values, target_unit)
.get_field_label(field_name, show_unit=True)
.validate_field_unit(field_name)
.get_compatible_units(field_name)
```

### FormatRegistry (Enhanced)

Unified registry for formats and field definitions:

```python
# Format management
.register_format(name, reader_class, data_handler_class)
.get_format_definition(name)
.list_format_definitions()

# Configuration management
.get_configs_directory()
.reload_format_definitions()
.save_format_definition(name, filepath)
.load_format_definition(filepath)

# Unit conversion
.convert_between_units(value, from_unit, to_unit)
```

## 🧪 Examples

### Enhanced Analysis Pipeline with Field Management
```python
from magnetrun import MagnetData, MagnetRun
from magnetrun.formats import FormatRegistry

# Load data with automatic field definitions
data = MagnetData.from_file('measurement.tdms')
run = MagnetRun('M9', 'Lab1', data)
run.prepare_data()

# Field validation and quality assessment
validation = data.get_field_validation_summary()
print(f"Field coverage: {validation['summary']['coverage_percent']:.1f}%")
print(f"Data quality: {validation['summary']['quality_percent']:.1f}%")

# Add calculated fields with proper metadata
data.add_data('Power', 'Power = Field * Current',
              field_type='power', unit='watt', symbol='P')

# Export with field information preserved
from magnetrun.io.writers import DataWriter
DataWriter.to_excel(data, 'results.xlsx')  # Includes field metadata sheet

# Create field-aware visualizations
from magnetrun.visualization.plotters import DataPlotter
DataPlotter.plot_field_validation_summary(data, save=True)
DataPlotter.plot_field_type_distribution(data, save=True)
```

### Working with Custom Field Definitions
```python
from magnetrun.formats import FormatDefinition, FormatRegistry
from magnetrun.core.fields import Field, FieldType

# Create custom format definition
registry = FormatRegistry()
custom_format = FormatDefinition("my_format", registry.ureg)

# Add fields with detailed metadata
custom_field = Field(
    name="CustomField",
    field_type=FieldType.MAGNETIC_FIELD,
    unit="millitesla",
    symbol="B_custom",
    description="Custom magnetic field measurement"
)
custom_format.add_field(custom_field)

# Save and use
custom_format.save_to_file("my_format.json")
registry.register_format_definition(custom_format)

# Now use with data
data = MagnetData.from_file("data.txt")
if data.format_type == "my_format":
    label = data.get_field_label("CustomField")  # "B_custom [mT]"
    compatible = data.get_compatible_units("CustomField")  # ['tesla', 'gauss', 'millitesla']
```

## 🤝 Contributing

Contributions are welcome! The JSON-based field system makes it especially easy to add new format definitions:

### Adding New Format Definitions
1. Create a JSON configuration file in `magnetrun/formats/configs/`
2. Define fields with proper types, units, symbols, and descriptions
3. Test with existing data files
4. Submit a pull request

### Adding New Features
1. Fork the repository
2. Create a feature branch
3. Add your improvements with field system integration
4. Add tests for new functionality
5. Update JSON configurations if needed
6. Submit a pull request

### Development Setup
```bash
git clone https://github.com/yourorg/magnetrun.git
cd magnetrun
pip install -e ".[dev]"
pytest tests/

# Work with format definitions
cd magnetrun/formats/configs/
# Edit JSON files directly - they're auto-loaded!
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Pint](https://pint.readthedocs.io/) for unit management
- TDMS file support via [npTDMS](https://nptdms.readthedocs.io/)
- Data manipulation with [Pandas](https://pandas.pydata.org/)
- JSON-based configuration for easy field management

## 📞 Support

- **Documentation**: Coming soon
- **Issues**: [GitHub Issues](https://github.com/yourorg/magnetrun/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourorg/magnetrun/discussions)

## 🆕 What's New in Field Management v2.1.0

### ✅ **Simplified Architecture**
- JSON configuration files replace complex Python field definitions
- Direct editing of field properties without programming
- Auto-loading from `magnetrun/formats/configs/` directory

### ✅ **Built-in Format Definitions**
- Complete field definitions for `pupitre`, `pigbrother`, and `bprofile` formats
- 180+ predefined fields with proper units, symbols, and descriptions
- Housing configurations with field mapping and voltage tap locations

### ✅ **Enhanced CLI**
- `magnetrun formats` command group for field management
- Field validation and quality control commands
- Unit conversion and compatibility checking

### ✅ **Improved Integration**
- Format classes have direct access to their field definitions
- Seamless field information in all data operations
- Comprehensive validation and quality reporting

### ✅ **Developer Friendly**
- Version control friendly JSON configurations
- Easy sharing and collaboration on field definitions
- Clear migration path from legacy field systems

---

*MagnetRun: Making magnetic measurement analysis simple, powerful, and extensible with modern field management.*
