
"""Reader for Pupitre CSV files with .txt extension."""

import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
from .base_reader import BaseReader

class PupitreReader(BaseReader):
    """Reader for Pupitre CSV files with .txt extension."""
    
    @property
    def format_name(self) -> str:
        return "pupitre"
    
    @property
    def supported_extensions(self) -> List[str]:
        return ['.txt']
    
    def can_read(self, filepath: Path) -> bool:
        """Check if file is a Pupitre format."""
        if filepath.suffix.lower() not in self.supported_extensions:
            return False
        
        try:
            # Read first few lines to check structure
            with open(filepath, 'r') as f:
                first_line = f.readline().strip()
                second_line = f.readline().strip()
            
            # Pupitre files typically have space-separated values
            # and don't have the specific bprofile column structure
            if ',' in first_line:
                return False  # CSV format, likely bprofile
            
            # Check if it looks like whitespace-separated data
            return len(first_line.split()) > 1 and len(second_line.split()) > 1
            
        except:
            return False
    
    def read(self, filepath: Path) -> Dict[str, Any]:
        """Read Pupitre file."""
        try:
            # Read with whitespace separator, skip first row
            data = pd.read_csv(filepath, sep=r'\s+', engine='python', skiprows=1)
            
            return {
                'data': data,
                'format_type': self.format_name,
                'metadata': {
                    'columns': data.columns.tolist(),
                    'shape': data.shape,
                    'file_path': str(filepath)
                }
            }
        except Exception as e:
            raise ValueError(f"Failed to read Pupitre file {filepath}: {e}")
