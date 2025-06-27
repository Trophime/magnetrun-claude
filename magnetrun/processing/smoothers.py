"""Signal smoothing operations."""

import numpy as np
from scipy.signal import savgol_filter

def savgol(y: np.ndarray, window: int, polyorder: int, deriv: int = 0) -> np.ndarray:
    """Apply Savitzky-Golay filter to data."""
    return savgol_filter(y, window, polyorder, deriv=deriv)

