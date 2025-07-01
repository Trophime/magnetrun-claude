"""Registry for managing format definitions with shared unit registry."""

from typing import Dict, List, Optional, Union
from pathlib import Path
from pint import UnitRegistry

from .format_definition import FormatDefinition


class FormatRegistry:
    """Registry for managing format definitions with shared unit registry."""

    def __init__(self, ureg: Optional[UnitRegistry] = None):
        self.ureg = ureg or self._create_unit_registry()
        self.formats: Dict[str, FormatDefinition] = {}
        self._load_builtin_formats()

    def _create_unit_registry(self) -> UnitRegistry:
        """Create shared unit registry."""
        ureg = UnitRegistry()

        # Add only the custom units we need
        ureg.define("percent = 0.01 = %")
        ureg.define("ppm = 1e-6")
        ureg.define("var = 1")  # For reactive power (VAr)

        return ureg

    def _load_builtin_formats(self):
        """Load built-in format definitions."""
        from .builtin_formats import create_pupitre_format, create_bprofile_format, create_pigbrother_format
        
        # Create built-in format definitions
        pupitre_format = create_pupitre_format(self.ureg)
        self.register_format(pupitre_format)

        bprofile_format = create_bprofile_format(self.ureg)
        self.register_format(bprofile_format)

        pigbrother_format = create_pigbrother_format(self.ureg)
        self.register_format(pigbrother_format)

    def register_format(self, format_def: FormatDefinition):
        """Register a format definition."""
        # Ensure format uses shared unit registry
        format_def.ureg = self.ureg
        self.formats[format_def.format_name] = format_def

    def get_format(self, format_name: str) -> Optional[FormatDefinition]:
        """Get format definition by name."""
        return self.formats.get(format_name)

    def list_formats(self) -> List[str]:
        """Get list of available format names."""
        return list(self.formats.keys())

    def save_format(self, format_name: str, filepath: Union[str, Path]):
        """Save a format definition to file."""
        format_def = self.get_format(format_name)
        if format_def:
            format_def.save_to_file(filepath)
        else:
            raise ValueError(f"Format '{format_name}' not found")

    def load_format(self, filepath: Union[str, Path]) -> FormatDefinition:
        """Load format definition from file and register it."""
        format_def = FormatDefinition.load_from_file(filepath, self.ureg)
        self.register_format(format_def)
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