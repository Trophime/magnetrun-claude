# magnetrun/core/__init__.py (UPDATED)
"""Core components for MagnetRun data handling - Logically Reorganized."""

# Main data handling classes
from .magnet_data import MagnetData
from .magnet_run import MagnetRun
from .base_data import BaseData

# Core field primitives (basic field components only)
from .fields import Field, FieldType

# Legacy unit management (deprecated)
from .units import UnitManager

# Main exports for public API
__all__ = [
    # Core data classes
    "MagnetData",
    "MagnetRun", 
    "BaseData",
    
    # Core field primitives
    "Field",
    "FieldType",
    
    # Legacy compatibility
    "UnitManager",
]

# Version info
__field_management_version__ = "2.1.0"

# Backward compatibility for format-related imports
import warnings


def _warn_format_import_location():
    """Warn about format-related imports from core."""
    warnings.warn(
        "Format-related classes have moved to magnetrun.formats. "
        "Use 'from magnetrun.formats import FormatRegistry, FormatDefinition' instead.",
        DeprecationWarning,
        stacklevel=3,
    )


# Provide deprecated format imports with warnings
def __getattr__(name):
    if name in ["FormatRegistry", "FormatDefinition"]:
        _warn_format_import_location()
        from ..formats import FormatRegistry, FormatDefinition
        return {"FormatRegistry": FormatRegistry, "FormatDefinition": FormatDefinition}[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
