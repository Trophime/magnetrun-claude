
#!/usr/bin/env python
"""
Advanced analysis examples for MagnetRun package.
"""

import numpy as np
from pathlib import Path
from magnetrun import MagnetData, MagnetRun
from magnetrun.visualization.plotters import DataPlotter
from magnetrun.processing.analysis import DataAnalyzer

def breakpoint_analysis_example():
    """Demonstrate breakpoint detection analysis."""
    print("=== Breakpoint Analysis Example ===")
    
    # Load sample data
    data_file = "examples/data/sample_measurement.tdms"
    if not Path(data_file).exists():
        print(f"Sample data file not found: {data_file}")
        return
    
    magnet_data = MagnetData.from_file(data_file)
    
    # Perform breakpoint analysis on Field data
    if 'Field' in magnet_data.keys:
        try:
            results = DataAnalyzer.detect_breakpoints(
                magnet_data, 
                'Field',
                window=10,
                level=90
            )
            
            print(f"Found {len(results['peaks'])} breakpoints")
            print(f"Threshold: {results['quantiles_der']:.2e}")
            
            # Create visualization
            DataPlotter.plot_breakpoints_analysis(
                magnet_data,
                ['Field'],
                window=10,
                level=90,
                file_path=data_file,
                save=True,
                show=False
            )
            
        except Exception as e:
            print(f"Error in breakpoint analysis: {e}")
    else:
        print("No 'Field' key found for breakpoint analysis")

def plateau_analysis_example():
    """Demonstrate plateau detection analysis."""
    print("\n=== Plateau Analysis Example ===")
    
    try:
        from magnetrun.utils.plateaux import nplateaus
        
        data_file = "examples/data/sample_measurement.tdms"
        if not Path(data_file).exists():
            print(f"Sample data file not found: {data_file}")
            return
        
        magnet_data = MagnetData.from_file(data_file)
        
        if 'Field' in magnet_data.keys:
            # Get unit information
            symbol, unit = magnet_data.get_unit_key('Field')
            
            plateaus = nplateaus(
                magnet_data,
                xField=("t", "t", "s"),
                yField=('Field', symbol, unit),
                threshold=1e-3,
                num_points_threshold=100,
                verbose=True
            )
            
            print(f"Found {len(plateaus)} plateaus")
            if plateaus:
                max_plateau = max(plateaus, key=lambda p: p['duration'])
                print(f"Longest plateau: {max_plateau['duration']:.2f}s at {max_plateau['value']:.3f}")
                
        else:
            print("No 'Field' key found for plateau analysis")
            
    except ImportError:
        print("Plateau analysis module not available")
    except Exception as e:
        print(f"Error in plateau analysis: {e}")

def batch_processing_example():
    """Demonstrate batch processing of multiple files."""
    print("\n=== Batch Processing Example ===")
    
    # Process all files in data directory
    data_dir = Path("examples/data/")
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}")
        return
    
    results = {}
    
    # Find all supported files
    file_patterns = ['*.tdms', '*.txt', '*.csv']
    files = []
    for pattern in file_patterns:
        files.extend(data_dir.glob(pattern))
    
    if not files:
        print("No data files found for batch processing")
        return
    
    for file_path in files:
        try:
            print(f"Processing: {file_path.name}")
            
            # Load data
            magnet_data = MagnetData.from_file(file_path)
            
            # Collect metadata
            info = magnet_data.get_info()
            results[file_path.name] = {
                'format': magnet_data.format_type,
                'keys': len(magnet_data.keys),
                'shape': info.get('metadata', {}).get('shape', 'Unknown')
            }
            
            # Create overview plot
            DataPlotter.create_overview_plot(
                magnet_data,
                template='standard',
                file_path=str(file_path),
                save=True,
                show=False
            )
            
        except Exception as e:
            print(f"  Error processing {file_path.name}: {e}")
            results[file_path.name] = {'error': str(e)}
    
    # Print summary
    print("\nBatch Processing Summary:")
    for filename, result in results.items():
        if 'error' in result:
            print(f"  {filename}: ERROR - {result['error']}")
        else:
            print(f"  {filename}: {result['format']} format, {result['keys']} keys, shape {result['shape']}")

def custom_analysis_pipeline():
    """Demonstrate a complete custom analysis pipeline."""
    print("\n=== Custom Analysis Pipeline ===")
    
    data_file = "examples/data/sample_measurement.tdms"
    if not Path(data_file).exists():
        print(f"Sample data file not found: {data_file}")
        return
    
    try:
        # Step 1: Load and prepare data
        magnet_data = MagnetData.from_file(data_file)
        magnet_run = MagnetRun("M9", "Lab1", magnet_data)
        magnet_run.prepare_data()
        
        # Step 2: Add calculated fields
        available_keys = magnet_data.keys
        if 'Field' in available_keys and 'Current' in available_keys:
            magnet_data.add_data('Power', 'Power = Field * Current')
            magnet_data.add_data('FieldSquared', 'FieldSquared = Field ** 2')
        
        # Step 3: Statistical analysis
        analysis_results = {}
        
        for key in ['Field', 'Current', 'Power']:
            if key in magnet_data.keys:
                data = magnet_data.get_data([key])
                analysis_results[key] = {
                    'mean': data[key].mean(),
                    'std': data[key].std(),
                    'min': data[key].min(),
                    'max': data[key].max(),
                    'range': data[key].max() - data[key].min()
                }
        
        # Step 4: Create comprehensive report
        print("Analysis Results:")
        for key, stats in analysis_results.items():
            print(f"  {key}:")
            for stat_name, value in stats.items():
                print(f"    {stat_name}: {value:.3f}")
        
        # Step 5: Generate plots
        output_dir = Path("analysis_output")
        output_dir.mkdir(exist_ok=True)
        
        # Time series plot
        DataPlotter.plot_time_series_to_file(
            magnet_data,
            list(analysis_results.keys()),
            normalize=True,
            file_path=str(data_file),
            save=True,
            show=False,
            output_dir=output_dir
        )
        
        # Overview plot
        DataPlotter.create_overview_plot(
            magnet_data,
            template='publication',
            file_path=str(data_file),
            save=True,
            show=False,
            output_dir=output_dir
        )
        
        print(f"Analysis complete. Results saved to {output_dir}/")
        
    except Exception as e:
        print(f"Error in analysis pipeline: {e}")

def main():
    """Run all advanced analysis examples."""
    breakpoint_analysis_example()
    plateau_analysis_example()
    batch_processing_example()
    custom_analysis_pipeline()

if __name__ == '__main__':
    main()
