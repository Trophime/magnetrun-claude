"""Unit management for MagnetRun data."""

from typing import Tuple, Any


class UnitManager:
    """Manages units and unit conversions for magnetic data."""

    def __init__(self):
        from ..formats.format_definition import get_global_ureg

        ureg = get_global_ureg()

        self._pigbrother_units = {
            "Courant": ("I", ureg.ampere),
            "Tension": ("U", ureg.volt),
            "Puissance": ("Power", ureg.watt),
            "Champ_magn": ("B", ureg.gauss),
        }

    def get_pigbrother_units(self, key: str) -> Tuple[str, Any]:
        """Get units for PigBrother data keys."""
        for entry in self._pigbrother_units:
            if entry in key:
                return self._pigbrother_units[entry]
        return ("", None)

    def infer_units_from_key(self, key: str) -> Tuple[str, Any]:
        """Infer units from key name."""
        from ..formats.format_definition import get_global_ureg

        ureg = get_global_ureg()

        if key == "timestamp":
            return ("time", None)
        elif key == "t":
            return ("t", ureg.second)
        elif key == "Field":
            return ("B", ureg.tesla)
        elif key.startswith("I"):
            return ("I", ureg.ampere)
        elif key.startswith("U"):
            return ("U", ureg.volt)
        elif key.startswith("T") or key in ["teb", "tsb"]:
            return ("T", ureg.degC)
        elif key.startswith("Rpm"):
            return ("Rpm", ureg.rpm)
        elif key.startswith("DR"):
            return ("%", ureg.percent)
        elif key.startswith("Flo"):
            return ("Q", ureg.liter / ureg.second)
        elif key == "debitbrut":
            return ("Q", ureg.meter**3 / ureg.hour)
        elif key.startswith("HP") or key.startswith("BP"):
            return ("P", ureg.bar)
        elif key in ["Pmagnet", "Ptot"] or key.startswith("Power"):
            return ("Power", ureg.megawatt)
        elif key == "Q":
            return ("Preac", ureg.megavar)
        elif key == "Position (mm)":
            return ("L", ureg.millimeter)
        elif "Profile" in key and "%" in key:
            return ("%", ureg.percent)
        return ("", None)
