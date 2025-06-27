"""Configuration settings for different housing types."""

from typing import Dict, List, Any

class HousingConfig:
    """Configuration for a specific housing type."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.ih_ref_channels = config.get('ih_ref_channels', [])
        self.ib_ref_channels = config.get('ib_ref_channels', [])
        self.field_mappings = config.get('field_mappings', {})
        self.remove_channels = config.get('remove_channels', [])
    
    def get_ih_formula(self) -> str:
        """Get formula for IH reference calculation."""
        if not self.ih_ref_channels:
            return ""
        return f"IH_ref = {' + '.join(self.ih_ref_channels)}"
    
    def get_ib_formula(self) -> str:
        """Get formula for IB reference calculation."""
        if not self.ib_ref_channels:
            return ""
        return f"IB_ref = {' + '.join(self.ib_ref_channels)}"

HOUSING_CONFIGS = {
    'M9': HousingConfig('M9', {
        'ih_ref_channels': ['Idcct1', 'Idcct2'],
        'ib_ref_channels': ['Idcct3', 'Idcct4'],
        'field_mappings': {
            'Flow1': 'FlowH', 'Flow2': 'FlowB',
            'Rpm1': 'RpmH', 'Rpm2': 'RpmB',
            'Tin1': 'TinH', 'Tin2': 'TinB',
            'HP1': 'HPH', 'HP2': 'HPB'
        },
        'remove_channels': ['Idcct1', 'Idcct2', 'Idcct3', 'Idcct4']
    }),
    'M8': HousingConfig('M8', {
        'ih_ref_channels': ['Idcct3', 'Idcct4'],
        'ib_ref_channels': ['Idcct1', 'Idcct2'],
        'field_mappings': {
            'Flow1': 'FlowB', 'Flow2': 'FlowH',
            'Rpm1': 'RpmB', 'Rpm2': 'RpmH',
            'Tin1': 'TinB', 'Tin2': 'TinH',
            'HP1': 'HPB', 'HP2': 'HPH'
        },
        'remove_channels': ['Idcct1', 'Idcct2', 'Idcct3', 'Idcct4']
    }),
    'M10': HousingConfig('M10', {
        'ih_ref_channels': ['Idcct3', 'Idcct4'],
        'ib_ref_channels': ['Idcct1', 'Idcct2'],
        'field_mappings': {
            'Flow1': 'FlowB', 'Flow2': 'FlowH',
            'Rpm1': 'RpmB', 'Rpm2': 'RpmH',
            'Tin1': 'TinB', 'Tin2': 'TinH',
            'HP1': 'HPB', 'HP2': 'HPH'
        },
        'remove_channels': ['Idcct1', 'Idcct2', 'Idcct3', 'Idcct4']
    })
}
