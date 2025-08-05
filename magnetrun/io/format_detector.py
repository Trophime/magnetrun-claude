
"""Auto-detect file format based on content and extension."""

from pathlib import Path
from typing import Optional, List
from .base_reader import BaseReader


class FormatDetector:
    """Automatically detect file format based on content and extension."""
    
    def __init__(self):
        self._readers: List[BaseReader] = []
        self._initialize_readers()
    
    def _initialize_readers(self) -> None:
        """Initialize all registered readers."""
        # Import here to avoid circular import
        from ..formats.registry import format_registry
        
        for format_name in format_registry.get_supported_formats():
            reader_class = format_registry.get_reader(format_name)
            self._readers.append(reader_class())
    
    def detect_format(self, filepath: Path) -> Optional[str]:
        """Detect format of the file."""
        for reader in self._readers:
            if reader.can_read(filepath):
                return reader.format_name
        return None
    
    def get_reader_for_file(self, filepath: Path) -> Optional[BaseReader]:
        """Get appropriate reader for the file."""
        for reader in self._readers:
            if reader.can_read(filepath):
                return reader
        return None
