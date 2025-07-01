"""Pupitre-specific data operations with integrated format definition."""

from typing import List, Dict, Any, Union, Optional
import pandas as pd
import numpy as np
from pathlib import Path
from ..core.base_data import BaseData
from ..exceptions import DataFormatError

class PupitreData(BaseData):
    """Handles pupitre DataFrame operations with integrated format definition."""
    
    def __init__(self, filename: str, data: pd.DataFrame, metadata: Optional[Dict] = None):
        super().__init__(filename, "pupitre", metadata)
        self.data = data.copy()
        self._keys = self.data.columns.tolist()
        
        # NEW: Direct reference to format definition
        self.definition = self._load_format_definition()
    
    def _load_format_definition(self):
        """Load format definition from JSON config."""
        # Import here to avoid circular import
        from .registry import FormatDefinition
        
        config_path = Path(__file__).parent / "configs" / "pupitre.json"
        if config_path.exists():
            return FormatDefinition.load_from_file(config_path)
        else:
            # Fallback to registry
            from .registry import format_registry
            return format_registry.get_format_definition("pupitre")
    
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
    
    def get_data(self, key: Optional[Union[str, List[str]]] = None) -> pd.DataFrame:
        """Get data for specified keys."""
        if key is None:
            return self.data.copy()
        
        selected_keys = self.validate_keys(key)
        return self.data[selected_keys].copy()
    
    def add_data(self, key: str, data_input: Union[str, pd.Series, np.ndarray], **kwargs) -> None:
        """Add new calculated column."""
        if key in self._keys:
            print(f"Warning: Key {key} already exists in DataFrame, overwriting")
        
        try:
            if isinstance(data_input, str):
                self._add_formula(key, data_input)
            elif isinstance(data_input, (pd.Series, np.ndarray, list)):
                self._add_direct_data(key, data_input)
            else:
                raise DataFormatError(f"Unsupported data input type: {type(data_input)}")
            
            if key not in self._keys:
                self._keys.append(key)
                
        except Exception as e:
            raise DataFormatError(f"Failed to add data for key '{key}': {e}")
    
    def _add_formula(self, key: str, formula: str) -> None:
        """Add data using a pandas eval formula."""
        try:
            if '=' in formula:
                _, expression = formula.split('=', 1)
                expression = expression.strip()
            else:
                expression = formula
            
            self.data[key] = self.data.eval(expression)
            
        except Exception as e:
            try:
                if expression.strip() in self.data.columns:
                    self.data[key] = self.data[expression.strip()]
                else:
                    raise e
            except:
                raise DataFormatError(f"Failed to evaluate formula '{formula}': {e}")
    
    def _add_direct_data(self, key: str, data_input: Union[pd.Series, np.ndarray, list]) -> None:
        """Add data directly from Series, array, or list."""
        if isinstance(data_input, pd.Series):
            if len(data_input) != len(self.data):
                raise DataFormatError(f"Series length {len(data_input)} doesn't match DataFrame length {len(self.data)}")
            self.data[key] = data_input.values
        elif isinstance(data_input, (np.ndarray, list)):
            if len(data_input) != len(self.data):
                raise DataFormatError(f"Array length {len(data_input)} doesn't match DataFrame length {len(self.data)}")
            self.data[key] = data_input
        else:
            raise DataFormatError(f"Unsupported data type: {type(data_input)}")
    
    def remove_data(self, keys: List[str]) -> None:
        """Remove columns from DataFrame."""
        existing_keys = [key for key in keys if key in self._keys]
        if existing_keys:
            self.data.drop(existing_keys, axis=1, inplace=True)
            super().remove_data(existing_keys)
    
    def rename_data(self, columns: Dict[str, str]) -> None:
        """Rename columns in DataFrame."""
        self.data.rename(columns=columns, inplace=True)
        super().rename_data(columns)
        self._keys = self.data.columns.tolist()
    
    def convert_field_values(self, key: str, values: Union[List[float], np.ndarray, pd.Series], 
                           target_unit: str) -> Union[List[float], np.ndarray, pd.Series]:
        """Convert field values to target unit using integrated definition."""
        if not self.definition:
            return values
        
        field = self.definition.get_field(key)
        if not field:
            return values
        
        if isinstance(values, pd.Series):
            converted = field.convert_values(values.tolist(), target_unit, self.definition.ureg)
            return pd.Series(converted, index=values.index)
        elif isinstance(values, np.ndarray):
            converted = field.convert_values(values.tolist(), target_unit, self.definition.ureg)
            return np.array(converted)
        else:
            return field.convert_values(values, target_unit, self.definition.ureg)
    
    def get_compatible_units(self, key: str) -> List[str]:
        """Get list of compatible units for a field using integrated definition."""
        if self.definition:
            return self.definition.get_compatible_units(key)
        return []
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about the dataset."""
        info = super().get_info()
        info['metadata']['shape'] = self.data.shape
        info['metadata']['dtypes'] = self.data.dtypes.to_dict()
        info['metadata']['memory_usage'] = self.data.memory_usage(deep=True).sum()
        
        # Add field definition information
        if self.definition:
            info['field_info'] = {
                'format_name': self.definition.format_name,
                'total_fields_defined': len(self.definition.fields),
                'data_keys_count': len(self.keys),
                'config_metadata': self.definition.metadata
            }
        
        return info
