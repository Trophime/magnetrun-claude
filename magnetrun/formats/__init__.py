# magnetrun/formats/__init__.py (UPDATED)
"""Format-specific data handlers with unified registry."""

from .format_definition import FormatDefinition
from .registry import format_registry, FormatRegistry
from .pupitre_data import PupitreData
from .pigbrother_data import PigbrotherData
from .bprofile_data import BprofileData

__all__ = [
    "FormatDefinition",
    "format_registry",
    "FormatRegistry", 
    "PupitreData",
    "PigbrotherData", 
    "BprofileData"
]
