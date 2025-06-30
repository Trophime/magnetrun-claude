"""MagnetRun - A Python package for analyzing magnetic measurement data."""

from .core.magnet_data import MagnetData
from .core.magnet_run import MagnetRun
from .io.readers import DataReader
from .processing.analysis import DataAnalyzer
from .config.housing_configs import HOUSING_CONFIGS

__version__ = "1.0.0"
__all__ = ["MagnetData", "MagnetRun", "DataReader", "DataAnalyzer", "HOUSING_CONFIGS"]
