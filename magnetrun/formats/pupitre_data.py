"""Pupitre-specific data operations with integrated format definition."""

import pandas as pd
from typing import Dict, Optional
from ..core.base_data import PandasBasedData


class PupitreData(PandasBasedData):
    """Pupitre-specific data operations."""

    def __init__(
        self, filename: str, data: pd.DataFrame, metadata: Optional[Dict] = None
    ):
        super().__init__(filename, "pupitre", data, metadata)
