"""CLI commands for managing centralized configuration system."""

import click
import json
import os
from pathlib import Path
from tabulate import tabulate

from ..formats.centralized_config import (
    get_config_manager,
    set_config_base_dir,
    get_config_info,
    setup_config_from_env,
)


@click.group(name="config")
def config_commands():
    """Manage MagnetRun configuration system."""
    pass


@config_commands.command()
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.option("--json-output", is_flag=True, help="Output in JSON format")
def info(verbose, json_output):
    """Show current configuration setup information."""
    config_info = get_config_info()

    if json_output:
        click.echo(json.dumps(config_info, indent=2))
        return

    click.echo("🔧 MagnetRun Configuration System")
    click.echo("=" * 50)

    # Basic paths
    click.echo(f"Base directory: {config_info['base_dir']}")
    click.echo(f"Formats directory: {config_info['formats_dir']}")
    click.echo(f"Housings directory: {config_info['housings_dir']}")
    click.echo(f"Field definitions directory: {config_info['field_definitions_dir']}")

    # Custom directories
    if config_info["custom_dirs"]:
        click.echo("\nCustom directories:")
        for name, path in config_info["custom_dirs"].items():
            click.echo(f"  {name}: {path}")

    # Directory existence status
    click.echo("\nDirectory status:")
    for name, exists in config_info["directories_exist"].items():
        status = "✅" if exists else "❌"
        click.echo(f"  {name}: {status}")

    # Configuration counts
    click.echo("\nConfiguration counts:")
    for name, count in config_info["config_counts"].items():
        click.echo(f"  {name}: {count}")

    if verbose:
        click.echo(f"\nCache size: {config_info['cache_size']} entries")

        # Environment variables
        click.echo("\nRelevant environment variables:")
        env_vars = [
            "MAGNETRUN_CONFIG_DIR",
            "MAGNETRUN_FORMATS_DIR",
            "MAGNETRUN_HOUSINGS_DIR",
            "MAGNETRUN_FIELD_DEFS_DIR",
        ]
        for var in env_vars:
            value = os.getenv(var, "Not set")
            click.echo(f"  {var}: {value}")


@config_commands.command()
@click.argument("base_dir", type=click.Path())
@click.option(
    "--create-dirs", is_flag=True, help="Create directories if they don't exist"
)
@click.option(
    "--copy-existing", is_flag=True, help="Copy existing configs to new location"
)
def set_base_dir(base_dir, create_dirs, copy_existing):
    """Set the base configuration directory."""
    base_path = Path(base_dir)

    if copy_existing:
        # Get current config manager to copy from
        current_cm = get_config_manager()
        old_base = current_cm.config_paths.base_dir

        if old_base.exists():
            click.echo(f"Copying configurations from {old_base} to {base_path}")
            import shutil

            if base_path.exists():
                click.echo(
                    "Warning: Target directory already exists. Files may be overwritten."
                )

            try:
                shutil.copytree(old_base, base_path, dirs_exist_ok=True)
                click.echo("✅ Configurations copied successfully")
            except Exception as e:
                click.echo(f"❌ Error copying configurations: {e}", err=True)
                return

    # Set new base directory
    new_cm = set_config_base_dir(base_path)

    if create_dirs:
        new_cm.config_paths.ensure_directories_exist()
        click.echo("✅ Created directory structure")

    click.echo(f"✅ Base configuration directory set to: {base_path}")

    # Show new info
    info_data = new_cm.get_config_info()
    click.echo("Available configurations:")
    for config_type, count in info_data["config_counts"].items():
        click.echo(f"  {config_type}: {count}")


@config_commands.command()
@click.option("--overwrite", is_flag=True, help="Overwrite existing configurations")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be created without actually creating",
)
def init(overwrite, dry_run):
    """Initialize configuration directories with default configurations."""
    cm = get_config_manager()

    if dry_run:
        click.echo("🔍 Dry run - showing what would be created:")
        click.echo(f"Base directory: {cm.config_paths.base_dir}")
        click.echo("Directories that would be created:")
        dirs = [
            cm.config_paths.formats_dir,
            cm.config_paths.housings_dir,
            cm.config_paths.field_definitions_dir,
        ]
        for directory in dirs:
            exists = "✅ exists" if directory.exists() else "🆕 would create"
            click.echo(f"  {directory}: {exists}")

        click.echo("\nDefault configurations that would be created:")
        formats = ["pupitre", "pigbrother", "bprofile"]
        housings = ["m9", "m8", "m10"]

        for fmt in formats:
            path = cm.get_format_config_path(fmt)
            exists = "✅ exists" if path.exists() else "🆕 would create"
            click.echo(f"  format/{fmt}.json: {exists}")

        for housing in housings:
            path = cm.get_housing_config_path(housing)
            exists = "✅ exists" if path.exists() else "🆕 would create"
            click.echo(f"  housing/{housing}.json: {exists}")

        return

    # Create directories
    cm.config_paths.ensure_directories_exist()
    click.echo("✅ Created directory structure")

    # Create default configurations
    results = cm.create_default_configs(overwrite=overwrite)

    created_count = sum(1 for success in results.values() if success)
    skipped_count = len(results) - created_count

    click.echo(f"✅ Created {created_count} default configurations")
    if skipped_count > 0:
        click.echo(
            f"⏭️  Skipped {skipped_count} existing configurations (use --overwrite to replace)"
        )

    if created_count > 0:
        click.echo("\nCreated configurations:")
        for name, success in results.items():
            if success:
                click.echo(f"  ✅ {name}")


@config_commands.command()
@click.argument(
    "config_type", type=click.Choice(["format", "housing", "field_definition"])
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json", "list"]),
    default="table",
    help="Output format",
)
def list(config_type, output_format):
    """List available configurations of a specific type."""
    cm = get_config_manager()
    configs = cm.list_configs(config_type)

    if not configs:
        click.echo(f"No {config_type} configurations found.")
        return

    if output_format == "json":
        click.echo(json.dumps(configs, indent=2))
    elif output_format == "list":
        for config in configs:
            click.echo(config)
    else:  # table
        click.echo(f"Available {config_type} configurations:")
        table_data = []

        for config_name in configs:
            config_data = cm.load_config(config_type, config_name)
            if config_data:
                description = config_data.get("metadata", {}).get(
                    "description", "No description"
                )
                path = getattr(cm, f"get_{config_type}_config_path")(config_name)
                table_data.append([config_name, description[:50], str(path)])
            else:
                table_data.append([config_name, "Failed to load", "Unknown"])

        headers = ["Name", "Description", "Path"]
        click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))


@config_commands.command()
@click.argument(
    "config_type", type=click.Choice(["format", "housing", "field_definition"])
)
@click.argument("config_name")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="Output format",
)
def show(config_type, config_name, output_format):
    """Show the contents of a specific configuration."""
    cm = get_config_manager()
    config_data = cm.load_config(config_type, config_name)

    if not config_data:
        click.echo(
            f"Configuration '{config_name}' not found in {config_type}s.", err=True
        )
        return

    if output_format == "json":
        click.echo(json.dumps(config_data, indent=2))
    elif output_format == "yaml":
        try:
            import yaml

            click.echo(yaml.dump(config_data, default_flow_style=False))
        except ImportError:
            click.echo("PyYAML not installed. Showing JSON format:")
            click.echo(json.dumps(config_data, indent=2))


@config_commands.command()
@click.argument(
    "config_type", type=click.Choice(["format", "housing", "field_definition"])
)
@click.argument("config_name")
@click.option("--editor", "-e", help="Editor to use (default: system default)")
def edit(config_type, config_name, editor):
    """Edit a configuration file."""
    import subprocess

    cm = get_config_manager()

    # Get config path
    if config_type == "format":
        config_path = cm.get_format_config_path(config_name)
    elif config_type == "housing":
        config_path = cm.get_housing_config_path(config_name)
    else:  # field_definition
        config_path = cm.get_field_definition_path(config_name)

    if not config_path.exists():
        click.echo(
            f"Configuration '{config_name}' does not exist. Create it first with 'magnetrun config create'."
        )
        return

    # Determine editor
    if not editor:
        editor = os.environ.get("EDITOR", "nano" if os.name != "nt" else "notepad")

    try:
        subprocess.run([editor, str(config_path)], check=True)
        click.echo(f"✅ Edited {config_path}")

        # Clear cache for this config
        cm.reload_config(config_type, config_name)
        click.echo("✅ Configuration reloaded")

    except subprocess.CalledProcessError:
        click.echo(f"❌ Failed to open editor: {editor}", err=True)
    except FileNotFoundError:
        click.echo(f"❌ Editor not found: {editor}", err=True)


@config_commands.command()
@click.argument(
    "config_type", type=click.Choice(["format", "housing", "field_definition"])
)
@click.argument("source_file", type=click.Path(exists=True))
@click.option("--name", help="Name for the imported configuration (default: filename)")
@click.option("--overwrite", is_flag=True, help="Overwrite existing configuration")
def import_config(config_type, source_file, name, overwrite):
    """Import a configuration from a JSON file."""
    cm = get_config_manager()
    source_path = Path(source_file)

    if not name:
        name = source_path.stem

    # Check if config already exists
    existing_configs = cm.list_configs(config_type)
    if name in existing_configs and not overwrite:
        click.echo(
            f"Configuration '{name}' already exists. Use --overwrite to replace it.",
            err=True,
        )
        return

    try:
        # Load and validate the source file
        with open(source_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        # Basic validation
        if config_type == "format" and "format_name" not in config_data:
            click.echo("Warning: Format configuration missing 'format_name' field")

        # Save to centralized config
        success = cm.save_config(config_type, name, config_data)

        if success:
            click.echo(f"✅ Successfully imported {config_type} configuration '{name}'")

            # Show path where it was saved
            if config_type == "format":
                saved_path = cm.get_format_config_path(name)
            elif config_type == "housing":
                saved_path = cm.get_housing_config_path(name)
            else:
                saved_path = cm.get_field_definition_path(name)

            click.echo(f"   Saved to: {saved_path}")
        else:
            click.echo("❌ Failed to import configuration", err=True)

    except json.JSONDecodeError as e:
        click.echo(f"❌ Invalid JSON file: {e}", err=True)
    except Exception as e:
        click.echo(f"❌ Error importing configuration: {e}", err=True)


@config_commands.command()
@click.argument(
    "config_type", type=click.Choice(["format", "housing", "field_definition"])
)
@click.argument("config_name")
@click.argument("output_file", type=click.Path())
def export(config_type, config_name, output_file):
    """Export a configuration to a JSON file."""
    cm = get_config_manager()
    config_data = cm.load_config(config_type, config_name)

    if not config_data:
        click.echo(f"Configuration '{config_name}' not found.", err=True)
        return

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        click.echo(f"✅ Configuration '{config_name}' exported to {output_path}")

    except Exception as e:
        click.echo(f"❌ Error exporting configuration: {e}", err=True)


@config_commands.command()
@click.argument("export_dir", type=click.Path())
@click.option(
    "--config-type",
    type=click.Choice(["format", "housing", "field_definition", "all"]),
    default="all",
    help="Type of configurations to export",
)
def export_all(export_dir, config_type):
    """Export all configurations to a directory."""
    cm = get_config_manager()
    export_path = Path(export_dir)
    export_path.mkdir(parents=True, exist_ok=True)

    config_types = (
        ["format", "housing", "field_definition"]
        if config_type == "all"
        else [config_type]
    )
    total_exported = 0

    for cfg_type in config_types:
        type_dir = export_path / cfg_type
        type_dir.mkdir(exist_ok=True)

        configs = cm.list_configs(cfg_type)
        click.echo(f"Exporting {len(configs)} {cfg_type} configurations...")

        for config_name in configs:
            config_data = cm.load_config(cfg_type, config_name)
            if config_data:
                output_file = type_dir / f"{config_name}.json"
                try:
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(config_data, f, indent=2, ensure_ascii=False)
                    total_exported += 1
                except Exception as e:
                    click.echo(f"  ❌ Failed to export {config_name}: {e}")

    click.echo(f"✅ Exported {total_exported} configurations to {export_path}")


@config_commands.command()
@click.argument("import_dir", type=click.Path(exists=True))
@click.option("--overwrite", is_flag=True, help="Overwrite existing configurations")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be imported without importing"
)
def import_all(import_dir, overwrite, dry_run):
    """Import all configurations from a directory structure."""
    cm = get_config_manager()
    import_path = Path(import_dir)

    config_types = ["format", "housing", "field_definition"]
    total_imported = 0
    total_skipped = 0

    for config_type in config_types:
        type_dir = import_path / config_type
        if not type_dir.exists():
            continue

        json_files = list(type_dir.glob("*.json"))
        if not json_files:
            continue

        click.echo(
            f"Found {len(json_files)} {config_type} configurations in {type_dir}"
        )

        existing_configs = set(cm.list_configs(config_type))

        for json_file in json_files:
            config_name = json_file.stem

            if config_name in existing_configs and not overwrite:
                if dry_run:
                    click.echo(f"  ⏭️  Would skip {config_name} (already exists)")
                else:
                    click.echo(f"  ⏭️  Skipped {config_name} (already exists)")
                total_skipped += 1
                continue

            if dry_run:
                click.echo(f"  🆕 Would import {config_name}")
                continue

            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)

                success = cm.save_config(config_type, config_name, config_data)
                if success:
                    click.echo(f"  ✅ Imported {config_name}")
                    total_imported += 1
                else:
                    click.echo(f"  ❌ Failed to import {config_name}")

            except Exception as e:
                click.echo(f"  ❌ Error importing {config_name}: {e}")

    if dry_run:
        click.echo(
            f"\nDry run complete. Would import {total_imported} and skip {total_skipped} configurations."
        )
    else:
        click.echo(
            f"\n✅ Imported {total_imported} configurations, skipped {total_skipped}"
        )


@config_commands.command()
def clear_cache():
    """Clear the configuration cache."""
    cm = get_config_manager()
    cm.clear_cache()
    click.echo("✅ Configuration cache cleared")


@config_commands.command()
def validate():
    """Validate all configurations for consistency and correctness."""
    cm = get_config_manager()

    config_types = ["format", "housing", "field_definition"]
    total_configs = 0
    total_errors = 0

    for config_type in config_types:
        configs = cm.list_configs(config_type)
        total_configs += len(configs)

        if not configs:
            continue

        click.echo(f"\n🔍 Validating {len(configs)} {config_type} configurations:")

        for config_name in configs:
            config_data = cm.load_config(config_type, config_name)

            if not config_data:
                click.echo(f"  ❌ {config_name}: Failed to load")
                total_errors += 1
                continue

            # Basic validation
            errors = []

            # Common validations
            if "metadata" not in config_data:
                errors.append("Missing 'metadata' section")

            # Format-specific validations
            if config_type == "format":
                if "format_name" not in config_data:
                    errors.append("Missing 'format_name' field")
                if "fields" not in config_data:
                    errors.append("Missing 'fields' array")
                elif not isinstance(config_data["fields"], list):
                    errors.append("'fields' must be an array")

            if errors:
                click.echo(f"  ❌ {config_name}:")
                for error in errors:
                    click.echo(f"     - {error}")
                total_errors += 1
            else:
                click.echo(f"  ✅ {config_name}")

    click.echo("\n📊 Validation Summary:")
    click.echo(f"   Total configurations: {total_configs}")
    click.echo(f"   Valid: {total_configs - total_errors}")
    click.echo(f"   Errors: {total_errors}")

    if total_errors == 0:
        click.echo("🎉 All configurations are valid!")
    else:
        click.echo("⚠️  Some configurations have errors. Please review and fix them.")


# Setup command to initialize from environment
@config_commands.command()
def setup():
    """Setup configuration system from environment variables."""
    click.echo("🔧 Setting up MagnetRun configuration from environment...")

    # Show current environment variables
    env_vars = [
        "MAGNETRUN_CONFIG_DIR",
        "MAGNETRUN_FORMATS_DIR",
        "MAGNETRUN_HOUSINGS_DIR",
        "MAGNETRUN_FIELD_DEFS_DIR",
    ]

    click.echo("Environment variables:")
    any_set = False
    for var in env_vars:
        value = os.getenv(var)
        if value:
            click.echo(f"  ✅ {var}={value}")
            any_set = True
        else:
            click.echo(f"  ⚪ {var} (not set)")

    if not any_set:
        click.echo("\nNo configuration environment variables set. Using defaults.")

    # Setup from environment
    try:
        config_paths = setup_config_from_env()
        click.echo("\n✅ Configuration system initialized")
        click.echo(f"   Base directory: {config_paths.base_dir}")

        # Show final status
        cm = get_config_manager()
        info_data = cm.get_config_info()

        click.echo("\nConfiguration counts:")
        for name, count in info_data["config_counts"].items():
            click.echo(f"  {name}: {count}")

    except Exception as e:
        click.echo(f"❌ Setup failed: {e}", err=True)
