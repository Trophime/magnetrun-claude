"""Main MagnetData class using composition pattern."""

from typing import List, Dict, Any, Union, Optional, Tuple
import pandas as pd
import numpy as np
from pathlib import Path

from .pandas_data import PandasData
from .tdms_data import TdmsData
from .units import UnitManager
from ..exceptions import DataFormatError, FileFormatError

class MagnetData:
    """Main class for handling magnetic measurement data."""
    
    def __init__(self, data_handler: Union[PandasData, TdmsData]):
        self._data_handler = data_handler
        self.unit_manager = UnitManager()
    
    @classmethod
    def from_pandas(cls, filename: str, data: pd.DataFrame) -> 'MagnetData':
        """Create MagnetData from pandas DataFrame."""
        keys = data.columns.values.tolist()
        handler = PandasData(filename, keys, data)
        return cls(handler)
    
    @classmethod
    def from_dict(cls, filename: str, groups: Dict, keys: List[str], data: Dict) -> 'MagnetData':
        """Create MagnetData from TDMS dict structure."""
        handler = TdmsData(filename, groups, keys, data)
        return cls(handler)
    
    # Delegate properties and methods to handler
    @property
    def filename(self) -> str:
        return self._data_handler.filename
    
    @property
    def keys(self) -> List[str]:
        return self._data_handler.keys
    
    @property
    def data_type(self) -> int:
        return self._data_handler.data_type
    
    @property
    def units(self) -> Dict[str, tuple]:
        return self._data_handler.units
    
    def get_data(self, key: Optional[Union[str, List[str]]] = None) -> pd.DataFrame:
        """Get data for specified keys."""
        return self._data_handler.get_data(key)
    
    def add_data(self, key: str, formula: str, unit: Optional[str] = None) -> None:
        """Add calculated column."""
        self._data_handler.add_data(key, formula, unit)
    
    def remove_data(self, keys: List[str]) -> None:
        """Remove columns."""
        self._data_handler.remove_data(keys)
    
    def rename_data(self, columns: Dict[str, str]) -> None:
        """Rename columns."""
        self._data_handler.rename_data(columns)
    
    def get_unit_key(self, key: str) -> Tuple[str, Any]:
        """Get unit information for a key."""
        if key not in self.keys:
            return self.unit_manager.infer_units_from_key(key)
        
        return self.units.get(key, ("", None))
