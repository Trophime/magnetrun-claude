"""Simple test to verify imports work correctly."""

def test_import_magnetdata():
    """Test that MagnetData can be imported."""
    from magnetrun import MagnetData
    assert MagnetData is not None

def test_import_magnetrun():
    """Test that MagnetRun can be imported."""
    from magnetrun import MagnetRun
    assert MagnetRun is not None

def test_import_formats():
    """Test that format components can be imported."""
    from magnetrun.formats import FormatRegistry, FormatDefinition
    assert FormatRegistry is not None
    assert FormatDefinition is not None

def test_import_fields():
    """Test that field components can be imported."""
    from magnetrun.core.fields import Field, FieldType
    assert Field is not None
    assert FieldType is not None

def test_from_pandas():
    """Test creating MagnetData from pandas (no file I/O)."""
    import pandas as pd
    from magnetrun import MagnetData
    
    df = pd.DataFrame({
        'Field': [0.0, 0.1, 0.2],
        'Current': [0.0, 1.0, 2.0],
        't': [0.0, 1.0, 2.0]
    })
    
    magnet_data = MagnetData.from_pandas("test.csv", df)
    
    assert magnet_data.filename == "test.csv"
    assert len(magnet_data.keys) == 3
    assert 'Field' in magnet_data.keys
    assert 'Current' in magnet_data.keys
    assert 't' in magnet_data.keys

def test_format_registry():
    """Test that FormatRegistry can be instantiated."""
    from magnetrun.formats import FormatRegistry
    
    registry = FormatRegistry()
    assert registry is not None
    # Test that it has the expected methods
    assert hasattr(registry, 'get_supported_formats')
    assert hasattr(registry, 'get_format_definition')
