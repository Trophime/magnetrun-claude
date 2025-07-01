"""Unified registry for data formats, readers, handlers, and field definitions."""

import json
from pathlib import Path
from typing import Dict, Type, List, Optional, Union, Any
from pint import UnitRegistry

from ..core.base_data import BaseData
from ..core.fields import Field, FieldType
from ..io.base_reader import BaseReader


class FormatDefinition:
    """Defines the structure of a data format with Pint integration."""

    def __init__(self, format_name: str, ureg: Optional[UnitRegistry] = None):
        self.format_name = format_name
        self.fields: Dict[str, Field] = {}
        self.metadata: Dict = {}
        self.ureg = ureg or self._create_unit_registry()

    def _create_unit_registry(self) -> UnitRegistry:
        """Create unit registry with custom magnet-specific units."""
        ureg = UnitRegistry()
        ureg.define("percent = 0.01 = %")
        ureg.define("ppm = 1e-6")
        ureg.define("var = 1")  # For reactive power (VAr)
        return ureg

    def add_field(self, field: Field):
        """Add a field to this format."""
        self.fields[field.name] = field

    def get_field(self, name: str) -> Optional[Field]:
        """Get field by name."""
        return self.fields.get(name)

    def list_fields(self) -> List[str]:
        """Get list of field names."""
        return list(self.fields.keys())

    def get_fields_by_type(self, field_type: FieldType) -> List[Field]:
        """Get all fields of a specific type."""
        return [
            field for field in self.fields.values() if field.field_type == field_type
        ]

    def convert_field_values(
        self, field_name: str, values: List[float], target_unit: str
    ) -> List[float]:
        """Convert values for a specific field to target unit."""
        field = self.get_field(field_name)
        if field:
            return field.convert_values(values, target_unit, self.ureg)
        return values

    def get_field_label(self, field_name: str, show_unit: bool = True) -> str:
        """Get formatted label for a field."""
        field = self.get_field(field_name)
        if field:
            return field.get_label(self.ureg, show_unit)
        return field_name

    def validate_field_unit(self, field_name: str) -> Dict[str, Any]:
        """Validate that field unit is properly defined."""
        field = self.get_field(field_name)
        if not field:
            return {"valid": False, "error": "Field not found"}

        try:
            unit_obj = field.get_unit_object(self.ureg)
            return {
                "valid": True,
                "unit_object": unit_obj,
                "formatted_unit": field.format_unit(self.ureg),
                "dimensionality": str(unit_obj.dimensionality),
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}

    def get_compatible_units(self, field_name: str) -> List[str]:
        """Get list of compatible units for a field."""
        field = self.get_field(field_name)
        if not field:
            return []

        # Common compatible units by field type
        compatible_map = {
            FieldType.MAGNETIC_FIELD: ["tesla", "gauss", "millitesla", "T", "G", "mT"],
            FieldType.CURRENT: ["ampere", "milliampere", "kiloampere", "A", "mA", "kA"],
            FieldType.VOLTAGE: ["volt", "millivolt", "kilovolt", "V", "mV", "kV"],
            FieldType.TEMPERATURE: ["celsius", "kelvin", "fahrenheit", "°C", "K", "°F"],
            FieldType.PRESSURE: ["pascal", "bar", "atmosphere", "torr", "Pa", "bar", "atm"],
            FieldType.POWER: ["watt", "kilowatt", "megawatt", "W", "kW", "MW"],
            FieldType.RESISTANCE: ["ohm", "milliohm", "kiloohm", "Ω", "mΩ", "kΩ"],
            FieldType.FLOW_RATE: ["liter/minute", "meter**3/hour", "L/min", "m³/h"],
            FieldType.ROTATION_SPEED: ["rpm", "hertz", "radian/second", "Hz", "rad/s"],
            FieldType.TIME: ["second", "minute", "hour", "s", "min", "h"],
            FieldType.PERCENTAGE: ["percent", "dimensionless", "%"],
            FieldType.COORDINATE: ["meter", "centimeter", "millimeter", "m", "cm", "mm"],
            FieldType.LENGTH: ["meter", "centimeter", "millimeter", "m", "cm", "mm"],
            FieldType.AREA: ["square_meter", "square_centimeter", "m**2", "cm**2"],
            FieldType.VOLUME: ["cubic_meter", "liter", "cubic_centimeter", "m**3", "L", "cm**3"],
            FieldType.INDEX: ["dimensionless"],
        }

        candidates = compatible_map.get(field.field_type, [])
        compatible = []
        for unit_str in candidates:
            if field.is_compatible_unit(unit_str, self.ureg):
                compatible.append(unit_str)
        return compatible

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "format_name": self.format_name,
            "metadata": self.metadata,
            "fields": [field.to_dict() for field in self.fields.values()],
        }

    @classmethod
    def from_dict(cls, data: Dict, ureg: Optional[UnitRegistry] = None) -> "FormatDefinition":
        """Create from dictionary."""
        format_def = cls(data["format_name"], ureg)
        format_def.metadata = data.get("metadata", {})

        for field_data in data.get("fields", []):
            field = Field.from_dict(field_data)
            format_def.add_field(field)

        return format_def

    def save_to_file(self, filepath: Union[str, Path]):
        """Save format definition to JSON file."""
        filepath = Path(filepath)
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: Union[str, Path], ureg: Optional[UnitRegistry] = None) -> "FormatDefinition":
        """Load format definition from JSON file."""
        filepath = Path(filepath)
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls.from_dict(data, ureg)


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
