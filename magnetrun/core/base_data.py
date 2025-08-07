"""Refactored base class for magnetic data handling with shared implementations."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union, Optional
import numpy as np
import pandas as pd
from ..exceptions import KeyNotFoundError, DataFormatError


# Integration with BaseData classes
class BaseData(ABC):
    """Updated BaseData that uses centralized config system."""

    def __init__(
        self, filename: str, format_type: str, metadata: Optional[Dict] = None
    ):
        self.filename = filename
        self.format_type = format_type
        self.metadata = metadata or {}
        self._keys: List[str] = []

        # Load format definition using centralized config
        self.definition = self._load_format_definition()

    def _load_format_definition(self):
        """Load format definition using centralized configuration system."""
        from ..formats.centralized_config import get_config_manager

        config_manager = get_config_manager()

        # Try to load from centralized config first
        config_data = config_manager.load_config("format", self.format_type)
        if config_data:
            try:
                from ..formats.format_definition import FormatDefinition

                return FormatDefinition.from_dict(config_data)
            except Exception as e:
                print(
                    f"Warning: Failed to load format definition for '{self.format_type}': {e}"
                )

        # Fallback to format registry
        from ..formats.registry import format_registry

        return format_registry.get_format_definition(self.format_type)

    @property
    def keys(self) -> List[str]:
        """Get available data keys."""
        return self._keys.copy()

    @abstractmethod
    def get_data(self, key: Optional[Union[str, List[str]]] = None) -> pd.DataFrame:
        """Get data for specified keys - must be implemented by subclasses."""
        pass

    def validate_keys(self, keys: Union[str, List[str]]) -> List[str]:
        """Validate that keys exist in the dataset - shared implementation."""
        if isinstance(keys, str):
            keys = [keys]

        invalid_keys = [k for k in keys if k not in self.keys]
        if invalid_keys:
            raise KeyNotFoundError(f"Keys not found: {invalid_keys}")

        return keys

    def remove_data(self, keys: List[str]) -> None:
        """Remove columns from data - shared implementation."""
        existing_keys = [k for k in keys if k in self._keys]
        for key in existing_keys:
            self._keys.remove(key)

    def rename_data(self, columns: Dict[str, str]) -> None:
        """Rename columns in data - shared implementation."""
        for old_key, new_key in columns.items():
            if old_key in self._keys:
                idx = self._keys.index(old_key)
                self._keys[idx] = new_key

    def get_info(self) -> Dict[str, Any]:
        """Get information about the dataset - shared base implementation."""
        info = {
            "filename": self.filename,
            "format_type": self.format_type,
            "num_keys": len(self.keys),
            "keys": self.keys,
            "metadata": self.metadata,
        }

        # Add field definition information if available
        if self.definition:
            info["field_info"] = {
                "format_name": self.definition.format_name,
                "total_fields_defined": len(self.definition.fields),
                "data_keys_count": len(self.keys),
                "config_metadata": self.definition.metadata,
            }

        return info

    def get_field_info(self, key: str) -> tuple:
        """Get field information using integrated definition - shared implementation."""
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
        """Get formatted label for plotting using integrated definition - shared implementation."""
        if self.definition:
            field = self.definition.get_field(key)
            if field:
                return field.get_label(self.definition.ureg, show_unit)
        return key

    def convert_field_values(
        self,
        key: str,
        values: Union[List[float], np.ndarray, pd.Series],
        target_unit: str,
    ) -> Union[List[float], np.ndarray, pd.Series]:
        """Convert field values to target unit using integrated definition - shared implementation."""
        if not self.definition:
            return values

        field = self.definition.get_field(key)
        if not field:
            return values

        if isinstance(values, pd.Series):
            converted = field.convert_values(
                values.tolist(), target_unit, self.definition.ureg
            )
            return pd.Series(converted, index=values.index)
        elif isinstance(values, np.ndarray):
            converted = field.convert_values(
                values.tolist(), target_unit, self.definition.ureg
            )
            return np.array(converted)
        else:
            return field.convert_values(values, target_unit, self.definition.ureg)

    # Abstract method for format-specific data addition
    @abstractmethod
    def add_data(
        self, key: str, data_input: Union[str, pd.Series, np.ndarray], **kwargs
    ) -> None:
        """Add new calculated column - must be implemented by subclasses."""
        pass

    # Abstract method for format-specific data storage access
    @abstractmethod
    def _get_underlying_data(self) -> Any:
        """Get the underlying data structure - must be implemented by subclasses."""
        pass


