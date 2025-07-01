"""Abstract base class for magnetic data handling - simplified without field management."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union, Optional
import numpy as np
import pandas as pd
from ..exceptions import KeyNotFoundError


class BaseData(ABC):
    """Abstract base class for magnetic data handling."""

    def __init__(
        self, filename: str, format_type: str, metadata: Optional[Dict] = None
    ):
        self.filename = filename
        self.format_type = format_type
        self.metadata = metadata or {}
        self._keys: List[str] = []

    @property
    def keys(self) -> List[str]:
        """Get available data keys."""
        return self._keys.copy()

    @abstractmethod
    def get_data(self, key: Optional[Union[str, List[str]]] = None) -> pd.DataFrame:
        """Get data for specified keys."""
        pass

    @abstractmethod
    def add_data(
        self, key: str, data_input: Union[str, pd.Series, np.ndarray], **kwargs
    ) -> None:
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
        existing_keys = [k for k in keys if k in self._keys]
        for key in existing_keys:
            self._keys.remove(key)

    def rename_data(self, columns: Dict[str, str]) -> None:
        """Rename columns in data."""
        for old_key, new_key in columns.items():
            if old_key in self._keys:
                idx = self._keys.index(old_key)
                self._keys[idx] = new_key

    def get_info(self) -> Dict[str, Any]:
        """Get information about the dataset."""
        return {
            "filename": self.filename,
            "format_type": self.format_type,
            "num_keys": len(self.keys),
            "keys": self.keys,
            "metadata": self.metadata,
        }
