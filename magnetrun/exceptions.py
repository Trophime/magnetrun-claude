
"""Exception classes for MagnetRun package."""

class MagnetRunError(Exception):
    """Base exception class for MagnetRun."""
    pass

class FileFormatError(MagnetRunError):
    """Raised when file format is not supported or invalid."""
    pass

class DataFormatError(MagnetRunError):
    """Raised when data format is invalid or corrupted."""
    pass

class KeyNotFoundError(MagnetRunError):
    """Raised when requested data key is not found."""
    pass

class UnitConversionError(MagnetRunError):
    """Raised when unit conversion fails."""
    pass

class AnalysisError(MagnetRunError):
    """Raised when analysis operation fails."""
    pass
