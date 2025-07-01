"""Data processing and formula commands."""

import click
from pathlib import Path
from .utils import load_magnet_data, add_time_column_if_needed, handle_error
from ..visualization.plotters import DataPlotter

@click.group(name='add')
def processing_commands():
    """Data processing and formula commands."""
    pass

@processing_commands.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--housing', default='M9', help='Housing type')
@click.option('--site', default='', help='Site identifier')
@click.option('--formula', help='Add new column with formula (e.g., "Power = Field * Current")')
@click.option('--compute', is_flag=True, help='Compute derived quantities (e.g., water density)')
@click.option('--plot-formula', is_flag=True, help='Plot the added formula')
@click.option('--vs-time', multiple=True, help='Keys to plot vs time')
@click.option('--key-pairs', multiple=True, help='Key pairs to plot (format: "key1;key2")')
@click.option('--normalize', is_flag=True, help='Normalize data before plotting')
@click.option('--save', is_flag=True, help='Save plots')
@click.pass_context
def formula(ctx, files, housing, site, formula, compute, plot_formula, vs_time, key_pairs, normalize, save):
    """Add calculated columns and optional plotting."""
    debug = ctx.obj.get('DEBUG', False)
    
    for file_path in files:
        click.echo(f"Processing: {file_path}")
        
        try:
            magnet_data, magnet_run = load_magnet_data(file_path, housing, site)
            add_time_column_if_needed(magnet_data, debug)
            
            if debug:
                click.echo(f"  Available keys: {magnet_data.keys}")
            
            if compute:
                _compute_derived_quantities(magnet_data)
            
            if formula:
                _add_formula(magnet_data, formula, file_path, plot_formula, vs_time, normalize, save)
            
            if key_pairs:
                _plot_key_pairs(magnet_data, key_pairs, file_path, save)
                
        except Exception as e:
            handle_error(e, debug, file_path)

@processing_commands.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--housing', default='M9', help='Housing type')
@click.option('--keys', multiple=True, help='Keys to filter (if not specified, uses all keys)')
@click.option('--min-value', type=float, help='Minimum value threshold')
@click.option('--max-value', type=float, help='Maximum value threshold')
@click.option('--exclude-zeros', is_flag=True, help='Exclude zero values')
@click.option('--sample-rate', type=int, help='Sample every N-th point')
@click.pass_context
def filter(ctx, files, housing, keys, min_value, max_value, exclude_zeros, sample_rate):
    """Filter data based on value criteria."""
    debug = ctx.obj.get('DEBUG', False)
    
    for file_path in files:
        click.echo(f"Filtering: {file_path}")
        
        try:
            magnet_data, magnet_run = load_magnet_data(file_path, housing)
            add_time_column_if_needed(magnet_data, debug)
            
            data = magnet_data.get_data()
            original_length = len(data)
            
            # Apply filters
            if keys:
                filter_keys = [k for k in keys if k in data.columns]
                if not filter_keys:
                    click.echo(f"    Warning: No valid filter keys found")
                    continue
            else:
                # Use all numeric columns
                filter_keys = data.select_dtypes(include=['number']).columns.tolist()
            
            mask = True
            
            if min_value is not None:
                for key in filter_keys:
                    mask = mask & (data[key] >= min_value)
            
            if max_value is not None:
                for key in filter_keys:
                    mask = mask & (data[key] <= max_value)
            
            if exclude_zeros:
                for key in filter_keys:
                    mask = mask & (data[key] != 0)
            
            filtered_data = data[mask]
            
            if sample_rate and sample_rate > 1:
                filtered_data = filtered_data.iloc[::sample_rate]
            
            click.echo(f"    Filtered from {original_length} to {len(filtered_data)} rows")
            
            # Save filtered data
            output_path = Path(file_path).with_suffix('_filtered.csv')
            filtered_data.to_csv(output_path, index=False)
            click.echo(f"    Saved filtered data: {output_path}")
            
        except Exception as e:
            handle_error(e, debug, file_path)

def _compute_derived_quantities(magnet_data):
    """Compute derived quantities like water density."""
    try:
        from pint import UnitRegistry
        ureg = UnitRegistry()
        
        click.echo("  Computing derived quantities...")
        # Implementation would go here
        
    except ImportError:
        click.echo("  Water cooling module not available")

def _add_formula(magnet_data, formula, file_path, plot_formula, vs_time, normalize, save):
    """Add a formula and optionally plot it."""
    click.echo(f"  Adding formula: {formula}")
    try:
        key_name = formula.split(' = ')[0].strip()
        magnet_data.add_data(key_name, formula)
        click.echo(f"  Added column: {key_name}")
        
        if plot_formula:
            plot_keys = [key_name]
            if vs_time:
                additional_keys = [k for k in vs_time if k in magnet_data.keys]
                plot_keys.extend(additional_keys)
            
            DataPlotter.plot_time_series_to_file(
                magnet_data, plot_keys, 't', normalize, True, file_path, save, not save
            )
            
    except Exception as e:
        click.echo(f"  Error adding formula: {e}", err=True)

def _plot_key_pairs(magnet_data, key_pairs, file_path, save):
    """Plot key vs key pairs."""
    DataPlotter.plot_xy_pairs_to_file(
        magnet_data, key_pairs, file_path, save, not save
    )
