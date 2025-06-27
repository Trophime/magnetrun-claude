"""Tests for data processing operations."""

import pytest
import pandas as pd
import numpy as np
from magnetrun.core.magnet_data import MagnetData
from magnetrun.processing.analysis import DataAnalyzer
from magnetrun.processing.time_operations import TimeProcessor

class TestDataAnalyzer:
    """Test data analysis functionality."""
    
    @pytest.fixture
    def sample_data_with_peaks(self):
        """Create sample data with known peaks."""
        t = np.linspace(0, 10, 100)
        # Create signal with peaks at t=2, 5, 8
        signal = np.exp(-(t-2)**2) + 0.8*np.exp(-(t-5)**2) + 0.6*np.exp(-(t-8)**2)
        noise = 0.01 * np.random.randn(len(t))
        
        df = pd.DataFrame({
            't': t,
            'Field': signal + noise
        })
        return MagnetData.from_pandas("test.txt", df)
    
    def test_find_peaks(self, sample_data_with_peaks):
        """Test peak detection."""
        peaks, properties = DataAnalyzer.find_peaks_in_data(
            sample_data_with_peaks, 'Field', height=0.3
        )
        
        # Should find approximately 3 peaks
        assert len(peaks) >= 2  # Allow for some noise tolerance
        assert len(peaks) <= 4
    
    def test_compute_statistics(self, sample_data_with_peaks):
        """Test statistics computation."""
        stats = DataAnalyzer.compute_statistics(sample_data_with_peaks, 'Field')
        
        assert 'mean' in stats.index
        assert 'std' in stats.index
        assert 'min' in stats.index
        assert 'max' in stats.index

class TestTimeProcessor:
    """Test time processing functionality."""
    
    @pytest.fixture
    def sample_data_with_datetime(self):
        """Create sample data with Date/Time columns."""
        df = pd.DataFrame({
            'Date': ['2023.01.01', '2023.01.01', '2023.01.01'],
            'Time': ['10:00:00', '10:00:01', '10:00:02'],
            'Field': [0.0, 1.0, 2.0]
        })
        return MagnetData.from_pandas("test.txt", df)
    
    def test_add_time_column(self, sample_data_with_datetime):
        """Test adding time column."""
        TimeProcessor.add_time_column(sample_data_with_datetime)
        
        keys = sample_data_with_datetime.keys
        assert 't' in keys
        assert 'timestamp' in keys
        assert 'Date' not in keys  # Should be removed
        assert 'Time' not in keys  # Should be removed
        
        # Check time values
        time_data = sample_data_with_datetime.get_data('t')
        expected_times = [0.0, 1.0, 2.0]  # Seconds from start
        np.testing.assert_array_almost_equal(time_data['t'].values, expected_times)
