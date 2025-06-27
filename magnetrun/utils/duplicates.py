"""Utilities for handling duplicate data."""

import pandas as pd
import numpy as np

def find_duplicates(data: pd.DataFrame, filename: str, time_column: str) -> pd.DataFrame:
    """Find and handle duplicate timestamps in data."""
    # Check for duplicates
    duplicates = data.duplicated(subset=[time_column])
    
    if duplicates.any():
        print(f"Warning: Found {duplicates.sum()} duplicate timestamps in {filename}")
        # Remove duplicates, keeping first occurrence
        data = data.drop_duplicates(subset=[time_column], keep='first')
    
    return data
