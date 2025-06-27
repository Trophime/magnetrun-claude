"""Plotting utilities for magnetic data."""

import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from typing import Optional, List
import pandas as pd

from ..core.magnet_data import MagnetData

matplotlib.rcParams["text.usetex"] = True

class DataPlotter:
    """Handles plotting operations for magnetic data."""
    
    @staticmethod
    def plot_time_series(
        magnet_data: MagnetData,
        y_keys: List[str],
        x_key: str = 't',
        normalize: bool = False,
        ax: Optional[plt.Axes] = None,
        show_grid: bool = True
    ) -> plt.Axes:
        """Plot time series data."""
        if ax is None:
            ax = plt.gca()
        
        for y_key in y_keys:
            DataPlotter._plot_single_series(
                magnet_data, x_key, y_key, ax, normalize, show_grid
            )
        
        return ax
    
    @staticmethod
    def _plot_single_series(
        magnet_data: MagnetData,
        x_key: str,
        y_key: str,
        ax: plt.Axes,
        normalize: bool,
        show_grid: bool
    ) -> None:
        """Plot a single data series."""
        # Get data
        data = magnet_data.get_data([x_key, y_key])
        
        # Get units
        y_symbol, y_unit = magnet_data.get_unit_key(y_key)
        x_symbol, x_unit = magnet_data.get_unit_key(x_key)
        
        # Normalize if requested
        if normalize:
            y_max = abs(data[y_key].max())
            data = data.copy()
            data[y_key] /= y_max
            label = f"{y_key} (norm with {y_max:.3e} {y_unit:~P})"
        else:
            label = y_key
        
        # Plot
        data.plot(x=x_key, y=y_key, ax=ax, label=label, grid=show_grid)
        
        # Set labels
        if y_unit is not None:
            if normalize:
                ax.set_ylabel("normalized")
            else:
                ax.set_ylabel(f"{y_symbol} [{y_unit:~P}]")
        
        if x_unit is not None:
            ax.set_xlabel(f"{x_symbol} [{x_unit:~P}]")
    
    @staticmethod
    def plot_xy(
        magnet_data: MagnetData,
        x_key: str,
        y_key: str,
        ax: Optional[plt.Axes] = None,
        **plot_kwargs
    ) -> plt.Axes:
        """Plot X vs Y data."""
        if ax is None:
            ax = plt.gca()
        
        # Get data
        data = magnet_data.get_data([x_key, y_key])
        
        # Get units
        y_symbol, y_unit = magnet_data.get_unit_key(y_key)
        x_symbol, x_unit = magnet_data.get_unit_key(x_key)
        
        # Plot
        data.plot(x=x_key, y=y_key, ax=ax, **plot_kwargs)
        
        # Set labels
        if y_unit is not None:
            ax.set_ylabel(f"{y_symbol} [{y_unit:~P}]")
        if x_unit is not None:
            ax.set_xlabel(f"{x_symbol} [{x_unit:~P}]")
        
        return ax
