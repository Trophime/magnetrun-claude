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

    def get_compatible_units(self, key: str) -> List[str]:
        """Get list of compatible units for a field using integrated definition - shared implementation."""
        if self.definition:
            return self.definition.get_compatible_units(key)
        return []

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


class PandasBasedData(BaseData):
    """Base class for data formats that use pandas DataFrames."""

    def __init__(
        self,
        filename: str,
        format_type: str,
        data: pd.DataFrame,
        metadata: Optional[Dict] = None,
    ):
        super().__init__(filename, format_type, metadata)
        self.data = data.copy()
        self._keys = self.data.columns.tolist()

    def get_data(self, key: Optional[Union[str, List[str]]] = None) -> pd.DataFrame:
        """Get data for specified keys - shared pandas implementation."""
        if key is None:
            return self.data.copy()

        selected_keys = self.validate_keys(key)
        return self.data[selected_keys].copy()

    def _get_underlying_data(self) -> pd.DataFrame:
        """Get the underlying DataFrame."""
        return self.data

    def add_data(
        self, key: str, data_input: Union[str, pd.Series, np.ndarray], **kwargs
    ) -> None:
        """Add new calculated column - shared pandas implementation."""
        if key in self._keys:
            print(f"Warning: Key {key} already exists in DataFrame, overwriting")

        try:
            if isinstance(data_input, str):
                self._add_formula(key, data_input)
            elif isinstance(data_input, (pd.Series, np.ndarray, list)):
                self._add_direct_data(key, data_input)
            else:
                raise DataFormatError(
                    f"Unsupported data input type: {type(data_input)}"
                )

            if key not in self._keys:
                self._keys.append(key)

        except Exception as e:
            raise DataFormatError(f"Failed to add data for key '{key}': {e}")

    def _add_formula(self, key: str, formula: str) -> None:
        """Add data using a pandas eval formula - shared implementation."""
        try:
            if "=" in formula:
                _, expression = formula.split("=", 1)
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
            except Exception as e:
                raise DataFormatError(f"Failed to evaluate formula '{formula}': {e}")

    def _add_direct_data(
        self, key: str, data_input: Union[pd.Series, np.ndarray, list]
    ) -> None:
        """Add data directly from Series, array, or list - shared implementation."""
        if isinstance(data_input, pd.Series):
            if len(data_input) != len(self.data):
                raise DataFormatError(
                    f"Series length {len(data_input)} doesn't match DataFrame length {len(self.data)}"
                )
            self.data[key] = data_input.values
        elif isinstance(data_input, (np.ndarray, list)):
            if len(data_input) != len(self.data):
                raise DataFormatError(
                    f"Array length {len(data_input)} doesn't match DataFrame length {len(self.data)}"
                )
            self.data[key] = data_input
        else:
            raise DataFormatError(f"Unsupported data type: {type(data_input)}")

    def remove_data(self, keys: List[str]) -> None:
        """Remove columns from DataFrame - pandas-specific implementation."""
        existing_keys = [key for key in keys if key in self._keys]
        if existing_keys:
            self.data.drop(existing_keys, axis=1, inplace=True)
            super().remove_data(existing_keys)

    def rename_data(self, columns: Dict[str, str]) -> None:
        """Rename columns in DataFrame - pandas-specific implementation."""
        self.data.rename(columns=columns, inplace=True)
        super().rename_data(columns)
        self._keys = self.data.columns.tolist()

    def get_info(self) -> Dict[str, Any]:
        """Get information about the dataset - enhanced pandas implementation."""
        info = super().get_info()
        info["metadata"]["shape"] = self.data.shape
        info["metadata"]["dtypes"] = self.data.dtypes.to_dict()
        info["metadata"]["memory_usage"] = self.data.memory_usage(deep=True).sum()
        return info


class TDMSBasedData(BaseData):
    """Base class for TDMS-based data formats with multiple groups."""

    def __init__(
        self,
        filename: str,
        format_type: str,
        groups: Dict,
        keys: List[str],
        data: Dict,
        metadata: Optional[Dict] = None,
    ):
        super().__init__(filename, format_type, metadata)
        self.groups = groups
        # Make copies of data to avoid modifying originals
        self.data = {group: df.copy() for group, df in data.items()}
        self._keys = keys.copy()

    def get_data(self, key: Optional[Union[str, List[str]]] = None) -> pd.DataFrame:
        """Get data for specified keys - TDMS-specific implementation."""
        if key is None:
            # Return combined data from all groups
            combined_data = []
            for group_name, group_data in self.data.items():
                # Add group prefix to columns
                prefixed_data = group_data.copy()
                prefixed_data.columns = [
                    f"{group_name}/{col}" for col in prefixed_data.columns
                ]
                combined_data.append(prefixed_data)

            if combined_data:
                return pd.concat(combined_data, axis=1)
            else:
                return pd.DataFrame()

        # Handle specific keys
        selected_keys = self.validate_keys(key)
        result_data = {}

        for key_name in selected_keys:
            if "/" in key_name:
                group_name, channel_name = key_name.split("/", 1)
                if (
                    group_name in self.data
                    and channel_name in self.data[group_name].columns
                ):
                    result_data[key_name] = self.data[group_name][channel_name]

        return pd.DataFrame(result_data)

    def _get_underlying_data(self) -> Dict:
        """Get the underlying TDMS data structure."""
        return self.data

    def add_data(
        self, key: str, data_input: Union[str, pd.Series, np.ndarray], **kwargs
    ) -> None:
        """Add new calculated column - TDMS-specific implementation."""
        # Implementation depends on which group to add to
        # This would need to be more sophisticated for real TDMS handling
        raise NotImplementedError("TDMS add_data requires group specification")
