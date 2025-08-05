"""Housing Configuration module for loading and managing JSON-based housing configurations."""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# Import field types from magnetrun.core.fields
try:
    from ..core.fields.field_types import FieldType
    from ..core.fields.field import Field
    from ..formats import FormatRegistry
except ImportError:
    # Fallback for development/testing
    print(
        "Warning: magnetrun.core.fields not available. Some features will be limited."
    )
    FieldType = None
    Field = None
    FormatRegistry = None


class MagnetType(Enum):
    """Enumeration of supported magnet types."""

    INSERT = "Insert"
    BITTERS = "Bitters"
    SUPRAS = "Supras"


class DataFormat(Enum):
    """Supported data formats."""

    PUPITRE = "pupitre"
    PIGBROTHER = "pigbrother"


@dataclass
class HousingConfig:
    """Configuration for a specific housing type loaded from JSON."""

    name: str
    config_data: Dict[str, Any]
    format_registry: Optional[Any] = None  # FormatRegistry instance

    def __post_init__(self):
        """Initialize format registry if available."""
        if FormatRegistry and not self.format_registry:
            self.format_registry = FormatRegistry()

        # MSite integration for geometry-based filtering
        self.msite_object = None
        # Load voltage tap locations from config data
        self._load_voltage_tap_locations_from_config()

    def _load_voltage_tap_locations_from_config(self):
        """Load voltage tap locations from config data structure."""
        self.voltage_tap_locations = {}

        for magnet_type_str in ["Insert", "Bitters", "Supras"]:
            if magnet_type_str in self.config_data:
                magnet_config = self.config_data[magnet_type_str]
                if (
                    isinstance(magnet_config, dict)
                    and "voltage_tap_locations" in magnet_config
                ):
                    locations = magnet_config["voltage_tap_locations"]
                    if isinstance(locations, dict):
                        self.voltage_tap_locations.update(locations)

        if self.voltage_tap_locations:
            print(
                f"Loaded {len(self.voltage_tap_locations)} voltage tap locations from {self.name} config"
            )

    def get_magnet_voltage_tap_locations(
        self, magnet_type: MagnetType
    ) -> Dict[str, List[float]]:
        """Get voltage tap locations for a specific magnet type."""
        magnet_config = self.config_data.get(magnet_type.value, {})
        if isinstance(magnet_config, dict):
            return magnet_config.get("voltage_tap_locations", {})
        return {}

    def set_magnet_voltage_tap_locations(
        self, magnet_type: MagnetType, tap_locations: Dict[str, List[float]]
    ) -> None:
        """Set voltage tap locations for a specific magnet type."""
        if magnet_type.value not in self.config_data:
            self.config_data[magnet_type.value] = {}

        magnet_config = self.config_data[magnet_type.value]
        if not isinstance(magnet_config, dict):
            self.config_data[magnet_type.value] = {}
            magnet_config = self.config_data[magnet_type.value]

        magnet_config["voltage_tap_locations"] = tap_locations.copy()

        # Update the combined voltage_tap_locations
        self._load_voltage_tap_locations_from_config()

    @classmethod
    def from_json_file(
        cls, housing_name: str, config_path: Optional[str] = None
    ) -> "HousingConfig":
        """Load housing configuration from JSON file."""
        if config_path is None:
            # Default config path
            config_path = (
                Path(__file__).parent / "configs" / f"{housing_name.lower()}.json"
            )

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Housing config file not found: {config_path}")

        with open(config_path, "r") as f:
            config_data = json.load(f)

        config = cls(name=housing_name, config_data=config_data)

        return config

    @classmethod
    def from_dict(
        cls, housing_name: str, config_dict: Dict[str, Any]
    ) -> "HousingConfig":
        """Create housing configuration from dictionary."""
        config = cls(name=housing_name, config_data=config_dict)

        return config

    def save_to_file(self, config_path: Optional[str] = None) -> None:
        """Save housing configuration to JSON file."""
        if config_path is None:
            config_path = (
                Path(__file__).parent / "configs" / f"{self.name.lower()}.json"
            )

        # Update timestamp
        self.update_timestamp()

        # Voltage tap locations are already in the config_data structure
        with open(config_path, "w") as f:
            json.dump(self.config_data, f, indent=2, sort_keys=False)

    def update_timestamp(self) -> None:
        """Update the timestamp in metadata."""
        if "metadata" not in self.config_data:
            self.config_data["metadata"] = {}
        self.config_data["metadata"]["timestamp"] = datetime.utcnow().isoformat() + "Z"

    def get_metadata(self) -> Dict[str, Any]:
        """Get housing metadata."""
        return self.config_data.get("metadata", {})

    def set_description(self, description: str) -> None:
        """Set housing description."""
        if "metadata" not in self.config_data:
            self.config_data["metadata"] = {}
        self.config_data["metadata"]["description"] = description

    def get_magnet_config(
        self, magnet_type: MagnetType, data_format: DataFormat
    ) -> Dict[str, Any]:
        """Get configuration for a specific magnet type and data format."""
        magnet_key = magnet_type.value
        format_key = data_format.value

        return self.config_data.get(magnet_key, {}).get(format_key, {})

    def set_magnet_config(
        self, magnet_type: MagnetType, data_format: DataFormat, config: Dict[str, Any]
    ) -> None:
        """Set configuration for a specific magnet type and data format."""
        magnet_key = magnet_type.value
        format_key = data_format.value

        if magnet_key not in self.config_data:
            self.config_data[magnet_key] = {}

        self.config_data[magnet_key][format_key] = config

    def get_field_config(
        self, magnet_type: MagnetType, data_format: DataFormat, field_category: str
    ) -> Dict[str, Any]:
        """Get complete field configuration including fields, field_type, symbol, unit, and optional formula."""
        magnet_config = self.get_magnet_config(magnet_type, data_format)
        return magnet_config.get(field_category, {})

    def create_field_object(
        self, magnet_type: MagnetType, data_format: DataFormat, field_category: str
    ) -> Optional[Any]:
        """Create a Field object from housing configuration."""
        if not Field or not FieldType:
            return None

        field_config = self.get_field_config(magnet_type, data_format, field_category)
        if not field_config:
            return None

        try:
            field_type = FieldType(field_config.get("field_type", "current"))

            # Use the field_category as the field name (this will be used for renaming)
            field_name = field_category

            return Field(
                name=field_name,
                field_type=field_type,
                unit=field_config.get("unit", "dimensionless"),
                symbol=field_config.get("symbol", field_name),
                description=f"{magnet_type.value} {field_category} for {data_format.value} format",
            )
        except (ValueError, KeyError) as e:
            print(f"Error creating field object for {field_category}: {e}")
            return None

    def get_fields(
        self, magnet_type: MagnetType, data_format: DataFormat, field_category: str
    ) -> List[str]:
        """Get source field names for a specific category."""
        field_config = self.get_field_config(magnet_type, data_format, field_category)

        # Handle both old format (list) and new format (dict with fields key)
        if isinstance(field_config, list):
            return field_config
        elif isinstance(field_config, dict):
            fields = field_config.get("fields", [])
            return fields if isinstance(fields, list) else [fields] if fields else []
        else:
            return []

    def get_field_type(
        self, magnet_type: MagnetType, data_format: DataFormat, field_category: str
    ) -> Optional[str]:
        """Get the field type for a category."""
        field_config = self.get_field_config(magnet_type, data_format, field_category)
        if isinstance(field_config, dict):
            return field_config.get("field_type")
        return None

    def get_field_symbol(
        self, magnet_type: MagnetType, data_format: DataFormat, field_category: str
    ) -> Optional[str]:
        """Get the symbol for a field category."""
        field_config = self.get_field_config(magnet_type, data_format, field_category)
        if isinstance(field_config, dict):
            return field_config.get("symbol")
        return None

    def get_field_unit(
        self, magnet_type: MagnetType, data_format: DataFormat, field_category: str
    ) -> Optional[str]:
        """Get the unit for a field category."""
        field_config = self.get_field_config(magnet_type, data_format, field_category)
        if isinstance(field_config, dict):
            return field_config.get("unit")
        return None

    def get_field_formula(
        self, magnet_type: MagnetType, data_format: DataFormat, field_category: str
    ) -> Optional[str]:
        """Get the formula for calculating fields in this category."""
        field_config = self.get_field_config(magnet_type, data_format, field_category)
        if isinstance(field_config, dict):
            return field_config.get("formula")
        return None

    def is_field_required(
        self, magnet_type: MagnetType, data_format: DataFormat, field_category: str
    ) -> bool:
        """Check if fields in this category are required in the data file."""
        field_config = self.get_field_config(magnet_type, data_format, field_category)
        if isinstance(field_config, dict):
            return field_config.get(
                "required", True
            )  # Default to True for backwards compatibility
        return True  # Old format assumes all fields are required

    def load_msite_geometry(self, msite_file: str) -> bool:
        """Load MSite geometry for voltage tap filtering."""
        try:
            # Import here to avoid circular imports
            try:
                from python_magnetgeo.MSite import MSite
            except ImportError:
                print("Warning: magnetgeo not available for MSite loading")
                return False

            self.msite_object = MSite.from_yaml(msite_file)
            self.msite_object.update()
            print(f"Loaded MSite geometry from {msite_file}")
            return True
        except Exception as e:
            print(f"Error loading MSite geometry: {e}")
            return False

    def set_voltage_tap_locations(self, tap_locations: Dict[str, List[float]]) -> None:
        """Set voltage tap locations (legacy method - consider using magnet-specific methods)."""
        # This is now a legacy method - we recommend using set_magnet_voltage_tap_locations
        print(
            "Warning: set_voltage_tap_locations is deprecated. Use set_magnet_voltage_tap_locations instead."
        )

        # For backwards compatibility, assume these are Insert locations
        self.set_magnet_voltage_tap_locations(MagnetType.INSERT, tap_locations)

    def add_voltage_tap_location(
        self, magnet_type: MagnetType, tap_name: str, coordinates: List[float]
    ) -> None:
        """Add a single voltage tap location for a specific magnet type."""
        if len(coordinates) != 3:
            raise ValueError("Coordinates must be [x, y, z]")

        current_locations = self.get_magnet_voltage_tap_locations(magnet_type)
        current_locations[tap_name] = coordinates.copy()
        self.set_magnet_voltage_tap_locations(magnet_type, current_locations)

    def remove_voltage_tap_location(
        self, magnet_type: MagnetType, tap_name: str
    ) -> bool:
        """Remove a voltage tap location for a specific magnet type."""
        current_locations = self.get_magnet_voltage_tap_locations(magnet_type)
        if tap_name in current_locations:
            del current_locations[tap_name]
            self.set_magnet_voltage_tap_locations(magnet_type, current_locations)
            return True
        return False

    def get_voltage_tap_location(self, tap_name: str) -> Optional[List[float]]:
        """Get coordinates [x, y, z] for a specific voltage tap."""
        return self.voltage_tap_locations.get(tap_name)

    def validate_config(self) -> List[str]:
        """Validate the configuration and return any issues found."""
        issues = []

        # Check metadata
        metadata = self.get_metadata()
        if not metadata.get("description"):
            issues.append("Missing description in metadata")

        # Check magnet configurations
        for magnet_type in MagnetType:
            if magnet_type.value not in self.config_data:
                issues.append(f"Missing configuration for {magnet_type.value}")
                continue

            for data_format in DataFormat:
                magnet_config = self.get_magnet_config(magnet_type, data_format)
                if not magnet_config:
                    issues.append(
                        f"Missing {data_format.value} configuration for {magnet_type.value}"
                    )
                    continue

                # Check field configurations
                for category, config in magnet_config.items():
                    if isinstance(config, dict):
                        # Check required fields
                        if not config.get("fields"):
                            issues.append(
                                f"No fields defined for {magnet_type.value}/{data_format.value}/{category}"
                            )

                        if not config.get("field_type"):
                            issues.append(
                                f"No field_type defined for {magnet_type.value}/{data_format.value}/{category}"
                            )

                        if not config.get("symbol"):
                            issues.append(
                                f"No symbol defined for {magnet_type.value}/{data_format.value}/{category}"
                            )

                        if not config.get("unit"):
                            issues.append(
                                f"No unit defined for {magnet_type.value}/{data_format.value}/{category}"
                            )

                        # Validate field_type if FieldType is available
                        if FieldType:
                            try:
                                FieldType(config.get("field_type", ""))
                            except ValueError:
                                issues.append(
                                    f"Invalid field_type '{config.get('field_type')}' for {magnet_type.value}/{data_format.value}/{category}"
                                )

        return issues


class HousingConfigManager:
    """Manager for housing configurations loaded from JSON files."""

    def __init__(self, config_directory: str = None):
        if config_directory is None:
            self.config_directory = Path(__file__).parent / "configs"
        else:
            self.config_directory = Path(config_directory)

        self._configs: Dict[str, HousingConfig] = {}
        self._load_configs()

    def _load_configs(self):
        """Load all housing configuration files from the config directory."""
        if not self.config_directory.exists():
            print(f"Warning: Config directory {self.config_directory} does not exist")
            return

        for config_file in self.config_directory.glob("*.json"):
            housing_name = config_file.stem.upper()  # M9, M10, etc.
            try:
                config = HousingConfig.from_json_file(housing_name, config_file)
                self._configs[housing_name] = config
                print(f"Loaded housing config: {housing_name}")
            except Exception as e:
                print(f"Warning: Failed to load config from {config_file}: {e}")

    def get_config(self, housing_name: str) -> Optional[HousingConfig]:
        """Get housing configuration by name."""
        return self._configs.get(housing_name.upper())

    def list_housings(self) -> List[str]:
        """Get list of available housing names."""
        return list(self._configs.keys())


# Global instance
housing_config_manager = HousingConfigManager()

# Define HOUSING_CONFIGS dictionary for backward compatibility
HOUSING_CONFIGS = {
    housing_name: housing_config_manager.get_config(housing_name)
    for housing_name in housing_config_manager.list_housings()
}


# Convenience functions
def get_housing_config(housing_name: str) -> Optional[HousingConfig]:
    """Get housing configuration by name."""
    return housing_config_manager.get_config(housing_name)


def list_housing_configs() -> List[str]:
    """List all available housing configurations."""
    return housing_config_manager.list_housings()
