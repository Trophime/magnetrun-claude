"""Refactored base class for magnetic data handling with shared implementations."""

from typing import List, Dict, Any, Union, Optional
import numpy as np
import pandas as pd
from ..exceptions import DataFormatError


# Integration with BaseData classes
from .base_data import BaseData


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
