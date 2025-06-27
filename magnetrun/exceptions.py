"""Custom exceptions for the MagnetRun package."""

class MagnetDataError(Exception):
    """Base exception for MagnetData operations."""
    pass

class DataFormatError(MagnetDataError):
    """Raised when data format is invalid."""
    pass

class UnitConversionError(MagnetDataError):
    """Raised when unit conversion fails."""
    pass

class KeyNotFoundError(MagnetDataError):
    """Raised when a data key is not found."""
    pass

class FileFormatError(MagnetDataError):
    """Raised when file format is not supported."""
    pass
