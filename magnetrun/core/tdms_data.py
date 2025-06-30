"""TDMS-specific data operations."""

from typing import List, Dict, Any, Union, Optional
import pandas as pd
import numpy as np
from datetime import datetime

from .base_data import BaseData
from .units import UnitManager
from ..exceptions import DataFormatError


class TdmsData(BaseData):
    """Handles TDMS data operations for MagnetRun data."""

    def __init__(self, filename: str, groups: Dict, keys: List[str], data: Dict):
        super().__init__(filename, groups, keys, 1)
        self.data = data
        self.unit_manager = UnitManager()
        self._setup_units()

    def _setup_units(self) -> None:
        """Set up units for TDMS data."""
        for entry in self.data:
            if entry == "t":
                self.units["t"] = ("t", self.unit_manager.ureg.second)
            else:
                group = entry
                if "/" in entry:
                    (group, channel) = entry.split("/")
                    if channel == "t":
                        self.units[entry] = ("t", self.unit_manager.ureg.second)

                self.units[entry] = self.unit_manager.get_pigbrother_units(group)

    def get_data(self, key: Optional[Union[str, List[str]]] = None) -> pd.DataFrame:
        """Get TDMS data for specified keys."""
        if key is None:
            # Return all data - need to decide how to handle multiple groups
            raise NotImplementedError("Getting all TDMS data not implemented")

        if isinstance(key, str):
            return self._get_single_key_data(key)
        elif isinstance(key, list):
            return self._get_multiple_keys_data(key)

    def _get_single_key_data(self, key: str) -> pd.DataFrame:
        """Get data for a single key."""
        if "/" not in key:
            raise DataFormatError(f"TDMS key must include group: {key}")

        group, channel = key.split("/")
        return self.data[group][[channel]]

    def _get_multiple_keys_data(self, keys: List[str]) -> pd.DataFrame:
        """Get data for multiple keys."""
        # Group keys by their group
        groups_channels = {}
        for key in keys:
            if "/" not in key:
                raise DataFormatError(f"TDMS key must include group: {key}")

            group, channel = key.split("/")
            if group not in groups_channels:
                groups_channels[group] = []
            groups_channels[group].append(channel)

        # For now, assume all keys are from the same group
        if len(groups_channels) > 1:
            raise DataFormatError("Multiple groups not supported in single query")

        group = list(groups_channels.keys())[0]
        channels = groups_channels[group]

        return self.data[group][channels]

    def add_data(self, key: str, formula: str, unit: Optional[str] = None) -> None:
        """Add calculated column to TDMS data."""
        if "/" not in key:
            raise DataFormatError(f"TDMS key must include group: {key}")

        group, channel = key.split("/")

        # Process formula to handle cross-group references
        processed_formula = self._process_formula(formula, group)

        try:
            self.data[group].eval(processed_formula, inplace=True)
            self.keys.append(key)

            # Set up metadata for new channel
            if group in self.groups and self.groups[group]:
                first_key = list(self.groups[group].keys())[0]
                self.groups[group][channel] = {
                    "wf_increment": self.groups[group][first_key]["wf_increment"]
                }

            if unit:
                self.units[key] = unit
            else:
                self.units[key] = self.unit_manager.get_pigbrother_units(group)

        except Exception as e:
            raise DataFormatError(
                f"Failed to add TDMS data with formula '{formula}': {e}"
            )

    def _process_formula(self, formula: str, target_group: str) -> str:
        """Process formula to handle cross-group references."""
        import re

        # Remove target group prefix from formula
        processed_formula = formula.replace(f"{target_group}/", "")

        # Handle cross-group references
        matches = re.findall(r"(\w+)/(\w+)", processed_formula)
        if matches:
            for matched_group, matched_channel in matches:
                # Copy data from other group to target group
                self.data[target_group][matched_channel] = self.data[matched_group][
                    matched_channel
                ]
                processed_formula = processed_formula.replace(f"{matched_group}/", "")

        return processed_formula
