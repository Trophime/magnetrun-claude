"""Time-related data operations."""

import numpy as np
import pandas as pd
from datetime import datetime
from ..core.magnet_data import MagnetData
from ..exceptions import DataFormatError

class TimeProcessor:
    """Handles time-related operations on magnetic data."""
    
    @staticmethod
    def add_time_column(magnet_data: MagnetData) -> None:
        """Add time column to pandas data."""
        if magnet_data.data_type != 0:
            raise DataFormatError("add_time_column only works with pandas data")
        
        data = magnet_data.get_data()
        keys = magnet_data.keys
        
        if "Date" not in keys or "Time" not in keys:
            raise DataFormatError("Cannot add time column: no Date or Time columns")
        
        try:
            # Convert Date column
            data["Date"] = pd.to_datetime(data.Date, cache=True, format="%Y.%m.%d")
        except Exception:
            raise DataFormatError(f"Failed to convert Date column in {magnet_data.filename}")
        
        try:
            # Convert Time column
            data["Time"] = pd.to_timedelta(data.Time)
        except Exception:
            raise DataFormatError(f"Failed to convert Time column in {magnet_data.filename}")
        
        try:
            # Create timestamp
            data["timestamp"] = data.Date + data.Time
        except Exception:
            raise DataFormatError(f"Failed to create timestamp column in {magnet_data.filename}")
        
        # Set reference time
        t0 = data.iloc[0]["timestamp"]
        
        # Remove duplicates
        data = TimeProcessor._find_and_remove_duplicates(data, magnet_data.filename)
        
        # Create relative time column
        data["t"] = data.apply(lambda row: (row.timestamp - t0).total_seconds(), axis=1)
        
        # Validate time intervals
        TimeProcessor._validate_time_intervals(data, magnet_data.filename)
        
        # Clean up original Date and Time columns
        data.drop(["Date", "Time"], axis=1, inplace=True)
        
        # Update magnet_data
        magnet_data._data_handler.data = data
        magnet_data._data_handler.keys = data.columns.values.tolist()
    
    @staticmethod
    def _find_and_remove_duplicates(data: pd.DataFrame, filename: str) -> pd.DataFrame:
        """Find and remove duplicate timestamps."""
        # This is a placeholder - implement actual duplicate removal logic
        duplicates = data.duplicated(subset=['timestamp'])
        if duplicates.any():
            print(f"Warning: Found {duplicates.sum()} duplicate timestamps in {filename}")
            data = data.drop_duplicates(subset=['timestamp'])
        return data
    
    @staticmethod
    def _validate_time_intervals(data: pd.DataFrame, filename: str) -> None:
        """Validate that time intervals are consistent."""
        times = data["t"].to_numpy()
        dt = np.diff(times)
        
        if dt.min() != dt.max():
            print(f"Warning: Inconsistent time intervals in {filename}: {dt.min()} to {dt.max()}")
