"""Updated FormatRegistry that uses the centralized configuration system."""

from typing import Dict, Type, List, Optional, Union
from pathlib import Path
from pint import UnitRegistry

from ..core.base_data import BaseData
from ..io.base_reader import BaseReader
from .format_definition import FormatDefinition
from .centralized_config import ConfigManager, get_config_manager


class FormatRegistry:
    """Unified registry using centralized configuration system."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self._readers: Dict[str, Type[BaseReader]] = {}
        self._data_handlers: Dict[str, Type[BaseData]] = {}
        self._format_definitions: Dict[str, FormatDefinition] = {}
        self.ureg = self._create_unit_registry()

        # Use centralized config manager
        self.config_manager = config_manager or get_config_manager()

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
        """Load format definitions using centralized config system."""
        format_names = self.config_manager.list_configs("format")

        for format_name in format_names:
            try:
                config_data = self.config_manager.load_config("format", format_name)
                if config_data:
                    format_def = FormatDefinition.from_dict(config_data, self.ureg)
                    self._format_definitions[format_def.format_name] = format_def
                    print(
                        f"Loaded format definition '{format_def.format_name}' from centralized config"
                    )
            except Exception as e:
                print(f"Warning: Failed to load format definition '{format_name}': {e}")

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

    def register_format(
        self,
        format_name: str,
        reader_class: Type[BaseReader],
        data_handler_class: Type[BaseData],
    ):
        """Register a format with its reader and data handler."""
        self._readers[format_name] = reader_class
        self._data_handlers[format_name] = data_handler_class

    def register_format_definition(self, format_def: FormatDefinition):
        """Register a format definition and save to centralized config."""
        format_def.ureg = self.ureg  # Ensure shared unit registry
        self._format_definitions[format_def.format_name] = format_def

        # Save to centralized config
        config_data = format_def.to_dict()
        self.config_manager.save_config("format", format_def.format_name, config_data)

    def get_format_definition(self, format_name: str) -> Optional[FormatDefinition]:
        """Get format definition by name."""
        # Try memory cache first
        if format_name in self._format_definitions:
            return self._format_definitions[format_name]

        # Try loading from centralized config
        config_data = self.config_manager.load_config("format", format_name)
        if config_data:
            try:
                format_def = FormatDefinition.from_dict(config_data, self.ureg)
                self._format_definitions[format_name] = format_def
                return format_def
            except Exception as e:
                print(
                    f"Warning: Failed to create format definition from config '{format_name}': {e}"
                )

        return None

    def get_format(self, format_name: str) -> Optional[FormatDefinition]:
        """Alias for get_format_definition for backward compatibility."""
        return self.get_format_definition(format_name)

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

    def list_formats(self) -> List[str]:
        """Get list of available format definitions."""
        # Combine in-memory and config-based formats
        config_formats = set(self.config_manager.list_configs("format"))
        memory_formats = set(self._format_definitions.keys())
        return list(config_formats.union(memory_formats))

    def list_format_definitions(self) -> List[str]:
        """Alias for list_formats for backward compatibility."""
        return self.list_formats()

    def get_configs_directory(self) -> Path:
        """Get the formats configuration directory."""
        return self.config_manager.config_paths.formats_dir

    def reload_formats(self):
        """Reload all format definitions from centralized config."""
        self._format_definitions.clear()
        self.config_manager.clear_cache()
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

    def convert_between_units(
        self, value: float, from_unit: str, to_unit: str
    ) -> float:
        """Convert value between arbitrary units using shared registry."""
        try:
            from_unit_obj = self.ureg.parse_expression(from_unit)
            to_unit_obj = self.ureg.parse_expression(to_unit)
            quantity = value * from_unit_obj
            return quantity.to(to_unit_obj).magnitude
        except Exception:
            return value

    def export_all_formats(self, export_dir: Union[str, Path]) -> Dict[str, bool]:
        """Export all format definitions to a directory."""
        export_dir = Path(export_dir)
        export_dir.mkdir(parents=True, exist_ok=True)

        results = {}
        for format_name in self.list_formats():
            try:
                format_def = self.get_format_definition(format_name)
                if format_def:
                    export_path = export_dir / f"{format_name}.json"
                    format_def.save_to_file(export_path)
                    results[format_name] = True
                else:
                    results[format_name] = False
            except Exception as e:
                print(f"Warning: Failed to export format '{format_name}': {e}")
                results[format_name] = False

        return results

    def import_formats_from_directory(
        self, import_dir: Union[str, Path], overwrite: bool = False
    ) -> Dict[str, bool]:
        """Import format definitions from a directory."""
        import_dir = Path(import_dir)
        if not import_dir.exists():
            return {}

        results = {}
        for json_file in import_dir.glob("*.json"):
            format_name = json_file.stem

            if not overwrite and format_name in self.list_formats():
                results[format_name] = False  # Already exists, not imported
                continue

            try:
                format_def = FormatDefinition.load_from_file(json_file, self.ureg)
                self.register_format_definition(format_def)
                results[format_name] = True
            except Exception as e:
                print(f"Warning: Failed to import format from '{json_file}': {e}")
                results[format_name] = False

        return results

    def get_config_info(self) -> Dict:
        """Get configuration information."""
        base_info = self.config_manager.get_config_info()

        format_info = {
            "loaded_formats": len(self._format_definitions),
            "available_formats": len(self.list_formats()),
            "registered_readers": len(self._readers),
            "registered_handlers": len(self._data_handlers),
            "formats_with_definitions": [
                fmt
                for fmt in self.list_formats()
                if self.get_format_definition(fmt) is not None
            ],
        }

        return {**base_info, **format_info}


# Updated global registry instance that uses centralized config
format_registry = FormatRegistry()
