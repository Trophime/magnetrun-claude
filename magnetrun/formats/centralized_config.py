"""Centralized configuration system with user-configurable paths."""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import warnings


@dataclass
class ConfigPaths:
    """Configuration for where to find config files."""
    
    # Default paths
    DEFAULT_BASE_DIR = Path(__file__).parent / "configs"
    
    # User-configurable paths (can be set via environment variables or API)
    base_dir: Path
    formats_dir: Path
    housings_dir: Path
    field_definitions_dir: Path
    custom_dirs: Dict[str, Path]
    
    @classmethod
    def from_environment(cls) -> 'ConfigPaths':
        """Create ConfigPaths from environment variables."""
        base_dir = Path(os.getenv('MAGNETRUN_CONFIG_DIR', cls.DEFAULT_BASE_DIR))
        
        return cls(
            base_dir=base_dir,
            formats_dir=base_dir / "formats",
            housings_dir=base_dir / "housings", 
            field_definitions_dir=base_dir / "field_definitions",
            custom_dirs={}
        )
    
    @classmethod
    def from_base_dir(cls, base_dir: Union[str, Path]) -> 'ConfigPaths':
        """Create ConfigPaths from a base directory."""
        base_dir = Path(base_dir)
        
        return cls(
            base_dir=base_dir,
            formats_dir=base_dir / "formats",
            housings_dir=base_dir / "housings",
            field_definitions_dir=base_dir / "field_definitions", 
            custom_dirs={}
        )
    
    def add_custom_dir(self, name: str, path: Union[str, Path]) -> None:
        """Add a custom configuration directory."""
        self.custom_dirs[name] = Path(path)
    
    def ensure_directories_exist(self) -> None:
        """Create directories if they don't exist."""
        directories = [
            self.base_dir,
            self.formats_dir,
            self.housings_dir,
            self.field_definitions_dir,
        ]
        directories.extend(self.custom_dirs.values())
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


class ConfigManager:
    """Central configuration manager with user-configurable paths."""
    
    _instance: Optional['ConfigManager'] = None
    _config_paths: Optional[ConfigPaths] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self._config_cache: Dict[str, Dict] = {}
            self.initialized = True
    
    @classmethod
    def initialize(cls, config_paths: Optional[ConfigPaths] = None) -> 'ConfigManager':
        """Initialize the config manager with specific paths."""
        if config_paths is None:
            config_paths = ConfigPaths.from_environment()
        
        cls._config_paths = config_paths
        instance = cls()
        instance._config_cache.clear()  # Clear cache when reinitializing
        
        # Ensure directories exist
        config_paths.ensure_directories_exist()
        
        return instance
    
    @classmethod
    def set_base_config_dir(cls, base_dir: Union[str, Path]) -> 'ConfigManager':
        """Set the base configuration directory and reinitialize."""
        config_paths = ConfigPaths.from_base_dir(base_dir)
        return cls.initialize(config_paths)
    
    @property
    def config_paths(self) -> ConfigPaths:
        """Get current configuration paths."""
        if self._config_paths is None:
            self._config_paths = ConfigPaths.from_environment()
            self._config_paths.ensure_directories_exist()
        return self._config_paths
    
    def get_format_config_path(self, format_name: str) -> Path:
        """Get path to format configuration file."""
        return self.config_paths.formats_dir / f"{format_name}.json"
    
    def get_housing_config_path(self, housing_name: str) -> Path:
        """Get path to housing configuration file."""
        return self.config_paths.housings_dir / f"{housing_name.lower()}.json"
    
    def get_field_definition_path(self, definition_name: str) -> Path:
        """Get path to field definition file."""
        return self.config_paths.field_definitions_dir / f"{definition_name}.json"
    
    def get_custom_config_path(self, category: str, config_name: str) -> Optional[Path]:
        """Get path to custom configuration file."""
        if category in self.config_paths.custom_dirs:
            return self.config_paths.custom_dirs[category] / f"{config_name}.json"
        return None
    
    def load_config(self, config_type: str, config_name: str, use_cache: bool = True) -> Optional[Dict]:
        """Load configuration from appropriate directory."""
        cache_key = f"{config_type}:{config_name}"
        
        if use_cache and cache_key in self._config_cache:
            return self._config_cache[cache_key]
        
        # Determine config path based on type
        if config_type == "format":
            config_path = self.get_format_config_path(config_name)
        elif config_type == "housing":
            config_path = self.get_housing_config_path(config_name)
        elif config_type == "field_definition":
            config_path = self.get_field_definition_path(config_name)
        elif config_type in self.config_paths.custom_dirs:
            config_path = self.get_custom_config_path(config_type, config_name)
        else:
            warnings.warn(f"Unknown config type: {config_type}")
            return None
        
        if not config_path or not config_path.exists():
            return None
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            if use_cache:
                self._config_cache[cache_key] = config_data
            
            return config_data
            
        except Exception as e:
            warnings.warn(f"Failed to load config {config_path}: {e}")
            return None
    
    def save_config(self, config_type: str, config_name: str, config_data: Dict) -> bool:
        """Save configuration to appropriate directory."""
        # Determine config path based on type
        if config_type == "format":
            config_path = self.get_format_config_path(config_name)
        elif config_type == "housing":
            config_path = self.get_housing_config_path(config_name)
        elif config_type == "field_definition":
            config_path = self.get_field_definition_path(config_name)
        elif config_type in self.config_paths.custom_dirs:
            config_path = self.get_custom_config_path(config_type, config_name)
        else:
            warnings.warn(f"Unknown config type: {config_type}")
            return False
        
        if not config_path:
            return False
        
        try:
            # Ensure parent directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            # Update cache
            cache_key = f"{config_type}:{config_name}"
            self._config_cache[cache_key] = config_data
            
            return True
            
        except Exception as e:
            warnings.warn(f"Failed to save config {config_path}: {e}")
            return False
    
    def list_configs(self, config_type: str) -> List[str]:
        """List available configurations of a given type."""
        if config_type == "format":
            config_dir = self.config_paths.formats_dir
        elif config_type == "housing":
            config_dir = self.config_paths.housings_dir
        elif config_type == "field_definition":
            config_dir = self.config_paths.field_definitions_dir
        elif config_type in self.config_paths.custom_dirs:
            config_dir = self.config_paths.custom_dirs[config_type]
        else:
            return []
        
        if not config_dir.exists():
            return []
        
        config_files = list(config_dir.glob("*.json"))
        return [f.stem for f in config_files]
    
    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._config_cache.clear()
    
    def reload_config(self, config_type: str, config_name: str) -> Optional[Dict]:
        """Reload a specific configuration, bypassing cache."""
        cache_key = f"{config_type}:{config_name}"
        if cache_key in self._config_cache:
            del self._config_cache[cache_key]
        return self.load_config(config_type, config_name, use_cache=True)
    
    def get_config_info(self) -> Dict:
        """Get information about current configuration setup."""
        paths = self.config_paths
        
        info = {
            "base_dir": str(paths.base_dir),
            "formats_dir": str(paths.formats_dir),
            "housings_dir": str(paths.housings_dir),
            "field_definitions_dir": str(paths.field_definitions_dir),
            "custom_dirs": {name: str(path) for name, path in paths.custom_dirs.items()},
            "directories_exist": {
                "base": paths.base_dir.exists(),
                "formats": paths.formats_dir.exists(),
                "housings": paths.housings_dir.exists(),
                "field_definitions": paths.field_definitions_dir.exists(),
            },
            "config_counts": {
                "formats": len(self.list_configs("format")),
                "housings": len(self.list_configs("housing")),
                "field_definitions": len(self.list_configs("field_definition")),
            },
            "cache_size": len(self._config_cache)
        }
        
        # Add custom directory info
        for name in paths.custom_dirs:
            info["directories_exist"][f"custom_{name}"] = paths.custom_dirs[name].exists()
            info["config_counts"][f"custom_{name}"] = len(self.list_configs(name))
        
        return info
    
    def create_default_configs(self, overwrite: bool = False) -> Dict[str, bool]:
        """Create default configuration files."""
        results = {}
        
        # Default format configurations
        default_formats = {
            "pupitre": {
                "format_name": "pupitre",
                "metadata": {
                    "description": "Pupitre control system data format",
                    "file_extension": ".txt",
                    "delimiter": "\t",
                    "header_row": True
                },
                "fields": []  # Would be populated with actual field definitions
            },
            "pigbrother": {
                "format_name": "pigbrother", 
                "metadata": {
                    "description": "PigBrother TDMS data acquisition format",
                    "file_extension": ".tdms",
                    "format_type": "binary",
                    "structure": "groups/channels"
                },
                "fields": []
            },
            "bprofile": {
                "format_name": "bprofile",
                "metadata": {
                    "description": "Magnetic field profile measurement data",
                    "file_extension": ".txt", 
                    "delimiter": ",",
                    "header_row": True
                },
                "fields": []
            }
        }
        
        for format_name, config in default_formats.items():
            config_path = self.get_format_config_path(format_name)
            if not config_path.exists() or overwrite:
                results[f"format_{format_name}"] = self.save_config("format", format_name, config)
            else:
                results[f"format_{format_name}"] = False  # Already exists, not overwritten
        
        # Default housing configurations
        default_housings = {
            "m9": {
                "metadata": {
                    "description": "M9 housing configuration for hybrid magnet",
                    "timestamp": "2025-01-07T14:30:00Z"
                },
                "Insert": {},
                "Bitters": {},
                "Supras": {}
            }
        }
        
        for housing_name, config in default_housings.items():
            config_path = self.get_housing_config_path(housing_name)
            if not config_path.exists() or overwrite:
                results[f"housing_{housing_name}"] = self.save_config("housing", housing_name, config)
            else:
                results[f"housing_{housing_name}"] = False
        
        return results


# Global config manager instance
config_manager = ConfigManager()


# Convenience functions
def get_config_manager() -> ConfigManager:
    """Get the global configuration manager."""
    return config_manager


def set_config_base_dir(base_dir: Union[str, Path]) -> ConfigManager:
    """Set the base configuration directory globally."""
    return ConfigManager.set_base_config_dir(base_dir)


def load_format_config(format_name: str) -> Optional[Dict]:
    """Load format configuration."""
    return config_manager.load_config("format", format_name)


def load_housing_config(housing_name: str) -> Optional[Dict]:
    """Load housing configuration."""
    return config_manager.load_config("housing", housing_name)


def save_format_config(format_name: str, config_data: Dict) -> bool:
    """Save format configuration."""
    return config_manager.save_config("format", format_name, config_data)


def save_housing_config(housing_name: str, config_data: Dict) -> bool:
    """Save housing configuration."""
    return config_manager.save_config("housing", housing_name, config_data)


def get_config_info() -> Dict:
    """Get information about current configuration setup."""
    return config_manager.get_config_info()


# Environment variable setup helper
def setup_config_from_env():
    """Setup configuration paths from environment variables.
    
    Environment variables:
    - MAGNETRUN_CONFIG_DIR: Base configuration directory
    - MAGNETRUN_FORMATS_DIR: Format configurations directory  
    - MAGNETRUN_HOUSINGS_DIR: Housing configurations directory
    - MAGNETRUN_FIELD_DEFS_DIR: Field definitions directory
    """
    base_dir = os.getenv('MAGNETRUN_CONFIG_DIR')
    if base_dir:
        config_paths = ConfigPaths.from_base_dir(base_dir)
        
        # Allow individual directory overrides
        if os.getenv('MAGNETRUN_FORMATS_DIR'):
            config_paths.formats_dir = Path(os.getenv('MAGNETRUN_FORMATS_DIR'))
        if os.getenv('MAGNETRUN_HOUSINGS_DIR'):
            config_paths.housings_dir = Path(os.getenv('MAGNETRUN_HOUSINGS_DIR'))
        if os.getenv('MAGNETRUN_FIELD_DEFS_DIR'):
            config_paths.field_definitions_dir = Path(os.getenv('MAGNETRUN_FIELD_DEFS_DIR'))
        
        ConfigManager.initialize(config_paths)
        
        return config_paths
    else:
        # Use defaults
        return ConfigManager.initialize().config_paths


# Usage examples and documentation
if __name__ == "__main__":
    # Example usage
    
    # 1. Use default paths
    cm = ConfigManager()
    print("Default config info:", cm.get_config_info())
    
    # 2. Set custom base directory
    cm = ConfigManager.set_base_config_dir("/path/to/my/configs")
    
    # 3. Add custom configuration category
    cm.config_paths.add_custom_dir("instruments", "/path/to/instrument/configs")
    
    # 4. Load configurations
    pupitre_config = load_format_config("pupitre")
    m9_config = load_housing_config("m9")
    
    # 5. Create default configurations if they don't exist
    results = cm.create_default_configs(overwrite=False)
    print("Created configs:", results)
