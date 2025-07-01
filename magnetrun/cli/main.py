#!/usr/bin/env python3
"""
Entry point for the MagnetRun CLI application.
Complete CLI definition with updated field management
"""

import click
from .info import info_commands
from .plotting import plotting_commands
from .analysis import analysis_commands
from .processing import processing_commands
from .selection import selection_commands
from .etl import etl_commands
from .formats import formats  # CORRECTED: Use new formats CLI


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.pass_context
def cli(ctx, debug):
    """MagnetRun CLI - Tools for processing and analyzing magnet measurement data.

    Available command groups:

    \b
    info      - File information and validation commands
    plot      - Visualization and plotting commands
    stats     - Statistical analysis and feature detection
    add       - Data processing and formula commands
    select    - Data extraction and conversion commands
    etl       - ETL operations for format-specific transformations
    formats   - Format management and validation commands (JSON-based)
    
    Use 'magnetrun COMMAND --help' for detailed help on each command group.
    
    The field management system now uses JSON configuration files for
    all LNCMI measurement formats (pupitre, pigbrother, bprofile).
    """
    # Ensure that ctx.obj exists and is a dict (in case `cli()` is called by way of the repl)
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug


# Register all command groups
cli.add_command(info_commands)
cli.add_command(plotting_commands)
cli.add_command(analysis_commands)
cli.add_command(processing_commands)
cli.add_command(selection_commands)
cli.add_command(etl_commands)
cli.add_command(formats)  # CORRECTED: Use new formats CLI


@cli.command()
def version():
    """Show version information."""
    try:
        from .. import __version__
        click.echo(f"MagnetRun CLI v{__version__}")
    except ImportError:
        click.echo("MagnetRun CLI (version unknown)")
    
    # Show field management version
    try:
        from ..core.fields import __field_management_version__
        click.echo(f"Field Management System: v{__field_management_version__}")
    except (ImportError, AttributeError):
        click.echo("Field Management System: v2.1.0 (JSON-based)")


@cli.command()
def examples():
    """Show usage examples with JSON-based field management."""
    examples_text = """
MagnetRun CLI Usage Examples:

File Information:
  magnetrun info show data.txt --list-keys
  magnetrun info validate *.dat
  magnetrun info formats

Plotting:
  magnetrun plot show data.txt --keys Field Current --save
  magnetrun plot subplots data.txt --keys Field Current Voltage --cols 2
  magnetrun plot overview data.txt --template publication --save
  magnetrun plot convert-units data.txt --field-name Field --units "tesla,gauss,millitesla" --save
  magnetrun plot field-validation data.txt --save
  magnetrun plot field-types data.txt --save

Analysis:
  magnetrun stats analyze data.txt --localmax --save
  magnetrun stats analyze data.txt --plateau --threshold 0.001
  magnetrun stats extrema data.txt --keys Field Current --mode both --save
  magnetrun stats stats data.txt --key Field --percentiles "10,25,50,75,90,99"

Data Processing:
  magnetrun add formula data.txt --formula "Power = Field * Current" --plot-formula
  magnetrun add formula data.txt --key-pairs "Field;Power"
  magnetrun add formula data.txt --compute

Data Selection:
  magnetrun select extract data.txt --key "Field;Current" 
  magnetrun select extract data.txt --time-range "10;20"
  magnetrun select extract data.txt --key-pairs "Field;Current,Voltage;Power"
  magnetrun select extract data.txt --convert

ETL Operations (Enhanced):
  magnetrun etl transform data.txt --normalize-units --add-metadata --add-field-info
  magnetrun etl migrate data.txt --target-format pupitre --map-fields
  magnetrun etl validate data.txt --check-units --check-ranges --check-field-definitions
  magnetrun etl merge file1.txt file2.txt --output-file merged.csv --preserve-field-info

Format Management (JSON-based):
  # List available format definitions
  magnetrun formats list --detailed
  
  # Show specific format
  magnetrun formats show pupitre
  
  # Edit format configuration files directly
  magnetrun formats edit pupitre
  
  # Show configs directory
  magnetrun formats configs
  
  # Reload formats after editing
  magnetrun formats reload --verbose
  
  # Validate format definitions
  magnetrun formats validate pupitre
  
  # Import and install custom formats
  magnetrun formats import my_format.json --install
  
  # Create format from data file
  magnetrun formats create my_format data.csv
  
  # Show fields in a format
  magnetrun formats fields pupitre --field-type current
  
  # Show compatible units
  magnetrun formats units pupitre Field
  
  # Convert between units
  magnetrun formats convert pupitre tesla gauss 1.5

Multiple Files:
  magnetrun plot show *.txt --keys Field --normalize --save
  magnetrun stats analyze measurement_*.dat --localmax
  magnetrun formats validate *.json --check-fields
  magnetrun etl validate *.dat --check-field-definitions --export-report

Key Improvements in Field Management:
  - JSON-based format definitions (easy to edit and share)
  - Auto-loading from configs directory
  - Direct access to field definitions in data classes
  - Comprehensive CLI for format management
  - Built-in definitions for pupitre, pigbrother, bprofile formats
  - Simplified workflow - edit JSON files directly
    """
    click.echo(examples_text)


@cli.command()
def migrate_help():
    """Show migration guide to JSON-based field system."""
    migration_text = """
Migration Guide: Complex → JSON-Based Field System

OLD COMPLEX WORKFLOW:
1. magnetrun field discover *.tdms --output fields.yaml
2. magnetrun field extend fields.yaml "B_coil" --field-type magnetic_field
3. magnetrun field check data.tdms --config fields.yaml --strict
4. magnetrun field merge config1.json config2.yaml --output combined.json

NEW JSON-BASED WORKFLOW:
1. magnetrun formats list --detailed
   (Built-in JSON format definitions automatically loaded)
   
2. magnetrun formats show pigbrother
   (Complete field definitions in JSON format)
   
3. magnetrun formats edit pupitre
   (Edit JSON configuration files directly)
   
4. magnetrun formats reload
   (Reload after editing JSON files)

KEY CHANGES:
✅ JSON configuration files instead of complex Python code
✅ Direct editing of format definitions
✅ Auto-loading from configs directory
✅ Format classes have integrated field definitions
✅ Unified registry in magnetrun.formats module
✅ Simplified import structure

DEPRECATED COMMANDS:
❌ magnetrun field discover    → Use magnetrun formats list
❌ magnetrun field extend      → Edit JSON files directly
❌ magnetrun field merge       → Use magnetrun formats merge
❌ magnetrun field check       → Use magnetrun formats validate

NEW COMMANDS:
🆕 magnetrun formats list      → List available format definitions
🆕 magnetrun formats show      → Show format details
🆕 magnetrun formats edit      → Edit JSON config files
🆕 magnetrun formats configs   → Show configs directory
🆕 magnetrun formats reload    → Reload JSON definitions
🆕 magnetrun formats validate  → Validate format definitions
🆕 magnetrun formats import    → Import custom formats
🆕 magnetrun formats create    → Create format from data

JSON CONFIG STRUCTURE:
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
      "symbol": "B_res",
      "description": "Resistive magnet field"
    }
  ]
}

BACKWARD COMPATIBILITY:
- Data analysis commands work unchanged
- File processing commands work unchanged  
- Existing data files work without changes
- Field operations use the same API
    """
    click.echo(migration_text)


@cli.command()
def formats_help():
    """Show detailed help for JSON-based format management."""
    formats_help_text = """
JSON-Based Format Management System

JSON CONFIGURATION FILES:
The system uses JSON files located in magnetrun/formats/configs/:

📊 pupitre.json - Pupitre control system format
📊 bprofile.json - Magnetic field profile format  
📊 pigbrother.json - PigBrother TDMS acquisition format

AUTOMATIC FEATURES:
✅ Auto-loading from configs directory on startup
✅ Format classes have direct access to their definitions
✅ Unified registry manages all format components
✅ Easy to edit and customize without programming
✅ Version control friendly JSON configuration

COMMON WORKFLOWS:

1. VIEW FORMAT DEFINITIONS:
   magnetrun formats list --detailed
   magnetrun formats show pupitre

2. EDIT FORMAT CONFIGURATIONS:
   magnetrun formats edit pupitre
   # Opens pupitre.json in your editor
   magnetrun formats reload
   # Reloads the changes

3. CREATE CUSTOM FORMATS:
   magnetrun formats create my_format data.csv
   magnetrun formats import custom.json --install

4. VALIDATE CONFIGURATIONS:
   magnetrun formats validate pupitre
   magnetrun formats validate --all

5. EXPLORE FIELDS:
   magnetrun formats fields pupitre --field-type current
   magnetrun formats units pupitre Field

6. MANAGE CONFIGS:
   magnetrun formats configs
   # Shows config directory and files

INTEGRATION WITH DATA CLASSES:
- Each format class (PupitreData, etc.) loads its JSON definition
- Direct access: data.definition.get_field("Field")
- Automatic field information in all operations
- Self-contained format implementations

EDITING CONFIGURATIONS:
You can directly edit the JSON files to:
- Add new field definitions
- Modify existing field properties (units, symbols, descriptions)
- Update metadata
- Customize field types

SHARING CONFIGURATIONS:
- JSON files are easily shareable
- Version control tracks changes clearly
- Copy JSON files between installations
- Export/import functionality available
    """
    click.echo(formats_help_text)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
