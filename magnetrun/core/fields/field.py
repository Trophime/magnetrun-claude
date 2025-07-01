"""Field definition with Pint integration."""

from dataclasses import dataclass
from typing import List, Dict, Any
from pint import UnitRegistry

from .field_types import FieldType


@dataclass
class Field:
    """Simple field definition with Pint integration."""

    name: str
    field_type: FieldType
    unit: str
    symbol: str = ""
    description: str = ""

    def __post_init__(self):
        """Set default symbol if not provided."""
        if not self.symbol:
            self.symbol = self._get_default_symbol()

    def _get_default_symbol(self) -> str:
        """Get default symbol based on field type."""
        symbol_map = {
            FieldType.TIME: "t",
            FieldType.MAGNETIC_FIELD: "B",
            FieldType.CURRENT: "I",
            FieldType.VOLTAGE: "U",
            FieldType.TEMPERATURE: "T",
            FieldType.PRESSURE: "P",
            FieldType.FLOW_RATE: "Q",
            FieldType.POWER: "P",
            FieldType.ROTATION_SPEED: "ω",
            FieldType.PERCENTAGE: "%",
            FieldType.RESISTANCE: "R",
            FieldType.COORDINATE: "x",
            FieldType.LENGTH: "L",
            FieldType.AREA: "A",
            FieldType.VOLUME: "V",
            FieldType.INDEX: "idx",
        }
        return symbol_map.get(self.field_type, self.name)

    def get_unit_object(self, ureg: UnitRegistry) -> Any:
        """Get Pint unit object."""
        try:
            return ureg.parse_expression(self.unit)
        except Exception:
            # Fallback to dimensionless if unit parsing fails
            return ureg.dimensionless

    def convert_value(
        self, value: float, target_unit: str, ureg: UnitRegistry
    ) -> float:
        """Convert value from field unit to target unit."""
        try:
            source_unit = self.get_unit_object(ureg)
            target_unit_obj = ureg.parse_expression(target_unit)

            # Create quantity with source unit
            quantity = value * source_unit
            # Convert to target unit
            converted = quantity.to(target_unit_obj)
            return converted.magnitude
        except Exception:
            # Return original value if conversion fails
            return value

    def convert_values(
        self, values: List[float], target_unit: str, ureg: UnitRegistry
    ) -> List[float]:
        """Convert list of values from field unit to target unit."""
        return [self.convert_value(val, target_unit, ureg) for val in values]

    def format_unit(self, ureg: UnitRegistry, format_style: str = "~P") -> str:
        """Format unit string using Pint formatting."""
        try:
            unit_obj = self.get_unit_object(ureg)
            return f"{unit_obj:{format_style}}"
        except Exception:
            return self.unit

    def get_label(
        self, ureg: UnitRegistry, show_unit: bool = True, format_style: str = "~P"
    ) -> str:
        """Get formatted label for plots: 'Symbol [unit]' or just 'Symbol'."""
        if show_unit:
            unit_str = self.format_unit(ureg, format_style)
            if unit_str and unit_str != "dimensionless":
                return f"{self.symbol} [{unit_str}]"
        return self.symbol

    def is_compatible_unit(self, target_unit: str, ureg: UnitRegistry) -> bool:
        """Check if target unit is compatible with field unit."""
        try:
            source_unit = self.get_unit_object(ureg)
            target_unit_obj = ureg.parse_expression(target_unit)

            # Check if they have the same dimensionality
            return source_unit.check(f"[{target_unit_obj.dimensionality}]")
        except Exception:
            return False

    def get_conversion_factor(self, target_unit: str, ureg: UnitRegistry) -> float:
        """Get conversion factor to target unit (multiply field values by this)."""
        try:
            return self.convert_value(1.0, target_unit, ureg)
        except Exception:
            return 1.0

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "field_type": self.field_type.value,
            "unit": self.unit,
            "symbol": self.symbol,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Field":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            field_type=FieldType(data["field_type"]),
            unit=data["unit"],
            symbol=data.get("symbol", ""),
            description=data.get("description", ""),
        )