"""Pandas-specific data operations."""

from typing import List, Dict, Any, Union, Optional
import pandas as pd
import numpy as np
from scipy import stats
from natsort import natsorted
import re

from .base_data import BaseData
from .units import UnitManager
from ..exceptions import DataFormatError

class PandasData(BaseData):
    """Handles pandas DataFrame operations for MagnetRun data."""
    
    def __init__(self, filename: str, keys: List[str], data: pd.DataFrame):
        super().__init__(filename, {}, keys, 0)
        self.data = data
        self.unit_manager = UnitManager()
        self._setup_units()
    
    def _setup_units(self) -> None:
        """Set up units for all keys."""
        for key in self.keys:
            self.units[key] = self.unit_manager.infer_units_from_key(key)
    
    def get_data(self, key: Optional[Union[str, List[str]]] = None) -> pd.DataFrame:
        """Get data for specified keys."""
        if key is None:
            return self.data
        
        selected_keys = self.validate_keys(key)
        return self.data[selected_keys]
    
    def add_data(self, key: str, formula: str, unit: Optional[str] = None) -> None:
        """Add new calculated column using pandas eval."""
        if key in self.keys:
            print(f"Key {key} already exists in DataFrame")
            return
        
        try:
            self.data.eval(formula, inplace=True)
            self.keys.append(key)
            
            if unit:
                self.units[key] = unit
            else:
                self.units[key] = self.unit_manager.infer_units_from_key(key)
                
        except Exception as e:
            raise DataFormatError(f"Failed to add data with formula '{formula}': {e}")
    
    def remove_data(self, keys: List[str]) -> None:
        """Remove columns from DataFrame."""
        existing_keys = [key for key in keys if key in self.keys]
        if existing_keys:
            self.data.drop(existing_keys, axis=1, inplace=True)
            super().remove_data(existing_keys)
    
    def rename_data(self, columns: Dict[str, str]) -> None:
        """Rename columns in DataFrame."""
        self.data.rename(columns=columns, inplace=True)
        super().rename_data(columns)
        self.keys = self.data.columns.values.tolist()
