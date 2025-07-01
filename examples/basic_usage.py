
#!/usr/bin/env python
"""
Basic usage examples for MagnetRun package.
"""

from magnetrun import MagnetData, MagnetRun
from magnetrun.visualization.plotters import DataPlotter
from pathlib import Path

def main():
    """Demonstrate basic MagnetRun usage."""
    
    # Example 1: Load and inspect data
    print("=== Example 1: Loading Data ===")
    
    # Load any supported format automatically
    data_file = "examples/data/sample_measurement.tdms"
    if Path(data_file).exists():
        magnet_data = MagnetData.from_file(data_file)
        
        print(f"Format: {magnet_data.format_type}")
        print(f"Available keys: {magnet_data.keys}")
        print(f"Data info: {magnet_data.get_info()}")
    else:
        print(f"Sample data file not found: {data_file}")
        print("Please provide a valid measurement file.")
        return
    
    # Example 2: Create MagnetRun for analysis
    print("\n=== Example 2: Analysis Setup ===")
    magnet_run = MagnetRun("M9", "Lab1", magnet_data)
    magnet_run.prepare_data()  # Apply housing-specific processing
    
    print(f"Housing: {magnet_run.housing}")
    print(f"Site: {magnet_run.site}")
    print(f"Available keys after processing: {magnet_run.get_keys()}")
    
    # Example 3: Data extraction
    print("\n=== Example 3: Data Extraction ===")
    try:
        # Get all data
        all_data = magnet_data.get_data()
        print(f"Data shape: {all_data.shape}")
        
        # Get specific columns
        if 'Field' in magnet_data.keys:
            field_data = magnet_data.get_data(['Field'])
            print(f"Field data: {field_data.head()}")
    except Exception as e:
        print(f"Error accessing data: {e}")
    
    # Example 4: Quick visualization
    print("\n=== Example 4: Visualization ===")
    try:
        # Quick plot with defaults
        DataPlotter.quick_plot(magnet_data, save=True)
        print("Created quick_plot.png")
        
        # Overview plot
        DataPlotter.create_overview_plot(
            magnet_data, 
            template='standard',
            file_path=data_file,
            save=True,
            show=False
        )
        print(f"Created overview plot")
        
    except Exception as e:
        print(f"Error creating plots: {e}")
    
    # Example 5: Add calculated data
    print("\n=== Example 5: Calculated Columns ===")
    try:
        if 'Field' in magnet_data.keys and 'Current' in magnet_data.keys:
            magnet_data.add_data('Power', 'Power = Field * Current')
            print("Added Power = Field * Current")
            print(f"Updated keys: {magnet_data.keys}")
    except Exception as e:
        print(f"Error adding calculated column: {e}")

if __name__ == '__main__':
    main()
