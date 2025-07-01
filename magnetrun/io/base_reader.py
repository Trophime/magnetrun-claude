
"""Abstract base class for file readers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from pathlib import Path

class BaseReader(ABC):
    """Abstract base class for file readers."""
    
    @abstractmethod
    def can_read(self, filepath: Path) -> bool:
        """Check if this reader can handle the file."""
        pass
    
    @abstractmethod
    def read(self, filepath: Path) -> Dict[str, Any]:
        """Read the file and return structured data."""
        pass
    
    @property
    @abstractmethod
    def format_name(self) -> str:
        """Name of the format this reader handles."""
        pass
    
    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """List of supported file extensions."""
        pass
