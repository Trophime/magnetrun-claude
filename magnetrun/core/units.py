"""Unit management for MagnetRun data."""

from typing import Tuple, Optional, Dict, Any
from pint import UnitRegistry

class UnitManager:
    """Manages units and unit conversions for magnetic data."""
    
    def __init__(self):
        self.ureg = UnitRegistry()
        self.ureg.define("percent = 1 / 100 = %")
        self.ureg.define("ppm = 1e-6 = ppm")
        self.ureg.define("var = 1")
        
        self._pigbrother_units = {
            "Courant": ("I", self.ureg.ampere),
            "Tension": ("U", self.ureg.volt),
            "Puissance": ("Power", self.ureg.watt),
            "Champ_magn": ("B", self.ureg.gauss),
        }
    
    def get_pigbrother_units(self, key: str) -> Tuple[str, Any]:
        """Get units for PigBrother data keys."""
        for entry in self._pigbrother_units:
            if entry in key:
                return self._pigbrother_units[entry]
        return ()
    
    def infer_units_from_key(self, key: str) -> Tuple[str, Any]:
        """Infer units from key name."""
        if key == "timestamp":
            return ("time", None)
        elif key == "t":
            return ("t", self.ureg.second)
        elif key == "Field":
            return ("B", self.ureg.tesla)
        elif key.startswith("I"):
            return ("I", self.ureg.ampere)
        elif key.startswith("U"):
            return ("U", self.ureg.volt)
        elif key.startswith("T") or key in ["teb", "tsb"]:
            return ("T", self.ureg.degC)
        elif key.startswith("Rpm"):
            return ("Rpm", self.ureg.rpm)
        elif key.startswith("DR"):
            return ("%", self.ureg.percent)
        elif key.startswith("Flo"):
            return ("Q", self.ureg.liter / self.ureg.second)
        elif key == "debitbrut":
            return ("Q", self.ureg.meter**3 / self.ureg.hour)
        elif key.startswith("HP") or key.startswith("BP"):
            return ("P", self.ureg.bar)
        elif key in ["Pmagnet", "Ptot"] or key.startswith("Power"):
            return ("Power", self.ureg.megawatt)
        elif key == "Q":
            return ("Preac", self.ureg.megavar)
        return ("", None)
