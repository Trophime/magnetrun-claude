# magnetrun/formats/format_definition.py
"""Format definition class - separated to avoid circular imports."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from pint import UnitRegistry
from ..core.fields import Field  # Import Field to avoid circular import

# Global ureg instance
_global_ureg = None


def get_global_ureg() -> UnitRegistry:
    """Get the global UnitRegistry instance."""
    global _global_ureg
    # print("get_global_ureg", _global_ureg, flush=True)
    if _global_ureg is None:
        _global_ureg = UnitRegistry(system="SI")
        _global_ureg.define("percent = 0.01 = %")
        _global_ureg.define("ppm = 1e-6")
        _global_ureg.define("var = 1")  # For reactive power (VAr)
    return _global_ureg


class FormatDefinition:
    """Defines the structure of a data format with Pint integration."""

    def __init__(self, format_name: str, ureg: Optional[UnitRegistry] = None):
        self.format_name = format_name
        self.fields: Dict[str, Field] = {}  # Use string annotation to avoid import
        self.metadata: Dict = {}
        self.ureg = get_global_ureg()

    def add_field(self, field):
        """Add a field to this format."""
        self.fields[field.name] = field

    def get_field(self, name: str):
        """Get field by name."""
        return self.fields.get(name)

    def list_fields(self) -> List[str]:
        """Get list of field names."""
        return list(self.fields.keys())

    def get_fields_by_type(self, field_type) -> List:
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

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "format_name": self.format_name,
            "metadata": self.metadata,
            "fields": [field.to_dict() for field in self.fields.values()],
        }

    @classmethod
    def from_dict(
        cls, data: Dict, ureg: Optional[UnitRegistry] = None
    ) -> "FormatDefinition":
        """Create from dictionary."""
        format_def = cls(data["format_name"], ureg)
        format_def.metadata = data.get("metadata", {})

        # Import Field here to avoid circular import
        from ..core.fields import Field

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
    def load_from_file(
        cls, filepath: Union[str, Path], ureg: Optional[UnitRegistry] = None
    ) -> "FormatDefinition":
        """Load format definition from JSON file."""
        filepath = Path(filepath)
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls.from_dict(data, ureg)
