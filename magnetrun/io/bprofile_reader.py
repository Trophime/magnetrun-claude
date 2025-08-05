"""Reader for Bprofile CSV files with .txt extension."""

import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
from .base_reader import BaseReader


class BprofileReader(BaseReader):
    """Reader for Bprofile CSV files with .txt extension."""

    @property
    def format_name(self) -> str:
        return "bprofile"

    @property
    def supported_extensions(self) -> List[str]:
        return [".txt"]

    def can_read(self, filepath: Path) -> bool:
        """Check if file is a Bprofile format."""
        if filepath.suffix.lower() not in self.supported_extensions:
            return False

        try:
            # Read first few lines to check structure
            with open(filepath, "r") as f:
                first_line = f.readline().strip()

            # Bprofile files have specific column structure
            expected_columns = [
                "Index",
                "Position (mm)",
                "Profile at Tr (%)",
                "Profile at max (%)",
            ]
            return first_line.split(",") == expected_columns
        except Exception as e:
            return False

    def read(self, filepath: Path) -> Dict[str, Any]:
        """Read Bprofile CSV file."""
        try:
            data = pd.read_csv(filepath)

            # Validate expected columns
            expected_columns = [
                "Index",
                "Position (mm)",
                "Profile at Tr (%)",
                "Profile at max (%)",
            ]
            if not all(col in data.columns for col in expected_columns):
                raise ValueError("Missing expected columns in Bprofile file")

            return {
                "data": data,
                "format_type": self.format_name,
                "metadata": {
                    "columns": data.columns.tolist(),
                    "shape": data.shape,
                    "file_path": str(filepath),
                },
            }
        except Exception as e:
            raise ValueError(f"Failed to read Bprofile file {filepath}: {e}")
