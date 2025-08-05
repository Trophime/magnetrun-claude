# magnetrun/core/fields/__init__.py (FIXED)
"""Core field components for MagnetRun data."""

# Core field components only
from .field_types import FieldType
from .field import Field

# Utility functions
from .utils import (
    create_format_config_from_data,
    guess_field_type,
    guess_unit,
    guess_symbol,
    validate_format_definition,
    merge_format_definitions,
    create_field_summary,
)

# Main exports
__all__ = [
    # Core classes
    "FieldType",
    "Field",
    # Utility functions
    "create_format_config_from_data",
    "guess_field_type",
    "guess_unit",
    "guess_symbol",
    "validate_format_definition",
    "merge_format_definitions",
    "create_field_summary",
]

# FIXED: Remove lazy imports that cause circular dependencies
# Instead, provide factory functions


def create_field_registry():
    """Create a format registry with built-in format definitions."""
    from ...formats.registry import FormatRegistry

    return FormatRegistry()


def create_magnet_data_with_fields(filepath, format_name=None):
    """Create MagnetData with automatic format detection and field management."""
    # FIXED: Import locally to avoid circular dependency
    from ..magnet_data import MagnetData

    return MagnetData.from_file(filepath)


# Add convenience functions to exports
__all__.extend(["create_field_registry", "create_magnet_data_with_fields"])

# Version info
__field_management_version__ = "2.1.0" 
