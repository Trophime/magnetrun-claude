"""Specialized plotting for breakpoint detection."""

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from typing import Dict, Any, List
import pandas as pd

def plot_breakpoints(
    file: str,
    channel: str,
    symbol: str,
    unit: str,
    ts: pd.Series,
    smoothed: np.ndarray,
    smoothed_der1: np.ndarray,
    smoothed_der2: np.ndarray,
    quantiles_der: float,
    peaks: np.ndarray,
    ignore_peaks: List[int],
    anomalies: List[int],
    level: int,
    save: bool = False,
    show: bool = False
) -> None:
    """
    Plot breakpoint detection results.
    
    Args:
        file: Filename for plot title and saving
        channel: Channel name
        symbol: Symbol for y-axis label
        unit: Unit for y-axis label
        ts: Time series data
        smoothed: Smoothed data
        smoothed_der1: First derivative of smoothed data
        smoothed_der2: Second derivative of smoothed data
        quantiles_der: Quantile threshold for derivative
        peaks: Detected peak indices
        ignore_peaks: Peak indices to ignore
        anomalies: Anomaly indices
        level: Percentile level used
        save: Whether to save the plot
        show: Whether to show the plot
    """
    fig = plt.figure(figsize=(16, 12))
    gs = gridspec.GridSpec(3, 1, height_ratios=[2, 1, 1])
    
    # Main data plot
    ax0 = plt.subplot(gs[0])
    t_values = np.arange(len(ts))
    ax0.plot(t_values, ts.values, label=channel, color="blue", marker="o", 
             linestyle="None", markersize=2, alpha=0.6)
    ax0.plot(t_values, smoothed, label="smoothed", color="red", linewidth=2)
    
    # Mark peaks
    if peaks.shape[0]:
        ax0.plot(peaks, smoothed[peaks], "go", markersize=8, label="peaks")
    
    if ignore_peaks:
        ax0.plot(ignore_peaks, smoothed[ignore_peaks], "yo", markersize=8, 
                label="ignored peaks")
    
    if anomalies:
        ax0.plot(anomalies, smoothed[anomalies], "ro", markersize=10, 
                label="anomalies", markeredgecolor='black')
    
    ax0.legend()
    ax0.grid(True, alpha=0.3)
    ax0.set_ylabel(f"{symbol} [{unit:~P}]")
    ax0.set_title(f"{file}: {channel} - Breakpoint Detection")
    
    # Second derivative plot
    ax1 = plt.subplot(gs[1], sharex=ax0)
    ax1.plot(t_values, np.abs(smoothed_der2), label="abs(2nd derivative)", color="red")
    ax1.axhline(y=quantiles_der, color='purple', linestyle='--', linewidth=2,
               label=f'{level}% threshold: {quantiles_der:.3e}')
    
    if peaks.shape[0]:
        ax1.plot(peaks, np.abs(smoothed_der2[peaks]), "go", markersize=8, label="peaks")
    
    if ignore_peaks:
        ax1.plot(ignore_peaks, np.abs(smoothed_der2[ignore_peaks]), "yo", 
                markersize=8, label="ignored peaks")
    
    if anomalies:
        ax1.plot(anomalies, np.abs(smoothed_der2[anomalies]), "ro", markersize=10, 
                label="anomalies", markeredgecolor='black')
    
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_ylabel("abs(2nd derivative)")
    ax1.set_title(f"Savitzky-Golay Filter [2nd order derivative] ({level}% threshold)")
    ax1.set_yscale('log')
    
    # Rolling standard deviation plot
    ax2 = plt.subplot(gs[2], sharex=ax0)
    window_size = min(50, len(ts) // 10)  # Adaptive window size
    rolling_std = pd.Series(ts.values).rolling(window=window_size, center=True).std()
    ax2.plot(t_values, rolling_std.values, label="rolling std", color="blue")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xlabel("Sample Index")
    ax2.set_ylabel("Rolling Std")
    ax2.set_title(f"Rolling Standard Deviation (window={window_size})")
    
    plt.tight_layout()
    
    if save:
        import os
        f_extension = os.path.splitext(file)[-1]
        output_path = f'{file.replace(f_extension, "")}-{channel}-detect_bkpts.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved breakpoint plot: {output_path}")
    
    if show:
        plt.show()
    
    if not show:
        plt.close()

def plot_breakpoint_comparison(
    file: str,
    channels: List[str],
    breakpoint_results: Dict[str, Dict[str, Any]],
    save: bool = False,
    show: bool = False
) -> None:
    """
    Compare breakpoint detection results across multiple channels.
    
    Args:
        file: Filename for plot title and saving
        channels: List of channel names
        breakpoint_results: Dictionary of breakpoint results per channel
        save: Whether to save the plot
        show: Whether to show the plot
    """
    n_channels = len(channels)
    fig, axes = plt.subplots(n_channels, 1, figsize=(14, 4*n_channels), sharex=True)
    
    if n_channels == 1:
        axes = [axes]
    
    for i, channel in enumerate(channels):
        if channel not in breakpoint_results:
            continue
        
        result = breakpoint_results[channel]
        ax = axes[i]
        
        # Plot smoothed data
        t_values = np.arange(len(result['smoothed']))
        ax.plot(t_values, result['smoothed'], 'b-', label='Smoothed', linewidth=1.5)
        
        # Mark breakpoints
        if len(result['peaks']) > 0:
            ax.plot(result['peaks'], result['smoothed'][result['peaks']], 
                   'ro', markersize=6, label=f"Breakpoints ({len(result['peaks'])})")
        
        ax.set_ylabel(f"{channel}")
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_title(f"{channel} - {len(result['peaks'])} breakpoints detected")
    
    axes[-1].set_xlabel("Sample Index")
    plt.suptitle(f"{file} - Breakpoint Detection Comparison", fontsize=14)
    plt.tight_layout()
    
    if save:
        import os
        f_extension = os.path.splitext(file)[-1]
        output_path = f'{file.replace(f_extension, "")}-breakpoint_comparison.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved comparison plot: {output_path}")
    
    if show:
        plt.show()
    
    if not show:
        plt.close()

if __name__ == '__main__':
    cli()

if __name__ == '__main__':
    cli()
