"""File reading utilities for various formats."""

from pathlib import Path
from typing import Union, Dict, List
import pandas as pd
from io import StringIO

from ..core.magnet_data import MagnetData
from ..core.magnet_run import MagnetRun
from ..exceptions import FileFormatError

class DataReader:
    """Factory class for reading different data formats."""
    
    @staticmethod
    def read_file(filepath: Union[str, Path], housing: str = "M9", site: str = "") -> MagnetRun:
        """Read data file and return MagnetRun object."""
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        suffix = filepath.suffix.lower()
        
        if suffix == '.txt':
            return DataReader._read_txt(filepath, housing, site)
        elif suffix == '.tdms':
            return DataReader._read_tdms(filepath, housing, site)
        elif suffix == '.csv':
            return DataReader._read_csv(filepath, housing, site)
        else:
            raise FileFormatError(f"Unsupported file format: {suffix}")
    
    @staticmethod
    def _read_txt(filepath: Path, housing: str, site: str) -> MagnetRun:
        """Read text file."""
        with open(filepath, 'r') as f:
            data = pd.read_csv(f, sep=r'\s+', engine='python', skiprows=1)
        
        magnet_data = MagnetData.from_pandas(str(filepath), data)
        magnet_run = MagnetRun(housing, site, magnet_data)
        magnet_run.prepare_data()
        
        return magnet_run
    
    @staticmethod
    def _read_tdms(filepath: Path, housing: str, site: str) -> MagnetRun:
        """Read TDMS file."""
        from nptdms import TdmsFile
        
        keys = []
        groups = {}
        data = {}
        
        # Apply time offset for downsampled data
        t_offset = 0
        if "Overview" in str(filepath):
            t_offset = 0.5
        elif "Archive" in str(filepath):
            t_offset = (1/120.) / 2.
        
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
                        columns={col: col.replace(" ", "_") for col in data[gname].columns},
                        inplace=True,
                    )
                else:
                    groups[gname]["Infos"] = group
        
        # Add reference calculations for power supplies
        DataReader._add_tdms_references(data, groups, keys)
        
        magnet_data = MagnetData.from_dict(str(filepath), groups, keys, data)
        return MagnetRun(housing, site, magnet_data)
    
    @staticmethod
    def _read_csv(filepath: Path, housing: str, site: str) -> MagnetRun:
        """Read CSV file."""
        data = pd.read_csv(filepath, sep=',', engine='python', skiprows=0)
        magnet_data = MagnetData.from_pandas(str(filepath), data)
        return MagnetRun(housing, site, magnet_data)
    
    @staticmethod
    def _add_tdms_references(data: Dict, groups: Dict, keys: List[str]) -> None:
        """Add reference calculations for TDMS data."""
        courants_group = "Courants_Alimentations"
        
        if courants_group in data:
            # Add GR1 reference
            if "Référence_A1" in data[courants_group]:
                data[courants_group]["Référence_GR1"] = (
                    data[courants_group]["Référence_A1"] + 
                    data[courants_group]["Référence_A2"]
                )
                keys.append(f"{courants_group}/Référence_GR1")
                groups[courants_group]["Référence_GR1"] = groups[courants_group]["Référence_A1"]
            
            # Add GR2 reference
            if "Référence_A3" in data[courants_group]:
                data[courants_group]["Référence_GR2"] = (
                    data[courants_group]["Référence_A3"] + 
                    data[courants_group]["Référence_A4"]
                )
                keys.append(f"{courants_group}/Référence_GR2")
                groups[courants_group]["Référence_GR2"] = groups[courants_group]["Référence_A3"]
