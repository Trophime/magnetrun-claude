"""Command-line interface using Click."""

import click
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from ..io.readers import DataReader
from ..io.writers import DataWriter
from ..processing.analysis import DataAnalyzer
from ..processing.cleaning import DataCleaner
from ..processing.time_operations import TimeProcessor
from ..visualization.plotters import DataPlotter

@click.group()
@click.version_option()
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.pass_context
def cli(ctx, debug):
    """MagnetRun - A tool for analyzing magnetic measurement data."""
    ctx.ensure_object(dict)
    ctx.obj['DEBUG'] = debug

@cli.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--housing', default='M9', help='Housing type (M8, M9, M10)')
@click.option('--site', default='', help='Site identifier')
@click.option('--insert', default='notdefined', help='Insert identifier')
@click.option('--list-keys', is_flag=True, help='List available data keys')
@click.option('--convert', is_flag=True, help='Convert to CSV format')
@click.pass_context
def info(ctx, files, housing, site, insert, list_keys, convert):
    """Display information about data files."""
    debug = ctx.obj.get('DEBUG', False)
    
    for file_path in files:
        click.echo(f"Processing: {file_path}")
        
        try:
            magnet_run = DataReader.read_file(file_path, housing, site)
            magnet_data = magnet_run.magnet_data
            
            if debug:
                click.echo(f"  Debug: File extension: {Path(file_path).suffix}")
                click.echo(f"  Debug: Data type: {magnet_data.data_type}")
            
            click.echo(f"  Housing: {magnet_run.housing}")
            click.echo(f"  Site: {magnet_run.site}")
            click.echo(f"  Data type: {magnet_data.data_type}")
            click.echo(f"  Keys count: {len(magnet_run.get_keys())}")
            
            # Display info about the data structure
            magnet_data._data_handler.info() if hasattr(magnet_data._data_handler, 'info') else None
            
            if list_keys:
                click.echo("  Available keys:")
                for key in magnet_run.get_keys():
                    click.echo(f"    {key}")
            
            if convert:
                if magnet_data.data_type == 0:  # Pandas data
                    output_path = Path(file_path).with_suffix('.csv')
                    DataWriter.to_csv(magnet_data, output_path)
                    click.echo(f"  Converted to: {output_path}")
                elif magnet_data.data_type == 1:  # TDMS data
                    for group_key in magnet_data._data_handler.data.keys():
                        output_path = Path(file_path).with_suffix(f'-{group_key}.csv')
                        # Convert each group separately
                        group_data = magnet_data._data_handler.data[group_key]
                        group_data.to_csv(output_path, sep='\t', index=True, header=True)
                        click.echo(f"  Converted group {group_key} to: {output_path}")
                
        except Exception as e:
            click.echo(f"  Error: {e}", err=True)
            if debug:
                import traceback
                click.echo(traceback.format_exc(), err=True)

@cli.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--housing', default='M9', help='Housing type')
@click.option('--site', default='', help='Site identifier')
@click.option('--formula', help='Add new column with formula (e.g., "Power = Field * Current")')
@click.option('--compute', is_flag=True, help='Compute derived quantities (e.g., water density)')
@click.option('--plot-formula', is_flag=True, help='Plot the added formula')
@click.option('--vs-time', multiple=True, help='Keys to plot vs time')
@click.option('--key-vs-key', multiple=True, help='Key pairs to plot (format: "key1-key2")')
@click.option('--normalize', is_flag=True, help='Normalize data before plotting')
@click.option('--save', is_flag=True, help='Save plots')
@click.pass_context
def add(ctx, files, housing, site, formula, compute, plot_formula, vs_time, key_vs_key, normalize, save):
    """Add calculated columns and optional plotting."""
    debug = ctx.obj.get('DEBUG', False)
    
    for file_path in files:
        click.echo(f"Processing: {file_path}")
        
        try:
            magnet_run = DataReader.read_file(file_path, housing, site)
            magnet_data = magnet_run.magnet_data
            
            # Add time column if needed for pandas data
            if magnet_data.data_type == 0:
                try:
                    TimeProcessor.add_time_column(magnet_data)
                except Exception as e:
                    if debug:
                        click.echo(f"  Could not add time column: {e}")
            
            if debug:
                click.echo(f"  Available keys: {magnet_data.keys}")
            
            if compute:
                # Compute water density (example from original code)
                try:
                    from pint import UnitRegistry
                    ureg = UnitRegistry()
                    
                    # This would need the actual cooling.water module
                    # For now, just demonstrate the pattern
                    click.echo("  Computing derived quantities...")
                    # magnet_data.compute_data(water.getRho, 'rho', ['HPH', 'TinH'], ('rho', ureg.kilogram / ureg.meter**3))
                    
                except ImportError:
                    click.echo("  Water cooling module not available")
            
            if formula:
                click.echo(f"  Adding formula: {formula}")
                try:
                    # Extract key name from formula
                    key_name = formula.split(' = ')[0].strip()
                    magnet_data.add_data(key_name, formula)
                    click.echo(f"  Added column: {key_name}")
                    
                    if plot_formula:
                        fig, ax = plt.subplots(figsize=(12, 6))
                        DataPlotter.plot_time_series(magnet_data, [key_name], normalize=normalize, ax=ax)
                        
                        # Add additional keys if specified
                        if vs_time:
                            additional_keys = [k for k in vs_time if k in magnet_data.keys]
                            if additional_keys:
                                DataPlotter.plot_time_series(magnet_data, additional_keys, normalize=normalize, ax=ax)
                        
                        ax.set_title(f"{Path(file_path).stem} - {key_name}")
                        ax.legend()
                        
                        if save:
                            output_path = Path(file_path).with_suffix(f'_{key_name}_vs_time.png')
                            plt.savefig(output_path, dpi=300, bbox_inches='tight')
                            click.echo(f"  Saved plot: {output_path}")
                        else:
                            plt.show()
                        plt.close()
                        
                except Exception as e:
                    click.echo(f"  Error adding formula: {e}", err=True)
            
            # Handle key vs key plotting
            if key_vs_key:
                for pair in key_vs_key:
                    if '-' in pair:
                        key1, key2 = pair.split('-', 1)
                        if key1 in magnet_data.keys and key2 in magnet_data.keys:
                            fig, ax = plt.subplots(figsize=(8, 6))
                            DataPlotter.plot_xy(magnet_data, key1, key2, ax=ax)
                            ax.set_title(f"{Path(file_path).stem} - {key1} vs {key2}")
                            
                            if save:
                                output_path = Path(file_path).with_suffix(f'_{key1}_vs_{key2}.png')
                                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                                click.echo(f"  Saved plot: {output_path}")
                            else:
                                plt.show()
                            plt.close()
                        else:
                            click.echo(f"  Warning: Keys '{key1}' or '{key2}' not found")
                
        except Exception as e:
            click.echo(f"  Error: {e}", err=True)
            if debug:
                import traceback
                click.echo(traceback.format_exc(), err=True)

@cli.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--housing', default='M9', help='Housing type')
@click.option('--keys', multiple=True, help='Keys to analyze')
@click.option('--detect-bkpts', is_flag=True, help='Detect breakpoints')
@click.option('--localmax', is_flag=True, help='Find local maxima')
@click.option('--plateau', is_flag=True, help='Find plateaus')
@click.option('--threshold', default=1e-3, type=float, help='Threshold for regime detection')
@click.option('--bthreshold', default=1e-3, type=float, help='B threshold for regime detection')
@click.option('--dthreshold', default=10.0, type=float, help='Duration threshold for regime detection')
@click.option('--window', default=10, type=int, help='Window size for analysis')
@click.option('--level', default=90, type=int, help='Percentile level for analysis')
@click.option('--save', is_flag=True, help='Save analysis plots')
@click.option('--show', is_flag=True, help='Show analysis plots')
@click.pass_context
def stats(ctx, files, housing, keys, detect_bkpts, localmax, plateau, threshold, bthreshold, dthreshold, window, level, save, show):
    """Perform statistical analysis and feature detection."""
    debug = ctx.obj.get('DEBUG', False)
    
    # Collect results for summary table
    results = []
    
    for file_path in files:
        click.echo(f"Analyzing: {file_path}")
        
        try:
            magnet_run = DataReader.read_file(file_path, housing)
            magnet_data = magnet_run.magnet_data
            
            # Add time column if needed
            if magnet_data.data_type == 0:
                try:
                    TimeProcessor.add_time_column(magnet_data)
                except Exception as e:
                    if debug:
                        click.echo(f"  Could not add time column: {e}")
            
            # Default to Field if no keys specified
            analysis_keys = list(keys) if keys else ['Field']
            
            file_results = {'file': Path(file_path).stem}
            
            for key in analysis_keys:
                if key not in magnet_data.keys:
                    click.echo(f"  Warning: Key '{key}' not found")
                    continue
                
                click.echo(f"  Analyzing key: {key}")
                
                # Get period for threshold calculations
                period = 1.0  # Default for pandas data
                if magnet_data.data_type == 1 and "/" in key:
                    group, channel = key.split("/")
                    period = magnet_data._data_handler.groups[group][channel]["wf_increment"]
                
                num_points_threshold = int(dthreshold / period)
                
                if localmax:
                    click.echo("  Finding local maxima...")
                    from scipy.signal import argrelextrema
                    
                    data = magnet_data.get_data([key])
                    field_values = data[key].values
                    
                    local_max_indices = argrelextrema(field_values, np.greater, mode='clip')
                    click.echo(f"    Found {len(local_max_indices[0])} local maxima")
                    
                    if show or save:
                        fig, ax = plt.subplots(figsize=(12, 6))
                        t_data = magnet_data.get_data(['t', key])
                        ax.plot(t_data['t'], t_data[key], 'b-', label=key)
                        ax.plot(t_data['t'].iloc[local_max_indices[0]], 
                               t_data[key].iloc[local_max_indices[0]], 'r*', 
                               markersize=10, label='Local Maxima')
                        ax.set_xlabel('Time [s]')
                        ax.set_ylabel(key)
                        ax.legend()
                        ax.grid(True)
                        ax.set_title(f"{Path(file_path).stem} - Local Maxima")
                        
                        if save:
                            output_path = Path(file_path).with_suffix(f'_{key}_localmax.png')
                            plt.savefig(output_path, dpi=300, bbox_inches='tight')
                            click.echo(f"    Saved plot: {output_path}")
                        if show:
                            plt.show()
                        plt.close()
                
                if plateau:
                    click.echo("  Detecting plateaus...")
                    from ..utils.plateaux import nplateaus
                    
                    try:
                        # Get unit information
                        symbol, unit = magnet_data.get_unit_key(key)
                        
                        plateaus_result = nplateaus(
                            magnet_data,
                            xField=("t", "t", "s"),
                            yField=(key, symbol, unit),
                            threshold=threshold,
                            num_points_threshold=num_points_threshold,
                            save=save,
                            show=show,
                            verbose=debug
                        )
                        
                        click.echo(f"    Found {len(plateaus_result)} plateaus")
                        
                        if plateaus_result:
                            # Find longest plateau
                            max_plateau = max(plateaus_result, key=lambda p: p['duration'])
                            file_results[f'{key}_plateau_max_duration'] = max_plateau['duration']
                            file_results[f'{key}_plateau_max_value'] = max_plateau['value']
                            
                            # Display plateau information
                            df_plateaux = pd.DataFrame(plateaus_result)
                            click.echo(f"    Plateau summary:")
                            click.echo(f"      Duration range: {df_plateaux['duration'].min():.2f} - {df_plateaux['duration'].max():.2f} s")
                            click.echo(f"      Value range: {df_plateaux['value'].min():.3f} - {df_plateaux['value'].max():.3f}")
                        else:
                            file_results[f'{key}_plateau_max_duration'] = 0
                            file_results[f'{key}_plateau_max_value'] = 0
                            
                    except Exception as e:
                        click.echo(f"    Error in plateau detection: {e}")
                
                if detect_bkpts:
                    click.echo("  Detecting breakpoints...")
                    
                    try:
                        breakpoint_result = DataAnalyzer.detect_breakpoints(
                            magnet_data, key, window=window, level=level
                        )
                        
                        peaks = breakpoint_result['peaks']
                        click.echo(f"    Found {len(peaks)} breakpoints")
                        
                        if show or save:
                            from ..visualization.breakpoint_plotter import plot_breakpoints
                            
                            # This would be a new module for breakpoint visualization
                            # For now, create a simple plot
                            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
                            
                            # Get data
                            data = magnet_data.get_data(['t', key])
                            t_values = data['t'].values
                            y_values = data[key].values
                            
                            # Plot original data
                            ax1.plot(t_values, y_values, 'b-', alpha=0.7, label=key)
                            ax1.plot(t_values, breakpoint_result['smoothed'], 'r-', label='Smoothed')
                            
                            # Mark breakpoints
                            if len(peaks) > 0:
                                ax1.plot(t_values[peaks], breakpoint_result['smoothed'][peaks], 
                                        'go', markersize=8, label='Breakpoints')
                            
                            ax1.set_ylabel(key)
                            ax1.legend()
                            ax1.grid(True)
                            ax1.set_title(f"{Path(file_path).stem} - Breakpoint Detection")
                            
                            # Plot second derivative
                            ax2.plot(t_values, np.abs(breakpoint_result['smoothed_der2']), 'g-', label='|2nd Derivative|')
                            ax2.axhline(y=breakpoint_result['quantiles_der'], color='r', 
                                       linestyle='--', label=f'{level}% Threshold')
                            
                            if len(peaks) > 0:
                                ax2.plot(t_values[peaks], np.abs(breakpoint_result['smoothed_der2'][peaks]), 
                                        'go', markersize=8, label='Breakpoints')
                            
                            ax2.set_xlabel('Time [s]')
                            ax2.set_ylabel('|2nd Derivative|')
                            ax2.legend()
                            ax2.grid(True)
                            
                            plt.tight_layout()
                            
                            if save:
                                output_path = Path(file_path).with_suffix(f'_{key}_breakpoints.png')
                                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                                click.echo(f"    Saved plot: {output_path}")
                            if show:
                                plt.show()
                            plt.close()
                            
                    except Exception as e:
                        click.echo(f"    Error in breakpoint detection: {e}")
                        if debug:
                            import traceback
                            click.echo(traceback.format_exc(), err=True)
            
            results.append(file_results)
            
        except Exception as e:
            click.echo(f"  Error: {e}", err=True)
            if debug:
                import traceback
                click.echo(traceback.format_exc(), err=True)
    
    # Display summary table if we have results
    if results and len(results) > 0:
        df_results = pd.DataFrame(results)
        click.echo("\n" + "="*50)
        click.echo("ANALYSIS SUMMARY")
        click.echo("="*50)
        click.echo(df_results.to_string(index=False))
        
        # Save summary to CSV
        summary_path = Path("analysis_summary.csv")
        df_results.to_csv(summary_path, index=False)
        click.echo(f"\nSummary saved to: {summary_path}")

@cli.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--housing', default='M9', help='Housing type')
@click.option('--keys', multiple=True, help='Keys to plot')
@click.option('--x-key', default='t', help='X-axis key')
@click.option('--key-vs-key', multiple=True, help='Key pairs to plot (format: "key1-key2")')
@click.option('--normalize', is_flag=True, help='Normalize data')
@click.option('--save', is_flag=True, help='Save plots')
@click.option('--output-dir', type=click.Path(), help='Output directory for plots')
@click.pass_context
def plot(ctx, files, housing, keys, x_key, key_vs_key, normalize, save, output_dir):
    """Generate plots from data."""
    debug = ctx.obj.get('DEBUG', False)
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
    
    for file_path in files:
        click.echo(f"Plotting: {file_path}")
        
        try:
            magnet_run = DataReader.read_file(file_path, housing)
            magnet_data = magnet_run.magnet_data
            
            # Add time column if needed
            if magnet_data.data_type == 0:
                try:
                    TimeProcessor.add_time_column(magnet_data)
                except Exception:
                    pass  # Continue without time column
            
            # Time series plots
            if keys:
                plot_keys = [k for k in keys if k in magnet_data.keys]
                
                if plot_keys:
                    fig, ax = plt.subplots(figsize=(12, 8))
                    
                    DataPlotter.plot_time_series(
                        magnet_data,
                        plot_keys,
                        x_key,
                        normalize,
                        ax
                    )
                    
                    ax.set_title(f"{Path(file_path).stem} - Time Series")
                    ax.legend()
                    
                    if save:
                        if output_dir:
                            output_path = output_dir / f"{Path(file_path).stem}_timeseries.png"
                        else:
                            output_path = Path(file_path).with_suffix('_timeseries.png')
                        
                        plt.savefig(output_path, dpi=300, bbox_inches='tight')
                        click.echo(f"  Saved plot: {output_path}")
                    else:
                        plt.show()
                    plt.close()
            
            # X-Y plots
            if key_vs_key:
                for pair in key_vs_key:
                    if '-' in pair:
                        key1, key2 = pair.split('-', 1)
                        if key1 in magnet_data.keys and key2 in magnet_data.keys:
                            fig, ax = plt.subplots(figsize=(8, 6))
                            DataPlotter.plot_xy(magnet_data, key1, key2, ax=ax)
                            ax.set_title(f"{Path(file_path).stem} - {key1} vs {key2}")
                            
                            if save:
                                if output_dir:
                                    output_path = output_dir / f"{Path(file_path).stem}_{key1}_vs_{key2}.png"
                                else:
                                    output_path = Path(file_path).with_suffix(f'_{key1}_vs_{key2}.png')
                                
                                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                                click.echo(f"  Saved plot: {output_path}")
                            else:
                                plt.show()
                            plt.close()
                        else:
                            click.echo(f"  Warning: Keys '{key1}' or '{key2}' not found")
            
            # Default plot if no specific keys given
            if not keys and not key_vs_key:
                default_keys = [k for k in ['Field', 'Current', 'IH', 'IB'] if k in magnet_data.keys]
                if default_keys:
                    fig, ax = plt.subplots(figsize=(12, 8))
                    DataPlotter.plot_time_series(magnet_data, default_keys[:2], x_key, normalize, ax)
                    ax.set_title(f"{Path(file_path).stem} - Default View")
                    ax.legend()
                    
                    if save:
                        if output_dir:
                            output_path = output_dir / f"{Path(file_path).stem}_default.png"
                        else:
                            output_path = Path(file_path).with_suffix('_default.png')
                        
                        plt.savefig(output_path, dpi=300, bbox_inches='tight')
                        click.echo(f"  Saved plot: {output_path}")
                    else:
                        plt.show()
                    plt.close()
            
        except Exception as e:
            click.echo(f"  Error: {e}", err=True)
            if debug:
                import traceback
                click.echo(traceback.format_exc(), err=True)

@cli.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--housing', default='M9', help='Housing type')
@click.option('--output-time', multiple=True, help='Extract data at specific times')
@click.option('--output-timerange', multiple=True, help='Extract data in time ranges (format: "start;end")')
@click.option('--output-key', multiple=True, help='Extract specific keys vs time')
@click.option('--extract-pairkeys', multiple=True, help='Extract key pairs (format: "key1-key2;key3-key4")')
@click.option('--convert', is_flag=True, help='Convert file to CSV')
@click.pass_context
def select(ctx, files, housing, output_time, output_timerange, output_key, extract_pairkeys, convert):
    """Extract and select data subsets."""
    debug = ctx.obj.get('DEBUG', False)
    
    for file_path in files:
        click.echo(f"Selecting from: {file_path}")
        
        try:
            magnet_run = DataReader.read_file(file_path, housing)
            magnet_data = magnet_run.magnet_data
            
            # Add time column if needed
            if magnet_data.data_type == 0:
                try:
                    TimeProcessor.add_time_column(magnet_data)
                except Exception as e:
                    if debug:
                        click.echo(f"  Could not add time column: {e}")
            
            # Extract data at specific times
            if output_time:
                click.echo("  Extracting data at specific times...")
                for time_list in output_time:
                    times = [float(t) for t in time_list.split(';')]
                    
                    for time_val in times:
                        if magnet_data.data_type == 0:
                            data = magnet_data.get_data()
                            # Find closest time
                            closest_idx = (data['t'] - time_val).abs().idxmin()
                            selected_data = data.iloc[[closest_idx]]
                            
                            output_path = Path(file_path).with_suffix(f'_at_{time_val:.3f}s.csv')
                            selected_data.to_csv(output_path, sep='\t', index=False, header=True)
                            click.echo(f"    Saved: {output_path}")
            
            # Extract data in time ranges
            if output_timerange:
                click.echo("  Extracting data in time ranges...")
                for time_range in output_timerange:
                    start_time, end_time = time_range.split(';')
                    start_time = float(start_time.replace(':', '-'))
                    end_time = float(end_time.replace(':', '-'))
                    
                    if magnet_data.data_type == 0:
                        data = magnet_data.get_data()
                        mask = (data['t'] >= start_time) & (data['t'] <= end_time)
                        selected_data = data[mask]
                        
                        output_path = Path(file_path).with_suffix(f'_from_{start_time:.1f}_to_{end_time:.1f}.csv')
                        selected_data.to_csv(output_path, sep='\t', index=False, header=True)
                        click.echo(f"    Saved: {output_path}")
                    
                    elif magnet_data.data_type == 1:
                        # Handle TDMS data
                        for group_name, group_data in magnet_data._data_handler.data.items():
                            if 't' in group_data.columns or group_data.index.name == 't':
                                # Extract time range from this group
                                # This would need more sophisticated time handling for TDMS
                                pass
            
            # Extract specific keys vs time
            if output_key:
                click.echo("  Extracting specific keys...")
                for key_list in output_key:
                    selected_keys = key_list.split(';') if ';' in key_list else [key_list]
                    
                    # Always include time if not present
                    if 't' not in selected_keys and 't' in magnet_data.keys:
                        selected_keys.insert(0, 't')
                    
                    # Validate keys exist
                    valid_keys = [k for k in selected_keys if k in magnet_data.keys]
                    
                    if valid_keys:
                        selected_data = magnet_data.get_data(valid_keys)
                        
                        key_name = '_'.join([k for k in valid_keys if k != 't'])
                        output_path = Path(file_path).with_suffix(f'_{key_name}_vs_Time.csv')
                        
                        selected_data.to_csv(output_path, sep='\t', index=False, header=True)
                        click.echo(f"    Saved: {output_path}")
                    else:
                        click.echo(f"    Warning: No valid keys found in {selected_keys}")
            
            # Extract key pairs
            if extract_pairkeys:
                click.echo("  Extracting key pairs...")
                for pair_list in extract_pairkeys:
                    pairs = pair_list.split(';')
                    
                    for pair in pairs:
                        if '-' in pair:
                            key1, key2 = pair.split('-', 1)
                            
                            if key1 in magnet_data.keys and key2 in magnet_data.keys:
                                pair_data = magnet_data.get_data([key1, key2])
                                
                                # Remove zero values
                                pair_data = pair_data[(pair_data[key1] != 0) & (pair_data[key2] != 0)]
                                
                                output_path = Path(file_path).with_suffix(f'_{pair}.csv')
                                pair_data.to_csv(output_path, sep='\t', index=False, header=False)
                                click.echo(f"    Saved pair: {output_path}")
                            else:
                                click.echo(f"    Warning: Keys '{key1}' or '{key2}' not found")
            
            # Convert entire file
            if convert:
                click.echo("  Converting file...")
                if magnet_data.data_type == 0:
                    output_path = Path(file_path).with_suffix('.csv')
                    DataWriter.to_csv(magnet_data, output_path)
                    click.echo(f"    Converted to: {output_path}")
                elif magnet_data.data_type == 1:
                    # Convert each group separately for TDMS
                    for group_name, group_data in magnet_data._data_handler.data.items():
                        output_path = Path(file_path).with_suffix(f'_{group_name}.csv')
                        group_data.to_csv(output_path, sep='\t', index=True, header=True)
                        click.echo(f"    Converted group {group_name} to: {output_path}")
            
        except Exception as e:
            click.echo(f"  Error: {e}", err=True)
            if debug:
                import traceback
                click.echo(traceback.format_exc(), err=True)
