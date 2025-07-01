
"""Common utilities for CLI commands."""

import click
from pathlib import Path
from typing import Tuple
from ..core.magnet_data import MagnetData
from ..core.magnet_run import MagnetRun

def load_magnet_data(file_path: str, housing: str = "M9", site: str = "") -> Tuple[MagnetData, MagnetRun]:
    """Load magnet data with error handling."""
    magnet_data = MagnetData.from_file(file_path)
    magnet_run = MagnetRun(housing, site, magnet_data)
    return magnet_data, magnet_run

def add_time_column_if_needed(magnet_data: MagnetData, debug: bool = False) -> None:
    """Add time column if needed and available."""
    if hasattr(magnet_data, '_add_time_if_needed'):
        try:
            magnet_data._add_time_if_needed()
        except Exception as e:
            if debug:
                click.echo(f"  Could not add time column: {e}")

def handle_error(e: Exception, debug: bool = False, file_path: str = "") -> None:
    """Standardized error handling."""
    if file_path:
        click.echo(f"  Error processing {file_path}: {e}", err=True)
    else:
        click.echo(f"  Error: {e}", err=True)
    
    if debug:
        import traceback
        click.echo(traceback.format_exc(), err=True)
