"""PigBrother TDMS-specific data operations with integrated format definition."""

from typing import List, Dict, Optional
from ..core.tdms_data import TDMSBasedData


class PigbrotherData(TDMSBasedData):
    """PigBrother TDMS-specific data operations."""

    def __init__(
        self,
        filename: str,
        groups: Dict,
        keys: List[str],
        data: Dict,
        metadata: Optional[Dict] = None,
    ):
        super().__init__(filename, "pigbrother", groups, keys, data, metadata)
