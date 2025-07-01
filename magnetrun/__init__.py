
"""
MagnetRun: A comprehensive Python package for analyzing magnetic measurement data.
"""

from .core.magnet_data import MagnetData
from .core.magnet_run import MagnetRun
from .exceptions import MagnetRunError, FileFormatError, DataFormatError, KeyNotFoundError

# Version information
__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__license__ = "MIT"

# Convenience imports
from .visualization.plotters import DataPlotter
from .formats.registry import format_registry

__all__ = [
    "MagnetData",
    "MagnetRun", 
    "DataPlotter",
    "format_registry",
    "MagnetRunError",
    "FileFormatError", 
    "DataFormatError",
    "KeyNotFoundError",
    "__version__",
]
