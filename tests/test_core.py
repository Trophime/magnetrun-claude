"""Tests for core functionality."""

import pytest
import pandas as pd
import numpy as np
from magnetrun.core.magnet_data import MagnetData
from magnetrun.core.magnet_run import MagnetRun
from magnetrun.core.pandas_data import PandasData

class TestMagnetData:
    """Test MagnetData functionality."""
    
    @pytest.fixture
    def sample_dataframe(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame({
            't': [0, 1, 2, 3, 4],
            'Field': [0.0, 1.0, 2.0, 1.5, 0.5],
            'Icoil1': [0, 10, 20, 15, 5],
            'Ucoil1': [0, 1, 2, 1.5, 0.5]
        })
    
    @pytest.fixture
    def magnet_data(self, sample_dataframe):
        """Create MagnetData instance for testing."""
        return MagnetData.from_pandas("test.txt", sample_dataframe)
    
    def test_creation_from_pandas(self, sample_dataframe):
        """Test creation from pandas DataFrame."""
        magnet_data = MagnetData.from_pandas("test.txt", sample_dataframe)
        
        assert magnet_data.filename == "test.txt"
        assert magnet_data.data_type == 0
        assert len(magnet_data.keys) == 4
        assert 'Field' in magnet_data.keys
        assert 't' in magnet_data.keys
    
    def test_get_data(self, magnet_data):
        """Test data retrieval."""
        # Get all data
        all_data = magnet_data.get_data()
        assert len(all_data.columns) == 4
        
        # Get specific column
        field_data = magnet_data.get_data('Field')
        assert len(field_data.columns) == 1
        assert 'Field' in field_data.columns
        
        # Get multiple columns
        multi_data = magnet_data.get_data(['t', 'Field'])
        assert len(multi_data.columns) == 2
    
    def test_add_data(self, magnet_data):
        """Test adding calculated columns."""
        # Add simple calculation
        magnet_data.add_data('Power', 'Power = Field * Icoil1')
        
        assert 'Power' in magnet_data.keys
        power_data = magnet_data.get_data('Power')
        expected = pd.Series([0, 10, 40, 22.5, 2.5], name='Power')
        pd.testing.assert_series_equal(power_data['Power'], expected)
    
    def test_remove_data(self, magnet_data):
        """Test removing columns."""
        initial_keys = len(magnet_data.keys)
        magnet_data.remove_data(['Ucoil1'])
        
        assert len(magnet_data.keys) == initial_keys - 1
        assert 'Ucoil1' not in magnet_data.keys
    
    def test_rename_data(self, magnet_data):
        """Test renaming columns."""
        magnet_data.rename_data({'Icoil1': 'Current'})
        
        assert 'Current' in magnet_data.keys
        assert 'Icoil1' not in magnet_data.keys

class TestMagnetRun:
    """Test MagnetRun functionality."""
    
    @pytest.fixture
    def sample_dataframe(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame({
            'Date': ['2023.01.01', '2023.01.01', '2023.01.01'],
            'Time': ['10:00:00', '10:00:01', '10:00:02'],
            'Field': [0.0, 1.0, 2.0],
            'Idcct1': [1, 2, 3],
            'Idcct2': [1, 2, 3],
            'Idcct3': [1, 2, 3],
            'Idcct4': [1, 2, 3],
        })
    
    @pytest.fixture
    def magnet_run(self, sample_dataframe):
        """Create MagnetRun instance for testing."""
        magnet_data = MagnetData.from_pandas("test.txt", sample_dataframe)
        return MagnetRun("M9", "test_site", magnet_data)
    
    def test_creation(self, magnet_run):
        """Test MagnetRun creation."""
        assert magnet_run.housing == "M9"
        assert magnet_run.site == "test_site"
        assert magnet_run.magnet_data is not None
    
    def test_prepare_data_m9(self, magnet_run):
        """Test data preparation for M9 housing."""
        magnet_run.prepare_data()
        
        # Check that reference currents were added
        assert 'IH_ref' in magnet_run.get_keys()
        assert 'IB_ref' in magnet_run.get_keys()
        
        # Check that original dcct channels were removed
        assert 'Idcct1' not in magnet_run.get_keys()
        assert 'Idcct2' not in magnet_run.get_keys()
    
    def test_housing_config(self, magnet_run):
        """Test housing configuration access."""
        config = magnet_run.housing_config
        assert config is not None
        assert config.name == "M9"
        assert 'Idcct1' in config.ih_ref_channels
        assert 'Idcct2' in config.ih_ref_channels
