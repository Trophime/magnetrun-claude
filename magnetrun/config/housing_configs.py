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
    from magnetrun.core.fields.field_types import FieldType
    from magnetrun.core.fields.field import Field
    from magnetrun.core.fields.format_registry import FormatRegistry
except ImportError:
    # Fallback for development/testing
    print("Warning: magnetrun.core.fields not available. Some features will be limited.")
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
                if isinstance(magnet_config, dict) and "voltage_tap_locations" in magnet_config:
                    locations = magnet_config["voltage_tap_locations"]
                    if isinstance(locations, dict):
                        self.voltage_tap_locations.update(locations)
        
        if self.voltage_tap_locations:
            print(f"Loaded {len(self.voltage_tap_locations)} voltage tap locations from {self.name} config")
    
    def get_magnet_voltage_tap_locations(self, magnet_type: MagnetType) -> Dict[str, List[float]]:
        """Get voltage tap locations for a specific magnet type."""
        magnet_config = self.config_data.get(magnet_type.value, {})
        if isinstance(magnet_config, dict):
            return magnet_config.get("voltage_tap_locations", {})
        return {}
    
    def set_magnet_voltage_tap_locations(self, magnet_type: MagnetType, 
                                       tap_locations: Dict[str, List[float]]) -> None:
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
    def from_json_file(cls, housing_name: str, config_path: Optional[str] = None) -> 'HousingConfig':
        """Load housing configuration from JSON file."""
        if config_path is None:
            # Default config path
            config_path = Path(__file__).parent / "configs" / f"{housing_name.lower()}.json"
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Housing config file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        config = cls(
            name=housing_name,
            config_data=config_data
        )
        
        return config
    
    @classmethod
    def from_dict(cls, housing_name: str, config_dict: Dict[str, Any]) -> 'HousingConfig':
        """Create housing configuration from dictionary."""
        config = cls(
            name=housing_name,
            config_data=config_dict
        )
        
        return config
    
    def save_to_file(self, config_path: Optional[str] = None) -> None:
        """Save housing configuration to JSON file."""
        if config_path is None:
            config_path = Path(__file__).parent / "configs" / f"{self.name.lower()}.json"
        
        # Update timestamp
        self.update_timestamp()
        
        # Voltage tap locations are already in the config_data structure
        with open(config_path, 'w') as f:
            json.dump(self.config_data, f, indent=2, sort_keys=False)
    
    def update_timestamp(self) -> None:
        """Update the timestamp in metadata."""
        if 'metadata' not in self.config_data:
            self.config_data['metadata'] = {}
        self.config_data['metadata']['timestamp'] = datetime.utcnow().isoformat() + 'Z'
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get housing metadata."""
        return self.config_data.get('metadata', {})
    
    def set_description(self, description: str) -> None:
        """Set housing description."""
        if 'metadata' not in self.config_data:
            self.config_data['metadata'] = {}
        self.config_data['metadata']['description'] = description
    
    def get_magnet_config(self, magnet_type: MagnetType, data_format: DataFormat) -> Dict[str, Any]:
        """Get configuration for a specific magnet type and data format."""
        magnet_key = magnet_type.value
        format_key = data_format.value
        
        return self.config_data.get(magnet_key, {}).get(format_key, {})
    
    def set_magnet_config(self, magnet_type: MagnetType, data_format: DataFormat, 
                         config: Dict[str, Any]) -> None:
        """Set configuration for a specific magnet type and data format."""
        magnet_key = magnet_type.value
        format_key = data_format.value
        
        if magnet_key not in self.config_data:
            self.config_data[magnet_key] = {}
        
        self.config_data[magnet_key][format_key] = config
    
    def get_field_config(self, magnet_type: MagnetType, data_format: DataFormat, 
                        field_category: str) -> Dict[str, Any]:
        """Get complete field configuration including fields, field_type, symbol, unit, and optional formula."""
        magnet_config = self.get_magnet_config(magnet_type, data_format)
        return magnet_config.get(field_category, {})
    
    def create_field_object(self, magnet_type: MagnetType, data_format: DataFormat,
                           field_category: str) -> Optional[Any]:
        """Create a Field object from housing configuration."""
        if not Field or not FieldType:
            return None
            
        field_config = self.get_field_config(magnet_type, data_format, field_category)
        if not field_config:
            return None
        
        try:
            field_type = FieldType(field_config.get('field_type', 'current'))
            
            # Use the field_category as the field name (this will be used for renaming)
            field_name = field_category
            
            return Field(
                name=field_name,
                field_type=field_type,
                unit=field_config.get('unit', 'dimensionless'),
                symbol=field_config.get('symbol', field_name),
                description=f"{magnet_type.value} {field_category} for {data_format.value} format"
            )
        except (ValueError, KeyError) as e:
            print(f"Error creating field object for {field_category}: {e}")
            return None
    
    def get_fields(self, magnet_type: MagnetType, data_format: DataFormat, 
                  field_category: str) -> List[str]:
        """Get source field names for a specific category."""
        field_config = self.get_field_config(magnet_type, data_format, field_category)
        
        # Handle both old format (list) and new format (dict with fields key)
        if isinstance(field_config, list):
            return field_config
        elif isinstance(field_config, dict):
            fields = field_config.get('fields', [])
            return fields if isinstance(fields, list) else [fields] if fields else []
        else:
            return []
    
    def get_field_type(self, magnet_type: MagnetType, data_format: DataFormat,
                      field_category: str) -> Optional[str]:
        """Get the field type for a category."""
        field_config = self.get_field_config(magnet_type, data_format, field_category)
        if isinstance(field_config, dict):
            return field_config.get('field_type')
        return None
    
    def get_field_symbol(self, magnet_type: MagnetType, data_format: DataFormat,
                        field_category: str) -> Optional[str]:
        """Get the symbol for a field category."""
        field_config = self.get_field_config(magnet_type, data_format, field_category)
        if isinstance(field_config, dict):
            return field_config.get('symbol')
        return None
    
    def get_field_unit(self, magnet_type: MagnetType, data_format: DataFormat,
                      field_category: str) -> Optional[str]:
        """Get the unit for a field category."""
        field_config = self.get_field_config(magnet_type, data_format, field_category)
        if isinstance(field_config, dict):
            return field_config.get('unit')
        return None
    
    def get_field_formula(self, magnet_type: MagnetType, data_format: DataFormat,
                         field_category: str) -> Optional[str]:
        """Get the formula for calculating fields in this category."""
        field_config = self.get_field_config(magnet_type, data_format, field_category)
        if isinstance(field_config, dict):
            return field_config.get('formula')
        return None
    
    def load_msite_geometry(self, msite_file: str) -> bool:
        """Load MSite geometry for voltage tap filtering."""
        try:
            # Import here to avoid circular imports
            try:
                from magnetgeo import MSite
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
        print("Warning: set_voltage_tap_locations is deprecated. Use set_magnet_voltage_tap_locations instead.")
        
        # For backwards compatibility, assume these are Insert locations
        self.set_magnet_voltage_tap_locations(MagnetType.INSERT, tap_locations)
    
    def add_voltage_tap_location(self, magnet_type: MagnetType, tap_name: str, 
                               coordinates: List[float]) -> None:
        """Add a single voltage tap location for a specific magnet type."""
        if len(coordinates) != 3:
            raise ValueError("Coordinates must be [x, y, z]")
        
        current_locations = self.get_magnet_voltage_tap_locations(magnet_type)
        current_locations[tap_name] = coordinates.copy()
        self.set_magnet_voltage_tap_locations(magnet_type, current_locations)
    
    def remove_voltage_tap_location(self, magnet_type: MagnetType, tap_name: str) -> bool:
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
    
    def filter_voltage_taps_by_geometry(self, magnet_type: MagnetType, data_format: DataFormat) -> None:
        """Filter voltage tap fields based on MSite geometry consistency."""
        if not self.msite_object:
            print("Warning: No MSite geometry loaded. Cannot filter voltage taps.")
            return
        
        # Get current voltage fields
        voltage_fields = self.get_fields(magnet_type, data_format, "coil_voltage")
        if not voltage_fields:
            return
        
        # Filter based on geometry consistency
        valid_voltage_fields = self._validate_voltage_taps_against_geometry(voltage_fields, magnet_type, data_format)
        
        if len(valid_voltage_fields) != len(voltage_fields):
            print(f"Filtered {data_format.value} voltage taps from {len(voltage_fields)} to {len(valid_voltage_fields)} based on {self.name} geometry")
            
            # Update the configuration with filtered fields
            field_config = self.get_field_config(magnet_type, data_format, "coil_voltage")
            if isinstance(field_config, dict):
                field_config['fields'] = valid_voltage_fields
                magnet_config = self.get_magnet_config(magnet_type, data_format)
                magnet_config['coil_voltage'] = field_config
                self.set_magnet_config(magnet_type, data_format, magnet_config)
    
    def _validate_voltage_taps_against_geometry(self, voltage_fields: List[str], 
                                              magnet_type: MagnetType, 
                                              data_format: DataFormat) -> List[str]:
        """Validate voltage taps against MSite geometry."""
        if not self.msite_object or magnet_type != MagnetType.INSERT:
            return voltage_fields  # Only filter Insert voltage taps for now
        
        valid_taps = []
        
        # Get Insert geometry information
        insert_magnets = [m for m in self.msite_object.magnets if m.__class__.__name__ == "Insert"]
        if not insert_magnets:
            print("Warning: No Insert magnets found in MSite geometry")
            return voltage_fields
        
        insert = insert_magnets[0]  # Assume first Insert
        
        # Get helices information
        if not hasattr(insert, 'helices') or not insert.helices:
            print("Warning: No helices found in Insert geometry")
            return voltage_fields
        
        # Determine measurement strategy based on site configuration
        measurement_strategy = self._determine_measurement_strategy(insert)
        
        for voltage_field in voltage_fields:
            # Extract coil number from field name
            coil_num = self._extract_coil_number_from_field(voltage_field, data_format)
            if coil_num is None:
                continue
            
            # Check if this voltage tap is consistent with geometry
            if self._is_voltage_tap_valid(coil_num, insert, measurement_strategy):
                valid_taps.append(voltage_field)
            else:
                print(f"Removing {voltage_field}: inconsistent with {self.name} geometry")
        
        return valid_taps
    
    def _determine_measurement_strategy(self, insert) -> str:
        """Determine if measurements are per helix or per helix couple."""
        # This logic depends on the specific site configuration
        # For M9, we might measure by helix couples, for others by individual helices
        
        num_helices = len(insert.helices) if insert.helices else 0
        
        # Site-specific logic (can be made configurable)
        if self.name.upper() == "M9":
            return "helix_couples"  # M9 measures by couples
        elif self.name.upper() == "M10":
            return "individual_helices"  # M10 measures individually
        else:
            # Default: if we have many helices, likely measured by couples
            return "helix_couples" if num_helices > 8 else "individual_helices"
    
    def _extract_coil_number_from_field(self, field_name: str, data_format: DataFormat) -> Optional[int]:
        """Extract coil number from field name, format-aware."""
        import re
        
        if data_format == DataFormat.PUPITRE:
            # Handle pupitre format: "Ucoil1", "Ucoil14", etc.
            match = re.search(r'coil(\d+)', field_name)
            if match:
                return int(match.group(1))
        
        elif data_format == DataFormat.PIGBROTHER:
            # Handle pigbrother format: "Tensions_Aimant/Interne1", "Tensions_Aimant/Interne7", etc.
            match = re.search(r'Interne(\d+)', field_name)
            if match:
                return int(match.group(1))
        
        return None
    
    def _extract_coil_number(self, field_name: str) -> Optional[int]:
        """Extract coil number from field name like 'Ucoil1', 'Icoil14', etc. (legacy method)."""
        import re
        match = re.search(r'coil(\d+)', field_name)
        if match:
            return int(match.group(1))
        return None
    
    def _is_voltage_tap_valid(self, coil_num: int, insert, measurement_strategy: str) -> bool:
        """Check if a voltage tap number is valid for the given geometry and strategy."""
        num_helices = len(insert.helices) if insert.helices else 0
        
        if measurement_strategy == "individual_helices":
            # Each helix has its own voltage tap
            return 1 <= coil_num <= num_helices
        
        elif measurement_strategy == "helix_couples":
            # Voltage taps are measured for couples of helices
            num_couples = (num_helices + 1) // 2  # Round up for odd numbers
            return 1 <= coil_num <= num_couples
        
        else:
            # Default: assume all coils up to number of helices are valid
            return 1 <= coil_num <= num_helices
    
    def get_filtered_voltage_tap_info(self, magnet_type: MagnetType, data_format: DataFormat) -> Dict[str, Any]:
        """Get information about voltage tap filtering results."""
        if not self.msite_object:
            return {"status": "no_geometry", "message": "No MSite geometry loaded"}
        
        voltage_fields = self.get_fields(magnet_type, data_format, "coil_voltage")
        if not voltage_fields:
            return {"status": "no_voltage_fields", "message": "No voltage fields defined"}
        
        valid_fields = self._validate_voltage_taps_against_geometry(voltage_fields, magnet_type, data_format)
        
        filtered_out = [f for f in voltage_fields if f not in valid_fields]
        
        return {
            "status": "filtered",
            "format": data_format.value,
            "original_count": len(voltage_fields),
            "valid_count": len(valid_fields),
            "filtered_out_count": len(filtered_out),
            "valid_fields": valid_fields,
            "filtered_out_fields": filtered_out,
            "measurement_strategy": self._determine_measurement_strategy(self.msite_object.magnets[0]) if self.msite_object.magnets else "unknown"
        }Type, data_format: DataFormat,
                         field_category: str) -> bool:
        """Check if fields in this category are required in the data file."""
        field_config = self.get_field_config(magnet_type, data_format, field_category)
        if isinstance(field_config, dict):
            return field_config.get('required', True)  # Default to True for backwards compatibility
        return True  # Old format assumes all fields are required
    
    def get_field_formula(self, magnet_type: MagnetType, data_format: DataFormat,
                         field_category: str) -> Optional[str]:
        """Get the formula for calculating fields in this category."""
        field_config = self.get_field_config(magnet_type, data_format, field_category)
        if isinstance(field_config, dict):
            return field_config.get('formula')
        return None
    
    def set_field_config(self, magnet_type: MagnetType, data_format: DataFormat,
                        field_category: str, fields: List[str], field_type: str,
                        symbol: str, unit: str, formula: Optional[str] = None) -> None:
        """Set complete field configuration."""
        field_config = {
            "fields": fields,
            "field_type": field_type,
            "symbol": symbol,
            "unit": unit
        }
        if formula:
            field_config["formula"] = formula
            
        magnet_config = self.get_magnet_config(magnet_type, data_format)
        magnet_config[field_category] = field_config
        self.set_magnet_config(magnet_type, data_format, magnet_config)
    
    def set_fields(self, magnet_type: MagnetType, data_format: DataFormat,
                  field_category: str, fields: List[str]) -> None:
        """Set fields for a specific category (preserving existing field_type/symbol/unit settings)."""
        field_config = self.get_field_config(magnet_type, data_format, field_category)
        if isinstance(field_config, dict):
            # Update existing config
            field_config['fields'] = fields
            magnet_config = self.get_magnet_config(magnet_type, data_format)
            magnet_config[field_category] = field_config
            self.set_magnet_config(magnet_type, data_format, magnet_config)
        else:
            # Create new config with defaults
            self.set_field_config(magnet_type, data_format, field_category, fields, 
                                "current", field_category, "dimensionless")
    
    def add_field(self, magnet_type: MagnetType, data_format: DataFormat,
                 field_category: str, field_name: str) -> None:
        """Add a field to a specific category."""
        current_fields = self.get_fields(magnet_type, data_format, field_category)
        if field_name not in current_fields:
            current_fields.append(field_name)
            self.set_fields(magnet_type, data_format, field_category, current_fields)
    
    def remove_field(self, magnet_type: MagnetType, data_format: DataFormat,
                    field_category: str, field_name: str) -> None:
        """Remove a field from a specific category."""
        current_fields = self.get_fields(magnet_type, data_format, field_category)
        if field_name in current_fields:
            current_fields.remove(field_name)
            self.set_fields(magnet_type, data_format, field_category, current_fields)
    
    def get_current_fields(self, magnet_type: MagnetType, data_format: DataFormat) -> List[str]:
        """Get current measurement fields."""
        return self.get_fields(magnet_type, data_format, 'current')
    
    def set_current_fields(self, magnet_type: MagnetType, data_format: DataFormat, 
                          fields: List[str]) -> None:
        """Set current measurement fields."""
        self.set_fields(magnet_type, data_format, 'current', fields)
    
    def get_current_formula(self, magnet_type: MagnetType, data_format: DataFormat) -> str:
        """Get current calculation formula."""
        magnet_config = self.get_magnet_config(magnet_type, data_format)
        return magnet_config.get('current_formula', '')
    
    def set_current_formula(self, magnet_type: MagnetType, data_format: DataFormat,
                           formula: str) -> None:
        """Set current calculation formula."""
        magnet_config = self.get_magnet_config(magnet_type, data_format)
        magnet_config['current_formula'] = formula
        self.set_magnet_config(magnet_type, data_format, magnet_config)
    
    def get_reference_current(self, magnet_type: MagnetType, data_format: DataFormat) -> List[str]:
        """Get reference current fields for a magnet type."""
        return self.get_fields(magnet_type, data_format, 'reference_current')
    
    def set_reference_current(self, magnet_type: MagnetType, data_format: DataFormat,
                             fields: List[str]) -> None:
        """Set reference current fields."""
        self.set_fields(magnet_type, data_format, 'reference_current', fields)
    
    def get_reference_formula(self, magnet_type: MagnetType, data_format: DataFormat) -> str:
        """Get reference current calculation formula."""
        magnet_config = self.get_magnet_config(magnet_type, data_format)
        return magnet_config.get('reference_current_formula', '')
    
    def set_reference_formula(self, magnet_type: MagnetType, data_format: DataFormat,
                             formula: str) -> None:
        """Set reference current calculation formula."""
        magnet_config = self.get_magnet_config(magnet_type, data_format)
        magnet_config['reference_current_formula'] = formula
        self.set_magnet_config(magnet_type, data_format, magnet_config)
    
    def get_coil_fields(self, magnet_type: MagnetType, data_format: DataFormat, 
                       measurement_type: str = 'current') -> List[str]:
        """Get coil measurement fields by type (current, voltage, temperature, resistance)."""
        field_key = f'coil_{measurement_type}'
        return self.get_fields(magnet_type, data_format, field_key)
    
    def set_coil_fields(self, magnet_type: MagnetType, data_format: DataFormat,
                       measurement_type: str, fields: List[str]) -> None:
        """Set coil measurement fields."""
        field_key = f'coil_{measurement_type}'
        self.set_fields(magnet_type, data_format, field_key, fields)
    
    def get_voltage_fields(self, magnet_type: MagnetType, data_format: DataFormat) -> List[str]:
        """Get voltage measurement fields."""
        return self.get_fields(magnet_type, data_format, 'voltage')
    
    def get_temperature_fields(self, magnet_type: MagnetType, data_format: DataFormat,
                             location: str = 'inlet') -> List[str]:
        """Get temperature fields by location (inlet, outlet)."""
        field_key = f'temperature_{location}'
        return self.get_fields(magnet_type, data_format, field_key)
    
    def get_pressure_fields(self, magnet_type: MagnetType, data_format: DataFormat,
                           pressure_type: str = 'high') -> List[str]:
        """Get pressure fields by type (high, low)."""
        field_key = f'pressure_{pressure_type}'
        return self.get_fields(magnet_type, data_format, field_key)
    
    def get_flow_fields(self, magnet_type: MagnetType, data_format: DataFormat) -> List[str]:
        """Get flow measurement fields."""
        return self.get_fields(magnet_type, data_format, 'flow')
    
    def get_field_measurements(self, magnet_type: MagnetType, data_format: DataFormat) -> List[str]:
        """Get magnetic field measurement fields."""
        return self.get_fields(magnet_type, data_format, 'field')
    
    def get_power_fields(self, magnet_type: MagnetType, data_format: DataFormat) -> List[str]:
        """Get power measurement fields."""
        return self.get_fields(magnet_type, data_format, 'power')
    
    def get_all_fields(self, magnet_type: MagnetType, data_format: DataFormat) -> List[str]:
        """Get all source field names defined for a magnet type and format."""
        magnet_config = self.get_magnet_config(magnet_type, data_format)
        all_fields = []
        
        for key, value in magnet_config.items():
            if isinstance(value, dict) and 'fields' in value:
                # New format
                fields = value['fields']
                if isinstance(fields, list):
                    all_fields.extend(fields)
                elif isinstance(fields, str):
                    all_fields.append(fields)
            elif isinstance(value, list):
                # Old format - list of fields
                all_fields.extend(value)
            elif isinstance(value, str) and not key.endswith('_formula'):
                # Old format - single field
                all_fields.append(value)
        
        return list(set(all_fields))  # Remove duplicates
    
    def get_source_fields(self, magnet_type: MagnetType, data_format: DataFormat) -> List[str]:
        """Get all source fields that should be read from the data file (no formula)."""
        magnet_config = self.get_magnet_config(magnet_type, data_format)
        source_fields = []
        
        for key, value in magnet_config.items():
            if isinstance(value, dict) and 'fields' in value:
                if not value.get('formula'):  # No formula = source field
                    fields = value['fields']
                    if isinstance(fields, list):
                        source_fields.extend(fields)
                    elif isinstance(fields, str):
                        source_fields.append(fields)
            elif isinstance(value, (list, str)) and not key.endswith('_formula'):
                # Old format - assume all fields are source fields
                if isinstance(value, list):
                    source_fields.extend(value)
                else:
                    source_fields.append(value)
        
        return list(set(source_fields))  # Remove duplicates
    
    def get_computed_field_categories(self, magnet_type: MagnetType, data_format: DataFormat) -> Dict[str, str]:
        """Get all field categories that should be computed via formulas."""
        magnet_config = self.get_magnet_config(magnet_type, data_format)
        computed_categories = {}
        
        for key, value in magnet_config.items():
            if isinstance(value, dict) and 'fields' in value:
                formula = value.get('formula')
                if formula:
                    computed_categories[key] = formula
        
        return computed_categories
    
    def apply_geometry_filtering(self, msite_file: str) -> Dict[str, Any]:
        """Apply geometry-based filtering after loading housing configuration."""
        results = {}
        
        # Load MSite geometry
        if self.load_msite_geometry(msite_file):
            results["msite_loaded"] = True
            results["voltage_tap_locations_available"] = len(self.voltage_tap_locations)
            
            # Filter voltage taps for all magnet types and formats
            for magnet_type in MagnetType:
                for data_format in DataFormat:
                    if magnet_type == MagnetType.INSERT:  # Only filter Insert voltage taps
                        filter_info = self.get_filtered_voltage_tap_info(magnet_type, data_format)
                        if filter_info["status"] == "filtered":
                            # Apply the filtering
                            self.filter_voltage_taps_by_geometry(magnet_type, data_format)
                            results[f"{magnet_type.value}_{data_format.value}"] = filter_info
        else:
            results["msite_loaded"] = False
            results["error"] = "Failed to load MSite geometry"
        
        return results
    
    def has_formula(self, magnet_type: MagnetType, data_format: DataFormat,
                   field_category: str) -> bool:
        """Check if a field category has a formula defined."""
        formula = self.get_field_formula(magnet_type, data_format, field_category)
        return formula is not None and formula.strip() != ""
    
    def get_custom_fields(self, magnet_type: MagnetType, data_format: DataFormat,
                         custom_key: str) -> List[str]:
        """Get custom fields by key."""
        return self.get_fields(magnet_type, data_format, custom_key)
    
    def get_ih_formula(self, data_format: DataFormat) -> str:
        """Get formula for IH reference calculation (Insert magnet)."""
        ref_fields = self.get_reference_current(MagnetType.INSERT, data_format)
        if not ref_fields:
            return ""
        return f"IH_ref = {' + '.join(ref_fields)}"
    
    def get_ib_formula(self, data_format: DataFormat) -> str:
        """Get formula for IB reference calculation (Bitters magnet).""" 
        ref_fields = self.get_reference_current(MagnetType.BITTERS, data_format)
        if not ref_fields:
            return ""
        return f"IB_ref = {' + '.join(ref_fields)}"
    
    def create_empty_magnet_config(self, magnet_type: MagnetType, data_format: DataFormat) -> None:
        """Create an empty configuration section for a magnet type and format."""
        empty_config = {
            "current": {
                "fields": [],
                "field_type": "current",
                "symbol": "I",
                "unit": "ampere"
            },
            "reference_current": {
                "fields": [],
                "field_type": "current", 
                "symbol": "I_ref",
                "unit": "ampere"
            },
            "voltage": {
                "fields": [],
                "field_type": "voltage",
                "symbol": "U",
                "unit": "volt"
            },
            "field": {
                "fields": [],
                "field_type": "magnetic_field",
                "symbol": "B", 
                "unit": "tesla"
            },
            "power": {
                "fields": [],
                "field_type": "power",
                "symbol": "P",
                "unit": "watt"
            }
        }
        self.set_magnet_config(magnet_type, data_format, empty_config)
    
    def validate_config(self) -> List[str]:
        """Validate the configuration and return any issues found."""
        issues = []
        
        # Check metadata
        metadata = self.get_metadata()
        if not metadata.get('description'):
            issues.append("Missing description in metadata")
        
        # Check magnet configurations
        for magnet_type in MagnetType:
            if magnet_type.value not in self.config_data:
                issues.append(f"Missing configuration for {magnet_type.value}")
                continue
            
            for data_format in DataFormat:
                magnet_config = self.get_magnet_config(magnet_type, data_format)
                if not magnet_config:
                    issues.append(f"Missing {data_format.value} configuration for {magnet_type.value}")
                    continue
                
                # Check field configurations
                for category, config in magnet_config.items():
                    if isinstance(config, dict):
                        # Check required fields
                        if not config.get('fields'):
                            issues.append(f"No fields defined for {magnet_type.value}/{data_format.value}/{category}")
                        
                        if not config.get('field_type'):
                            issues.append(f"No field_type defined for {magnet_type.value}/{data_format.value}/{category}")
                        
                        if not config.get('symbol'):
                            issues.append(f"No symbol defined for {magnet_type.value}/{data_format.value}/{category}")
                        
                        if not config.get('unit'):
                            issues.append(f"No unit defined for {magnet_type.value}/{data_format.value}/{category}")
                        
                        # Validate field_type if FieldType is available
                        if FieldType:
                            try:
                                FieldType(config.get('field_type', ''))
                            except ValueError:
                                issues.append(f"Invalid field_type '{config.get('field_type')}' for {magnet_type.value}/{data_format.value}/{category}")
        
        return issues
    
    def copy_config_between_formats(self, magnet_type: MagnetType, 
                                   source_format: DataFormat, 
                                   target_format: DataFormat) -> None:
        """Copy configuration from one format to another for the same magnet type."""
        source_config = self.get_magnet_config(magnet_type, source_format)
        if source_config:
            self.set_magnet_config(magnet_type, target_format, source_config.copy())
    
    def list_available_categories(self, magnet_type: MagnetType, data_format: DataFormat) -> List[str]:
        """List all available field categories for a magnet type and format."""
        magnet_config = self.get_magnet_config(magnet_type, data_format)
        return [key for key in magnet_config.keys() if not key.endswith('_formula')]
    
    def validate_config(self) -> List[str]:
        """Validate the configuration and return any issues found."""
        issues = []
        
        # Check metadata
        metadata = self.get_metadata()
        if not metadata.get('description'):
            issues.append("Missing description in metadata")
        
        # Check magnet configurations
        for magnet_type in MagnetType:
            if magnet_type.value not in self.config_data:
                issues.append(f"Missing configuration for {magnet_type.value}")
                continue
            
            for data_format in DataFormat:
                magnet_config = self.get_magnet_config(magnet_type, data_format)
                if not magnet_config:
                    issues.append(f"Missing {data_format.value} configuration for {magnet_type.value}")
                    continue
                
                # Check for current fields if current_formula exists
                if magnet_config.get('current_formula') and not magnet_config.get('current'):
                    issues.append(f"Current formula exists but no current fields defined for {magnet_type.value}/{data_format.value}")
                
                # Check for reference fields if reference_formula exists
                if magnet_config.get('reference_current_formula') and not magnet_config.get('reference_current'):
                    issues.append(f"Reference formula exists but no reference fields defined for {magnet_type.value}/{data_format.value}")
        
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
    
    def create_new_config(self, housing_name: str, description: str = "") -> HousingConfig:
        """Create a new housing configuration."""
        config_data = {
            "metadata": {
                "description": description or f"{housing_name} housing configuration",
                "timestamp": datetime.utcnow().isoformat() + 'Z'
            }
        }
        
        config = HousingConfig.from_dict(housing_name, config_data)
        
        # Create empty configurations for all magnet types and formats
        for magnet_type in MagnetType:
            for data_format in DataFormat:
                config.create_empty_magnet_config(magnet_type, data_format)
        
        self._configs[housing_name.upper()] = config
        return config
    
    def save_config(self, housing_name: str, config_path: Optional[str] = None) -> bool:
        """Save a housing configuration to file."""
        config = self.get_config(housing_name)
        if not config:
            return False
        
        try:
            config.save_to_file(config_path)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def delete_config(self, housing_name: str) -> bool:
        """Delete a housing configuration."""
        housing_key = housing_name.upper()
        if housing_key in self._configs:
            del self._configs[housing_key]
            
            # Also delete the file
            config_path = self.config_directory / f"{housing_name.lower()}.json"
            if config_path.exists():
                config_path.unlink()
            
            return True
        return False
    
    def list_housings(self) -> List[str]:
        """Get list of available housing names."""
        return list(self._configs.keys())
    
    def validate_all_configs(self) -> Dict[str, List[str]]:
        """Validate all configurations and return issues."""
        validation_results = {}
        for housing_name, config in self._configs.items():
            issues = config.validate_config()
            if issues:
                validation_results[housing_name] = issues
        return validation_results


# Global instance
housing_config_manager = HousingConfigManager()

# Convenience functions
def get_housing_config(housing_name: str) -> Optional[HousingConfig]:
    """Get housing configuration by name."""
    return housing_config_manager.get_config(housing_name)

def create_housing_config(housing_name: str, description: str = "") -> HousingConfig:
    """Create a new housing configuration."""
    return housing_config_manager.create_new_config(housing_name, description)

def save_housing_config(housing_name: str, config_path: Optional[str] = None) -> bool:
    """Save housing configuration to file."""
    return housing_config_manager.save_config(housing_name, config_path)

def list_housing_configs() -> List[str]:
    """List all available housing configurations."""
    return housing_config_manager.list_housings()

def get_field_mappings_for_etl(self, magnet_type: MagnetType, data_format: DataFormat) -> Dict[str, Dict[str, Any]]:
    """Get field mappings in format suitable for ETL operations."""
    magnet_config = self.get_magnet_config(magnet_type, data_format)
    mappings = {}
    
    for category, config in magnet_config.items():
        if isinstance(config, dict):
            field_obj = self.create_field_object(magnet_type, data_format, category)
            if field_obj:
                mappings[category] = {
                    'source_fields': config.get('fields', []),
                    'target_field': category,  # Use category as target field name
                    'field_object': field_obj,
                    'formula': config.get('formula'),
                    'has_formula': bool(config.get('formula')),
                    'voltage_tap_locations': self._get_tap_locations_for_fields(config.get('fields', []))
                }
    
    return mappings

def _get_tap_locations_for_fields(self, fields: List[str]) -> Dict[str, List[float]]:
    """Get voltage tap locations for a list of fields."""
    locations = {}
    for field in fields:
        if field in self.voltage_tap_locations:
            locations[field] = self.voltage_tap_locations[field]
    return locations


# Convenience functions for geometry filtering
def load_housing_with_geometry(housing_name: str, msite_file: str) -> Optional[HousingConfig]:
    """Load housing configuration and apply geometry-based filtering."""
    config = get_housing_config(housing_name)
    if not config:
        config = create_housing_config(housing_name, f"{housing_name} housing with geometry filtering")
    
    # Apply geometry filtering (voltage tap locations are already loaded from JSON)
    results = config.apply_geometry_filtering(msite_file)
    
    print(f"Geometry filtering results for {housing_name}:")
    for key, value in results.items():
        print(f"  {key}: {value}")
    
    return config