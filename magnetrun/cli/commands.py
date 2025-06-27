"""Command-line interface using Click."""

import click
from pathlib import Path
from typing import List

from ..io.readers import DataReader
from ..io.writers import DataWriter
from ..processing.analysis import DataAnalyzer
from ..processing.cleaning import DataCleaner
from ..processing.time_operations import TimeProcessor
from ..visualization.plotters import DataPlotter

@click.group()
@click.version_option()
def cli():
    """MagnetRun - A tool for analyzing magnetic measurement data."""
    pass

@cli.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True))
@click.option('--housing', default='M9', help='Housing type (M8, M9, M10)')
@click.option('--site', default='', help='Site identifier')
@click.option('--list-keys', is_flag=True, help='List available data keys')
@click.option('--convert', is_flag=True, help='Convert to CSV format')
def info(files, housing, site, list_keys, convert):
    """Display information about data files."""
    for file_path in files:
        click.echo(f"Processing: {file_path}")
        
        try:
            magnet_run = DataReader.read_file(file_path, housing, site)
            
            click.echo(f"  Housing: {magnet_run.housing}")
            click.echo(f"  Site: {magnet_run.site}")
            click.echo(f"  Data type: {magnet_run.magnet_data.data_type}")
            click.echo(f"  Keys count: {len(magnet_run.get_keys())}")
            
            if list_keys:
                click.echo("  Available keys:")
                for key in magnet_run.get_keys():
                    click.echo(f"    {key}")
            
            if convert:
                output_path = Path(file_path).with_suffix('.csv')
                DataWriter.to_csv(magnet_run.magnet_data, output_path)
                click.echo(f"  Converted to: {output_path}")
                
        except Exception as e:
            click.echo(f"  Error: {e}", err=True)

@cli.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True))
@click.option('--housing', default='M9', help='Housing type')
@click.option('--keys', multiple=True, help='Keys to analyze')
@click.option('--plateaus', is_flag=True, help='Detect plateaus')
@click.option('--peaks', is_flag=True, help='Find peaks')
@click.option('--breakpoints', is_flag=True, help='Detect breakpoints')
@click.option('--threshold', default=1e-3, help='Threshold for analysis')
@click.option('--save', is_flag=True, help='Save results to file')
def analyze(files, housing, keys, plateaus, peaks, breakpoints, threshold, save):
    """Perform statistical analysis on data."""
    for file_path in files:
        click.echo(f"Analyzing: {file_path}")
        
        try:
            magnet_run = DataReader.read_file(file_path, housing)
            
            # Add time column if needed
            if magnet_run.magnet_data.data_type == 0:
                try:
                    TimeProcessor.add_time_column(magnet_run.magnet_data)
                except Exception as e:
                    click.echo(f"  Could not add time column: {e}")
            
            analysis_keys = keys if keys else ['Field']
            
            for key in analysis_keys:
                if key not in magnet_run.get_keys():
                    click.echo(f"  Warning: Key '{key}' not found")
                    continue
                
                click.echo(f"  Analyzing key: {key}")
                
                if plateaus:
                    result = DataAnalyzer.detect_plateaus(
                        magnet_run.magnet_data, key, threshold
                    )
                    click.echo(f"    Found {len(result)} plateaus")
                
                if peaks:
                    peaks_result, _ = DataAnalyzer.find_peaks_in_data(
                        magnet_run.magnet_data, key
                    )
                    click.echo(f"    Found {len(peaks_result)} peaks")
                
                if breakpoints:
                    bp_result = DataAnalyzer.detect_breakpoints(
                        magnet_run.magnet_data, key
                    )
                    click.echo(f"    Found {len(bp_result['peaks'])} breakpoints")
                
        except Exception as e:
            click.echo(f"  Error: {e}", err=True)

@cli.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True))
@click.option('--housing', default='M9', help='Housing type')
@click.option('--keys', multiple=True, help='Keys to plot')
@click.option('--x-key', default='t', help='X-axis key')
@click.option('--normalize', is_flag=True, help='Normalize data')
@click.option('--save', is_flag=True, help='Save plots')
@click.option('--output-dir', type=click.Path(), help='Output directory for plots')
def plot(files, housing, keys, x_key, normalize, save, output_dir):
    """Generate plots from data."""
    import matplotlib.pyplot as plt
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
    
    for file_path in files:
        click.echo(f"Plotting: {file_path}")
        
        try:
            magnet_run = DataReader.read_file(file_path, housing)
            
            # Add time column if needed
            if magnet_run.magnet_data.data_type == 0:
                try:
                    TimeProcessor.add_time_column(magnet_run.magnet_data)
                except Exception:
                    pass  # Continue without time column
            
            plot_keys = list(keys) if keys else ['Field']
            available_keys = [k for k in plot_keys if k in magnet_run.get_keys()]
            
            if not available_keys:
                click.echo("  No valid keys found for plotting")
                continue
            
            # Create plot
            fig, ax = plt.subplots(figsize=(12, 8))
            
            DataPlotter.plot_time_series(
                magnet_run.magnet_data,
                available_keys,
                x_key,
                normalize,
                ax
            )
            
            ax.set_title(f"{Path(file_path).stem}")
            ax.legend()
            
            if save:
                if output_dir:
                    output_path = output_dir / f"{Path(file_path).stem}_plot.png"
                else:
                    output_path = Path(file_path).with_suffix('.png')
                
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                click.echo(f"  Saved plot: {output_path}")
            else:
                plt.show()
            
            plt.close()
            
        except Exception as e:
            click.echo(f"  Error: {e}", err=True)

if __name__ == '__main__':
    cli()
