"""Main MagnetData class with updated field management integration."""

from typing import Union, Optional, Tuple, Any, List
import pandas as pd
import numpy as np
from pathlib import Path
from .base_data import BaseData

# CORRECTED: Import from new locations
from ..formats import FormatRegistry, FormatDefinition
from ..core.fields import Field, FieldType, create_format_config_from_data

from ..exceptions import FileFormatError


class MagnetData:
    """Main factory class for handling magnetic measurement data with updated field management."""

    def __init__(
        self,
        data_handler: BaseData,
        format_name: str,
        field_registry: Optional[FormatRegistry] = None,
    ):
        self._data_handler = data_handler
        self._format_name = format_name
        self._field_registry = field_registry or FormatRegistry()

        # Get or create format definition
        self._format_def = self._field_registry.get_format_definition(format_name)
        if not self._format_def:
            # Create basic format definition from data keys if not found
            self._format_def = create_format_config_from_data(
                self._data_handler.keys, format_name, self._field_registry.ureg
            )
            self._field_registry.register_format_definition(self._format_def)

    @classmethod
    def from_file(
        cls, filepath: Union[str, Path], field_config: Optional[Union[str, Path]] = None
    ) -> "MagnetData":
        """Create MagnetData by auto-detecting file format."""
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        # Import here to avoid circular imports
        from ..io.format_detector import FormatDetector
        from ..formats.registry import get_format_registry

        # Detect format
        detector = FormatDetector()
        format_name = detector.detect_format(filepath)

        if format_name is None:
            raise FileFormatError(f"Unknown file format: {filepath}")

        # Get reader and read file
        reader = detector.get_reader_for_file(filepath)
        file_data = reader.read(filepath)

        # Create appropriate data handler
        handler_class = get_format_registry().get_data_handler(format_name)

        # Create handler based on format
        if format_name in ["bprofile", "pupitre"]:
            handler = handler_class(
                filename=str(filepath),
                data=file_data["data"],
                metadata=file_data["metadata"],
            )
        elif format_name == "pigbrother":
            handler = handler_class(
                filename=str(filepath),
                groups=file_data["groups"],
                keys=file_data["keys"],
                data=file_data["data"],
                metadata=file_data["metadata"],
            )
        else:
            raise FileFormatError(
                f"Handler creation not implemented for format: {format_name}"
            )

        # Create field registry
        field_registry = get_format_registry()

        # Load field configuration if provided
        if field_config:
            try:
                custom_format = FormatDefinition.load_from_file(
                    field_config, field_registry.ureg
                )
                field_registry.register_format_definition(custom_format)
            except Exception as e:
                print(f"Warning: Could not load field config {field_config}: {e}")

        return cls(handler, format_name, field_registry)

    @classmethod
    def from_pandas(
        cls,
        filename: str,
        data: pd.DataFrame,
        format_type: str = "pupitre",
        field_registry: Optional[FormatRegistry] = None,
    ) -> "MagnetData":
        """Create MagnetData from pandas DataFrame."""
        from ..formats.pupitre_data import PupitreData

        handler = PupitreData(filename, data)
        return cls(handler, format_type, field_registry)

    @classmethod
    def from_dict(
        cls,
        filename: str,
        groups: dict,
        keys: list,
        data: dict,
        format_type: str = "pigbrother",
        field_registry: Optional[FormatRegistry] = None,
    ) -> "MagnetData":
        """Create MagnetData from TDMS dict structure."""
        from ..formats.pigbrother_data import PigbrotherData

        handler = PigbrotherData(filename, groups, keys, data)
        return cls(handler, format_type, field_registry)

    # Delegate properties and methods to handler
    @property
    def filename(self) -> str:
        return self._data_handler.filename

    @property
    def keys(self) -> List[str]:
        return self._data_handler.keys

    @property
    def format_type(self) -> str:
        return self._format_name

    @property
    def metadata(self) -> dict:
        return self._data_handler.metadata

    @property
    def field_registry(self) -> FormatDefinition:
        """Get the format definition (replaces old field registry)."""
        return self._format_def

    @property
    def format_definition(self) -> FormatDefinition:
        """Get the format definition."""
        return self._format_def

    def get_data(self, key: Optional[Union[str, List[str]]] = None) -> pd.DataFrame:
        """Get data for specified keys."""
        return self._data_handler.get_data(key)

    def add_data(
        self,
        key: str,
        formula: str,
        field_type: Optional[str] = None,
        unit: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> None:
        """Add calculated column with field management."""
        # Add data to handler
        self._data_handler.add_data(key, formula)

        # Add field to format definition if not exists
        if not self._format_def.get_field(key):
            # Determine field type
            if field_type:
                try:
                    field_type_enum = FieldType(field_type)
                except ValueError:
                    print(f"Warning: Unknown field type '{field_type}', using INDEX")
                    field_type_enum = FieldType.INDEX
            else:
                from ..core.fields import guess_field_type

                field_type_enum = guess_field_type(key)

            # Determine unit
            if not unit:
                from ..core.fields import guess_unit

                unit = guess_unit(key, field_type_enum)

            # Determine symbol
            if not symbol:
                from ..core.fields import guess_symbol

                symbol = guess_symbol(key, field_type_enum)

            # Create and add field
            field = Field(
                name=key,
                field_type=field_type_enum,
                unit=unit,
                symbol=symbol,
                description=f"Calculated field: {key}",
            )
            self._format_def.add_field(field)

    def remove_data(self, keys: List[str]) -> None:
        """Remove columns."""
        self._data_handler.remove_data(keys)

    def rename_data(self, columns: dict) -> None:
        """Rename columns."""
        self._data_handler.rename_data(columns)

    def get_info(self) -> dict:
        """Get information about the dataset."""
        info = self._data_handler.get_info()

        # Add field information
        info["field_info"] = {
            "format_name": self._format_name,
            "total_fields_defined": len(self._format_def.fields),
            "data_keys_count": len(self.keys),
            "field_coverage": self._get_field_coverage(),
        }

        # Add data shape information if available
        try:
            data = self.get_data()
            info["metadata"]["shape"] = data.shape
        except Exception:
            pass

        return info

    def get_field_info(self, key: str) -> Tuple[str, Any, str]:
        """Get field information for a key."""
        # CORRECTED: Try to get from data handler first (if it has integrated definition)
        if hasattr(self._data_handler, "get_field_info"):
            return self._data_handler.get_field_info(key)

        # Fallback to format definition
        field = self._format_def.get_field(key)
        if field:
            symbol = field.symbol
            unit = field.get_unit_object(self._field_registry.ureg)
            unit_string = field.format_unit(self._field_registry.ureg)
            return symbol, unit, unit_string
        else:
            # Fallback for unknown fields
            return key, None, ""

    def get_display_info(self, key: str) -> Tuple[str, Any, str]:
        """Get display information for a key."""
        # In updated system, display info is the same as field info
        return self.get_field_info(key)

    def get_field_label(self, key: str, show_unit: bool = True) -> str:
        """Get formatted label for plotting."""
        # CORRECTED: Try to get from data handler first (if it has integrated definition)
        if hasattr(self._data_handler, "get_field_label"):
            return self._data_handler.get_field_label(key, show_unit)

        # Fallback to format definition
        field = self._format_def.get_field(key)
        if field:
            return field.get_label(self._field_registry.ureg, show_unit)
        return key

    def convert_field_values(
        self,
        key: str,
        values: Union[List[float], np.ndarray, pd.Series],
        target_unit: str,
    ) -> Union[List[float], np.ndarray, pd.Series]:
        """Convert field values to target unit."""
        # CORRECTED: Try to get from data handler first (if it has integrated definition)
        if hasattr(self._data_handler, "convert_field_values"):
            return self._data_handler.convert_field_values(key, values, target_unit)

        # Fallback to format definition
        field = self._format_def.get_field(key)
        if not field:
            return values

        if isinstance(values, pd.Series):
            converted = field.convert_values(
                values.tolist(), target_unit, self._field_registry.ureg
            )
            return pd.Series(converted, index=values.index)
        elif isinstance(values, np.ndarray):
            converted = field.convert_values(
                values.tolist(), target_unit, self._field_registry.ureg
            )
            return np.array(converted)
        else:
            return field.convert_values(values, target_unit, self._field_registry.ureg)

    def _get_field_coverage(self) -> float:
        """Calculate percentage of keys that have field definitions."""
        if not self.keys:
            return 0.0

        defined_count = sum(
            1 for key in self.keys if self._format_def.get_field(key) is not None
        )
        return (defined_count / len(self.keys)) * 100

    def validate_keys(self, keys: Union[str, List[str]]) -> List[str]:
        """Validate that keys exist in the dataset."""
        return self._data_handler.validate_keys(keys)

    def has_key(self, key: str) -> bool:
        """Check if a key exists in the dataset."""
        return key in self.keys

    def get_numeric_keys(self) -> List[str]:
        """Get list of numeric keys suitable for analysis."""
        try:
            data = self.get_data()
            numeric_columns = data.select_dtypes(include=[np.number]).columns.tolist()
            return [k for k in numeric_columns if k in self.keys]
        except Exception:
            return []

    def get_data_summary(self) -> dict:
        """Get summary statistics for numeric columns with field information."""
        try:
            numeric_keys = self.get_numeric_keys()
            if not numeric_keys:
                return {}

            data = self.get_data(numeric_keys)
            summary = data.describe().to_dict()

            # Add field information
            for key in summary:
                field = self._format_def.get_field(key)
                if field:
                    summary[key]["symbol"] = field.symbol
                    summary[key]["unit"] = field.format_unit(self._field_registry.ureg)
                    summary[key]["field_type"] = field.field_type.value
                    summary[key]["label"] = field.get_label(self._field_registry.ureg)
                else:
                    summary[key]["symbol"] = key
                    summary[key]["unit"] = ""
                    summary[key]["field_type"] = "unknown"
                    summary[key]["label"] = key

            return summary
        except Exception as e:
            return {"error": str(e)}

    def validate_field_data(self, key: str) -> dict:
        """Validate data for a specific field."""
        field = self._format_def.get_field(key)
        if not field:
            return {"status": "no_field_definition", "key": key}

        try:
            data = self.get_data([key])
            values = data[key].dropna()

            validation_result = {
                "key": key,
                "field_type": field.field_type.value,
                "total_values": len(data),
                "valid_values": len(values),
                "invalid_values": 0,
                "null_values": len(data) - len(values),
                "issues": [],
                "field_unit": field.unit,
                "field_symbol": field.symbol,
            }

            # Basic validation - check for numeric values where expected
            if field.field_type != FieldType.INDEX:
                try:
                    numeric_values = pd.to_numeric(values, errors="coerce")
                    invalid_mask = numeric_values.isna()
                    invalid_count = invalid_mask.sum()

                    validation_result["invalid_values"] = invalid_count
                    validation_result["valid_values"] = len(values) - invalid_count

                    if invalid_count > 0:
                        validation_result["issues"].append(
                            {
                                "type": "non_numeric_values",
                                "count": invalid_count,
                                "description": f"Found {invalid_count} non-numeric values",
                            }
                        )
                except Exception as e:
                    validation_result["issues"].append(
                        {"type": "validation_error", "description": str(e)}
                    )

            # Determine overall status
            if (
                validation_result["invalid_values"] == 0
                and len(validation_result["issues"]) == 0
            ):
                validation_result["status"] = "valid"
            elif (
                validation_result["invalid_values"] < validation_result["valid_values"]
            ):
                validation_result["status"] = "mostly_valid"
            else:
                validation_result["status"] = "invalid"

            return validation_result

        except Exception as e:
            return {"status": "error", "key": key, "error": str(e)}

    def get_field_validation_summary(self) -> dict:
        """Get validation summary for all fields."""
        validation_results = {}
        for key in self.keys:
            validation_results[key] = self.validate_field_data(key)

        # Calculate summary statistics
        total_fields = len(validation_results)
        valid_fields = sum(
            1 for r in validation_results.values() if r.get("status") == "valid"
        )
        mostly_valid_fields = sum(
            1 for r in validation_results.values() if r.get("status") == "mostly_valid"
        )
        invalid_fields = sum(
            1
            for r in validation_results.values()
            if r.get("status") in ["invalid", "error"]
        )
        undefined_fields = sum(
            1
            for r in validation_results.values()
            if r.get("status") == "no_field_definition"
        )

        return {
            "summary": {
                "total_fields": total_fields,
                "valid_fields": valid_fields,
                "mostly_valid_fields": mostly_valid_fields,
                "invalid_fields": invalid_fields,
                "undefined_fields": undefined_fields,
                "coverage_percent": (
                    ((total_fields - undefined_fields) / total_fields * 100)
                    if total_fields > 0
                    else 0
                ),
                "quality_percent": (
                    ((valid_fields + mostly_valid_fields) / total_fields * 100)
                    if total_fields > 0
                    else 0
                ),
            },
            "field_results": validation_results,
        }

    def save_format_definition(self, filepath: Union[str, Path]) -> None:
        """Save the current format definition to file."""
        self._format_def.save_to_file(filepath)

    def load_format_definition(self, filepath: Union[str, Path]) -> None:
        """Load format definition from file and apply to current data."""
        loaded_format = FormatDefinition.load_from_file(
            filepath, self._field_registry.ureg
        )

        # Update format name to match current data
        loaded_format.format_name = self._format_name

        # Register the loaded format
        self._field_registry.register_format_definition(loaded_format)
        self._format_def = loaded_format

    def auto_validate_units(self) -> dict:
        """Automatically validate unit definitions for all fields."""
        validation_results = {}

        for field_name in self._format_def.list_fields():
            validation_results[field_name] = self._format_def.validate_field_unit(
                field_name
            )

        # Summary
        valid_units = sum(
            1 for r in validation_results.values() if r.get("valid", False)
        )
        total_fields = len(validation_results)

        return {
            "summary": {
                "total_fields": total_fields,
                "valid_units": valid_units,
                "invalid_units": total_fields - valid_units,
                "validity_percent": (
                    (valid_units / total_fields * 100) if total_fields > 0 else 0
                ),
            },
            "field_results": validation_results,
        }

    def get_format_statistics(self) -> dict:
        """Get comprehensive statistics about the format and data."""
        field_type_counts = {}
        unit_counts = {}

        for field in self._format_def.fields.values():
            # Count field types
            field_type = field.field_type.value
            field_type_counts[field_type] = field_type_counts.get(field_type, 0) + 1

            # Count units
            unit = field.unit
            unit_counts[unit] = unit_counts.get(unit, 0) + 1

        return {
            "format_name": self._format_name,
            "total_defined_fields": len(self._format_def.fields),
            "total_data_keys": len(self.keys),
            "field_coverage_percent": self._get_field_coverage(),
            "field_type_distribution": field_type_counts,
            "unit_distribution": unit_counts,
            "metadata": self._format_def.metadata,
        }
