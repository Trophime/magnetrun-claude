"""ETL (Extract, Transform, Load) commands for format-specific data operations - Updated for JSON-based Field System."""

import click
from pathlib import Path
import pandas as pd
from .utils import load_magnet_data, add_time_column_if_needed, handle_error
from ..io.writers import DataWriter

# CORRECTED: Import from new locations
from ..formats import FormatRegistry, FormatDefinition
from ..core.fields import Field, FieldType


@click.group(name='etl')
def etl_commands():
    """ETL (Extract, Transform, Load) operations for data processing."""
    pass

@etl_commands.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--housing', default='M9', help='Housing type')
@click.option('--site', default='', help='Site identifier')
@click.option('--output-format', default='csv', type=click.Choice(['csv', 'json', 'parquet', 'excel']), 
              help='Output format for transformed data')
@click.option('--output-dir', type=click.Path(), help='Output directory for processed files')
@click.option('--normalize-units', is_flag=True, help='Normalize units to standard SI units')
@click.option('--add-metadata', is_flag=True, help='Add metadata columns to output')
@click.option('--validate', is_flag=True, help='Validate data quality during transformation')
@click.option('--add-field-info', is_flag=True, help='Add field information (symbols, units) to output')
@click.pass_context
def transform(ctx, files, housing, site, output_format, output_dir, normalize_units, add_metadata, validate, add_field_info):
    """Transform data using format-specific ETL operations with field management."""
    debug = ctx.obj.get('DEBUG', False)
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
    
    for file_path in files:
        click.echo(f"Processing ETL for: {file_path}")
        
        try:
            magnet_data, magnet_run = load_magnet_data(file_path, housing, site)
            add_time_column_if_needed(magnet_data, debug)
            
            # Get the format-specific ETL processor
            etl_processor = _get_etl_processor(magnet_data.format_type)
            
            # Perform format-specific transformations
            transformed_data = etl_processor.transform(
                magnet_data, 
                normalize_units=normalize_units,
                add_metadata=add_metadata,
                add_field_info=add_field_info,
                validate=validate,
                debug=debug
            )
            
            # Save transformed data
            _save_transformed_data(
                transformed_data, file_path, output_format, output_dir, 
                magnet_data.format_type, debug
            )
            
        except Exception as e:
            handle_error(e, debug, file_path)

@etl_commands.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--housing', default='M9', help='Housing type')
@click.option('--target-format', required=True, 
              type=click.Choice(['pupitre', 'pigbrother', 'bprofile']),
              help='Target format for migration')
@click.option('--output-dir', type=click.Path(), help='Output directory for migrated files')
@click.option('--preserve-metadata', is_flag=True, help='Preserve original metadata')
@click.option('--map-fields', is_flag=True, help='Map field names to target format conventions')
@click.pass_context
def migrate(ctx, files, housing, target_format, output_dir, preserve_metadata, map_fields):
    """Migrate data between different formats with field mapping."""
    debug = ctx.obj.get('DEBUG', False)
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
    
    for file_path in files:
        click.echo(f"Migrating: {file_path} -> {target_format}")
        
        try:
            magnet_data, magnet_run = load_magnet_data(file_path, housing)
            
            if magnet_data.format_type == target_format:
                click.echo(f"  Skipping: already in {target_format} format")
                continue
            
            # Perform migration
            migrated_data = _migrate_format(
                magnet_data, target_format, preserve_metadata, map_fields, debug
            )
            
            # Save migrated data
            _save_migrated_data(
                migrated_data, file_path, target_format, output_dir, debug
            )
            
        except Exception as e:
            handle_error(e, debug, file_path)

@etl_commands.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--housing', default='M9', help='Housing type')
@click.option('--check-units', is_flag=True, help='Validate unit consistency')
@click.option('--check-ranges', is_flag=True, help='Check data ranges for anomalies')
@click.option('--check-missing', is_flag=True, help='Check for missing values')
@click.option('--check-duplicates', is_flag=True, help='Check for duplicate records')
@click.option('--check-field-definitions', is_flag=True, help='Check field definition coverage')
@click.option('--export-report', is_flag=True, help='Export validation report')
@click.pass_context
def validate(ctx, files, housing, check_units, check_ranges, check_missing, check_duplicates, check_field_definitions, export_report):
    """Validate data quality and consistency with field definitions."""
    debug = ctx.obj.get('DEBUG', False)
    
    all_results = []
    
    for file_path in files:
        click.echo(f"Validating: {file_path}")
        
        try:
            magnet_data, magnet_run = load_magnet_data(file_path, housing)
            
            # Get format-specific validator
            validator = _get_validator(magnet_data.format_type)
            
            # Run validation checks
            validation_results = validator.validate(
                magnet_data,
                check_units=check_units,
                check_ranges=check_ranges,
                check_missing=check_missing,
                check_duplicates=check_duplicates,
                check_field_definitions=check_field_definitions,
                debug=debug
            )
            
            validation_results['file'] = Path(file_path).name
            all_results.append(validation_results)
            
            # Display results
            _display_validation_results(validation_results, file_path)
            
        except Exception as e:
            handle_error(e, debug, file_path)
    
    if export_report and all_results:
        _export_validation_report(all_results)

@etl_commands.command()
@click.argument('input_files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--housing', default='M9', help='Housing type')
@click.option('--output-file', required=True, type=click.Path(), help='Output file for merged data')
@click.option('--merge-strategy', default='concat', 
              type=click.Choice(['concat', 'join', 'align']),
              help='Strategy for merging multiple files')
@click.option('--time-align', is_flag=True, help='Align data by time columns')
@click.option('--preserve-field-info', is_flag=True, help='Preserve field information in merged data')
@click.pass_context
def merge(ctx, input_files, housing, output_file, merge_strategy, time_align, preserve_field_info):
    """Merge multiple data files into a single dataset with field management."""
    debug = ctx.obj.get('DEBUG', False)
    
    click.echo(f"Merging {len(input_files)} files using {merge_strategy} strategy")
    
    try:
        datasets = []
        for file_path in input_files:
            click.echo(f"  Loading: {file_path}")
            magnet_data, _ = load_magnet_data(file_path, housing)
            add_time_column_if_needed(magnet_data, debug)
            datasets.append(magnet_data)
        
        # Perform merge based on strategy
        merged_data = _merge_datasets(datasets, merge_strategy, time_align, preserve_field_info, debug)
        
        # Save merged data
        _save_merged_data(merged_data, output_file, debug)
        
        click.echo(f"Successfully merged data saved to: {output_file}")
        
    except Exception as e:
        handle_error(e, debug)

# ETL Processor Classes
class BaseETLProcessor:
    """Base class for format-specific ETL processors with field management."""
    
    def transform(self, magnet_data, normalize_units=False, add_metadata=False, add_field_info=False, validate=False, debug=False):
        """Transform data using format-specific operations with field management."""
        data = magnet_data.get_data()
        
        if add_field_info:
            data = self._add_field_information(magnet_data, data)
        
        if normalize_units:
            data = self._normalize_units(magnet_data, data)
        
        if add_metadata:
            data = self._add_metadata(magnet_data, data)
        
        if validate:
            self._validate_data(magnet_data, data, debug)
        
        return data
    
    def _add_field_information(self, magnet_data, data):
        """Add field information as metadata columns."""
        field_info_data = []
        
        for column in data.columns:
            field_info = magnet_data.get_field_info(column)
            symbol, unit_obj, unit_string = field_info
            
            field_info_data.append({
                'column': column,
                'symbol': symbol,
                'unit': unit_string,
                'label': magnet_data.get_field_label(column)
            })
        
        # Add field info as a separate sheet/table (for Excel) or as comments (for CSV)
        # For now, we'll add summary columns
        if field_info_data:
            # Create field summary
            field_summary = pd.DataFrame(field_info_data)
            # Store as attribute for later use
            data._field_summary = field_summary
        
        return data
    
    def _normalize_units(self, magnet_data, data):
        """Normalize units to standard SI using field definitions."""
        format_def = magnet_data.field_registry
        
        for column in data.columns:
            field = format_def.get_field(column)
            if field:
                # Get SI-compatible unit for field type
                si_units = {
                    FieldType.MAGNETIC_FIELD: "tesla",
                    FieldType.CURRENT: "ampere",
                    FieldType.VOLTAGE: "volt",
                    FieldType.TEMPERATURE: "kelvin",
                    FieldType.PRESSURE: "pascal",
                    FieldType.POWER: "watt",
                    FieldType.TIME: "second"
                }
                
                si_unit = si_units.get(field.field_type, field.unit)
                current_unit = field.unit
                
                if current_unit != si_unit:
                    try:
                        # Convert values to SI
                        converted_values = magnet_data.convert_field_values(column, data[column], si_unit)
                        data[f"{column}_SI"] = converted_values
                        # Optionally replace original column
                        # data[column] = converted_values
                    except Exception as e:
                        if debug:
                            click.echo(f"    Warning: Could not convert {column} to SI: {e}")
        
        return data
    
    def _add_metadata(self, magnet_data, data):
        """Add metadata columns with field information."""
        data['source_file'] = magnet_data.filename
        data['format_type'] = magnet_data.format_type
        data['field_coverage_percent'] = magnet_data._get_field_coverage()
        return data
    
    def _validate_data(self, magnet_data, data, debug):
        """Validate data quality with field definitions."""
        validation_summary = magnet_data.get_field_validation_summary()
        
        if debug:
            click.echo(f"    Data shape: {data.shape}")
            click.echo(f"    Field coverage: {validation_summary['summary']['coverage_percent']:.1f}%")
            click.echo(f"    Data quality: {validation_summary['summary']['quality_percent']:.1f}%")

class PupitreETLProcessor(BaseETLProcessor):
    """ETL processor for Pupitre format data with field awareness."""
    
    def transform(self, magnet_data, normalize_units=False, add_metadata=False, add_field_info=False, validate=False, debug=False):
        click.echo("  Applying Pupitre-specific transformations...")
        
        data = super().transform(magnet_data, normalize_units, add_metadata, add_field_info, validate, debug)
        
        # Pupitre-specific transformations
        data = self._clean_pupitre_data(data)
        data = self._standardize_pupitre_fields(magnet_data, data)
        
        if debug:
            click.echo(f"    Pupitre transformation complete. Shape: {data.shape}")
        
        return data
    
    def _clean_pupitre_data(self, data):
        """Clean Pupitre-specific data issues."""
        # Remove any trailing whitespace from string columns
        string_cols = data.select_dtypes(include=['object']).columns
        for col in string_cols:
            data[col] = data[col].astype(str).str.strip()
        
        return data
    
    def _standardize_pupitre_fields(self, magnet_data, data):
        """Standardize field names and units for Pupitre data."""
        format_def = magnet_data.field_registry
        
        # Apply field-based standardization
        standardized_columns = {}
        for col in data.columns:
            field = format_def.get_field(col)
            if field:
                # Use field symbol as standardized name
                std_name = field.symbol
                if std_name != col and std_name not in data.columns:
                    standardized_columns[col] = std_name
        
        if standardized_columns:
            data = data.rename(columns=standardized_columns)
        
        return data

class PigbrotherETLProcessor(BaseETLProcessor):
    """ETL processor for PigBrother TDMS format data with field management."""
    
    def transform(self, magnet_data, normalize_units=False, add_metadata=False, add_field_info=False, validate=False, debug=False):
        click.echo("  Applying PigBrother TDMS-specific transformations...")
        
        # For TDMS, we need to handle multiple groups
        transformed_groups = {}
        
        # Get all groups from the data handler
        if hasattr(magnet_data._data_handler, 'data'):
            for group_name, group_data in magnet_data._data_handler.data.items():
                click.echo(f"    Processing group: {group_name}")
                
                # Create a temporary MagnetData-like object for the group
                group_columns = [f"{group_name}/{col}" for col in group_data.columns]
                
                # Transform each group separately
                transformed_data = group_data.copy()
                
                if add_field_info:
                    transformed_data = self._add_tdms_field_info(magnet_data, transformed_data, group_name)
                
                if normalize_units:
                    transformed_data = self._normalize_tdms_units(magnet_data, transformed_data, group_name)
                
                if add_metadata:
                    transformed_data = self._add_tdms_metadata(magnet_data, transformed_data, group_name)
                
                transformed_groups[group_name] = transformed_data
        
        if debug:
            click.echo(f"    PigBrother transformation complete. Groups: {list(transformed_groups.keys())}")
        
        return transformed_groups
    
    def _add_tdms_field_info(self, magnet_data, data, group_name):
        """Add TDMS field information."""
        format_def = magnet_data.field_registry
        
        # Add field info for each column
        for col in data.columns:
            full_key = f"{group_name}/{col}"
            field = format_def.get_field(full_key)
            if field:
                # Add field metadata as attributes (for HDF5/NetCDF) or comments
                if hasattr(data[col], 'attrs'):
                    data[col].attrs = {
                        'symbol': field.symbol,
                        'unit': field.unit,
                        'field_type': field.field_type.value,
                        'description': field.description
                    }
        
        return data
    
    def _normalize_tdms_units(self, magnet_data, data, group_name):
        """Normalize TDMS units using field definitions."""
        format_def = magnet_data.field_registry
        
        for col in data.columns:
            full_key = f"{group_name}/{col}"
            field = format_def.get_field(full_key)
            if field:
                # Get SI unit for field type
                si_units = {
                    FieldType.MAGNETIC_FIELD: "tesla",
                    FieldType.CURRENT: "ampere",
                    FieldType.VOLTAGE: "volt",
                    FieldType.POWER: "watt"
                }
                si_unit = si_units.get(field.field_type, field.unit)
                
                if field.unit != si_unit:
                    try:
                        converted_values = magnet_data.convert_field_values(full_key, data[col], si_unit)
                        data[f"{col}_SI"] = converted_values
                    except Exception:
                        pass  # Skip conversion errors
        
        return data
    
    def _add_tdms_metadata(self, magnet_data, data, group_name):
        """Add TDMS-specific metadata with field information."""
        data['group_name'] = group_name
        data['source_file'] = magnet_data.filename
        data['format_type'] = magnet_data.format_type
        
        # Add field count for this group
        format_def = magnet_data.field_registry
        group_field_count = sum(1 for key in format_def.fields.keys() if key.startswith(f"{group_name}/"))
        data['group_field_count'] = group_field_count
        
        return data

class BprofileETLProcessor(BaseETLProcessor):
    """ETL processor for Bprofile format data with field management."""
    
    def transform(self, magnet_data, normalize_units=False, add_metadata=False, add_field_info=False, validate=False, debug=False):
        click.echo("  Applying Bprofile-specific transformations...")
        
        data = super().transform(magnet_data, normalize_units, add_metadata, add_field_info, validate, debug)
        
        # Bprofile-specific transformations
        data = self._process_profile_data(data)
        data = self._calculate_profile_metrics(magnet_data, data)
        
        if debug:
            click.echo(f"    Bprofile transformation complete. Shape: {data.shape}")
        
        return data
    
    def _process_profile_data(self, data):
        """Process profile-specific data."""
        # Ensure position is properly ordered
        if 'Position (mm)' in data.columns:
            data = data.sort_values('Position (mm)')
        
        return data
    
    def _calculate_profile_metrics(self, magnet_data, data):
        """Calculate profile-specific metrics using field information."""
        format_def = magnet_data.field_registry
        
        # Find profile columns using field definitions
        profile_cols = []
        for col in data.columns:
            field = format_def.get_field(col)
            if field and field.field_type == field.field_type.PERCENTAGE and 'profile' in field.description.lower():
                profile_cols.append(col)
        
        # Calculate statistics for profile columns
        for col in profile_cols:
            data[f'{col}_mean'] = data[col].mean()
            data[f'{col}_std'] = data[col].std()
            data[f'{col}_range'] = data[col].max() - data[col].min()
        
        return data

# Validator Classes
class BaseValidator:
    """Base validator for data quality checks with field management."""
    
    def validate(self, magnet_data, check_units=False, check_ranges=False, 
                check_missing=False, check_duplicates=False, check_field_definitions=False, debug=False):
        results = {
            'format': magnet_data.format_type,
            'issues': [],
            'warnings': [],
            'info': []
        }
        
        data = magnet_data.get_data()
        
        if check_field_definitions:
            self._check_field_definitions(magnet_data, results)
        
        if check_missing:
            self._check_missing_values(data, results)
        
        if check_duplicates:
            self._check_duplicates(data, results)
        
        if check_ranges:
            self._check_data_ranges(magnet_data, data, results)
        
        if check_units:
            self._check_units(magnet_data, results)
        
        return results
    
    def _check_field_definitions(self, magnet_data, results):
        """Check field definition coverage."""
        coverage = magnet_data._get_field_coverage()
        if coverage < 50:
            results['issues'].append(f"Low field definition coverage: {coverage:.1f}%")
        elif coverage < 80:
            results['warnings'].append(f"Moderate field definition coverage: {coverage:.1f}%")
        else:
            results['info'].append(f"Good field definition coverage: {coverage:.1f}%")
    
    def _check_missing_values(self, data, results):
        missing = data.isnull().sum()
        missing_cols = missing[missing > 0]
        
        if len(missing_cols) > 0:
            results['warnings'].append(f"Missing values found in columns: {missing_cols.to_dict()}")
        else:
            results['info'].append("No missing values found")
    
    def _check_duplicates(self, data, results):
        duplicates = data.duplicated().sum()
        if duplicates > 0:
            results['warnings'].append(f"Found {duplicates} duplicate rows")
        else:
            results['info'].append("No duplicate rows found")
    
    def _check_data_ranges(self, magnet_data, data, results):
        """Check data ranges using field definitions."""
        format_def = magnet_data.field_registry
        
        for col in data.columns:
            field = format_def.get_field(col)
            if field:
                # Check for infinite values
                if pd.api.types.is_numeric_dtype(data[col]) and data[col].isinf().any():
                    results['issues'].append(f"Infinite values found in {col}")
                
                # Check field-specific constraints
                if field.field_type.value in ['current', 'voltage', 'power', 'magnetic_field']:
                    # These can have negative values in some contexts
                    negative_count = (data[col] < 0).sum() if pd.api.types.is_numeric_dtype(data[col]) else 0
                    if negative_count > 0:
                        results['warnings'].append(f"Found {negative_count} negative values in {col} ({field.field_type.value})")
    
    def _check_units(self, magnet_data, results):
        """Check unit consistency using field definitions."""
        format_def = magnet_data.field_registry
        unit_issues = []
        
        for key in magnet_data.keys:
            field = format_def.get_field(key)
            if field:
                # Validate unit definition
                validation = format_def.validate_field_unit(key)
                if not validation.get('valid', False):
                    unit_issues.append(f"{key}: {validation.get('error', 'Invalid unit')}")
            else:
                unit_issues.append(f"{key}: No field definition found")
        
        if unit_issues:
            results['warnings'].extend(unit_issues)
        else:
            results['info'].append("All field units are properly defined")

# Helper Functions
def _get_etl_processor(format_type):
    """Get the appropriate ETL processor for the format."""
    processors = {
        'pupitre': PupitreETLProcessor(),
        'pigbrother': PigbrotherETLProcessor(),
        'bprofile': BprofileETLProcessor()
    }
    return processors.get(format_type, BaseETLProcessor())

def _get_validator(format_type):
    """Get the appropriate validator for the format."""
    # For now, use base validator for all formats
    return BaseValidator()

def _save_transformed_data(data, file_path, output_format, output_dir, format_type, debug):
    """Save transformed data to specified format."""
    base_name = Path(file_path).stem
    
    if output_dir:
        output_path = output_dir / f"{base_name}_transformed"
    else:
        output_path = Path(file_path).parent / f"{base_name}_transformed"
    
    if isinstance(data, dict):
        # Handle multiple groups (TDMS)
        for group_name, group_data in data.items():
            group_output_path = Path(str(output_path) + f"_{group_name}")
            _save_data_file(group_data, group_output_path, output_format)
    else:
        _save_data_file(data, output_path, output_format)

def _save_data_file(data, output_path, output_format):
    """Save a single DataFrame to file."""
    if output_format == 'csv':
        output_file = output_path.with_suffix('.csv')
        data.to_csv(output_file, index=False)
    elif output_format == 'json':
        output_file = output_path.with_suffix('.json')
        data.to_json(output_file, orient='records', indent=2)
    elif output_format == 'parquet':
        output_file = output_path.with_suffix('.parquet')
        data.to_parquet(output_file, index=False)
    elif output_format == 'excel':
        output_file = output_path.with_suffix('.xlsx')
        # Save field summary as separate sheet if available
        if hasattr(data, '_field_summary'):
            with pd.ExcelWriter(output_file) as writer:
                data.to_excel(writer, sheet_name='Data', index=False)
                data._field_summary.to_excel(writer, sheet_name='Field_Info', index=False)
        else:
            data.to_excel(output_file, index=False)
    
    click.echo(f"  Saved: {output_file}")

def _migrate_format(magnet_data, target_format, preserve_metadata, map_fields, debug):
    """Migrate data to target format with field mapping."""
    from ..core.simplified_field_system import FormatRegistry
    
    registry = FormatRegistry()
    source_format_def = magnet_data.field_registry
    target_format_def = registry.get_format(target_format)
    
    data = magnet_data.get_data()
    
    if map_fields and target_format_def:
        # Create field mapping between formats
        field_mapping = {}
        
        for source_field_name in data.columns:
            source_field = source_format_def.get_field(source_field_name)
            if source_field:
                # Find corresponding field in target format by type and symbol
                for target_field_name, target_field in target_format_def.fields.items():
                    if (target_field.field_type == source_field.field_type and 
                        target_field.symbol == source_field.symbol):
                        field_mapping[source_field_name] = target_field_name
                        break
        
        # Apply field mapping
        if field_mapping:
            data = data.rename(columns=field_mapping)
            if debug:
                click.echo(f"    Applied field mappings: {field_mapping}")
    
    if preserve_metadata:
        # Add original format info
        data['original_format'] = magnet_data.format_type
        data['original_filename'] = magnet_data.filename
        data['target_format'] = target_format
    
    return data

def _save_migrated_data(data, file_path, target_format, output_dir, debug):
    """Save migrated data."""
    base_name = Path(file_path).stem
    
    if output_dir:
        output_path = output_dir / f"{base_name}_migrated_{target_format}.csv"
    else:
        output_path = Path(file_path).parent / f"{base_name}_migrated_{target_format}.csv"
    
    data.to_csv(output_path, index=False)
    click.echo(f"  Migrated data saved: {output_path}")

def _display_validation_results(results, file_path):
    """Display validation results."""
    click.echo(f"  Validation results for {Path(file_path).name}:")
    
    if results['issues']:
        click.echo("    Issues:")
        for issue in results['issues']:
            click.echo(f"      ❌ {issue}")
    
    if results['warnings']:
        click.echo("    Warnings:")
        for warning in results['warnings']:
            click.echo(f"      ⚠️  {warning}")
    
    if results['info']:
        for info in results['info']:
            click.echo(f"      ✅ {info}")

def _export_validation_report(all_results):
    """Export validation report to file."""
    report_df = pd.DataFrame(all_results)
    report_path = Path("validation_report.csv")
    report_df.to_csv(report_path, index=False)
    click.echo(f"Validation report exported: {report_path}")

def _merge_datasets(datasets, merge_strategy, time_align, preserve_field_info, debug):
    """Merge multiple datasets with field information preservation."""
    if merge_strategy == 'concat':
        # Simple concatenation with field info preservation
        all_data = []
        field_info_summary = []
        
        for i, dataset in enumerate(datasets):
            data = dataset.get_data()
            data['source_file'] = dataset.filename
            data['source_index'] = i
            
            if preserve_field_info:
                # Collect field information
                for col in data.columns:
                    if col not in ['source_file', 'source_index']:
                        field_info = dataset.get_field_info(col)
                        symbol, unit_obj, unit_string = field_info
                        field_info_summary.append({
                            'source_file': dataset.filename,
                            'column': col,
                            'symbol': symbol,
                            'unit': unit_string,
                            'format': dataset.format_type
                        })
            
            all_data.append(data)
        
        merged_data = pd.concat(all_data, ignore_index=True)
        
        if preserve_field_info and field_info_summary:
            # Store field info for later use
            merged_data._field_info = pd.DataFrame(field_info_summary)
        
        return merged_data
    
    elif merge_strategy == 'join':
        # Join on common columns (like time) with field compatibility checking
        if time_align and all(dataset.has_key('t') for dataset in datasets):
            merged = datasets[0].get_data(['t'])
            
            for i, dataset in enumerate(datasets[1:], 1):
                data = dataset.get_data()
                
                # Check for field compatibility when merging
                common_cols = set(merged.columns) & set(data.columns)
                if common_cols and preserve_field_info:
                    for col in common_cols:
                        if col != 't':  # Skip time column
                            field1 = datasets[0].get_field_info(col)
                            field2 = dataset.get_field_info(col)
                            if field1[2] != field2[2]:  # Different units
                                if debug:
                                    click.echo(f"    Warning: Unit mismatch for {col}: {field1[2]} vs {field2[2]}")
                
                merged = merged.merge(data, on='t', how='outer', suffixes=('', f'_file{i}'))
            
            return merged
    
    # Default fallback
    return datasets[0].get_data()

def _save_merged_data(data, output_file, debug):
    """Save merged data with field information if available."""
    output_path = Path(output_file)
    
    if output_path.suffix == '.csv':
        data.to_csv(output_path, index=False)
        
        # Save field info separately if available
        if hasattr(data, '_field_info'):
            field_info_path = output_path.with_suffix('.field_info.csv')
            data._field_info.to_csv(field_info_path, index=False)
            if debug:
                click.echo(f"    Field information saved to: {field_info_path}")
                
    elif output_path.suffix == '.json':
        data.to_json(output_path, orient='records', indent=2)
    elif output_path.suffix == '.parquet':
        data.to_parquet(output_path, index=False)
    elif output_path.suffix in ['.xlsx', '.xls']:
        # Save with field info as separate sheet
        with pd.ExcelWriter(output_path) as writer:
            data.to_excel(writer, sheet_name='Data', index=False)
            if hasattr(data, '_field_info'):
                data._field_info.to_excel(writer, sheet_name='Field_Info', index=False)
    else:
        # Default to CSV
        output_path = output_path.with_suffix('.csv')
        data.to_csv(output_path, index=False)
