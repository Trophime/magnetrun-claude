"""
MagnetRun: A comprehensive Python package for analyzing magnetic measurement data.
"""

from .core.magnet_data import MagnetData
from .core.magnet_run import MagnetRun
from .exceptions import (
    MagnetRunError,
    FileFormatError,
    DataFormatError,
    KeyNotFoundError,
)

# Version information
__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__license__ = "MIT"


# Lazy imports to avoid circular dependencies
def __getattr__(name):
    """Lazy loading of modules to avoid circular imports."""
    if name == "MagnetData":
        from .core.magnet_data import MagnetData

        return MagnetData
    elif name == "MagnetRun":
        from .core.magnet_run import MagnetRun

        return MagnetRun
    elif name == "DataPlotter":
        from .visualization.plotters import DataPlotter

        return DataPlotter
    elif name == "format_registry":
        from .formats.registry import format_registry

        return format_registry
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


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
