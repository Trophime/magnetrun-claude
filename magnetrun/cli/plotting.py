"""Visualization commands using enhanced DataPlotter - Breakpoint functionality removed."""

import click
from pathlib import Path
import matplotlib.pyplot as plt
from .utils import load_magnet_data, add_time_column_if_needed, handle_error
from ..visualization.plotters import DataPlotter

@click.group(name='plot')
def plotting_commands():
    """Visualization commands."""
    pass

@plotting_commands.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--housing', default='M9', help='Housing type')
@click.option('--keys', multiple=True, help='Keys to plot')
@click.option('--x-key', default='t', help='X-axis key')
@click.option('--key-vs-key', multiple=True, help='Key pairs to plot (format: "key1-key2")')
@click.option('--normalize', is_flag=True, help='Normalize data')
@click.option('--save', is_flag=True, help='Save plots')
@click.option('--show', is_flag=True, help='Show plots')
@click.option('--output-dir', type=click.Path(), help='Output directory for plots')
@click.option('--grid/--no-grid', default=True, help='Show/hide grid')
@click.option('--style', default='default', help='Matplotlib style')
@click.pass_context
def show(ctx, files, housing, keys, x_key, key_vs_key, normalize, save, show, output_dir, grid, style):
    """Generate plots from data."""
    debug = ctx.obj.get('DEBUG', False)
    
    if style != 'default':
        plt.style.use(style)
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
    
    for file_path in files:
        click.echo(f"Plotting: {file_path}")
        
        try:
            magnet_data, magnet_run = load_magnet_data(file_path, housing)
            add_time_column_if_needed(magnet_data)
            
            if keys:
                DataPlotter.plot_time_series_to_file(
                    magnet_data, keys, x_key, normalize, grid, file_path, save, show, output_dir
                )
            
            if key_vs_key:
                DataPlotter.plot_xy_pairs_to_file(
                    magnet_data, key_vs_key, file_path, save, show, output_dir
                )
            
            if not keys and not key_vs_key:
                DataPlotter.plot_default_view(
                    magnet_data, x_key, normalize, grid, file_path, save, show, output_dir
                )
            
        except Exception as e:
            handle_error(e, debug, file_path)

@plotting_commands.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--housing', default='M9', help='Housing type')
@click.option('--keys', multiple=True, help='Keys to create subplots for')
@click.option('--x-key', default='t', help='X-axis key')
@click.option('--normalize', is_flag=True, help='Normalize data')
@click.option('--save', is_flag=True, help='Save plots')
@click.option('--show', is_flag=True, help='Show plots')
@click.option('--output-dir', type=click.Path(), help='Output directory for plots')
@click.option('--cols', default=2, type=int, help='Number of columns in subplot grid')
@click.pass_context
def subplots(ctx, files, housing, keys, x_key, normalize, save, show, output_dir, cols):
    """Create subplot grid for multiple keys."""
    debug = ctx.obj.get('DEBUG', False)
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
    
    for file_path in files:
        click.echo(f"Creating subplots for: {file_path}")
        
        try:
            magnet_data, magnet_run = load_magnet_data(file_path, housing)
            add_time_column_if_needed(magnet_data)
            
            DataPlotter.create_subplots(
                magnet_data, keys, x_key, normalize, cols, file_path, save, show, output_dir
            )
                
        except Exception as e:
            handle_error(e, debug, file_path)

@plotting_commands.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--housing', default='M9', help='Housing type')
@click.option('--template', default='standard', 
              type=click.Choice(['standard', 'publication', 'presentation']),
              help='Plot template style')
@click.option('--save', is_flag=True, help='Save plots')
@click.option('--show', is_flag=True, help='Show plots')
@click.option('--output-dir', type=click.Path(), help='Output directory for plots')
@click.pass_context
def overview(ctx, files, housing, template, save, show, output_dir):
    """Create overview plot with predefined layout."""
    debug = ctx.obj.get('DEBUG', False)
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
    
    for file_path in files:
        click.echo(f"Creating overview plot for: {file_path}")
        
        try:
            magnet_data, magnet_run = load_magnet_data(file_path, housing)
            add_time_column_if_needed(magnet_data)
            
            DataPlotter.create_overview_plot(
                magnet_data, template, file_path, save, show, output_dir
            )
            
        except Exception as e:
            handle_error(e, debug, file_path)

@plotting_commands.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--housing', default='M9', help='Housing type')
@click.option('--field-name', required=True, help='Field name to convert')
@click.option('--units', required=True, help='Comma-separated list of target units')
@click.option('--save', is_flag=True, help='Save plots')
@click.option('--show', is_flag=True, help='Show plots')
@click.option('--output-dir', type=click.Path(), help='Output directory for plots')
@click.pass_context
def convert_units(ctx, files, housing, field_name, units, save, show, output_dir):
    """Create unit conversion comparison plots."""
    debug = ctx.obj.get('DEBUG', False)
    
    target_units = [unit.strip() for unit in units.split(',')]
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
    
    for file_path in files:
        click.echo(f"Creating unit conversion plot for: {file_path}")
        
        try:
            magnet_data, magnet_run = load_magnet_data(file_path, housing)
            add_time_column_if_needed(magnet_data)
            
            DataPlotter.plot_unit_conversion_comparison(
                magnet_data, field_name, target_units, file_path, save, show, output_dir
            )
            
        except Exception as e:
            handle_error(e, debug, file_path)

@plotting_commands.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--housing', default='M9', help='Housing type')
@click.option('--save', is_flag=True, help='Save plots')
@click.option('--show', is_flag=True, help='Show plots')
@click.option('--output-dir', type=click.Path(), help='Output directory for plots')
@click.pass_context
def field_validation(ctx, files, housing, save, show, output_dir):
    """Create field validation summary plots."""
    debug = ctx.obj.get('DEBUG', False)
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
    
    for file_path in files:
        click.echo(f"Creating field validation plot for: {file_path}")
        
        try:
            magnet_data, magnet_run = load_magnet_data(file_path, housing)
            add_time_column_if_needed(magnet_data)
            
            DataPlotter.plot_field_validation_summary(
                magnet_data, file_path, save, show, output_dir
            )
            
        except Exception as e:
            handle_error(e, debug, file_path)

@plotting_commands.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--housing', default='M9', help='Housing type')
@click.option('--save', is_flag=True, help='Save plots')
@click.option('--show', is_flag=True, help='Show plots')
@click.option('--output-dir', type=click.Path(), help='Output directory for plots')
@click.pass_context
def field_types(ctx, files, housing, save, show, output_dir):
    """Create field type distribution plots."""
    debug = ctx.obj.get('DEBUG', False)
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
    
    for file_path in files:
        click.echo(f"Creating field type distribution plot for: {file_path}")
        
        try:
            magnet_data, magnet_run = load_magnet_data(file_path, housing)
            add_time_column_if_needed(magnet_data)
            
            DataPlotter.plot_field_type_distribution(
                magnet_data, file_path, save, show, output_dir
            )
            
        except Exception as e:
            handle_error(e, debug, file_path)
