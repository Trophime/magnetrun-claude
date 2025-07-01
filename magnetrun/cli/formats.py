"""CLI commands for format management."""

import json
import sys
from pathlib import Path
from typing import Optional, List
import click
from tabulate import tabulate
import pandas as pd

from ..formats import FormatRegistry, FormatDefinition
from ..core.fields import (
    FieldType,
    Field,
    validate_format_definition,
    create_field_summary,
    create_format_config_from_data
)


@click.group()
def formats():
    """Manage field format definitions."""
    pass


@formats.command()
@click.option('--detailed', '-d', is_flag=True, help='Show detailed field information')
@click.option('--format', '-f', 'output_format', type=click.Choice(['table', 'json']), 
              default='table', help='Output format')
def list(detailed: bool, output_format: str):
    """List available format definitions."""
    registry = FormatRegistry()
    format_names = registry.list_formats()
    
    if not format_names:
        click.echo("No format definitions found.")
        return
    
    if output_format == 'json':
        if detailed:
            output = {}
            for name in format_names:
                format_def = registry.get_format(name)
                output[name] = create_field_summary(format_def)
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo(json.dumps(format_names, indent=2))
        return
    
    # Table output
    if detailed:
        table_data = []
        for name in format_names:
            format_def = registry.get_format(name)
            summary = create_field_summary(format_def)
            
            # Count fields by type
            type_counts = []
            for field_type, info in summary["by_type"].items():
                type_counts.append(f"{field_type}: {info['count']}")
            
            table_data.append([
                name,
                summary["total_fields"],
                ", ".join(type_counts[:3]) + ("..." if len(type_counts) > 3 else ""),
                len(summary["units_used"]),
                format_def.metadata.get("description", "")
            ])
        
        headers = ["Format", "Fields", "Types (top 3)", "Units", "Description"]
        click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))
    else:
        for name in format_names:
            format_def = registry.get_format(name)
            click.echo(f"  {name:<15} - {format_def.metadata.get('description', 'No description')}")


@formats.command()
@click.argument('format_name')
@click.option('--output', '-o', type=click.Path(), help='Save to file instead of stdout')
@click.option('--format', '-f', 'output_format', type=click.Choice(['json', 'table', 'summary']), 
              default='table', help='Output format')
def show(format_name: str, output: Optional[str], output_format: str):
    """Show detailed information about a format definition."""
    registry = FormatRegistry()
    format_def = registry.get_format(format_name)
    
    if not format_def:
        click.echo(f"Format '{format_name}' not found.", err=True)
        click.echo("Available formats:")
        for name in registry.list_formats():
            click.echo(f"  {name}")
@formats.command()
@click.option('--verbose', '-v', is_flag=True, help='Show loading details')
def reload(verbose: bool):
    """Reload all format definitions from configs directory."""
    registry = FormatRegistry()
    old_count = len(registry.list_formats())
    
    if verbose:
        click.echo(f"Reloading formats from {registry.get_configs_directory()}")
    
    registry.reload_formats()
    new_count = len(registry.list_formats())
    
    click.echo(f"Reloaded {new_count} formats (was {old_count})")
    
    if verbose:
        for format_name in registry.list_formats():
            format_def = registry.get_format(format_name)
            click.echo(f"  {format_name}: {len(format_def.fields)} fields")


@formats.command()
def configs():
    """Show path to configs directory and list config files."""
    registry = FormatRegistry()
    configs_dir = registry.get_configs_directory()
    
    click.echo(f"Configs directory: {configs_dir}")
    click.echo(f"Directory exists: {configs_dir.exists()}")
    
    if configs_dir.exists():
        json_files = list(configs_dir.glob("*.json"))
        click.echo(f"\nJSON config files ({len(json_files)}):")
        for json_file in json_files:
            click.echo(f"  {json_file.name}")
            
        # Show any non-JSON files (might be user additions)
        other_files = [f for f in configs_dir.iterdir() if f.is_file() and f.suffix != '.json']
        if other_files:
            click.echo(f"\nOther files:")
            for other_file in other_files:
                click.echo(f"  {other_file.name}")


@formats.command()
@click.argument('format_name')
@click.option('--editor', '-e', help='Editor to use (default: system default)')
def edit(format_name: str, editor: Optional[str]):
    """Edit a format definition file."""
    import subprocess
    import os
    
    registry = FormatRegistry()
    configs_dir = registry.get_configs_directory()
    config_file = configs_dir / f"{format_name}.json"
    
    if not config_file.exists():
        click.echo(f"Config file {config_file} not found.")
        click.echo("Available formats:")
        for name in registry.list_formats():
            click.echo(f"  {name}")
        sys.exit(1)
    
    # Determine editor
    if not editor:
        editor = os.environ.get('EDITOR', 'nano' if os.name != 'nt' else 'notepad')
    
    try:
        subprocess.run([editor, str(config_file)], check=True)
        click.echo(f"Edited {config_file}")
        click.echo("Run 'magnetrun formats reload' to apply changes.")
    except subprocess.CalledProcessError:
        click.echo(f"Failed to open editor: {editor}", err=True)
    except FileNotFoundError:
        click.echo(f"Editor not found: {editor}", err=True)
    
    if output_format == 'json':
        output_data = format_def.to_dict()
        content = json.dumps(output_data, indent=2)
    elif output_format == 'summary':
        summary = create_field_summary(format_def)
        content = json.dumps(summary, indent=2)
    else:  # table
        content = _format_definition_to_table(format_def)
    
    if output:
        Path(output).write_text(content)
        click.echo(f"Format definition saved to {output}")
    else:
        click.echo(content)


@formats.command()
@click.argument('format_name')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
def export(format_name: str, output: Optional[str]):
    """Export a format definition to JSON file."""
    registry = FormatRegistry()
    format_def = registry.get_format(format_name)
    
    if not format_def:
        click.echo(f"Format '{format_name}' not found.", err=True)
        sys.exit(1)
    
    if not output:
        output = f"{format_name}_format.json"
    
    format_def.save_to_file(output)
    click.echo(f"Format '{format_name}' exported to {output}")


@formats.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--name', help='Override format name from file')
@click.option('--install', is_flag=True, help='Install to configs directory')
def import_format(filepath: str, name: Optional[str], install: bool):
    """Import a format definition from JSON file."""
    try:
        registry = FormatRegistry()
        format_def = FormatDefinition.load_from_file(filepath, registry.ureg)
        
        if name:
            format_def.format_name = name
        
        if install:
            # Copy to configs directory
            configs_dir = registry.get_configs_directory()
            configs_dir.mkdir(exist_ok=True)
            target_file = configs_dir / f"{format_def.format_name}.json"
            format_def.save_to_file(target_file)
            click.echo(f"Format '{format_def.format_name}' installed to {target_file}")
        else:
            registry.register_format(format_def)
            click.echo(f"Format '{format_def.format_name}' imported successfully (temporary).")
        
        # Show summary
        summary = create_field_summary(format_def)
        click.echo(f"  {summary['total_fields']} fields defined")
        for field_type, info in summary["by_type"].items():
            click.echo(f"  {field_type}: {info['count']} fields")
            
    except Exception as e:
        click.echo(f"Failed to import format: {e}", err=True)
        sys.exit(1)


@formats.command()
@click.argument('format_name')
def validate(format_name: str):
    """Validate a format definition for common issues."""
    registry = FormatRegistry()
    format_def = registry.get_format(format_name)
    
    if not format_def:
        click.echo(f"Format '{format_name}' not found.", err=True)
        sys.exit(1)
    
    validation = validate_format_definition(format_def)
    
    click.echo(f"Validation results for '{format_name}':")
    click.echo(f"  Status: {'✓ VALID' if validation['valid'] else '✗ INVALID'}")
    click.echo(f"  Total fields: {validation['total_fields']}")
    
    if validation['issues']:
        click.echo("\n❌ Issues found:")
        for issue in validation['issues']:
            click.echo(f"  - {issue}")
    
    if validation['warnings']:
        click.echo("\n⚠️  Warnings:")
        for warning in validation['warnings']:
            click.echo(f"  - {warning}")
    
    if validation['valid'] and not validation['warnings']:
        click.echo("\n✅ No issues found!")
    
    # Show field type distribution
    click.echo("\nField type distribution:")
    for field_type, count in validation['field_types'].items():
        if count > 0:
            click.echo(f"  {field_type}: {count}")


@formats.command()
@click.argument('format_name')
@click.option('--field-type', '-t', type=click.Choice([ft.value for ft in FieldType]), 
              help='Filter by field type')
@click.option('--search', '-s', help='Search in field names or descriptions')
@click.option('--output', '-o', type=click.Path(), help='Save to CSV file')
def fields(format_name: str, field_type: Optional[str], search: Optional[str], output: Optional[str]):
    """List fields in a format definition."""
    registry = FormatRegistry()
    format_def = registry.get_format(format_name)
    
    if not format_def:
        click.echo(f"Format '{format_name}' not found.", err=True)
        sys.exit(1)
    
    # Collect field data
    field_data = []
    for field in format_def.fields.values():
        # Apply filters
        if field_type and field.field_type.value != field_type:
            continue
        if search and search.lower() not in field.name.lower() and search.lower() not in field.description.lower():
            continue
        
        field_data.append({
            'name': field.name,
            'type': field.field_type.value,
            'unit': field.unit,
            'symbol': field.symbol,
            'description': field.description
        })
    
    if not field_data:
        click.echo("No fields match the criteria.")
        return
    
    if output:
        # Save to CSV
        df = pd.DataFrame(field_data)
        df.to_csv(output, index=False)
        click.echo(f"Field data saved to {output}")
    else:
        # Display as table
        headers = ['Name', 'Type', 'Unit', 'Symbol', 'Description']
        table_data = [[f['name'], f['type'], f['unit'], f['symbol'], f['description'][:50] + '...' if len(f['description']) > 50 else f['description']] for f in field_data]
        click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))


@formats.command()
@click.argument('format_name')
@click.argument('data_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file for new format')
@click.option('--description', help='Description for the new format')
def create(format_name: str, data_file: str, output: Optional[str], description: Optional[str]):
    """Create a new format definition from a data file."""
    try:
        # Try to read the data file to get column names
        file_path = Path(data_file)
        
        if file_path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path, nrows=0)  # Just read headers
            data_keys = df.columns.tolist()
        elif file_path.suffix.lower() == '.txt':
            # Try both comma and whitespace separated
            try:
                df = pd.read_csv(file_path, nrows=0)
                data_keys = df.columns.tolist()
            except:
                df = pd.read_csv(file_path, sep=r'\s+', nrows=0)
                data_keys = df.columns.tolist()
        else:
            click.echo(f"Unsupported file format: {file_path.suffix}", err=True)
            sys.exit(1)
        
        # Create format definition
        registry = FormatRegistry()
        format_def = create_format_config_from_data(data_keys, format_name, registry.ureg)
        
        if description:
            format_def.metadata['description'] = description
        format_def.metadata['created_from'] = str(file_path)
        format_def.metadata['file_extension'] = file_path.suffix
        
        # Save to file
        if not output:
            output = f"{format_name}_format.json"
        
        format_def.save_to_file(output)
        
        click.echo(f"Format '{format_name}' created with {len(data_keys)} fields.")
        click.echo(f"Saved to: {output}")
        click.echo("\n📝 Review and edit the generated format definition:")
        click.echo(f"   magnetrun formats show {format_name}")
        click.echo("   magnetrun formats validate " + format_name)
        
    except Exception as e:
        click.echo(f"Failed to create format: {e}", err=True)
        sys.exit(1)


@formats.command()
@click.argument('base_format')
@click.argument('overlay_format')
@click.argument('output_name')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
def merge(base_format: str, overlay_format: str, output_name: str, output: Optional[str]):
    """Merge two format definitions."""
    from ..core.fields.utils import merge_format_definitions
    
    registry = FormatRegistry()
    
    base_def = registry.get_format(base_format)
    if not base_def:
        click.echo(f"Base format '{base_format}' not found.", err=True)
        sys.exit(1)
    
    overlay_def = registry.get_format(overlay_format)
    if not overlay_def:
        click.echo(f"Overlay format '{overlay_format}' not found.", err=True)
        sys.exit(1)
    
    # Merge formats
    merged_def = merge_format_definitions(base_def, overlay_def)
    merged_def.format_name = output_name
    
    # Save merged format
    if not output:
        output = f"{output_name}_format.json"
    
    merged_def.save_to_file(output)
    
    click.echo(f"Merged '{base_format}' and '{overlay_format}' into '{output_name}'")
    click.echo(f"Saved to: {output}")
    
    # Show summary
    summary = create_field_summary(merged_def)
    click.echo(f"Result: {summary['total_fields']} total fields")


@formats.command()
@click.argument('format_name')
@click.argument('from_unit')
@click.argument('to_unit')
@click.argument('value', type=float)
def convert(format_name: str, from_unit: str, to_unit: str, value: float):
    """Convert values between units using format registry."""
    registry = FormatRegistry()
    
    try:
        converted_value = registry.convert_between_units(value, from_unit, to_unit)
        click.echo(f"{value} {from_unit} = {converted_value} {to_unit}")
    except Exception as e:
        click.echo(f"Conversion failed: {e}", err=True)
        sys.exit(1)


@formats.command()
@click.argument('format_name')
@click.argument('field_name')
def units(format_name: str, field_name: str):
    """Show compatible units for a field."""
    registry = FormatRegistry()
    format_def = registry.get_format(format_name)
    
    if not format_def:
        click.echo(f"Format '{format_name}' not found.", err=True)
        sys.exit(1)
    
    field = format_def.get_field(field_name)
    if not field:
        click.echo(f"Field '{field_name}' not found in format '{format_name}'.", err=True)
        available_fields = list(format_def.fields.keys())
        click.echo(f"Available fields: {', '.join(available_fields)}")
        sys.exit(1)
    
    compatible_units = format_def.get_compatible_units(field_name)
    
    click.echo(f"Field: {field.name}")
    click.echo(f"Current unit: {field.unit}")
    click.echo(f"Symbol: {field.symbol}")
    click.echo(f"Type: {field.field_type.value}")
    click.echo(f"\nCompatible units:")
    for unit in compatible_units:
        click.echo(f"  {unit}")


def _format_definition_to_table(format_def: FormatDefinition) -> str:
    """Convert format definition to a readable table format."""
    output = []
    
    # Header
    output.append(f"Format Definition: {format_def.format_name}")
    output.append("=" * (20 + len(format_def.format_name)))
    
    # Metadata
    if format_def.metadata:
        output.append("\nMetadata:")
        for key, value in format_def.metadata.items():
            output.append(f"  {key}: {value}")
    
    # Fields by type
    output.append(f"\nFields ({len(format_def.fields)} total):")
    
    for field_type in FieldType:
        fields_of_type = format_def.get_fields_by_type(field_type)
        if fields_of_type:
            output.append(f"\n{field_type.value.upper().replace('_', ' ')} ({len(fields_of_type)}):")
            
            table_data = []
            for field in fields_of_type:
                table_data.append([
                    field.name,
                    field.symbol,
                    field.unit,
                    field.description[:60] + '...' if len(field.description) > 60 else field.description
                ])
            
            headers = ['Name', 'Symbol', 'Unit', 'Description']
            output.append(tabulate(table_data, headers=headers, tablefmt="simple"))
    
    return "\n".join(output)


# Main CLI entry point
if __name__ == '__main__':
    formats()
        
