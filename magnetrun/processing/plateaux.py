"""Plateau detection utilities."""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
import matplotlib.pyplot as plt

def nplateaus(
    magnet_data,
    xField: Tuple[str, str, str],
    yField: Tuple[str, str, str], 
    threshold: float = 1e-3,
    num_points_threshold: int = 100,
    save: bool = False,
    show: bool = False,
    verbose: bool = False
) -> List[Dict[str, Any]]:
    """
    Detect plateaus in magnetic field data.
    
    Args:
        magnet_data: MagnetData object
        xField: Tuple of (key, symbol, unit) for x-axis
        yField: Tuple of (key, symbol, unit) for y-axis
        threshold: Threshold for plateau detection
        num_points_threshold: Minimum number of points for a plateau
        save: Whether to save plots
        show: Whether to show plots
        verbose: Enable verbose output
    
    Returns:
        List of plateau dictionaries with start, end, value, duration
    """
    x_key, x_symbol, x_unit = xField
    y_key, y_symbol, y_unit = yField
    
    # Get data
    try:
        data = magnet_data.get_data([x_key, y_key])
    except:
        # Handle TDMS format
        if "/" in y_key:
            data = magnet_data.get_data([y_key])
            # Add time column for TDMS
            group, channel = y_key.split("/")
            if magnet_data.data_type == 1:
                dt = magnet_data.groups[group][channel]["wf_increment"]
                t_offset = magnet_data.groups[group][channel].get("wf_start_offset", 0)
                data[x_key] = data.index * dt + t_offset
        else:
            raise
    
    plateaus = []
    
    if len(data) < num_points_threshold:
        return plateaus
    
    # Simple plateau detection algorithm
    y_values = data[y_key].values
    x_values = data[x_key].values
    
    # Calculate rolling standard deviation
    window_size = min(num_points_threshold, len(y_values) // 10)
    rolling_std = pd.Series(y_values).rolling(window=window_size, center=True).std()
    
    # Find regions where std is below threshold
    plateau_mask = rolling_std < threshold
    
    # Find continuous regions
    diff = np.diff(np.concatenate(([False], plateau_mask, [False])).astype(int))
    starts = np.where(diff == 1)[0]
    ends = np.where(diff == -1)[0]
    
    for start, end in zip(starts, ends):
        if end - start >= num_points_threshold:
            plateau_start = x_values[start]
            plateau_end = x_values[end-1]
            plateau_value = np.mean(y_values[start:end])
            
            plateaus.append({
                'start': plateau_start,
                'end': plateau_end,
                'value': plateau_value,
                'duration': plateau_end - plateau_start
            })
    
    # Plotting
    if show or save:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        # Plot original data
        ax1.plot(x_values, y_values, 'b-', alpha=0.7, label=f'{y_symbol}')
        ax1.set_ylabel(f'{y_symbol} [{y_unit}]')
        ax1.grid(True)
        ax1.legend()
        
        # Highlight plateaus
        for plateau in plateaus:
            ax1.axvspan(plateau['start'], plateau['end'], alpha=0.3, color='red')
        
        # Plot rolling std
        ax2.plot(x_values, rolling_std, 'g-', label='Rolling Std')
        ax2.axhline(y=threshold, color='r', linestyle='--', label=f'Threshold ({threshold})')
        ax2.set_xlabel(f'{x_symbol} [{x_unit}]')
        ax2.set_ylabel('Rolling Std')
        ax2.grid(True)
        ax2.legend()
        
        plt.tight_layout()
        
        if save:
            filename = f"{magnet_data.filename}_{y_key.replace('/', '_')}_plateaus.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()
    
    return plateaus
