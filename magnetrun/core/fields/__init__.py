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
    create_field_summary
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
    "create_field_summary"
]

# Version info
__field_management_version__ = "2.1.0""""Field management system for MagnetRun data."""

# Core field components
from .field_types import FieldType
from .field import Field
from .format_definition import FormatDefinition
from .format_registry import FormatRegistry

# Utility functions
from .utils import (
    create_format_config_from_data,
    guess_field_type,
    guess_unit,
    guess_symbol,
    validate_format_definition,
    merge_format_definitions,
    create_field_summary
)

# Built-in formats
from .builtin_formats import (
    create_pupitre_format,
    create_bprofile_format,
    create_pigbrother_format
)

# Main exports
__all__ = [
    # Core classes
    "FieldType",
    "Field", 
    "FormatDefinition",
    "FormatRegistry",
    
    # Utility functions
    "create_format_config_from_data",
    "guess_field_type",
    "guess_unit", 
    "guess_symbol",
    "validate_format_definition",
    "merge_format_definitions",
    "create_field_summary",
    
    # Built-in format creators
    "create_pupitre_format",
    "create_bprofile_format",
    "create_pigbrother_format"
]

# Backward compatibility aliases
FieldRegistry = FormatRegistry
FieldConfigurationManager = FormatRegistry

# Convenience functions
def create_field_registry():
    """Create a format registry with built-in format definitions."""
    return FormatRegistry()


def create_magnet_data_with_fields(filepath, format_name=None):
    """Create MagnetData with automatic format detection and field management."""
    from ..magnet_data import MagnetData
    return MagnetData.from_file(filepath)


__all__.extend(["create_field_registry", "create_magnet_data_with_fields"])

# Version info
__field_management_version__ = "2.1.0"
