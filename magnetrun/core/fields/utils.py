# magnetrun/core/fields/utils.py (UPDATED)
"""Utility functions for field management and format creation."""

from typing import List, Optional
from pint import UnitRegistry

from .field import Field
from .field_types import FieldType


def create_format_config_from_data(data_keys: List[str], format_name: str):
    """Create a format configuration from a list of data keys (for new formats)."""
    # Import here to avoid circular import
    from ...formats.format_definition import get_global_ureg, FormatDefinition

    ureg = get_global_ureg()
    format_def = FormatDefinition(format_name, ureg)

    for key in data_keys:
        # Simple heuristic to guess field type
        field_type = guess_field_type(key)
        unit = guess_unit(key, field_type)
        symbol = guess_symbol(key, field_type)

        field = Field(
            name=key,
            field_type=field_type,
            unit=unit,
            symbol=symbol,
            description=f"Auto-detected field: {key}",
        )
        format_def.add_field(field)

    return format_def


def guess_field_type(name: str) -> FieldType:
    """Simple heuristic to guess field type from name."""
    name_lower = name.lower()

    if "time" in name_lower or name_lower == "t":
        return FieldType.TIME
    elif "field" in name_lower or name_lower.startswith("b"):
        return FieldType.MAGNETIC_FIELD
    elif name_lower.startswith("i") or "current" in name_lower:
        return FieldType.CURRENT
    elif name_lower.startswith("u") or "voltage" in name_lower:
        return FieldType.VOLTAGE
    elif name_lower.startswith("t") or "temp" in name_lower:
        return FieldType.TEMPERATURE
    elif "pressure" in name_lower or name_lower.startswith("p"):
        return FieldType.PRESSURE
    elif "flow" in name_lower or "debit" in name_lower:
        return FieldType.FLOW_RATE
    elif "power" in name_lower:
        return FieldType.POWER
    elif "rpm" in name_lower:
        return FieldType.ROTATION_SPEED
    elif "dr" in name_lower or "resistance" in name_lower:
        return FieldType.RESISTANCE
    else:
        return FieldType.INDEX  # Default fallback


def guess_unit(name: str, field_type: FieldType) -> str:
    """Simple heuristic to guess unit from field type."""
    unit_map = {
        FieldType.TIME: "second",
        FieldType.MAGNETIC_FIELD: "tesla",
        FieldType.CURRENT: "ampere",
        FieldType.VOLTAGE: "volt",
        FieldType.TEMPERATURE: "celsius",
        FieldType.PRESSURE: "bar",
        FieldType.FLOW_RATE: "liter/minute",
        FieldType.POWER: "watt",
        FieldType.ROTATION_SPEED: "rpm",
        FieldType.PERCENTAGE: "percent",
        FieldType.RESISTANCE: "ohm",
        FieldType.INDEX: "dimensionless",
    }
    return unit_map.get(field_type, "dimensionless")


def guess_symbol(name: str, field_type: FieldType) -> str:
    """Simple heuristic to guess symbol from name and type."""
    name_lower = name.lower()

    # Specific name patterns
    if "field" in name_lower:
        return "B"
    elif name_lower.startswith("i"):
        return "I"
    elif name_lower.startswith("u"):
        return "U"
    elif name_lower.startswith("t") and "temp" in name_lower:
        return "T"
    elif "rpm" in name_lower:
        return "ω"
    elif "pressure" in name_lower:
        return "P"
    elif "flow" in name_lower:
        return "Q"
    elif "power" in name_lower:
        return "P"
    elif "resistance" in name_lower or "dr" in name_lower:
        return "R"
    else:
        # Use field type default
        field = Field("temp", field_type, "dimensionless")
        return field._get_default_symbol()


def validate_format_definition(format_def) -> dict:
    """Validate a format definition for common issues."""
    issues = []
    warnings = []

    # Check for duplicate symbols
    symbols = {}
    for field_name, field in format_def.fields.items():
        if field.symbol in symbols:
            issues.append(
                f"Duplicate symbol '{field.symbol}' used by '{field_name}' and '{symbols[field.symbol]}'"
            )
        else:
            symbols[field.symbol] = field_name

    # Check for missing descriptions
    missing_descriptions = [
        name for name, field in format_def.fields.items() if not field.description
    ]
    if missing_descriptions:
        warnings.append(f"Fields missing descriptions: {missing_descriptions}")

    # Check for unusual units
    for field_name, field in format_def.fields.items():
        try:
            unit_obj = field.get_unit_object(format_def.ureg)
            if (
                str(unit_obj.dimensionality) == "dimensionless"
                and field.field_type != FieldType.INDEX
            ):
                if field.field_type not in [FieldType.PERCENTAGE, FieldType.TIME]:
                    warnings.append(
                        f"Field '{field_name}' has dimensionless unit but type '{field.field_type.value}'"
                    )
        except Exception as e:
            issues.append(f"Invalid unit '{field.unit}' for field '{field_name}': {e}")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "total_fields": len(format_def.fields),
        "field_types": {
            ft.value: len(format_def.get_fields_by_type(ft)) for ft in FieldType
        },
    }


def merge_format_definitions(base_format, overlay_format):
    """Merge two format definitions, with overlay taking precedence."""
    # Import here to avoid circular import
    from ...formats.format_definition import FormatDefinition

    merged = FormatDefinition(base_format.format_name, base_format.ureg)

    # Copy base metadata and fields
    merged.metadata = base_format.metadata.copy()
    for field in base_format.fields.values():
        merged.add_field(field)

    # Apply overlay
    merged.metadata.update(overlay_format.metadata)
    for field in overlay_format.fields.values():
        merged.add_field(field)  # This will overwrite existing fields with same name

    return merged


def create_field_summary(format_def) -> dict:
    """Create a summary of fields in a format definition."""
    summary = {
        "format_name": format_def.format_name,
        "total_fields": len(format_def.fields),
        "by_type": {},
        "units_used": set(),
        "symbols_used": set(),
    }

    # Count by type
    for field_type in FieldType:
        fields_of_type = format_def.get_fields_by_type(field_type)
        if fields_of_type:
            summary["by_type"][field_type.value] = {
                "count": len(fields_of_type),
                "fields": [f.name for f in fields_of_type],
            }

    # Collect units and symbols
    for field in format_def.fields.values():
        summary["units_used"].add(field.unit)
        summary["symbols_used"].add(field.symbol)

    # Convert sets to sorted lists for JSON serialization
    summary["units_used"] = sorted(list(summary["units_used"]))
    summary["symbols_used"] = sorted(list(summary["symbols_used"]))

    return summary
