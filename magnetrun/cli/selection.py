"""Data extraction and conversion commands."""

import click
from pathlib import Path
from .utils import load_magnet_data, add_time_column_if_needed, handle_error
from ..io.writers import DataWriter

@click.group(name='select')
def selection_commands():
    """Data extraction and conversion commands."""
    pass

@selection_commands.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--housing', default='M9', help='Housing type')
@click.option('--time', multiple=True, help='Extract data at specific times')
@click.option('--time-range', multiple=True, help='Extract data in time ranges (format: "start;end")')
@click.option('--key', multiple=True, help='Extract specific keys vs time')
@click.option('--key-pairs', multiple=True, help='Extract key pairs (format: "key1;key2" or multiple pairs "key1;key2,key3;key4")')
@click.option('--convert', is_flag=True, help='Convert file to CSV')
@click.pass_context
def extract(ctx, files, housing, time, time_range, key, key_pairs, convert):
    """Extract and select data subsets."""
    debug = ctx.obj.get('DEBUG', False)
    
    for file_path in files:
        click.echo(f"Selecting from: {file_path}")
        
        try:
            magnet_data, magnet_run = load_magnet_data(file_path, housing)
            add_time_column_if_needed(magnet_data, debug)
            
            if time:
                _extract_at_times(magnet_data, time, file_path)
            
            if time_range:
                _extract_time_ranges(magnet_data, time_range, file_path)
            
            if key:
                _extract_keys_vs_time(magnet_data, key, file_path)
            
            if key_pairs:
                _extract_key_pairs(magnet_data, key_pairs, file_path)
            
            if convert:
                _convert_entire_file(magnet_data, file_path)
            
        except Exception as e:
            handle_error(e, debug, file_path)

def _extract_at_times(magnet_data, time_options, file_path):
    """Extract data at specific times."""
    click.echo("  Extracting data at specific times...")
    for time_list in time_options:
        times = [float(t) for t in time_list.split(';')]
        
        for time_val in times:
            data = magnet_data.get_data()
            
            if 't' in data.columns:
                closest_idx = (data['t'] - time_val).abs().idxmin()
                selected_data = data.iloc[[closest_idx]]
                
                output_path = Path(file_path).with_suffix(f'_at_{time_val:.3f}s.csv')
                selected_data.to_csv(output_path, sep='\t', index=False, header=True)
                click.echo(f"    Saved: {output_path}")
            else:
                click.echo("    Warning: No time column found for time extraction")

def _extract_time_ranges(magnet_data, time_range_options, file_path):
    """Extract data in time ranges."""
    click.echo("  Extracting data in time ranges...")
    for time_range in time_range_options:
        start_time, end_time = time_range.split(';')
        start_time = float(start_time.replace(':', '-'))
        end_time = float(end_time.replace(':', '-'))
        
        data = magnet_data.get_data()
        
        if 't' in data.columns:
            mask = (data['t'] >= start_time) & (data['t'] <= end_time)
            selected_data = data[mask]
            
            output_path = Path(file_path).with_suffix(f'_from_{start_time:.1f}_to_{end_time:.1f}.csv')
            selected_data.to_csv(output_path, sep='\t', index=False, header=True)
            click.echo(f"    Saved: {output_path}")
        else:
            click.echo("    Warning: No time column found for time range extraction")

def _extract_keys_vs_time(magnet_data, key_options, file_path):
    """Extract specific keys vs time."""
    click.echo("  Extracting specific keys...")
    for key_list in key_options:
        selected_keys = key_list.split(';') if ';' in key_list else [key_list]
        
        # Always include time if not present
        if 't' not in selected_keys and 't' in magnet_data.keys:
            selected_keys.insert(0, 't')
        
        # Validate keys exist
        valid_keys = [k for k in selected_keys if k in magnet_data.keys]
        
        if valid_keys:
            selected_data = magnet_data.get_data(valid_keys)
            
            key_name = '_'.join([k for k in valid_keys if k != 't'])
            output_path = Path(file_path).with_suffix(f'_{key_name}_vs_Time.csv')
            
            selected_data.to_csv(output_path, sep='\t', index=False, header=True)
            click.echo(f"    Saved: {output_path}")
        else:
            click.echo(f"    Warning: No valid keys found in {selected_keys}")

def _extract_key_pairs(magnet_data, key_pairs_options, file_path):
    """Extract key pairs."""
    click.echo("  Extracting key pairs...")
    for pair_list in key_pairs_options:
        # Support both comma-separated pairs and single pairs
        if ',' in pair_list:
            pairs = pair_list.split(',')
        else:
            pairs = [pair_list]
        
        for pair in pairs:
            if ';' in pair:
                key1, key2 = pair.split(';', 1)
                
                if key1 in magnet_data.keys and key2 in magnet_data.keys:
                    pair_data = magnet_data.get_data([key1, key2])
                    
                    # Remove zero values
                    pair_data = pair_data[(pair_data[key1] != 0) & (pair_data[key2] != 0)]
                    
                    output_path = Path(file_path).with_suffix(f'_{key1}_{key2}.csv')
                    pair_data.to_csv(output_path, sep='\t', index=False, header=False)
                    click.echo(f"    Saved pair: {output_path}")
                else:
                    click.echo(f"    Warning: Keys '{key1}' or '{key2}' not found")
            else:
                click.echo(f"    Warning: Invalid pair format '{pair}', expected 'key1;key2'")

def _convert_entire_file(magnet_data, file_path):
    """Convert entire file to CSV."""
    click.echo("  Converting file...")
    
    if magnet_data.format_type in ["pandas", "pupitre", "bprofile"]:
        output_path = Path(file_path).with_suffix('.csv')
        DataWriter.to_csv(magnet_data, output_path)
        click.echo(f"    Converted to: {output_path}")
        
    elif magnet_data.format_type == "pigbrother":
        # Convert each group separately for pigbrother format
        all_keys = magnet_data.keys
        groups = {}
        
        # Group keys by their group name (everything before the first '/')
        for key in all_keys:
            if "/" in key:
                group_name = key.split("/")[0]
                if group_name not in groups:
                    groups[group_name] = []
                groups[group_name].append(key)
            else:
                # Keys without group go to 'main' group
                if 'main' not in groups:
                    groups['main'] = []
                groups['main'].append(key)
        
        # Convert each group to a separate CSV file
        base_path = Path(file_path).with_suffix('')
        for group_name, group_keys in groups.items():
            try:
                group_data = magnet_data.get_data(group_keys)
                output_path = base_path.with_suffix(f'_{group_name}.csv')
                group_data.to_csv(output_path, index=False)
                click.echo(f"    Converted group '{group_name}' to: {output_path}")
            except Exception as e:
                click.echo(f"    Warning: Could not convert group '{group_name}': {e}")
                
    else:
        # Generic conversion for other formats
        try:
            output_path = Path(file_path).with_suffix('.csv')
            data = magnet_data.get_data()
            data.to_csv(output_path, index=False)
            click.echo(f"    Converted to: {output_path}")
        except Exception as e:
            click.echo(f"    Error converting file: {e}")


