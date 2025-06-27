"""Tests for I/O operations."""

import pytest
import tempfile
import pandas as pd
from pathlib import Path
from magnetrun.io.readers import DataReader
from magnetrun.io.writers import DataWriter
from magnetrun.core.magnet_data import MagnetData

class TestDataReader:
    """Test data reading functionality."""
    
    def test_read_csv_file(self):
        """Test reading CSV files."""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("t,Field,Current\n")
            f.write("0,0.0,0\n")
            f.write("1,1.0,10\n")
            f.write("2,2.0,20\n")
            temp_path = f.name
        
        try:
            magnet_run = DataReader.read_file(temp_path, housing="M9")
            
            assert magnet_run.housing == "M9"
            assert len(magnet_run.get_keys()) == 3
            assert 't' in magnet_run.get_keys()
            assert 'Field' in magnet_run.get_keys()
            
        finally:
            Path(temp_path).unlink()
    
    def test_unsupported_format(self):
        """Test handling of unsupported file formats."""
        with tempfile.NamedTemporaryFile(suffix='.xyz') as f:
            with pytest.raises(Exception):  # Should raise FileFormatError
                DataReader.read_file(f.name)

class TestDataWriter:
    """Test data writing functionality."""
    
    def test_write_csv(self):
        """Test writing to CSV format."""
        # Create sample data
        df = pd.DataFrame({
            't': [0, 1, 2],
            'Field': [0.0, 1.0, 2.0],
            'Current': [0, 10, 20]
        })
        magnet_data = MagnetData.from_pandas("test.txt", df)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name
        
        try:
            DataWriter.to_csv(magnet_data, temp_path)
            
            # Read back and verify
            read_df = pd.read_csv(temp_path, sep='\t')
            assert len(read_df) == 3
            assert list(read_df.columns) == ['t', 'Field', 'Current']
            
        finally:
            Path(temp_path).unlink()
