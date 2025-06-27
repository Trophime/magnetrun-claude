"""MagnetRun class for high-level data operations."""

from typing import Optional
import pandas as pd

from .magnet_data import MagnetData
from ..config.housing_configs import HOUSING_CONFIGS, HousingConfig
from ..exceptions import DataFormatError

class MagnetRun:
    """High-level interface for magnet run data analysis."""
    
    def __init__(self, housing: str, site: str, data: Optional[MagnetData] = None):
        self.housing = housing
        self.site = site
        self.magnet_data = data
        self._housing_config = HOUSING_CONFIGS.get(housing)
    
    @property
    def housing_config(self) -> Optional[HousingConfig]:
        """Get housing configuration."""
        return self._housing_config
    
    def get_data(self, key: Optional[str] = None) -> pd.DataFrame:
        """Get data from MagnetData."""
        if self.magnet_data is None:
            raise DataFormatError("No MagnetData associated")
        return self.magnet_data.get_data(key)
    
    def get_keys(self) -> list:
        """Get available data keys."""
        if self.magnet_data is None:
            raise DataFormatError("No MagnetData associated")
        return self.magnet_data.keys
    
    def prepare_data(self, debug: bool = False) -> None:
        """Prepare data according to housing configuration."""
        if self.magnet_data is None or self._housing_config is None:
            return
        
        # Add reference calculations
        if self._housing_config.ih_ref_channels:
            formula = self._housing_config.get_ih_formula()
            self.magnet_data.add_data("IH_ref", formula)
        
        if self._housing_config.ib_ref_channels:
            formula = self._housing_config.get_ib_formula()
            self.magnet_data.add_data("IB_ref", formula)
        
        # Apply field mappings
        if self._housing_config.field_mappings:
            self.magnet_data.rename_data(self._housing_config.field_mappings)
        
        # Remove specified channels
        if self._housing_config.remove_channels:
            self.magnet_data.remove_data(self._housing_config.remove_channels)
