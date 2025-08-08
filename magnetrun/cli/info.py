"""Information and validation commands."""

import click
from pathlib import Path

# FIXED: Import directly from module instead of top-level package
from ..core.magnet_data import MagnetData
from ..core.magnet_run import MagnetRun
from ..io.writers import DataWriter
from ..formats.registry import get_format_registry
from ..io.format_detector import FormatDetector
from .utils import handle_error


def load_magnet_data(file_path, housing, site=""):
    """Load magnet data - moved here to avoid circular import."""
    magnet_data = MagnetData.from_file(file_path)
    magnet_run = MagnetRun(housing, site, magnet_data)
    return magnet_data, magnet_run


@click.group(name="info")
def info_commands():
    """File information and validation commands."""
    pass


@info_commands.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--housing", default="M9", help="Housing type (M8, M9, M10)")
@click.option("--site", default="", help="Site identifier")
@click.option("--list-keys", is_flag=True, help="List available data keys")
@click.option("--convert", is_flag=True, help="Convert to CSV format")
@click.pass_context
def show(ctx, files, housing, site, list_keys, convert):
    """Display information about data files."""
    debug = ctx.obj.get("DEBUG", False)

    for file_path in files:
        click.echo(f"Processing: {file_path}")

        try:
            magnet_data, magnet_run = load_magnet_data(file_path, housing, site)

            if debug:
                click.echo(f"  Debug: File extension: {Path(file_path).suffix}")
                click.echo(f"  Debug: Format type: {magnet_data.format_type}")

            click.echo(f"  Housing: {magnet_run.housing}")
            click.echo(f"  Site: {magnet_run.site}")
            click.echo(f"  Format: {magnet_data.format_type}")
            click.echo(f"  Keys count: {len(magnet_run.get_keys())}")

            info_dict = magnet_data.get_info()
            click.echo(f"  Filename: {info_dict['filename']}")
            click.echo(
                f"  Data shape: {info_dict.get('metadata', {}).get('shape', 'N/A')}"
            )

            if list_keys:
                click.echo("  Available keys:")
                for key in magnet_run.get_keys():
                    click.echo(f"    {key}")

            if convert:
                _convert_file(magnet_data, file_path)

        except Exception as e:
            handle_error(e, debug, file_path)


@info_commands.command()
@click.pass_context
def formats(ctx):
    """List supported file formats and their characteristics."""
    click.echo("Supported File Formats:")
    click.echo("=" * 50)

    # detector = FormatDetector()

    fregistry = get_format_registry()
    for format_name in fregistry.get_supported_formats():
        reader_class = fregistry.get_reader(format_name)
        reader_instance = reader_class()

        click.echo(f"\n{format_name.upper()}")
        click.echo(f"  Extensions: {', '.join(reader_instance.supported_extensions)}")
        click.echo(
            f"  Description: {reader_instance.__doc__ or 'No description available'}"
        )

        data_handler_class = fregistry.get_data_handler(format_name)
        click.echo(f"  Handler: {data_handler_class.__name__}")


@info_commands.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True), required=True)
@click.pass_context
def validate(ctx, files):
    """Validate files and show detected formats."""
    detector = FormatDetector()

    click.echo("File Format Validation:")
    click.echo("=" * 50)

    for file_path in files:
        file_path = Path(file_path)
        detected_format = detector.detect_format(file_path)

        if detected_format:
            click.echo(f"✓ {file_path.name}: {detected_format}")

            try:
                reader = detector.get_reader_for_file(file_path)
                file_data = reader.read(file_path)
                metadata = file_data.get("metadata", {})

                if "shape" in metadata:
                    click.echo(f"    Shape: {metadata['shape']}")
                if "columns" in metadata:
                    click.echo(f"    Columns: {len(metadata['columns'])}")

            except Exception as e:
                click.echo(f"    Warning: Could not read file details: {e}")
        else:
            click.echo(f"✗ {file_path.name}: Unknown format")


def _convert_file(magnet_data, file_path):
    """Helper function to convert files to CSV."""
    if magnet_data.format_type in ["pandas", "pupitre", "bprofile"]:
        output_path = Path(file_path).with_suffix(".csv")
        DataWriter.to_csv(magnet_data, output_path)
        click.echo(f"  Converted to: {output_path}")

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
                if "main" not in groups:
                    groups["main"] = []
                groups["main"].append(key)

        # Convert each group to a separate CSV file
        base_path = Path(file_path).with_suffix("")
        for group_name, group_keys in groups.items():
            try:
                group_data = magnet_data.get_data(group_keys)
                output_path = base_path.with_suffix(f"_{group_name}.csv")
                group_data.to_csv(output_path, index=False)
                click.echo(f"  Converted group '{group_name}' to: {output_path}")
            except Exception as e:
                click.echo(f"  Warning: Could not convert group '{group_name}': {e}")

    else:
        # Generic conversion for other formats
        try:
            output_path = Path(file_path).with_suffix(".csv")
            data = magnet_data.get_data()
            data.to_csv(output_path, index=False)
            click.echo(f"  Converted to: {output_path}")
        except Exception as e:
            click.echo(f"  Error converting file: {e}")
