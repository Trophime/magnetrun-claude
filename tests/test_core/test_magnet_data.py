import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch

from magnetrun import MagnetData, MagnetRun
from magnetrun.exceptions import FileFormatError, KeyNotFoundError


class TestMagnetData:
    """Test cases for MagnetData class."""

    def test_from_pandas(self):
        """Test creating MagnetData from pandas DataFrame."""
        df = pd.DataFrame(
            {"Field": [0.0, 0.1, 0.2], "Current": [0.0, 1.0, 2.0], "t": [0.0, 1.0, 2.0]}
        )

        magnet_data = MagnetData.from_pandas("test.csv", df)

        assert magnet_data.filename == "test.csv"
        assert len(magnet_data.keys) == 3
        assert "Field" in magnet_data.keys
        assert "Current" in magnet_data.keys
        assert "t" in magnet_data.keys

    @patch("magnetrun.io.format_detector.FormatDetector")
    def test_from_file_auto_detection(self, mock_detector):
        """Test auto-detection when loading from file."""
        # Mock format detection
        mock_detector_instance = Mock()
        mock_detector_instance.detect_format.return_value = "pupitre"
        mock_detector_instance.get_reader_for_file.return_value = Mock()
        mock_detector.return_value = mock_detector_instance

        # Mock reader
        mock_reader = Mock()
        mock_reader.read.return_value = {
            "data": pd.DataFrame({"Field": [1, 2], "Current": [3, 4]}),
            "metadata": {"shape": (2, 2)},
        }
        mock_detector_instance.get_reader_for_file.return_value = mock_reader

        with patch("pathlib.Path.exists", return_value=True):
            magnet_data = MagnetData.from_file("test.txt")

        assert magnet_data is not None

    def test_get_data_all(self):
        """Test getting all data."""
        df = pd.DataFrame({"Field": [0.0, 0.1, 0.2], "Current": [0.0, 1.0, 2.0]})

        magnet_data = MagnetData.from_pandas("test.csv", df)
        result = magnet_data.get_data()

        assert result.shape == (3, 2)
        assert list(result.columns) == ["Field", "Current"]

    def test_get_data_specific_keys(self):
        """Test getting specific keys."""
        df = pd.DataFrame(
            {
                "Field": [0.0, 0.1, 0.2],
                "Current": [0.0, 1.0, 2.0],
                "Temperature": [20.0, 20.1, 20.2],
            }
        )

        magnet_data = MagnetData.from_pandas("test.csv", df)
        result = magnet_data.get_data(["Field", "Current"])

        assert result.shape == (3, 2)
        assert list(result.columns) == ["Field", "Current"]

    def test_add_data(self):
        """Test adding calculated data."""
        df = pd.DataFrame({"Field": [1.0, 2.0, 3.0], "Current": [2.0, 3.0, 4.0]})

        magnet_data = MagnetData.from_pandas("test.csv", df)
        magnet_data.add_data("Power", "Power = Field * Current")

        assert "Power" in magnet_data.keys
        result = magnet_data.get_data(["Power"])
        expected = [2.0, 6.0, 12.0]  # Field * Current
        assert result["Power"].tolist() == expected

    def test_remove_data(self):
        """Test removing data columns."""
        df = pd.DataFrame(
            {
                "Field": [1.0, 2.0, 3.0],
                "Current": [2.0, 3.0, 4.0],
                "Temperature": [20.0, 20.1, 20.2],
            }
        )

        magnet_data = MagnetData.from_pandas("test.csv", df)
        original_count = len(magnet_data.keys)

        magnet_data.remove_data(["Temperature"])

        assert len(magnet_data.keys) == original_count - 1
        assert "Temperature" not in magnet_data.keys
        assert "Field" in magnet_data.keys
        assert "Current" in magnet_data.keys

    def test_rename_data(self):
        """Test renaming data columns."""
        df = pd.DataFrame({"Field": [1.0, 2.0, 3.0], "Current": [2.0, 3.0, 4.0]})

        magnet_data = MagnetData.from_pandas("test.csv", df)
        magnet_data.rename_data(
            {"Field": "MagneticField", "Current": "ElectricCurrent"}
        )

        assert "Field" not in magnet_data.keys
        assert "Current" not in magnet_data.keys
        assert "MagneticField" in magnet_data.keys
        assert "ElectricCurrent" in magnet_data.keys

    def test_get_info(self):
        """Test getting data information."""
        df = pd.DataFrame({"Field": [1.0, 2.0, 3.0], "Current": [2.0, 3.0, 4.0]})

        magnet_data = MagnetData.from_pandas("test.csv", df)
        info = magnet_data.get_info()

        assert "filename" in info
        assert "format_type" in info
        assert "num_keys" in info
        assert "keys" in info
        assert info["filename"] == "test.csv"
        assert info["num_keys"] == 2


class TestMagnetRun:
    """Test cases for MagnetRun class."""

    def test_initialization(self):
        """Test MagnetRun initialization."""
        df = pd.DataFrame({"Field": [1, 2, 3], "Current": [4, 5, 6]})
        magnet_data = MagnetData.from_pandas("test.csv", df)

        magnet_run = MagnetRun("M9", "Lab1", magnet_data)

        assert magnet_run.housing == "M9"
        assert magnet_run.site == "Lab1"
        assert magnet_run.magnet_data == magnet_data

    def test_get_data(self):
        """Test getting data through MagnetRun."""
        df = pd.DataFrame({"Field": [1, 2, 3], "Current": [4, 5, 6]})
        magnet_data = MagnetData.from_pandas("test.csv", df)
        magnet_run = MagnetRun("M9", "Lab1", magnet_data)

        result = magnet_run.get_data("Field")
        assert result.shape == (3, 1)
        assert list(result.columns) == ["Field"]

    def test_get_keys(self):
        """Test getting keys through MagnetRun."""
        df = pd.DataFrame({"Field": [1, 2, 3], "Current": [4, 5, 6]})
        magnet_data = MagnetData.from_pandas("test.csv", df)
        magnet_run = MagnetRun("M9", "Lab1", magnet_data)

        keys = magnet_run.get_keys()
        assert len(keys) == 2
        assert "Field" in keys
        assert "Current" in keys
