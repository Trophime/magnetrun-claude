"""Data cleaning operations."""

from typing import List
import pandas as pd
import numpy as np
from natsort import natsorted
import re

from ..core.magnet_data import MagnetData
from ..exceptions import DataFormatError

class DataCleaner:
    """Handles data cleaning operations."""
    
    @staticmethod
    def cleanup_pandas_data(magnet_data: MagnetData, debug: bool = False) -> None:
        """Clean up pandas data by removing empty and duplicate columns."""
        if magnet_data.data_type != 0:
            raise DataFormatError("cleanup_pandas_data only works with pandas data")
        
        data = magnet_data.get_data()
        
        if debug:
            print(f"Clean up Data: filename={magnet_data.filename}, keys={magnet_data.keys}")
        
        # Find initial current keys
        init_ikeys = natsorted([key for key in magnet_data.keys if re.match(r"Icoil\d+", key)])
        
        # Find empty columns (except Flow and Field columns)
        empty_cols = [
            col for col in data.columns[(data == 0).all()].values.tolist()
            if not col.startswith("Flow") and not col.startswith("Field")
        ]
        
        # Remove empty columns
        if empty_cols:
            data = data.drop(empty_cols, axis=1)
        
        # Remove duplicate columns (except Ucoil columns)
        duplicate_cols = DataCleaner._get_duplicate_columns(data)
        really_dropped_columns = [col for col in duplicate_cols if not col.startswith("Ucoil")]
        
        if really_dropped_columns:
            data.drop(really_dropped_columns, axis=1, inplace=True)
        
        # Process voltage probes
        DataCleaner._process_voltage_probes(data, debug)
        
        # Process current keys
        DataCleaner._process_current_keys(data, init_ikeys, debug)
        
        # Update magnet_data with cleaned data
        magnet_data._data_handler.data = data
        magnet_data._data_handler.keys = data.columns.values.tolist()
    
    @staticmethod
    def _get_duplicate_columns(df: pd.DataFrame) -> List[str]:
        """Find columns with duplicate data."""
        duplicate_column_names = set()
        
        for x in range(df.shape[1]):
            col = df.iloc[:, x]
            for y in range(x + 1, df.shape[1]):
                other_col = df.iloc[:, y]
                if col.equals(other_col):
                    duplicate_column_names.add(df.columns.values[y])
        
        return list(duplicate_column_names)
    
    @staticmethod
    def _process_voltage_probes(data: pd.DataFrame, debug: bool = False) -> None:
        """Process voltage probe data to create UH and UB columns."""
        from itertools import groupby
        
        # Find Ucoil columns
        ukeys = natsorted([str(key) for key in data.columns if re.match(r"Ucoil\d+", key)])
        
        if not ukeys:
            return
        
        # Extract indices and group consecutive ones
        uindex = [int(ukey.replace("Ucoil", "")) for ukey in ukeys]
        gb = groupby(enumerate(uindex), key=lambda x: x[0] - x[1])
        all_groups = ([i[1] for i in g] for _, g in gb)
        uprobes = list(filter(lambda x: len(x) > 1, all_groups))
        
        if not uprobes:
            raise DataFormatError("No Uprobes found during cleanup")
        
        # Create UH from first group
        uh_cols = [f"Ucoil{i}" for i in uprobes[0]]
        data["UH"] = data[uh_cols].sum(axis=1)
        
        if debug:
            print(f"UH: {uh_cols}")
        
        # Create UB from second group if it exists
        if len(uprobes) > 1:
            ub_cols = [f"Ucoil{i}" for i in uprobes[1]]
            data["UB"] = data[ub_cols].sum(axis=1)
            
            if debug:
                print(f"UB: {ub_cols}")
    
    @staticmethod
    def _process_current_keys(data: pd.DataFrame, init_ikeys: List[str], debug: bool = False) -> None:
        """Process current measurement keys."""
        ikeys = natsorted([key for key in data.columns if re.match(r"Icoil\d+", key)])
        
        if debug:
            print(f"IKeys = {ikeys} ({len(ikeys)})")
        
        if len(ikeys) == 1:
            # Add second current measurement if missing
            if init_ikeys[-1] not in ikeys and init_ikeys[-2] not in ikeys:
                # IH only case
                data[init_ikeys[-2]] = data[init_ikeys[-2]]
            else:
                # IB only case
                data[init_ikeys[0]] = data[init_ikeys[0]]
        
        elif len(ikeys) > 2:
            # Remove duplicates based on similarity
            DataCleaner._remove_similar_current_keys(data, ikeys, debug)

    @staticmethod
    def _remove_similar_current_keys(data: pd.DataFrame, ikeys: List[str], debug: bool = False) -> None:
        """Remove similar current keys based on mean difference."""
        remove_ikeys = []
        
        for i in range(len(ikeys)):
            for j in range(i + 1, len(ikeys)):
                diff = data[ikeys[i]] - data[ikeys[j]]
                error = diff.mean()
                
                if debug:
                    print(f"diff[{ikeys[i]}_{ikeys[j]}]: mean={error}, std={diff.std()}")
                
                if abs(error) <= 1.0e-2:
                    remove_ikeys.append(ikeys[j])
        
        if remove_ikeys and debug:
            print(f"remove_ikeys: {remove_ikeys}")
        
        if remove_ikeys:
            data.drop(remove_ikeys, axis=1, inplace=True)
