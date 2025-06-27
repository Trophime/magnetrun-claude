"""Base data handling for MagnetRun."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union, Optional
import pandas as pd
from ..exceptions import KeyNotFoundError

class BaseData(ABC):
    """Abstract base class for magnetic data handling."""
    
    def __init__(self, filename: str, groups: Dict, keys: List[str], data_type: int):
        self.filename = filename
        self.groups = groups
        self.keys = keys
        self.data_type = data_type
        self.units: Dict[str, tuple] = {}
    
    @abstractmethod
    def get_data(self, key: Optional[Union[str, List[str]]] = None) -> pd.DataFrame:
        """Get data for specified keys."""
        pass
    
    @abstractmethod
    def add_data(self, key: str, formula: str, unit: Optional[str] = None) -> None:
        """Add new calculated column."""
        pass
    
    def validate_keys(self, keys: Union[str, List[str]]) -> List[str]:
        """Validate that keys exist in the dataset."""
        if isinstance(keys, str):
            keys = [keys]
        
        invalid_keys = [k for k in keys if k not in self.keys]
        if invalid_keys:
            raise KeyNotFoundError(f"Keys not found: {invalid_keys}")
        
        return keys
    
    def remove_data(self, keys: List[str]) -> None:
        """Remove columns from data."""
        for key in keys:
            if key in self.keys:
                self.keys.remove(key)
    
    def rename_data(self, columns: Dict[str, str]) -> None:
        """Rename columns in data."""
        for old_key, new_key in columns.items():
            if old_key in self.keys:
                idx = self.keys.index(old_key)
                self.keys[idx] = new_key
