"""CLI commands for format management with centralized configuration system."""

import os
import json
import sys
from pathlib import Path
from typing import Optional
import click
from tabulate import tabulate
import pandas as pd

# UPDATED: Import from centralized config system
from ..formats.centralized_config import get_config_manager
from ..formats.registry import FormatRegistry
from ..formats.format_definition import FormatDefinition
from ..core.fields import (
    FieldType,
    validate_format_definition,
    create_field_summary,
    create_format_config_from_data,
)


@click.group()
def formats():
    """Manage field format definitions using centralized configuration."""
    pass


@formats.command()
@click.option("--detailed", "-d", is_flag=True, help="Show detailed field information")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def list(detailed: bool, output_format: str):
    """List available format definitions from centralized config."""
    config_manager = get_config_manager()
    format_names = config_manager.list_configs("format")

    if not format_names:
        click.echo("No format definitions found.")
        click.echo(f"Config directory: {config_manager.config_paths.formats_dir}")
        click.echo("Run 'magnetrun config init' to create default configurations.")
        return

    if output_format == "json":
        if detailed:
            output = {}
            registry = FormatRegistry(config_manager)
            for name in format_names:
                format_def = registry.get_format(name)
                if format_def:
                    output[name] = create_field_summary(format_def)
                else:
                    output[name] = {"error": "Failed to load format definition"}
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo(json.dumps(format_names, indent=2))
        return

    # Table output
    if detailed:
        table_data = []
        registry = FormatRegistry(config_manager)

        for name in format_names:
            format_def = registry.get_format(name)
            if format_def:
                summary = create_field_summary(format_def)

                # Count fields by type
                type_counts = []
                for field_type, info in summary["by_type"].items():
                    type_counts.append(f"{field_type}: {info['count']}")

                table_data.append(
                    [
                        name,
                        summary["total_fields"],
                        ", ".join(type_counts[:3])
                        + ("..." if len(type_counts) > 3 else ""),
                        len(summary["units_used"]),
                        format_def.metadata.get("description", ""),
                        str(config_manager.get_format_config_path(name)),
                    ]
                )
            else:
                table_data.append(
                    [name, "?", "Failed to load", "?", "Error loading", "?"]
                )

        headers = [
            "Format",
            "Fields",
            "Types (top 3)",
            "Units",
            "Description",
            "Config Path",
        ]
        click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))
    else:
        click.echo("Available format definitions:")
        registry = FormatRegistry(config_manager)
        for name in format_names:
            format_def = registry.get_format(name)
            description = "No description"
            if format_def:
                description = format_def.metadata.get("description", "No description")
            click.echo(f"  {name:<15} - {description}")


@formats.command()
@click.argument("format_name")
@click.option(
    "--output", "-o", type=click.Path(), help="Save to file instead of stdout"
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["json", "table", "summary"]),
    default="table",
    help="Output format",
)
def show(format_name: str, output: Optional[str], output_format: str):
    """Show detailed information about a format definition from centralized config."""
    config_manager = get_config_manager()
    registry = FormatRegistry(config_manager)
    format_def = registry.get_format(format_name)

    if not format_def:
        click.echo(f"Format '{format_name}' not found.", err=True)
        available_formats = config_manager.list_configs("format")
        if available_formats:
            click.echo("Available formats:")
            for name in available_formats:
                click.echo(f"  {name}")
        else:
            click.echo(
                "No format definitions available. Run 'magnetrun config init' to create defaults."
            )
        sys.exit(1)

    if output_format == "json":
        output_data = format_def.to_dict()
        content = json.dumps(output_data, indent=2)
    elif output_format == "summary":
        summary = create_field_summary(format_def)
        content = json.dumps(summary, indent=2)
    else:  # table
        content = _format_definition_to_table(format_def)
        # Add config path information
        config_path = config_manager.get_format_config_path(format_name)
        content += f"\n\nConfiguration file: {config_path}"

    if output:
        Path(output).write_text(content)
        click.echo(f"Format definition saved to {output}")
    else:
        click.echo(content)


@formats.command()
@click.option("--verbose", "-v", is_flag=True, help="Show loading details")
def reload(verbose: bool):
    """Reload all format definitions from centralized configuration."""
    config_manager = get_config_manager()
    registry = FormatRegistry(config_manager)

    old_count = len(registry.list_formats())

    if verbose:
        click.echo(f"Reloading formats from {config_manager.config_paths.formats_dir}")

    # Clear caches and reload
    config_manager.clear_cache()
    registry.reload_formats()

    new_count = len(registry.list_formats())

    click.echo(f"Reloaded {new_count} formats (was {old_count})")

    if verbose:
        for format_name in registry.list_formats():
            format_def = registry.get_format(format_name)
            if format_def:
                click.echo(f"  {format_name}: {len(format_def.fields)} fields")
            else:
                click.echo(f"  {format_name}: Failed to load")


@formats.command()
def configs():
    """Show path to configs directory and list config files."""
    config_manager = get_config_manager()
    configs_dir = config_manager.config_paths.formats_dir

    click.echo(f"Formats directory: {configs_dir}")
    click.echo(f"Directory exists: {configs_dir.exists()}")

    if configs_dir.exists():
        json_files = list(configs_dir.glob("*.json"))
        click.echo(f"\nJSON config files ({len(json_files)}):")
        for json_file in json_files:
            click.echo(f"  {json_file.name}")

        # Show any non-JSON files (might be user additions)
        other_files = [
            f for f in configs_dir.iterdir() if f.is_file() and f.suffix != ".json"
        ]
        if other_files:
            click.echo("\nOther files:")
            for other_file in other_files:
                click.echo("  {other_file.name}")
    else:
        click.echo(
            "\nDirectory does not exist. Run 'magnetrun config init' to create it."
        )

    # Show config system info
    config_info = config_manager.get_config_info()
    click.echo(f"\nBase config directory: {config_info['base_dir']}")
    click.echo(
        f"Total format configs: {config_info['config_counts'].get('formats', 0)}"
    )


@formats.command()
@click.argument("format_name")
@click.option("--editor", "-e", help="Editor to use (default: system default)")
def edit(format_name: str, editor: Optional[str]):
    """Edit a format definition file using centralized config."""
    import subprocess
    import os

    config_manager = get_config_manager()
    config_file = config_manager.get_format_config_path(format_name)

    if not config_file.exists():
        click.echo(f"Format configuration '{format_name}' does not exist.")
        available_formats = config_manager.list_configs("format")
        if available_formats:
            click.echo("Available formats:")
            for name in available_formats:
                click.echo(f"  {name}")
        else:
            click.echo(
                "No format configurations found. Run 'magnetrun config init' to create defaults."
            )
        sys.exit(1)

    # Determine editor
    if not editor:
        editor = os.environ.get("EDITOR", "nano" if os.name != "nt" else "notepad")

    try:
        subprocess.run([editor, str(config_file)], check=True)
        click.echo(f"Edited {config_file}")

        # Reload the specific format configuration
        config_manager.reload_config("format", format_name)
        click.echo("Format configuration reloaded")

    except subprocess.CalledProcessError:
        click.echo(f"Failed to open editor: {editor}", err=True)
    except FileNotFoundError:
        click.echo(f"Editor not found: {editor}", err=True)


@formats.command()
@click.argument("format_name")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def export(format_name: str, output: Optional[str]):
    """Export a format definition to JSON file."""
    config_manager = get_config_manager()
    registry = FormatRegistry(config_manager)
    format_def = registry.get_format(format_name)

    if not format_def:
        click.echo(f"Format '{format_name}' not found.", err=True)
        sys.exit(1)

    if not output:
        output = f"{format_name}_format.json"

    format_def.save_to_file(output)
    click.echo(f"Format '{format_name}' exported to {output}")


@formats.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option("--name", help="Override format name from file")
@click.option("--install", is_flag=True, help="Install to centralized config directory")
def import_format(filepath: str, name: Optional[str], install: bool):
    """Import a format definition from JSON file to centralized config."""
    try:
        config_manager = get_config_manager()
        registry = FormatRegistry(config_manager)

        # Load the format definition
        format_def = FormatDefinition.load_from_file(filepath, registry.ureg)

        if name:
            format_def.format_name = name

        if install:
            # Save to centralized config system
            config_data = format_def.to_dict()
            success = config_manager.save_config(
                "format", format_def.format_name, config_data
            )

            if success:
                config_path = config_manager.get_format_config_path(
                    format_def.format_name
                )
                click.echo(
                    f"Format '{format_def.format_name}' installed to centralized config"
                )
                click.echo(f"  Config file: {config_path}")
            else:
                click.echo("Failed to install format to centralized config", err=True)
                sys.exit(1)
        else:
            # Just register temporarily (not persistent)
            registry.register_format_definition(format_def)
            click.echo(
                f"Format '{format_def.format_name}' imported successfully (temporary)."
            )
            click.echo("Use --install to save to centralized configuration.")

        # Show summary
        summary = create_field_summary(format_def)
        click.echo(f"  {summary['total_fields']} fields defined")
        for field_type, info in summary["by_type"].items():
            click.echo(f"  {field_type}: {info['count']} fields")

    except Exception as e:
        click.echo(f"Failed to import format: {e}", err=True)
        sys.exit(1)


@formats.command()
@click.argument("format_name")
def validate(format_name: str):
    """Validate a format definition for common issues."""
    config_manager = get_config_manager()
    registry = FormatRegistry(config_manager)
    format_def = registry.get_format(format_name)

    if not format_def:
        click.echo(f"Format '{format_name}' not found.", err=True)
        sys.exit(1)

    validation = validate_format_definition(format_def)

    click.echo(f"Validation results for '{format_name}':")
    click.echo(f"  Status: {'✓ VALID' if validation['valid'] else '✗ INVALID'}")
    click.echo(f"  Total fields: {validation['total_fields']}")

    # Show config file path
    config_path = config_manager.get_format_config_path(format_name)
    click.echo(f"  Config file: {config_path}")

    if validation["issues"]:
        click.echo("\n❌ Issues found:")
        for issue in validation["issues"]:
            click.echo(f"  - {issue}")

    if validation["warnings"]:
        click.echo("\n⚠️  Warnings:")
        for warning in validation["warnings"]:
            click.echo(f"  - {warning}")

    if validation["valid"] and not validation["warnings"]:
        click.echo("\n✅ No issues found!")

    # Show field type distribution
    click.echo("\nField type distribution:")
    for field_type, count in validation["field_types"].items():
        if count > 0:
            click.echo(f"  {field_type}: {count}")


@formats.command()
@click.option("--all", is_flag=True, help="Validate all format definitions")
def validate_all(all):
    """Validate all format definitions in centralized config."""
    config_manager = get_config_manager()
    registry = FormatRegistry(config_manager)

    format_names = config_manager.list_configs("format")
    if not format_names:
        click.echo("No format definitions found to validate.")
        return

    click.echo(f"Validating {len(format_names)} format definitions...")

    total_valid = 0
    total_invalid = 0
    validation_results = []

    for format_name in format_names:
        format_def = registry.get_format(format_name)
        if not format_def:
            click.echo(f"❌ {format_name}: Failed to load")
            total_invalid += 1
            continue

        validation = validate_format_definition(format_def)
        validation_results.append((format_name, validation))

        if validation["valid"]:
            total_valid += 1
            if validation["warnings"]:
                click.echo(
                    f"⚠️  {format_name}: Valid with {len(validation['warnings'])} warnings"
                )
            else:
                click.echo(f"✅ {format_name}: Valid")
        else:
            total_invalid += 1
            click.echo(f"❌ {format_name}: {len(validation['issues'])} issues")

    # Summary
    click.echo("\n📊 Validation Summary:")
    click.echo(f"  Total: {len(format_names)}")
    click.echo(f"  Valid: {total_valid}")
    click.echo(f"  Invalid: {total_invalid}")

    # Show details for invalid formats
    if total_invalid > 0:
        click.echo("\n❌ Invalid formats:")
        for format_name, validation in validation_results:
            if not validation["valid"]:
                click.echo(f"\n  {format_name}:")
                for issue in validation["issues"]:
                    click.echo(f"    - {issue}")


@formats.command()
@click.argument("format_name")
@click.option(
    "--field-type",
    "-t",
    type=click.Choice([ft.value for ft in FieldType]),
    help="Filter by field type",
)
@click.option("--search", "-s", help="Search in field names or descriptions")
@click.option("--output", "-o", type=click.Path(), help="Save to CSV file")
def fields(
    format_name: str,
    field_type: Optional[str],
    search: Optional[str],
    output: Optional[str],
):
    """List fields in a format definition from centralized config."""
    config_manager = get_config_manager()
    registry = FormatRegistry(config_manager)
    format_def = registry.get_format(format_name)

    if not format_def:
        click.echo(f"Format '{format_name}' not found.", err=True)
        sys.exit(1)

    # Collect field data
    field_data = []
    for field in format_def.fields.values():
        # Apply filters
        if field_type and field.field_type.value != field_type:
            continue
        if (
            search
            and search.lower() not in field.name.lower()
            and search.lower() not in field.description.lower()
        ):
            continue

        field_data.append(
            {
                "name": field.name,
                "type": field.field_type.value,
                "unit": field.unit,
                "symbol": field.symbol,
                "description": field.description,
            }
        )

    if not field_data:
        click.echo("No fields match the criteria.")
        return

    if output:
        # Save to CSV
        df = pd.DataFrame(field_data)
        df.to_csv(output, index=False)
        click.echo(f"Field data saved to {output}")
    else:
        # Display as table
        headers = ["Name", "Type", "Unit", "Symbol", "Description"]
        table_data = [
            [
                f["name"],
                f["type"],
                f["unit"],
                f["symbol"],
                (
                    f["description"][:50] + "..."
                    if len(f["description"]) > 50
                    else f["description"]
                ),
            ]
            for f in field_data
        ]
        click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))

    # Show config file path
    config_path = config_manager.get_format_config_path(format_name)
    click.echo(f"\nConfiguration file: {config_path}")


@formats.command()
@click.argument("format_name")
@click.argument("data_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file for new format")
@click.option("--description", help="Description for the new format")
@click.option("--install", is_flag=True, help="Install to centralized config")
def create(
    format_name: str,
    data_file: str,
    output: Optional[str],
    description: Optional[str],
    install: bool,
):
    """Create a new format definition from a data file and save to centralized config."""
    try:
        # Try to read the data file to get column names
        file_path = Path(data_file)

        if file_path.suffix.lower() == ".csv":
            df = pd.read_csv(file_path, nrows=0)  # Just read headers
            data_keys = df.columns.tolist()
        elif file_path.suffix.lower() == ".txt":
            # Try both comma and whitespace separated
            try:
                df = pd.read_csv(file_path, nrows=0)
                data_keys = df.columns.tolist()
            except Exception:
                df = pd.read_csv(file_path, sep=r"\s+", nrows=0)
                data_keys = df.columns.tolist()
        else:
            click.echo(f"Unsupported file format: {file_path.suffix}", err=True)
            sys.exit(1)

        # Create format definition using centralized config
        config_manager = get_config_manager()
        registry = FormatRegistry(config_manager)
        format_def = create_format_config_from_data(
            data_keys, format_name, registry.ureg
        )

        if description:
            format_def.metadata["description"] = description
        format_def.metadata["created_from"] = str(file_path)
        format_def.metadata["file_extension"] = file_path.suffix

        if install:
            # Save to centralized config
            config_data = format_def.to_dict()
            success = config_manager.save_config("format", format_name, config_data)

            if success:
                config_path = config_manager.get_format_config_path(format_name)
                click.echo(
                    f"Format '{format_name}' created and installed to centralized config"
                )
                click.echo(f"  Config file: {config_path}")
            else:
                click.echo("Failed to install format to centralized config", err=True)

        # Also save to file if requested
        if output:
            format_def.save_to_file(output)
            click.echo(f"Format definition also saved to: {output}")
        elif not install:
            # If not installing and no output file, save with default name
            output = f"{format_name}_format.json"
            format_def.save_to_file(output)
            click.echo(f"Format definition saved to: {output}")

        click.echo(f"\nFormat '{format_name}' created with {len(data_keys)} fields.")

        click.echo("\n📝 Next steps:")
        if install:
            click.echo(f"   magnetrun formats show {format_name}")
            click.echo(f"   magnetrun formats edit {format_name}")
        else:
            click.echo(
                f"   magnetrun formats import {output if output else f'{format_name}_format.json'} --install"
            )
        click.echo(f"   magnetrun formats validate {format_name}")

    except Exception as e:
        click.echo(f"Failed to create format: {e}", err=True)
        sys.exit(1)


@formats.command()
@click.argument("base_format")
@click.argument("overlay_format")
@click.argument("output_name")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option(
    "--install", is_flag=True, help="Install merged format to centralized config"
)
def merge(
    base_format: str,
    overlay_format: str,
    output_name: str,
    output: Optional[str],
    install: bool,
):
    """Merge two format definitions from centralized config."""
    from ..core.fields.utils import merge_format_definitions

    config_manager = get_config_manager()
    registry = FormatRegistry(config_manager)

    base_def = registry.get_format(base_format)
    if not base_def:
        click.echo(f"Base format '{base_format}' not found.", err=True)
        sys.exit(1)

    overlay_def = registry.get_format(overlay_format)
    if not overlay_def:
        click.echo(f"Overlay format '{overlay_format}' not found.", err=True)
        sys.exit(1)

    # Merge formats
    merged_def = merge_format_definitions(base_def, overlay_def)
    merged_def.format_name = output_name

    if install:
        # Save to centralized config
        config_data = merged_def.to_dict()
        success = config_manager.save_config("format", output_name, config_data)

        if success:
            config_path = config_manager.get_format_config_path(output_name)
            click.echo(f"Merged format '{output_name}' installed to centralized config")
            click.echo(f"  Config file: {config_path}")
        else:
            click.echo(
                "Failed to install merged format to centralized config", err=True
            )

    # Save to file if requested
    if output:
        merged_def.save_to_file(output)
        click.echo(f"Merged format also saved to: {output}")
    elif not install:
        # If not installing and no output file, save with default name
        output = f"{output_name}_format.json"
        merged_def.save_to_file(output)
        click.echo(f"Merged format saved to: {output}")

    click.echo(f"\nMerged '{base_format}' and '{overlay_format}' into '{output_name}'")

    # Show summary
    summary = create_field_summary(merged_def)
    click.echo(f"Result: {summary['total_fields']} total fields")


@formats.command()
@click.option("--export-dir", type=click.Path(), help="Directory to export all formats")
def backup(export_dir: Optional[str]):
    """Backup all format configurations from centralized config."""
    config_manager = get_config_manager()

    if not export_dir:
        export_dir = (
            f"magnetrun_formats_backup_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
        )

    export_path = Path(export_dir)
    export_path.mkdir(parents=True, exist_ok=True)

    registry = FormatRegistry(config_manager)
    results = registry.export_all_formats(export_path)

    exported_count = sum(1 for success in results.values() if success)
    failed_count = len(results) - exported_count

    click.echo(f"✅ Exported {exported_count} format definitions to {export_path}")
    if failed_count > 0:
        click.echo(f"❌ Failed to export {failed_count} formats")
        for format_name, success in results.items():
            if not success:
                click.echo(f"  - {format_name}")

    # Also copy the entire formats directory
    import shutil

    formats_backup = export_path / "configs_backup"
    try:
        shutil.copytree(config_manager.config_paths.formats_dir, formats_backup)
        click.echo(f"✅ Full formats directory backed up to {formats_backup}")
    except Exception as e:
        click.echo(f"⚠️  Warning: Could not backup full directory: {e}")


@formats.command()
@click.argument("import_dir", type=click.Path(exists=True))
@click.option("--overwrite", is_flag=True, help="Overwrite existing formats")
def restore(import_dir: str, overwrite: bool):
    """Restore format configurations to centralized config from backup."""
    config_manager = get_config_manager()
    registry = FormatRegistry(config_manager)

    import_path = Path(import_dir)
    results = registry.import_formats_from_directory(import_path, overwrite=overwrite)

    imported_count = sum(1 for success in results.values() if success)
    skipped_count = len(results) - imported_count

    click.echo(f"✅ Imported {imported_count} format definitions")
    if skipped_count > 0:
        click.echo(
            f"⏭️  Skipped {skipped_count} existing formats (use --overwrite to replace)"
        )
        for format_name, success in results.items():
            if not success:
                click.echo(f"  - {format_name}")

    if imported_count > 0:
        click.echo("\nReloading format registry...")
        registry.reload_formats()
        click.echo("✅ Format registry reloaded")


def _format_definition_to_table(format_def: FormatDefinition) -> str:
    """Convert format definition to a readable table format."""
    output = []

    # Header
    output.append(f"Format Definition: {format_def.format_name}")
    output.append("=" * (20 + len(format_def.format_name)))

    # Metadata
    if format_def.metadata:
        output.append("\nMetadata:")
        for key, value in format_def.metadata.items():
            output.append(f"  {key}: {value}")

    # Fields by type
    output.append(f"\nFields ({len(format_def.fields)} total):")

    for field_type in FieldType:
        fields_of_type = format_def.get_fields_by_type(field_type)
        if fields_of_type:
            output.append(
                f"\n{field_type.value.upper().replace('_', ' ')} ({len(fields_of_type)}):"
            )

            table_data = []
            for field in fields_of_type:
                table_data.append(
                    [
                        field.name,
                        field.symbol,
                        field.unit,
                        (
                            field.description[:60] + "..."
                            if len(field.description) > 60
                            else field.description
                        ),
                    ]
                )

            headers = ["Name", "Symbol", "Unit", "Description"]
            output.append(tabulate(table_data, headers=headers, tablefmt="simple"))

    return "\n".join(output)


# Add command for config system status
@formats.command()
def status():
    """Show centralized configuration system status."""
    config_manager = get_config_manager()
    registry = FormatRegistry(config_manager)

    click.echo("🔧 Format Configuration System Status")
    click.echo("=" * 50)

    # Basic info
    config_info = config_manager.get_config_info()
    registry_info = registry.get_config_info()

    click.echo(f"Base directory: {config_info['base_dir']}")
    click.echo(f"Formats directory: {config_info['formats_dir']}")
    click.echo(
        f"Directory exists: {'✅' if config_info['directories_exist']['formats'] else '❌'}"
    )

    # Counts
    click.echo("\nConfiguration counts:")
    click.echo(f"  Available formats: {registry_info['available_formats']}")
    click.echo(f"  Loaded in registry: {registry_info['loaded_formats']}")
    click.echo(f"  Registered readers: {registry_info['registered_readers']}")
    click.echo(f"  Registered handlers: {registry_info['registered_handlers']}")

    # Cache info
    click.echo("\nCache status:")
    click.echo(f"  Cached configurations: {config_info['cache_size']}")

    # List formats with status
    if registry_info["available_formats"] > 0:
        click.echo("\nFormat definitions:")

        table_data = []
        for format_name in config_manager.list_configs("format"):
            format_def = registry.get_format(format_name)
            config_path = config_manager.get_format_config_path(format_name)

            if format_def:
                status = "✅ Loaded"
                fields_count = len(format_def.fields)
                description = format_def.metadata.get("description", "No description")[
                    :40
                ]
            else:
                status = "❌ Error"
                fields_count = "?"
                description = "Failed to load"

            file_exists = "✅" if config_path.exists() else "❌"

            table_data.append(
                [format_name, status, fields_count, file_exists, description]
            )

        headers = ["Format", "Status", "Fields", "File", "Description"]
        click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))

    # Environment variables
    click.echo("\nEnvironment variables:")
    env_vars = [
        ("MAGNETRUN_CONFIG_DIR", "Base config directory"),
        ("MAGNETRUN_FORMATS_DIR", "Formats directory override"),
    ]

    for var_name, description in env_vars:
        value = os.getenv(var_name, "Not set")
        click.echo(f"  {var_name}: {value}")

    # Recommendations
    recommendations = []

    if not config_info["directories_exist"]["formats"]:
        recommendations.append(
            "Run 'magnetrun config init' to create configuration directories"
        )

    if registry_info["available_formats"] == 0:
        recommendations.append(
            "Run 'magnetrun config init' to create default format definitions"
        )

    if registry_info["loaded_formats"] < registry_info["available_formats"]:
        recommendations.append(
            "Some formats failed to load - run 'magnetrun formats validate-all'"
        )

    if recommendations:
        click.echo("\n💡 Recommendations:")
        for rec in recommendations:
            click.echo(f"  • {rec}")


# Add command to migrate from old hardcoded configs
@formats.command()
@click.argument("source_dir", type=click.Path(exists=True))
@click.option(
    "--dry-run", is_flag=True, help="Show what would be migrated without doing it"
)
@click.option("--overwrite", is_flag=True, help="Overwrite existing configurations")
def migrate_from_old(source_dir: str, dry_run: bool, overwrite: bool):
    """Migrate format definitions from old hardcoded config directory."""
    config_manager = get_config_manager()
    source_path = Path(source_dir)

    # Look for JSON files in the source directory
    json_files = list(source_path.glob("*.json"))

    if not json_files:
        click.echo(f"No JSON files found in {source_path}")
        return

    click.echo(f"Found {len(json_files)} JSON files in {source_path}")

    migrated_count = 0
    skipped_count = 0
    errors = []

    for json_file in json_files:
        format_name = json_file.stem

        if dry_run:
            click.echo(f"Would migrate: {json_file.name} -> {format_name}")
            continue

        # Check if already exists
        existing_config = config_manager.load_config("format", format_name)
        if existing_config and not overwrite:
            click.echo(f"⏭️  Skipped {format_name} (already exists)")
            skipped_count += 1
            continue

        try:
            # Load and validate the JSON file
            with open(json_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            # Basic validation for format files
            if "format_name" not in config_data:
                config_data["format_name"] = format_name

            if "metadata" not in config_data:
                config_data["metadata"] = {}

            if "description" not in config_data["metadata"]:
                config_data["metadata"][
                    "description"
                ] = f"Migrated from {json_file.name}"

            # Save to centralized config
            success = config_manager.save_config("format", format_name, config_data)

            if success:
                click.echo(f"✅ Migrated {format_name}")
                migrated_count += 1
            else:
                click.echo(f"❌ Failed to migrate {format_name}")
                errors.append(format_name)

        except Exception as e:
            click.echo(f"❌ Error migrating {format_name}: {e}")
            errors.append(format_name)

    if dry_run:
        click.echo(f"\nDry run complete. Would migrate {len(json_files)} files.")
        return

    # Summary
    click.echo("\n📊 Migration Summary:")
    click.echo(f"  Migrated: {migrated_count}")
    click.echo(f"  Skipped: {skipped_count}")
    click.echo(f"  Errors: {len(errors)}")

    if errors:
        click.echo("\n❌ Files with errors:")
        for error_file in errors:
            click.echo(f"  - {error_file}")

    if migrated_count > 0:
        click.echo("\n✅ Migration complete! Formats saved to:")
        click.echo(f"   {config_manager.config_paths.formats_dir}")
        click.echo("\nNext steps:")
        click.echo("  magnetrun formats reload")
        click.echo("  magnetrun formats validate-all")


# Add environment integration commands
@formats.command()
def env_info():
    """Show environment variable configuration for formats."""
    import os

    click.echo("🌍 Environment Variable Configuration")
    click.echo("=" * 50)

    # Current values
    env_vars = [
        ("MAGNETRUN_CONFIG_DIR", "Base configuration directory"),
        ("MAGNETRUN_FORMATS_DIR", "Formats configuration directory"),
        ("MAGNETRUN_HOUSINGS_DIR", "Housing configuration directory"),
        ("MAGNETRUN_FIELD_DEFS_DIR", "Field definitions directory"),
    ]

    click.echo("Current values:")
    for var_name, description in env_vars:
        value = os.getenv(var_name, "Not set")
        status = "✅ Set" if value != "Not set" else "⚪ Default"
        click.echo(f"  {var_name}")
        click.echo(f"    Value: {value}")
        click.echo(f"    Status: {status}")
        click.echo(f"    Purpose: {description}")
        click.echo()

    # Show current effective paths
    config_manager = get_config_manager()
    click.echo("Effective configuration paths:")
    click.echo(f"  Base: {config_manager.config_paths.base_dir}")
    click.echo(f"  Formats: {config_manager.config_paths.formats_dir}")
    click.echo(f"  Housings: {config_manager.config_paths.housings_dir}")
    click.echo(
        f"  Field definitions: {config_manager.config_paths.field_definitions_dir}"
    )

    # Usage examples
    click.echo("\n💡 Usage examples:")
    click.echo("  # Set custom base directory")
    click.echo("  export MAGNETRUN_CONFIG_DIR=/path/to/configs")
    click.echo()
    click.echo("  # Override specific directories")
    click.echo("  export MAGNETRUN_FORMATS_DIR=/shared/formats")
    click.echo("  export MAGNETRUN_HOUSINGS_DIR=/local/housings")
    click.echo()
    click.echo("  # Apply changes")
    click.echo("  magnetrun config setup")


# Main CLI entry point
if __name__ == "__main__":
    formats()
