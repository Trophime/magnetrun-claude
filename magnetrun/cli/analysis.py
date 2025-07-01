"""Statistical analysis and feature detection commands - Breakpoint functionality removed."""

import click
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from .utils import load_magnet_data, add_time_column_if_needed, handle_error
from ..processing.analysis import DataAnalyzer

@click.group(name='stats')
def analysis_commands():
    """Statistical analysis and feature detection commands."""
    pass

@analysis_commands.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--housing', default='M9', help='Housing type')
@click.option('--keys', multiple=True, help='Keys to analyze')
@click.option('--localmax', is_flag=True, help='Find local maxima')
@click.option('--plateau', is_flag=True, help='Find plateaus')
@click.option('--threshold', default=1e-3, type=float, help='Threshold for regime detection')
@click.option('--dthreshold', default=10.0, type=float, help='Duration threshold for regime detection')
@click.option('--save', is_flag=True, help='Save analysis plots')
@click.option('--show', is_flag=True, help='Show analysis plots')
@click.pass_context
def analyze(ctx, files, housing, keys, localmax, plateau, threshold, dthreshold, save, show):
    """Perform statistical analysis and feature detection."""
    debug = ctx.obj.get('DEBUG', False)
    results = []
    
    for file_path in files:
        click.echo(f"Analyzing: {file_path}")
        
        try:
            magnet_data, magnet_run = load_magnet_data(file_path, housing)
            add_time_column_if_needed(magnet_data, debug)
            
            analysis_keys = list(keys) if keys else ['Field']
            file_results = {'file': Path(file_path).stem}
            
            for key in analysis_keys:
                if key not in magnet_data.keys:
                    click.echo(f"  Warning: Key '{key}' not found")
                    continue
                
                click.echo(f"  Analyzing key: {key}")
                
                if localmax:
                    _find_local_maxima(magnet_data, key, file_path, save, show)
                
                if plateau:
                    plateau_results = _detect_plateaus(magnet_data, key, threshold, dthreshold, file_path, save, show, debug)
                    file_results.update(plateau_results)
            
            results.append(file_results)
            
        except Exception as e:
            handle_error(e, debug, file_path)
    
    # Display summary
    if results:
        _display_analysis_summary(results)

@analysis_commands.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--housing', default='M9', help='Housing type')
@click.option('--key', required=True, help='Key to use for statistics')
@click.option('--percentiles', default='25,50,75,90,95', help='Comma-separated percentiles to calculate')
@click.pass_context
def stats(ctx, files, housing, key, percentiles):
    """Show basic statistics for selected data."""
    debug = ctx.obj.get('DEBUG', False)
    
    percentile_list = [float(p) for p in percentiles.split(',')]
    
    for file_path in files:
        click.echo(f"Statistics for: {file_path}")
        
        try:
            magnet_data, magnet_run = load_magnet_data(file_path, housing)
            
            if key not in magnet_data.keys:
                click.echo(f"    Warning: Key '{key}' not found")
                continue
            
            data = magnet_data.get_data([key])
            series = data[key]
            
            # Get field information for better display
            field_label = magnet_data.get_field_label(key)
            
            click.echo(f"  Key: {key} ({field_label})")
            click.echo(f"    Count: {len(series)}")
            click.echo(f"    Mean: {series.mean():.6f}")
            click.echo(f"    Std: {series.std():.6f}")
            click.echo(f"    Min: {series.min():.6f}")
            click.echo(f"    Max: {series.max():.6f}")
            
            for p in percentile_list:
                value = series.quantile(p/100)
                click.echo(f"    {p}%: {value:.6f}")
            
        except Exception as e:
            handle_error(e, debug, file_path)

@analysis_commands.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--housing', default='M9', help='Housing type')
@click.option('--keys', multiple=True, help='Keys to analyze for extrema')
@click.option('--mode', default='maxima', type=click.Choice(['maxima', 'minima', 'both']),
              help='Type of extrema to find')
@click.option('--save', is_flag=True, help='Save extrema plots')
@click.option('--show', is_flag=True, help='Show extrema plots')
@click.option('--output-dir', type=click.Path(), help='Output directory for plots')
@click.pass_context
def extrema(ctx, files, housing, keys, mode, save, show, output_dir):
    """Find and plot local extrema (maxima/minima)."""
    debug = ctx.obj.get('DEBUG', False)
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
    
    for file_path in files:
        click.echo(f"Finding extrema in: {file_path}")
        
        try:
            magnet_data, magnet_run = load_magnet_data(file_path, housing)
            add_time_column_if_needed(magnet_data, debug)
            
            analysis_keys = list(keys) if keys else ['Field']
            
            for key in analysis_keys:
                if key not in magnet_data.keys:
                    click.echo(f"  Warning: Key '{key}' not found")
                    continue
                
                click.echo(f"  Finding {mode} for key: {key}")
                
                if mode in ['maxima', 'both']:
                    _find_local_maxima(magnet_data, key, file_path, save, show, output_dir)
                
                if mode in ['minima', 'both']:
                    _find_local_minima(magnet_data, key, file_path, save, show, output_dir)
                
        except Exception as e:
            handle_error(e, debug, file_path)

def _find_local_maxima(magnet_data, key, file_path, save, show, output_dir=None):
    """Find and plot local maxima."""
    extrema_results = DataAnalyzer.find_local_extrema(magnet_data, key, 'maxima')
    local_max_indices = extrema_results.get('maxima', np.array([]))
    
    click.echo(f"    Found {len(local_max_indices)} local maxima")
    
    if save or show:
        from ..visualization.plotters import DataPlotter
        DataPlotter.plot_local_maxima(
            magnet_data, key, local_max_indices, file_path, save, show, output_dir
        )

def _find_local_minima(magnet_data, key, file_path, save, show, output_dir=None):
    """Find and plot local minima."""
    extrema_results = DataAnalyzer.find_local_extrema(magnet_data, key, 'minima')
    local_min_indices = extrema_results.get('minima', np.array([]))
    
    click.echo(f"    Found {len(local_min_indices)} local minima")
    
    if save or show:
        fig, ax = plt.subplots(figsize=(12, 6))
        
        try:
            data = magnet_data.get_data(['t', key])
            x_values = data['t']
            x_label = magnet_data.get_field_label('t')
        except:
            data = magnet_data.get_data([key])
            x_values = data.index
            x_label = 'Index'
        
        # Get field information for y-axis
        y_label = magnet_data.get_field_label(key)
        
        ax.plot(x_values, data[key], 'b-', label=key)
        if len(local_min_indices) > 0:
            ax.plot(x_values.iloc[local_min_indices], 
                   data[key].iloc[local_min_indices], 'r*', 
                   markersize=10, label='Local Minima')
        
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.legend()
        ax.grid(True)
        ax.set_title(f"{Path(file_path).stem} - Local Minima")
        
        if save:
            if output_dir:
                output_path = output_dir / f"{Path(file_path).stem}_{key}_localmin.png"
            else:
                output_path = Path(file_path).with_suffix(f'_{key}_localmin.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            click.echo(f"    Saved plot: {output_path}")
        
        if show:
            plt.show()
        
        plt.close()

def _detect_plateaus(magnet_data, key, threshold, dthreshold, file_path, save, show, debug):
    """Detect plateaus in the data."""
    try:
        # This would use the plateaux utility if available
        # For now, return empty results
        click.echo(f"    Plateau detection not implemented yet")
        return {
            f'{key}_plateau_max_duration': 0,
            f'{key}_plateau_max_value': 0
        }
    except Exception as e:
        click.echo(f"    Error in plateau detection: {e}")
        return {}

def _display_analysis_summary(results):
    """Display analysis summary table."""
    if results:
        df_results = pd.DataFrame(results)
        click.echo("\n" + "="*50)
        click.echo("ANALYSIS SUMMARY")
        click.echo("="*50)
        click.echo(df_results.to_string(index=False))
        
        summary_path = Path("analysis_summary.csv")
        df_results.to_csv(summary_path, index=False)
        click.echo(f"\nSummary saved to: {summary_path}")
