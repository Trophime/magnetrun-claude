"""Pytest configuration and shared fixtures."""

import pytest
import pandas as pd
import numpy as np

@pytest.fixture
def simple_dataframe():
    """Simple DataFrame for basic testing."""
    return pd.DataFrame({
        't': [0, 1, 2, 3, 4],
        'Field': [0.0, 1.0, 2.0, 1.5, 0.5],
        'Current': [0, 10, 20, 15, 5]
    })

@pytest.fixture
def complex_dataframe():
    """More complex DataFrame for advanced testing."""
    np.random.seed(42)  # For reproducible tests
    n_points = 1000
    t = np.linspace(0, 100, n_points)
    
    # Simulate magnetic field ramp
    field = np.where(t < 20, 0, 
                    np.where(t < 40, (t-20)/20 * 2.0,
                            np.where(t < 80, 2.0, 
                                   2.0 - (t-80)/20 * 2.0)))
    
    # Add some noise
    field += 0.01 * np.random.randn(n_points)
    
    return pd.DataFrame({
        't': t,
        'Field': field,
        'Icoil1': field * 100 + np.random.randn(n_points),
        'Ucoil1': field * 10 + 0.1 * np.random.randn(n_points),
        'FlowH': 2.5 + 0.1 * np.random.randn(n_points),
        'TinH': 20 + np.random.randn(n_points)
    })
