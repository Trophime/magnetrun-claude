# magnetrun/cli/field_commands.py
"""Field management CLI commands for MagnetRun - Updated for Simplified Field System."""

import click
import json
from pathlib import Path
from typing import List, Optional
import pandas as pd

from ..core.simplified_field_system import FormatRegistry, FormatDefinition, Field, FieldType
from ..core.magnet_data import MagnetData


@click.group(name='field')
def field_commands():
    """Field management commands for data validation and analysis.
    
    Manage field definitions, validate data consistency, and analyze field
    properties using the built-in comprehensive format definitions.
    
    Examples:
        magnetrun field formats --show-details
        magnetrun field check data.tdms --format pigbrother --strict
        magnetrun field info --format pupitre --show-fields
        magnetrun field convert data.tdms "Field" --from tesla --to gauss
    """
    pass


@click.command()
@click.option('--show-details', is_flag=True, help='Show detailed format information')
@click.option('--show-fields', is_flag=True, help='Show field counts for each format')
@click.option('--export-csv', type=click.Path(), help='Export format summary to CSV')
def formats(show_details, show_fields, export_csv):
    """List available format definitions and their characteristics.
    
    Shows built-in format definitions for LNCMI measurement systems.
    
    Examples:
        magnetrun field formats
        magnetrun field formats --show-details
        magnetrun field formats --show-fields --export-csv formats.csv
    """
    registry = FormatRegistry()
    available_formats = registry.list_formats()
    
    click.echo("📋 Available Format Definitions:")
    click.echo("=" * 50)
    
    format_data = []
    
    for format_name in available_formats:
        format_def = registry.get_format(format_name)
        if format_def:
            field_count = len(format_def.fields)
            field_types = set(f.field_type.value for f in format_def.fields.values())
            
            format_info = {
                'format': format_name,
                'fields_count': field_count,
                'field_types_count': len(field_types),
                'description': format_def.metadata.get('description', 'No description')
            }
            format_data.append(format_info)
            
            click.echo(f"\n🔧 {format_name.upper()}")
            click.echo(f"   Fields: {field_count}")
            click.echo(f"   Description: {format_info['description']}")
            
            if show_details:
                click.echo(f"   Field types: {len(field_types)} types")
                click.echo(f"   Metadata keys: {list(format_def.metadata.keys())}")
            
            if show_fields:
                type_counts = {}
                for field in format_def.fields.values():
                    field_type = field.field_type.value
                    type_counts[field_type] = type_counts.get(field_type, 0) + 1
                
                click.echo("   Field type distribution:")
                for field_type, count in sorted(type_counts.items()):
                    click.echo(f"     {field_type}: {count}")
    
    if export_csv and format_data:
        df = pd.DataFrame(format_data)
        df.to_csv(export_csv, index=False)
        click.echo(f"\n📊 Format summary exported to: {export_csv}")


@click.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--format', 'format_name', help='Override automatic format detection')
@click.option('--strict', is_flag=True, help='Strict validation mode (fail on warnings)')
@click.option('--show-coverage', is_flag=True, help='Show field coverage statistics')
@click.option('--show-issues', is_flag=True, help='Show detailed validation issues')
@click.option('--output-report', type=click.Path(), help='Save validation report to file')
@click.option('--report-format', type=click.Choice(['json', 'csv', 'text']), 
              default='text', help='Output format for validation report')
def check(files, format_name, strict, show_coverage, show_issues, output_report, report_format):
    """Check data files against field definitions.
    
    Validates file format, field presence, data quality, and coverage
    using comprehensive built-in field definitions.
    
    Examples:
        magnetrun field check *.tdms
        magnetrun field check data.txt --format pupitre --strict
        magnetrun field check experiment/*.csv --show-coverage
        magnetrun field check data.tdms --output-report validation.json --report-format json
    """
    registry = FormatRegistry()
    validation_results = []
    overall_status = "PASS"
    
    click.echo(f"🔍 Validating {len(files)} files...")
    
    with click.progressbar(files, label='Processing files') as file_bar:
        for file_path in file_bar:
            try:
                # Load data
                magnet_data = MagnetData.from_file(file_path)
                
                # Override format if specified
                if format_name:
                    if format_name not in registry.list_formats():
                        click.echo(f"❌ Unknown format: {format_name}", err=True)
                        continue
                    magnet_data._format_name = format_name
                    magnet_data._format_def = registry.get_format(format_name)
                
                # Validate
                validation_summary = magnet_data.get_field_validation_summary()
                file_result = {
                    'file': str(file_path),
                    'format': magnet_data.format_type,
                    'summary': validation_summary['summary'],
                    'field_results': validation_summary['field_results'] if show_issues else {}
                }
                
                # Determine status
                coverage = validation_summary['summary']['coverage_percent']
                quality = validation_summary['summary']['quality_percent']
                
                if coverage < 50:
                    file_result['status'] = 'ERROR'
                    overall_status = 'ERROR'
                elif quality < 80 or coverage < 80:
                    file_result['status'] = 'WARNING'
                    if overall_status != 'ERROR':
                        overall_status = 'WARNING'
                else:
                    file_result['status'] = 'PASS'
                
                validation_results.append(file_result)
                
            except Exception as e:
                error_result = {
                    'file': str(file_path),
                    'status': 'ERROR',
                    'error': str(e),
                    'summary': {}
                }
                validation_results.append(error_result)
                overall_status = 'ERROR'
    
    # Display results
    _display_validation_summary(validation_results, overall_status, show_coverage, show_issues)
    
    # Save report if requested
    if output_report:
        _save_validation_report(validation_results, output_report, report_format)
        click.echo(f"📄 Report saved: {output_report}")
    
    # Exit with appropriate code
    if overall_status == "ERROR" or (strict and overall_status == "WARNING"):
        raise click.ClickException("Validation failed")


@click.command()
@click.option('--format', 'format_name', type=click.Choice(['pupitre', 'pigbrother', 'bprofile']),
              help='Show info for specific format')
@click.option('--show-fields', is_flag=True, help='Show detailed field information')
@click.option('--show-units', is_flag=True, help='Show unit information')
@click.option('--show-types', is_flag=True, help='Show field type distribution')
@click.option('--field-name', help='Show detailed info for specific field')
@click.option('--export-csv', type=click.Path(), help='Export field list to CSV')
def info(format_name, show_fields, show_units, show_types, field_name, export_csv):
    """Show information about format definitions and fields.
    
    Examples:
        magnetrun field info --format pupitre
        magnetrun field info --format pigbrother --show-fields
        magnetrun field info --field-name "Field" --format pupitre
        magnetrun field info --show-types --export-csv field_types.csv
    """
    registry = FormatRegistry()
    
    if format_name:
        # Show specific format info
        format_def = registry.get_format(format_name)
        if not format_def:
            click.echo(f"❌ Format '{format_name}' not found", err=True)
            return
        
        _display_format_info(format_def, show_fields, show_units, show_types, field_name)
    else:
        # Show overview of all formats
        click.echo("📋 Format Definitions Overview:")
        click.echo("=" * 50)
        
        for fmt_name in registry.list_formats():
            fmt_def = registry.get_format(fmt_name)
            if fmt_def:
                click.echo(f"\n{fmt_name.upper()}: {len(fmt_def.fields)} fields")
                if show_types:
                    type_counts = {}
                    for field in fmt_def.fields.values():
                        field_type = field.field_type.value
                        type_counts[field_type] = type_counts.get(field_type, 0) + 1
                    for field_type, count in sorted(type_counts.items()):
                        click.echo(f"  {field_type}: {count}")
    
    if export_csv:
        _export_fields_to_csv(registry, format_name, export_csv)
        click.echo(f"📊 Field information exported to: {export_csv}")


@click.command()
@click.argument('data_file', type=click.Path(exists=True))
@click.argument('field_name')
@click.option('--from-unit', required=True, help='Source unit')
@click.option('--to-unit', required=True, help='Target unit')
@click.option('--show-values', is_flag=True, help='Show sample converted values')
@click.option('--save-converted', type=click.Path(), help='Save converted data to file')
def convert(data_file, field_name, from_unit, to_unit, show_values, save_converted):
    """Convert field values between units.
    
    Examples:
        magnetrun field convert data.tdms "Field" --from tesla --to gauss
        magnetrun field convert data.txt "Current" --from ampere --to milliampere --show-values
        magnetrun field convert data.tdms "Field" --from tesla --to gauss --save-converted converted.csv
    """
    try:
        magnet_data = MagnetData.from_file(data_file)
        format_def = magnet_data.field_registry
        
        if field_name not in magnet_data.keys:
            click.echo(f"❌ Field '{field_name}' not found in data", err=True)
            return
        
        field = format_def.get_field(field_name)
        if not field:
            click.echo(f"❌ No field definition found for '{field_name}'", err=True)
            return
        
        # Check unit compatibility
        if not field.is_compatible_unit(to_unit, format_def.ureg):
            click.echo(f"⚠️  Warning: '{to_unit}' may not be compatible with field type '{field.field_type.value}'")
        
        # Get conversion factor
        conversion_factor = field.get_conversion_factor(to_unit, format_def.ureg)
        click.echo(f"🔄 Conversion: {from_unit} → {to_unit}")
        click.echo(f"   Factor: {conversion_factor}")
        
        if show_values:
            data = magnet_data.get_data([field_name])
            original_values = data[field_name].head(5)
            converted_values = magnet_data.convert_field_values(field_name, original_values, to_unit)
            
            click.echo("\n📊 Sample Values:")
            for orig, conv in zip(original_values, converted_values):
                click.echo(f"   {orig:10.3f} {from_unit} → {conv:10.3f} {to_unit}")
        
        if save_converted:
            data = magnet_data.get_data()
            data[f"{field_name}_{to_unit}"] = magnet_data.convert_field_values(
                field_name, data[field_name], to_unit
            )
            data.to_csv(save_converted, index=False)
            click.echo(f"💾 Converted data saved to: {save_converted}")
            
    except Exception as e:
        click.echo(f"❌ Conversion failed: {e}", err=True)


@click.command()
@click.option('--formats', help='Comma-separated list of formats to compare')
@click.option('--field-types', help='Show only specific field types (comma-separated)')
@click.option('--show-units', is_flag=True, help='Include unit information in comparison')
@click.option('--export-csv', type=click.Path(), help='Export comparison to CSV')
def compare(formats, field_types, show_units, export_csv):
    """Compare field definitions across formats.
    
    Examples:
        magnetrun field compare --formats pupitre,pigbrother
        magnetrun field compare --field-types magnetic_field,current --show-units
        magnetrun field compare --formats all --export-csv comparison.csv
    """
    registry = FormatRegistry()
    
    if formats == 'all':
        format_list = registry.list_formats()
    elif formats:
        format_list = [f.strip() for f in formats.split(',')]
    else:
        format_list = registry.list_formats()
    
    # Validate formats
    available_formats = registry.list_formats()
    invalid_formats = [f for f in format_list if f not in available_formats]
    if invalid_formats:
        click.echo(f"❌ Invalid formats: {invalid_formats}", err=True)
        return
    
    click.echo(f"📊 Comparing formats: {', '.join(format_list)}")
    click.echo("=" * 60)
    
    comparison_data = []
    all_field_names = set()
    
    # Collect all field names
    for format_name in format_list:
        format_def = registry.get_format(format_name)
        if format_def:
            all_field_names.update(format_def.fields.keys())
    
    # Filter by field types if specified
    if field_types:
        type_list = [t.strip() for t in field_types.split(',')]
        filtered_field_names = set()
        for format_name in format_list:
            format_def = registry.get_format(format_name)
            if format_def:
                for field_name, field in format_def.fields.items():
                    if field.field_type.value in type_list:
                        filtered_field_names.add(field_name)
        all_field_names = filtered_field_names
    
    # Create comparison
    for field_name in sorted(all_field_names):
        row_data = {'field_name': field_name}
        
        click.echo(f"\n🔧 {field_name}")
        for format_name in format_list:
            format_def = registry.get_format(format_name)
            field = format_def.get_field(field_name) if format_def else None
            
            if field:
                symbol = field.symbol
                field_type = field.field_type.value
                unit = field.unit if show_units else ""
                status = "✓"
                row_data[f'{format_name}_present'] = True
                row_data[f'{format_name}_symbol'] = symbol
                row_data[f'{format_name}_type'] = field_type
                if show_units:
                    row_data[f'{format_name}_unit'] = unit
                
                info = f"{status} {symbol} ({field_type})"
                if show_units and unit:
                    info += f" [{unit}]"
            else:
                status = "✗"
                info = f"{status} Not defined"
                row_data[f'{format_name}_present'] = False
            
            click.echo(f"   {format_name:12}: {info}")
        
        comparison_data.append(row_data)
    
    if export_csv and comparison_data:
        df = pd.DataFrame(comparison_data)
        df.to_csv(export_csv, index=False)
        click.echo(f"\n📊 Comparison exported to: {export_csv}")


# Helper functions
def _display_validation_summary(results: List, overall_status: str, show_coverage: bool, show_issues: bool):
    """Display validation summary."""
    total_files = len(results)
    error_files = sum(1 for r in results if r.get('status') == 'ERROR')
    warning_files = sum(1 for r in results if r.get('status') == 'WARNING')
    pass_files = total_files - error_files - warning_files
    
    click.echo(f"\n{'='*60}")
    click.echo("📊 Validation Summary:")
    click.echo(f"  Overall Status: {overall_status}")
    click.echo(f"  Files processed: {total_files}")
    click.echo(f"  ✅ Passed: {pass_files}")
    click.echo(f"  ⚠️  Warnings: {warning_files}")
    click.echo(f"  ❌ Errors: {error_files}")
    
    if show_coverage:
        click.echo("\n📈 Field Coverage by File:")
        for result in results:
            if 'summary' in result and result['summary']:
                coverage = result['summary'].get('coverage_percent', 0)
                quality = result['summary'].get('quality_percent', 0)
                status_icon = "✅" if result.get('status') == 'PASS' else ("⚠️" if result.get('status') == 'WARNING' else "❌")
                click.echo(f"  {status_icon} {Path(result['file']).name}: {coverage:.1f}% coverage, {quality:.1f}% quality")
    
    if show_issues:
        click.echo("\n🔍 Detailed Issues:")
        for result in results:
            if result.get('status') in ['ERROR', 'WARNING'] and 'field_results' in result:
                click.echo(f"\n  📁 {Path(result['file']).name}:")
                for field_name, field_result in result['field_results'].items():
                    if field_result.get('status') in ['error', 'invalid', 'no_field_definition']:
                        status = field_result.get('status', 'unknown')
                        click.echo(f"    ❌ {field_name}: {status}")


def _save_validation_report(results: List, output_path: Path, format: str):
    """Save validation report to file."""
    output_path = Path(output_path)
    
    if format == 'json':
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    elif format == 'csv':
        # Flatten results for CSV
        flattened = []
        for result in results:
            summary = result.get('summary', {})
            flat_result = {
                'file': result['file'],
                'format': result.get('format', ''),
                'status': result.get('status', ''),
                'total_fields': summary.get('total_fields', 0),
                'valid_fields': summary.get('valid_fields', 0),
                'invalid_fields': summary.get('invalid_fields', 0),
                'coverage_percent': summary.get('coverage_percent', 0),
                'quality_percent': summary.get('quality_percent', 0)
            }
            flattened.append(flat_result)
        
        df = pd.DataFrame(flattened)
        df.to_csv(output_path, index=False)
    else:  # text format
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("FIELD VALIDATION REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            for result in results:
                f.write(f"File: {result['file']}\n")
                f.write(f"Status: {result.get('status', 'unknown')}\n")
                if 'summary' in result:
                    summary = result['summary']
                    f.write(f"Coverage: {summary.get('coverage_percent', 0):.1f}%\n")
                    f.write(f"Quality: {summary.get('quality_percent', 0):.1f}%\n")
                f.write("\n")


def _display_format_info(format_def: FormatDefinition, show_fields: bool, show_units: bool, 
                        show_types: bool, field_name: str):
    """Display detailed format information."""
    click.echo(f"📋 Format: {format_def.format_name.upper()}")
    click.echo("=" * 50)
    
    click.echo(f"Total fields: {len(format_def.fields)}")
    click.echo(f"Description: {format_def.metadata.get('description', 'No description')}")
    
    if field_name:
        # Show specific field info
        field = format_def.get_field(field_name)
        if field:
            click.echo(f"\n🔧 Field: {field_name}")
            click.echo(f"   Symbol: {field.symbol}")
            click.echo(f"   Type: {field.field_type.value}")
            click.echo(f"   Unit: {field.unit}")
            click.echo(f"   Description: {field.description}")
            
            if show_units:
                compatible_units = format_def.get_compatible_units(field_name)
                click.echo(f"   Compatible units: {', '.join(compatible_units)}")
        else:
            click.echo(f"❌ Field '{field_name}' not found in format '{format_def.format_name}'")
    
    if show_types:
        type_counts = {}
        for field in format_def.fields.values():
            field_type = field.field_type.value
            type_counts[field_type] = type_counts.get(field_type, 0) + 1
        
        click.echo("\n🏷️  Field Type Distribution:")
        for field_type, count in sorted(type_counts.items()):
            click.echo(f"   {field_type}: {count}")
    
    if show_fields:
        click.echo("\n🔧 Field Details:")
        for field_name in sorted(format_def.fields.keys()):
            field = format_def.fields[field_name]
            info = f"   {field_name}: {field.symbol} ({field.field_type.value})"
            if show_units:
                info += f" [{field.unit}]"
            click.echo(info)


def _export_fields_to_csv(registry: FormatRegistry, format_name: str, output_file: Path):
    """Export field definitions to CSV."""    
    import csv
    
    field_data = []
    
    if format_name:
        # Export specific format
        format_def = registry.get_format(format_name)
        if format_def:
            for field in format_def.fields.values():
                field_data.append({
                    'format': format_name,
                    'name': field.name,
                    'symbol': field.symbol,
                    'field_type': field.field_type.value,
                    'unit': field.unit,
                    'description': field.description
                })
    else:
        # Export all formats
        for fmt_name in registry.list_formats():
            format_def = registry.get_format(fmt_name)
            if format_def:
                for field in format_def.fields.values():
                    field_data.append({
                        'format': fmt_name,
                        'name': field.name,
                        'symbol': field.symbol,
                        'field_type': field.field_type.value,
                        'unit': field.unit,
                        'description': field.description
                    })
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        if field_data:
            fieldnames = field_data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(field_data)


# Register all commands
field_commands.add_command(formats)
field_commands.add_command(check)
field_commands.add_command(info)
field_commands.add_command(convert)
field_commands.add_command(compare)
