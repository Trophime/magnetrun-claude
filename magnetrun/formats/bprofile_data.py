"""Bprofile-specific data operations with integrated format definition."""

from typing import List, Dict, Any, Union, Optional
import pandas as pd
import numpy as np
from pathlib import Path
from ..core.base_data import BaseData
from ..exceptions import DataFormatError

class BprofileData(BaseData):
    """Handles Bprofile CSV data operations with integrated format definition."""
    
    def __init__(self, filename: str, data: pd.DataFrame, metadata: Optional[Dict] = None):
        super().__init__(filename, "bprofile", metadata)
        self.data = data.copy()
        self._keys = self.data.columns.tolist()
        
        # NEW: Direct reference to format definition
        self.definition = self._load_format_definition()
    
    def _load_format_definition(self):
        """Load format definition from JSON config."""
        # Import here to avoid circular import
        from .registry import FormatDefinition
        
        config_path = Path(__file__).parent / "configs" / "bprofile.json"
        if config_path.exists():
            return FormatDefinition.load_from_file(config_path)
        else:
            # Fallback to registry
            from .registry import format_registry
            return format_registry.get_format_definition("bprofile")
    
    def get_field_info(self, key: str) -> tuple:
        """Get field information using integrated definition."""
        if self.definition:
            field = self.definition.get_field(key)
            if field:
                symbol = field.symbol
                unit = field.get_unit_object(self.definition.ureg)
                unit_string = field.format_unit(self.definition.ureg)
                return symbol, unit, unit_string
        
        # Fallback for unknown fields
        return key, None, ""
    
    def get_field_label(self, key: str, show_unit: bool = True) -> str:
        """Get formatted label for plotting using integrated definition."""
        if self.definition:
            field = self.definition.get_field(key)
            if field:
                return field.get_label(self.definition.ureg, show_unit)
        return key
