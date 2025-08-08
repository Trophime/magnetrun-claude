"""Simplified Housing Configuration module for handling JSON structure."""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


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
class GroupConfig:
    """Configuration for a field group."""

    fields: List[str]
    field_type: str
    description: str
    symbol: Optional[str] = None
    unit: Optional[str] = None


@dataclass
class ComputedFieldConfig:
    """Configuration for a computed field."""

    fields: List[str]
    field_type: str
    symbol: str
    unit: str
    formula: str
    description: Optional[str] = None


@dataclass
class CheckConfig:
    """Configuration for data validation checks."""

    check_type: str
    description: str
    fields: Optional[List[str]] = None
    group: Optional[str] = None
    exact: Optional[str] = None
    tolerance: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass
class HousingConfig:
    """Configuration for housing types with JSON structure support."""

    name: str
    config_data: Dict[str, Any]

    def __post_init__(self):
        """Initialize and parse configuration."""
        self._parse_config_structure()

    def _parse_config_structure(self):
        """Parse the JSON configuration structure."""
        # Parse metadata
        self.metadata = self.config_data.get("metadata", {})

        # Parse magnet configurations
        self.magnet_configs = {}
        for magnet_type in MagnetType:
            magnet_key = magnet_type.value
            if magnet_key in self.config_data:
                self.magnet_configs[magnet_type] = {}
                magnet_data = self.config_data[magnet_key]

                for format_type in DataFormat:
                    format_key = format_type.value
                    if format_key in magnet_data:
                        format_config = magnet_data[format_key]
                        self.magnet_configs[magnet_type][format_type] = {
                            "groups": self._parse_groups(
                                format_config.get("groups", {})
                            ),
                            "aliases": format_config.get("aliases", {}),
                            "computed_fields": self._parse_computed_fields(
                                format_config.get("computed_fields", {})
                            ),
                            "checks": self._parse_checks(
                                format_config.get("checks", {})
                            ),
                        }

    def _parse_groups(self, groups_data: Dict[str, Any]) -> Dict[str, GroupConfig]:
        """Parse groups configuration."""
        groups = {}
        for group_name, group_data in groups_data.items():
            groups[group_name] = GroupConfig(
                fields=group_data.get("fields", []),
                field_type=group_data.get("field_type", ""),
                description=group_data.get("description", ""),
                symbol=group_data.get("symbol"),
                unit=group_data.get("unit"),
            )
        return groups

    def _parse_computed_fields(
        self, computed_data: Dict[str, Any]
    ) -> Dict[str, ComputedFieldConfig]:
        """Parse computed fields configuration."""
        computed_fields = {}
        for field_name, field_data in computed_data.items():
            computed_fields[field_name] = ComputedFieldConfig(
                fields=field_data.get("fields", []),
                field_type=field_data.get("field_type", ""),
                symbol=field_data.get("symbol", ""),
                unit=field_data.get("unit", ""),
                formula=field_data.get("formula", ""),
                description=field_data.get("description"),
            )
        return computed_fields

    def _parse_checks(self, checks_data: Dict[str, Any]) -> Dict[str, CheckConfig]:
        """Parse checks configuration."""
        checks = {}
        for check_name, check_data in checks_data.items():
            checks[check_name] = CheckConfig(
                check_type=check_data.get("check_type", ""),
                description=check_data.get("description", ""),
                fields=check_data.get("fields"),
                group=check_data.get("group"),
                exact=check_data.get("exact"),
                tolerance=check_data.get("tolerance"),
                min_value=check_data.get("min_value"),
                max_value=check_data.get("max_value"),
            )
        return checks

    def get_metadata(self) -> Dict[str, Any]:
        """Get housing metadata."""
        return self.metadata

    def set_description(self, description: str) -> None:
        """Set housing description."""
        if "metadata" not in self.config_data:
            self.config_data["metadata"] = {}
        self.config_data["metadata"]["description"] = description
        self.metadata = self.config_data["metadata"]

    def get_magnet_config(
        self, magnet_type: MagnetType, data_format: DataFormat
    ) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific magnet type and data format."""
        return self.magnet_configs.get(magnet_type, {}).get(data_format)

    def set_magnet_config(
        self, magnet_type: MagnetType, data_format: DataFormat, config: Dict[str, Any]
    ) -> None:
        """Set configuration for a specific magnet type and data format."""
        magnet_key = magnet_type.value
        format_key = data_format.value

        if magnet_key not in self.config_data:
            self.config_data[magnet_key] = {}

        self.config_data[magnet_key][format_key] = config

        # Re-parse the configuration
        self._parse_config_structure()

    def get_groups(
        self, magnet_type: MagnetType, data_format: DataFormat
    ) -> Dict[str, GroupConfig]:
        """Get field groups for a magnet type and format."""
        config = self.get_magnet_config(magnet_type, data_format)
        return config.get("groups", {}) if config else {}

    def get_aliases(
        self, magnet_type: MagnetType, data_format: DataFormat
    ) -> Dict[str, str]:
        """Get field aliases for a magnet type and format."""
        config = self.get_magnet_config(magnet_type, data_format)
        return config.get("aliases", {}) if config else {}

    def get_computed_fields(
        self, magnet_type: MagnetType, data_format: DataFormat
    ) -> Dict[str, ComputedFieldConfig]:
        """Get computed fields for a magnet type and format."""
        config = self.get_magnet_config(magnet_type, data_format)
        return config.get("computed_fields", {}) if config else {}

    def get_checks(
        self, magnet_type: MagnetType, data_format: DataFormat
    ) -> Dict[str, CheckConfig]:
        """Get validation checks for a magnet type and format."""
        config = self.get_magnet_config(magnet_type, data_format)
        return config.get("checks", {}) if config else {}

    def get_all_fields(
        self, magnet_type: MagnetType, data_format: DataFormat
    ) -> List[str]:
        """Get all fields mentioned in the configuration for a magnet type and format."""
        all_fields = set()

        # Add fields from groups
        groups = self.get_groups(magnet_type, data_format)
        for group_config in groups.values():
            all_fields.update(group_config.fields)

        # Add fields from aliases (both old and new names)
        aliases = self.get_aliases(magnet_type, data_format)
        all_fields.update(aliases.keys())
        all_fields.update(aliases.values())

        # Add fields from computed field inputs
        computed_fields = self.get_computed_fields(magnet_type, data_format)
        for computed_config in computed_fields.values():
            all_fields.update(computed_config.fields)

        # Add computed field names themselves
        all_fields.update(computed_fields.keys())

        return sorted(list(all_fields))

    def get_field_info(
        self, field_name: str, magnet_type: MagnetType, data_format: DataFormat
    ) -> Dict[str, Any]:
        """Get detailed information about a specific field."""
        info = {
            "field_name": field_name,
            "found_in": [],
            "field_type": None,
            "symbol": None,
            "unit": None,
            "description": None,
            "is_computed": False,
            "is_alias": False,
        }

        # Check if field is in any group
        groups = self.get_groups(magnet_type, data_format)
        for group_name, group_config in groups.items():
            if field_name in group_config.fields:
                info["found_in"].append(f"group:{group_name}")
                info["field_type"] = group_config.field_type
                info["symbol"] = group_config.symbol
                info["unit"] = group_config.unit
                info["description"] = group_config.description

        # Check if field is an alias
        aliases = self.get_aliases(magnet_type, data_format)
        if field_name in aliases:
            info["found_in"].append("alias_source")
            info["is_alias"] = True
            info["alias_target"] = aliases[field_name]
        elif field_name in aliases.values():
            info["found_in"].append("alias_target")
            info["is_alias"] = True
            # Find the source
            for source, target in aliases.items():
                if target == field_name:
                    info["alias_source"] = source
                    break

        # Check if field is computed
        computed_fields = self.get_computed_fields(magnet_type, data_format)
        if field_name in computed_fields:
            computed_config = computed_fields[field_name]
            info["found_in"].append("computed_field")
            info["is_computed"] = True
            info["field_type"] = computed_config.field_type
            info["symbol"] = computed_config.symbol
            info["unit"] = computed_config.unit
            info["description"] = computed_config.description
            info["formula"] = computed_config.formula
            info["input_fields"] = computed_config.fields

        return info

    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the configuration structure."""
        summary = {
            "name": self.name,
            "metadata": self.metadata,
            "magnet_types": {},
            "total_fields": 0,
            "total_computed_fields": 0,
            "total_aliases": 0,
            "total_checks": 0,
        }

        for magnet_type, formats in self.magnet_configs.items():
            magnet_summary = {"formats": {}, "total_fields": 0}

            for data_format, config in formats.items():
                format_summary = {
                    "groups": len(config["groups"]),
                    "aliases": len(config["aliases"]),
                    "computed_fields": len(config["computed_fields"]),
                    "checks": len(config["checks"]),
                    "total_fields": len(self.get_all_fields(magnet_type, data_format)),
                }

                magnet_summary["formats"][data_format.value] = format_summary
                magnet_summary["total_fields"] += format_summary["total_fields"]

                summary["total_fields"] += format_summary["total_fields"]
                summary["total_computed_fields"] += format_summary["computed_fields"]
                summary["total_aliases"] += format_summary["aliases"]
                summary["total_checks"] += format_summary["checks"]

            summary["magnet_types"][magnet_type.value] = magnet_summary

        return summary

    def to_json(self, indent: int = 2) -> str:
        """Export configuration to JSON string."""
        return json.dumps(self.config_data, indent=indent)

    def save_to_file(self, filepath: str) -> None:
        """Save configuration to JSON file."""
        # Update timestamp
        if "metadata" not in self.config_data:
            self.config_data["metadata"] = {}
        self.config_data["metadata"]["timestamp"] = datetime.utcnow().isoformat() + "Z"

        with open(filepath, "w") as f:
            json.dump(self.config_data, f, indent=2)


class HousingConfigManager:
    """Simplified manager for housing configurations."""

    def __init__(self, config_directory: Optional[str] = None):
        self.config_directory = config_directory or self._get_default_config_dir()
        self.configurations: Dict[str, HousingConfig] = {}

    def _get_default_config_dir(self) -> str:
        """Get default configuration directory."""
        current_dir = Path(__file__).parent
        print(f"current_dir: {current_dir}")
        return str(current_dir / "configs" / "housings")

    def list_configurations(self) -> List[str]:
        """List all available JSON configuration files."""
        config_dir = Path(self.config_directory)

        if not config_dir.exists():
            print(f"Warning: Housing config directory not found: {config_dir}")
            return []

        json_files = list(config_dir.glob("*.json"))
        return [f.stem for f in json_files]

    def load_configuration(self, housing_name: str) -> Optional[HousingConfig]:
        """Load a specific configuration file."""
        config_dir = Path(self.config_directory)
        filepath = config_dir / f"{housing_name}.json"
        print(f"Loading configuration from {filepath}...", flush=True)

        if not filepath.exists():
            print(f"Configuration file not found: {filepath}")
            return None

        try:
            with open(filepath, "r") as f:
                config_data = json.load(f)

            config = HousingConfig(housing_name, config_data)
            self.configurations[housing_name] = config
            return config

        except Exception as e:
            print(f"Error loading configuration from {filepath}: {e}")
            return None

    def get_configuration(self, housing_name: str) -> Optional[HousingConfig]:
        """Get configuration for a housing type, loading if needed."""
        if housing_name not in self.configurations:
            return self.load_configuration(housing_name)
        return self.configurations.get(housing_name)

    def save_configuration(
        self, config: HousingConfig, housing_name: Optional[str] = None
    ) -> bool:
        """Save configuration to file."""
        name = housing_name or config.name
        config_dir = Path(self.config_directory)
        config_dir.mkdir(parents=True, exist_ok=True)

        filepath = config_dir / f"{name}.json"

        try:
            config.save_to_file(str(filepath))
            self.configurations[name] = config
            return True
        except Exception as e:
            print(f"Error saving configuration to {filepath}: {e}")
            return False

    def create_configuration(
        self, housing_name: str, metadata: Optional[Dict[str, Any]] = None
    ) -> HousingConfig:
        """Create a new empty configuration."""
        config_data = {
            "metadata": metadata
            or {
                "description": f"{housing_name} housing configuration",
                "created": datetime.utcnow().isoformat() + "Z",
                "version": "2.0",
            }
        }

        config = HousingConfig(housing_name, config_data)
        return config


# Global configuration manager instance
_global_manager: Optional[HousingConfigManager] = None


def get_housing_config_manager(
    config_directory: Optional[str] = None,
) -> HousingConfigManager:
    """Get global housing configuration manager instance."""
    global _global_manager
    if _global_manager is None:
        _global_manager = HousingConfigManager(config_directory)
    return _global_manager


def get_housing_config(housing_name: str) -> Optional[HousingConfig]:
    """Get housing configuration by name."""
    manager = get_housing_config_manager()
    return manager.get_configuration(housing_name.lower())
