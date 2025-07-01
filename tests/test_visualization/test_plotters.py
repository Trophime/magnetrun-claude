
import pytest
import matplotlib.pyplot as plt
import pandas as pd
from unittest.mock import Mock, patch
from pathlib import Path

from magnetrun import MagnetData
from magnetrun.visualization.plotters import DataPlotter

class TestDataPlotter:
    """Test cases for DataPlotter class."""
    
    @pytest.fixture
    def sample_magnet_data(self):
        """Create sample MagnetData for testing."""
        df = pd.DataFrame({
            'Field': [0.0, 0.1, 0.2, 0.3, 0.4],
            'Current': [0.0, 1.0, 2.0, 3.0, 4.0],
            't': [0.0, 1.0, 2.0, 3.0, 4.0]
        })
        return MagnetData.from_pandas("test.csv", df)
    
    def test_plot_time_series(self, sample_magnet_data):
        """Test basic time series plotting."""
        fig, ax = plt.subplots()
        
        result_ax = DataPlotter.plot_time_series(
            sample_magnet_data,
            ['Field'],
            x_key='t',
            ax=ax
        )
        
        assert result_ax == ax
        assert len(ax.lines) > 0
        plt.close(fig)
    
    def test_plot_xy(self, sample_magnet_data):
        """Test X-Y plotting."""
        fig, ax = plt.subplots()
        
        result_ax = DataPlotter.plot_xy(
            sample_magnet_data,
            'Field',
            'Current',
            ax=ax
        )
        
        assert result_ax == ax
        assert len(ax.lines) > 0
        plt.close(fig)
    
    def test_get_default_keys(self, sample_magnet_data):
        """Test default key selection."""
        default_keys = DataPlotter.get_default_keys(sample_magnet_data)
        
        assert isinstance(default_keys, list)
        assert len(default_keys) > 0
        assert 'Field' in default_keys
        assert 'Current' in default_keys
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.show')
    def test_plot_time_series_to_file(self, mock_show, mock_savefig, sample_magnet_data):
        """Test time series plotting with file output."""
        DataPlotter.plot_time_series_to_file(
            sample_magnet_data,
            ['Field', 'Current'],
            file_path="test.csv",
            save=True,
            show=False
        )
        
        mock_savefig.assert_called_once()
        mock_show.assert_not_called()
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.show')
    def test_create_overview_plot(self, mock_show, mock_savefig, sample_magnet_data):
        """Test overview plot creation."""
        DataPlotter.create_overview_plot(
            sample_magnet_data,
            template='standard',
            file_path="test.csv",
            save=True,
            show=False
        )
        
        mock_savefig.assert_called_once()
        mock_show.assert_not_called()
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.show')
    def test_quick_plot(self, mock_show, mock_savefig, sample_magnet_data):
        """Test quick plot functionality."""
        DataPlotter.quick_plot(
            sample_magnet_data,
            keys=['Field'],
            plot_type='time_series',
            save=True,
            show=False
        )
        
        mock_savefig.assert_called_once()
        mock_show.assert_not_called()
