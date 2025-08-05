"""Reader for PigBrother TDMS files."""

from pathlib import Path
from typing import Dict, Any, List
from .base_reader import BaseReader


class PigbrotherReader(BaseReader):
    """Reader for PigBrother TDMS files."""

    @property
    def format_name(self) -> str:
        return "pigbrother"

    @property
    def supported_extensions(self) -> List[str]:
        return [".tdms"]

    def can_read(self, filepath: Path) -> bool:
        """Check if file is a TDMS format."""
        if filepath.suffix.lower() not in self.supported_extensions:
            return False

        try:
            # Try to import and open TDMS file
            from nptdms import TdmsFile

            with TdmsFile.open(str(filepath)) as tdms_file:
                # Basic validation - should have groups
                return len(list(tdms_file.groups())) > 0
        except Exception as e:
            return False

    def read(self, filepath: Path) -> Dict[str, Any]:
        """Read TDMS file."""
        try:
            from nptdms import TdmsFile

            keys = []
            groups = {}
            data = {}

            # Apply time offset for downsampled data
            t_offset = 0
            if "Overview" in str(filepath):
                t_offset = 0.5
            elif "Archive" in str(filepath):
                t_offset = (1 / 120.0) / 2.0

            with TdmsFile.open(str(filepath)) as tdms_file:
                for group in tdms_file.groups():
                    gname = group.name.replace(" ", "_").replace("_et_Ref.", "")
                    groups[gname] = {}

                    if gname != "Infos":
                        data[gname] = {}

                        for channel in group.channels():
                            cname = channel.name.replace(" ", "_")
                            keys.append(f"{gname}/{cname}")
                            groups[gname][cname] = channel.properties

                            # Update time offset
                            if "wf_start_offset" in groups[gname][cname]:
                                groups[gname][cname]["wf_start_offset"] = t_offset

                        # Get dataframe for this group
                        data[gname] = group.as_dataframe(
                            time_index=False,
                            absolute_time=False,
                            scaled_data=True,
                        )

                        # Clean column names
                        data[gname].rename(
                            columns={
                                col: col.replace(" ", "_")
                                for col in data[gname].columns
                            },
                            inplace=True,
                        )
                    else:
                        groups[gname]["Infos"] = group

            # Add reference calculations for power supplies
            self._add_tdms_references(data, groups, keys)

            return {
                "groups": groups,
                "keys": keys,
                "data": data,
                "format_type": self.format_name,
                "metadata": {
                    "num_groups": len(groups),
                    "num_keys": len(keys),
                    "file_path": str(filepath),
                },
            }

        except Exception as e:
            raise ValueError(f"Failed to read TDMS file {filepath}: {e}")

    def _add_tdms_references(self, data: Dict, groups: Dict, keys: List[str]) -> None:
        """Add reference calculations for TDMS data."""
        courants_group = "Courants_Alimentations"

        if courants_group in data:
            # Add GR1 reference
            if "Référence_A1" in data[courants_group].columns:
                data[courants_group]["Référence_GR1"] = (
                    data[courants_group]["Référence_A1"]
                    + data[courants_group]["Référence_A2"]
                )
                keys.append(f"{courants_group}/Référence_GR1")
                if "Référence_A1" in groups[courants_group]:
                    groups[courants_group]["Référence_GR1"] = groups[courants_group][
                        "Référence_A1"
                    ]

            # Add GR2 reference
            if "Référence_A3" in data[courants_group].columns:
                data[courants_group]["Référence_GR2"] = (
                    data[courants_group]["Référence_A3"]
                    + data[courants_group]["Référence_A4"]
                )
                keys.append(f"{courants_group}/Référence_GR2")
                if "Référence_A3" in groups[courants_group]:
                    groups[courants_group]["Référence_GR2"] = groups[courants_group][
                        "Référence_A3"
                    ]
