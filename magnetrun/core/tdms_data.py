"""Refactored base class for magnetic data handling with shared implementations."""

from typing import List, Dict, Union, Optional
import numpy as np
import pandas as pd


# Integration with BaseData classes
from .base_data import BaseData


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
