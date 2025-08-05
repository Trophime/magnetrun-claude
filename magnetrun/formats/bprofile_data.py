"""Bprofile-specific data operations with integrated format definition."""

from typing import Dict, Optional
import pandas as pd
from ..core.base_data import PandasBasedData


class BprofileData(PandasBasedData):
    """Bprofile-specific data operations."""

    def __init__(
        self, filename: str, data: pd.DataFrame, metadata: Optional[Dict] = None
    ):
        super().__init__(filename, "bprofile", data, metadata)
