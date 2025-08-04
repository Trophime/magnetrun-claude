# magnetrun/formats/registry.py (UPDATED)
"""Unified registry for data formats, readers, handlers, and field definitions."""

import json
from pathlib import Path
from typing import Dict, Type, List, Optional, Union
from pint import UnitRegistry

from ..core.base_data import BaseData
from ..core.fields import Field, FieldType
from ..io.base_reader import BaseReader
from .format_definition import FormatDefinition


class FormatRegistry:
    """Unified registry for data formats, readers, handlers, and field definitions."""

    def __init__(self, configs_dir: Optional[Path] = None):
        self._readers: Dict[str, Type[BaseReader]] = {}
        self._data_handlers: Dict[str, Type[BaseData]] = {}
        self._format_definitions: Dict[str, FormatDefinition] = {}
        self.ureg = self._create_unit_registry()
        self.configs_dir = configs_dir or (Path(__file__).parent / "configs")
        
        # Load everything
        self._load_format_definitions()
        self._register_built_in_formats()

    def _create_unit_registry(self) -> UnitRegistry:
        """Create shared unit registry."""
        ureg = UnitRegistry()
        ureg.define("percent = 0.01 = %")
        ureg.define("ppm = 1e-6")
        ureg.define("var = 1")  # For reactive power (VAr)
        return ureg

    def _load_format_definitions(self):
        """Load format definitions from JSON configuration files."""
        if not self.configs_dir.exists():
            print(f"Warning: Configs directory {self.configs_dir} does not exist")
            return
        
        for json_file in self.configs_dir.glob("*.json"):
            try:
                format_def = FormatDefinition.load_from_file(json_file, self.ureg)
                self._format_definitions[format_def.format_name] = format_def
                print(f"Loaded format definition '{format_def.format_name}' from {json_file.name}")
            except Exception as e:
                print(f"Warning: Failed to load format definition from {json_file}: {e}")

    def _register_built_in_formats(self):
        """Register built-in format readers and handlers."""
        from .pupitre_data import PupitreData
        from .pigbrother_data import PigbrotherData
        from .bprofile_data import BprofileData
        from ..io.pupitre_reader import PupitreReader
        from ..io.pigbrother_reader import PigbrotherReader
        from ..io.bprofile_reader import BprofileReader

        self.register_format("pupitre", PupitreReader, PupitreData)
        self.register_format("pigbrother", PigbrotherReader, PigbrotherData)
        self.register_format("bprofile", BprofileReader, BprofileData)

    def register_format(self, format_name: str, reader_class: Type[BaseReader], data_handler_class: Type[BaseData]):
        """Register a format with its reader and data handler."""
        self._readers[format_name] = reader_class
        self._data_handlers[format_name] = data_handler_class

    def register_format_definition(self, format_def: FormatDefinition):
        """Register a format definition."""
        format_def.ureg = self.ureg  # Ensure shared unit registry
        self._format_definitions[format_def.format_name] = format_def

    def get_format_definition(self, format_name: str) -> Optional[FormatDefinition]:
        """Get format definition by name."""
        return self._format_definitions.get(format_name)

    def get_reader(self, format_name: str) -> Type[BaseReader]:
        """Get reader class for format."""
        if format_name not in self._readers:
            raise ValueError(f"Unknown format: {format_name}")
        return self._readers[format_name]

    def get_data_handler(self, format_name: str) -> Type[BaseData]:
        """Get data handler class for format."""
        if format_name not in self._data_handlers:
            raise ValueError(f"Unknown format: {format_name}")
        return self._data_handlers[format_name]

    def get_supported_formats(self) -> List[str]:
        """Get list of supported formats."""
        return list(self._readers.keys())

    def list_format_definitions(self) -> List[str]:
        """Get list of available format definitions."""
        return list(self._format_definitions.keys())

    def get_config_file_path(self, format_name: str) -> Optional[Path]:
        """Get path to the JSON config file for a format."""
        config_file = self.configs_dir / f"{format_name}.json"
        return config_file if config_file.exists() else None

    def reload_format_definitions(self):
        """Reload all format definitions from JSON files."""
        self._format_definitions.clear()
        self._load_format_definitions()

    def save_format_definition(self, format_name: str, filepath: Union[str, Path]):
        """Save a format definition to file."""
        format_def = self.get_format_definition(format_name)
        if format_def:
            format_def.save_to_file(filepath)
        else:
            raise ValueError(f"Format definition '{format_name}' not found")

    def load_format_definition(self, filepath: Union[str, Path]) -> FormatDefinition:
        """Load format definition from file and register it."""
        format_def = FormatDefinition.load_from_file(filepath, self.ureg)
        self.register_format_definition(format_def)
        return format_def

    def convert_between_units(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert value between arbitrary units using shared registry."""
        try:
            from_unit_obj = self.ureg.parse_expression(from_unit)
            to_unit_obj = self.ureg.parse_expression(to_unit)
            quantity = value * from_unit_obj
            return quantity.to(to_unit_obj).magnitude
        except Exception:
            return value


# Global registry instance
format_registry = FormatRegistry()
