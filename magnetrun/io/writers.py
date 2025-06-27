"""File writing utilities."""

from pathlib import Path
from typing import Union, List
import pandas as pd

from ..core.magnet_data import MagnetData

class DataWriter:
    """Utilities for writing data to various formats."""
    
    @staticmethod
    def to_csv(
        magnet_data: MagnetData, 
        filepath: Union[str, Path], 
        keys: List[str] = None,
        separator: str = '\t'
    ) -> None:
        """Write data to CSV format."""
        filepath = Path(filepath)
        
        if keys is None:
            data = magnet_data.get_data()
        else:
            data = magnet_data.get_data(keys)
        
        data.to_csv(filepath, sep=separator, index=False, header=True)
    
    @staticmethod
    def to_excel(
        magnet_data: MagnetData, 
        filepath: Union[str, Path], 
        keys: List[str] = None
    ) -> None:
        """Write data to Excel format."""
        filepath = Path(filepath)
        
        if keys is None:
            data = magnet_data.get_data()
        else:
            data = magnet_data.get_data(keys)
        
        data.to_excel(filepath, index=False)
