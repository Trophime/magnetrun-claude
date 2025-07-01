"""Plotting utilities for magnetic data with JSON-based field management integration."""

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib
import numpy as np
from typing import Optional, List, Dict, Any
import pandas as pd
from pathlib import Path

from ..core.magnet_data import MagnetData
# CORRECTED: Import from new locations
from ..core.fields import Field, FieldType

matplotlib.rcParams["text.usetex"] = True


class DataPlotter:
    """Handles plotting operations for magnetic data with JSON-based field management."""

    @staticmethod
    def plot_time_series(
        magnet_data: MagnetData,
        y_keys: List[str],
        x_key: str = "t",
        normalize: bool = False,
        ax: Optional[plt.Axes] = None,
        show_grid: bool = True,
    ) -> plt.Axes:
        """Plot time series data with proper field labels using JSON-based field system."""
        if ax is None:
            ax = plt.gca()

        for y_key in y_keys:
            DataPlotter._plot_single_series(
                magnet_data, x_key, y_key, ax, normalize, show_grid
            )

        return ax

    @staticmethod
    def _plot_single_series(
        magnet_data: MagnetData,
        x_key: str,
        y_key: str,
        ax: plt.Axes,
        normalize: bool,
        show_grid: bool,
    ) -> None:
        """Plot a single data series with field information from JSON-based system."""
        # Get data
        data = magnet_data.get_data([x_key, y_key])

        # Get field information from JSON-based field system
        format_def = magnet_data.field_registry

        # Get field labels using JSON-based system
        y_label = magnet_data.get_field_label(y_key, show_unit=not normalize)
        x_label = magnet_data.get_field_label(x_key, show_unit=True)

        # Normalize if requested
        if normalize:
            y_max = abs(data[y_key].max())
            data = data.copy()
            data[y_key] /= y_max

            # Get unit for normalization info
            y_field = format_def.get_field(y_key)
            y_unit = y_field.unit if y_field else ""
            label = f"{y_key} (norm with {y_max:.3e} {y_unit})"
        else:
            label = y_key

        # Plot
        data.plot(x=x_key, y=y_key, ax=ax, label=label, grid=show_grid)

        # Set labels using field information
        if normalize:
            ax.set_ylabel("normalized")
        else:
            ax.set_ylabel(y_label)

        ax.set_xlabel(x_label)

    @staticmethod
    def plot_xy(
        magnet_data: MagnetData,
        x_key: str,
        y_key: str,
        ax: Optional[plt.Axes] = None,
        **plot_kwargs,
    ) -> plt.Axes:
        """Plot X vs Y data with proper field labels using JSON-based field system."""
        if ax is None:
            ax = plt.gca()

        # Get data
        data = magnet_data.get_data([x_key, y_key])

        # Get field labels using JSON-based system
        y_label = magnet_data.get_field_label(y_key)
        x_label = magnet_data.get_field_label(x_key)

        # Plot
        data.plot(x=x_key, y=y_key, ax=ax, **plot_kwargs)

        # Set labels using field information
        ax.set_ylabel(y_label)
        ax.set_xlabel(x_label)

        return ax

    @staticmethod
    def plot_time_series_to_file(
        magnet_data: MagnetData,
        keys: List[str],
        x_key: str = "t",
        normalize: bool = False,
        show_grid: bool = True,
        file_path: str = "",
        save: bool = False,
        show: bool = False,
        output_dir: Optional[Path] = None,
    ) -> None:
        """Plot time series and optionally save to file."""
        fig, ax = plt.subplots(figsize=(12, 6))

        DataPlotter.plot_time_series(magnet_data, keys, x_key, normalize, ax, show_grid)

        ax.set_title(f"{Path(file_path).stem} - Time Series")
        ax.legend()

        if save:
            output_path = DataPlotter._get_output_path(
                file_path, f"_{x_key}_vs_{'_'.join(keys)}.png", output_dir
            )
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            print(f"Saved plot: {output_path}")

        if show:
            plt.show()

        plt.close()

    @staticmethod
    def plot_xy_pairs_to_file(
        magnet_data: MagnetData,
        key_pairs: List[str],
        file_path: str = "",
        save: bool = False,
        show: bool = False,
        output_dir: Optional[Path] = None,
    ) -> None:
        """Plot key pairs and optionally save to file."""
        for pair in key_pairs:
            if ";" in pair:
                key1, key2 = pair.split(";", 1)
                if key1 in magnet_data.keys and key2 in magnet_data.keys:
                    fig, ax = plt.subplots(figsize=(8, 6))
                    DataPlotter.plot_xy(magnet_data, key1, key2, ax=ax)
                    ax.set_title(f"{Path(file_path).stem} - {key1} vs {key2}")

                    if save:
                        output_path = DataPlotter._get_output_path(
                            file_path, f"_{key1}_vs_{key2}.png", output_dir
                        )
                        plt.savefig(output_path, dpi=300, bbox_inches="tight")
                        print(f"Saved plot: {output_path}")

                    if show:
                        plt.show()

                    plt.close()

    @staticmethod
    def plot_default_view(
        magnet_data: MagnetData,
        x_key: str = "t",
        normalize: bool = False,
        show_grid: bool = True,
        file_path: str = "",
        save: bool = False,
        show: bool = False,
        output_dir: Optional[Path] = None,
    ) -> None:
        """Plot default view using field type priorities from JSON-based system."""
        # Use field registry to find most relevant fields
        format_def = magnet_data.field_registry

        # Priority order for default plotting
        priority_types = [
            FieldType.MAGNETIC_FIELD,
            FieldType.CURRENT,
            FieldType.VOLTAGE,
            FieldType.POWER,
            FieldType.TEMPERATURE,
        ]

        available_keys = []

        # Find keys by priority field types
        for field_type in priority_types:
            for field_name, field in format_def.fields.items():
                if (
                    field.field_type == field_type
                    and field_name in magnet_data.keys
                    and field_name != x_key
                    and field_name not in available_keys
                ):
                    available_keys.append(field_name)
                    if len(available_keys) >= 3:  # Limit to 3 keys for readability
                        break
            if len(available_keys) >= 3:
                break

        # Fallback if no field types match
        if not available_keys:
            all_keys = list(magnet_data.keys)
            available_keys = [k for k in all_keys if k != x_key][:3]

        if available_keys:
            DataPlotter.plot_time_series_to_file(
                magnet_data,
                available_keys,
                x_key,
                normalize,
                show_grid,
                file_path,
                save,
                show,
                output_dir,
            )

    @staticmethod
    def plot_field_validation_summary(
        magnet_data: MagnetData,
        file_path: str = "",
        save: bool = False,
        show: bool = False,
        output_dir: Optional[Path] = None,
    ) -> None:
        """Plot field validation summary using JSON-based field system."""
        # Get field validation summary
        validation_summary = magnet_data.get_field_validation_summary()
        summary_stats = validation_summary["summary"]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # Field coverage pie chart
        coverage_percent = summary_stats["coverage_percent"]
        uncovered_percent = 100 - coverage_percent

        ax1.pie(
            [coverage_percent, uncovered_percent],
            labels=["Defined Fields", "Undefined Fields"],
            colors=["#2ecc71", "#e74c3c"],
            autopct="%1.1f%%",
            startangle=90,
        )
        ax1.set_title("Field Definition Coverage")

        # Validation status distribution
        valid_fields = summary_stats["valid_fields"]
        mostly_valid_fields = summary_stats["mostly_valid_fields"]
        invalid_fields = summary_stats["invalid_fields"]
        undefined_fields = summary_stats["undefined_fields"]

        categories = ["Valid", "Mostly Valid", "Invalid", "Undefined"]
        values = [valid_fields, mostly_valid_fields, invalid_fields, undefined_fields]
        colors = ["#2ecc71", "#f39c12", "#e74c3c", "#95a5a6"]

        ax2.bar(categories, values, color=colors)
        ax2.set_title("Field Validation Status")
        ax2.set_xlabel("Validation Status")
        ax2.set_ylabel("Number of Fields")
        plt.setp(ax2.get_xticklabels(), rotation=45, ha="right")

        # Add statistics text
        quality_percent = summary_stats["quality_percent"]
        fig.suptitle(
            f"Field Analysis Summary\nCoverage: {coverage_percent:.1f}% | Quality: {quality_percent:.1f}%",
            fontsize=14,
        )

        plt.tight_layout()

        if save:
            output_path = DataPlotter._get_output_path(
                file_path, "_field_validation_summary.png", output_dir
            )
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            print(f"Saved plot: {output_path}")

        if show:
            plt.show()

        plt.close()

    @staticmethod
    def plot_field_type_distribution(
        magnet_data: MagnetData,
        file_path: str = "",
        save: bool = False,
        show: bool = False,
        output_dir: Optional[Path] = None,
    ) -> None:
        """Plot field type distribution using JSON-based field system."""
        format_def = magnet_data.field_registry

        # Count field types for available data
        field_type_counts = {}
        undefined_count = 0

        for key in magnet_data.keys:
            field = format_def.get_field(key)
            if field:
                field_type = field.field_type.value
                field_type_counts[field_type] = field_type_counts.get(field_type, 0) + 1
            else:
                undefined_count += 1

        if undefined_count > 0:
            field_type_counts["undefined"] = undefined_count

        if field_type_counts:
            fig, ax = plt.subplots(figsize=(10, 6))

            types = list(field_type_counts.keys())
            counts = list(field_type_counts.values())

            bars = ax.bar(types, counts)

            # Color bars by field type
            colors = {
                "magnetic_field": "#e74c3c",
                "current": "#3498db",
                "voltage": "#f39c12",
                "power": "#9b59b6",
                "temperature": "#e67e22",
                "pressure": "#1abc9c",
                "flow_rate": "#34495e",
                "time": "#95a5a6",
                "undefined": "#bdc3c7",
            }

            for bar, field_type in zip(bars, types):
                bar.set_color(colors.get(field_type, "#34495e"))

            ax.set_title(f"{Path(file_path).stem} - Field Type Distribution")
            ax.set_xlabel("Field Type")
            ax.set_ylabel("Number of Fields")
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.annotate(
                    f"{int(height)}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                )

            plt.tight_layout()

            if save:
                output_path = DataPlotter._get_output_path(
                    file_path, "_field_type_distribution.png", output_dir
                )
                plt.savefig(output_path, dpi=300, bbox_inches="tight")
                print(f"Saved plot: {output_path}")

            if show:
                plt.show()

            plt.close()

    @staticmethod
    def create_subplots(
        magnet_data: MagnetData,
        keys: List[str],
        x_key: str = "t",
        normalize: bool = False,
        cols: int = 2,
        file_path: str = "",
        save: bool = False,
        show: bool = False,
        output_dir: Optional[Path] = None,
    ) -> None:
        """Create subplot grid for multiple keys with field information."""
        if not keys:
            # Use field type priority to select default keys
            format_def = magnet_data.field_registry
            priority_types = [
                FieldType.MAGNETIC_FIELD,
                FieldType.CURRENT,
                FieldType.VOLTAGE,
                FieldType.POWER,
                FieldType.TEMPERATURE,
                FieldType.PRESSURE,
            ]

            keys = []
            for field_type in priority_types:
                for field_name, field in format_def.fields.items():
                    if (
                        field.field_type == field_type
                        and field_name in magnet_data.keys
                        and field_name != x_key
                        and field_name not in keys
                    ):
                        keys.append(field_name)
                        if len(keys) >= 6:  # Limit to 6 keys
                            break
                if len(keys) >= 6:
                    break

            # Fallback
            if not keys:
                keys = [k for k in magnet_data.keys if k != x_key][:6]

        n_keys = len(keys)
        rows = (n_keys + cols - 1) // cols

        fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 4 * rows))
        if rows == 1 and cols == 1:
            axes = [axes]
        elif rows == 1 or cols == 1:
            axes = axes.flatten()
        else:
            axes = axes.flatten()

        format_def = magnet_data.field_registry

        for i, key in enumerate(keys):
            if i < len(axes):
                DataPlotter.plot_time_series(
                    magnet_data, [key], x_key, normalize, axes[i]
                )

                # Use field information for subplot title
                field = format_def.get_field(key)
                if field and field.description:
                    title = f"{key}\n({field.description})"
                elif field:
                    title = f"{field.symbol} ({field.field_type.value})"
                else:
                    title = key

                axes[i].set_title(title, fontsize=10)
                axes[i].legend(fontsize=8)

        # Hide unused subplots
        for i in range(len(keys), len(axes)):
            axes[i].set_visible(False)

        plt.suptitle(f"{Path(file_path).stem} - Subplots", fontsize=14)
        plt.tight_layout()

        if save:
            output_path = DataPlotter._get_output_path(
                file_path, "_subplots.png", output_dir
            )
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            print(f"Saved plot: {output_path}")

        if show:
            plt.show()

        plt.close()

    @staticmethod
    def create_overview_plot(
        magnet_data: MagnetData,
        template: str = "standard",
        file_path: str = "",
        save: bool = False,
        show: bool = False,
        output_dir: Optional[Path] = None,
    ) -> None:
        """Create overview plot with predefined layout using JSON-based field system."""
        # Apply template styles
        if template == "publication":
            plt.style.use("seaborn-v0_8-paper")
        elif template == "presentation":
            plt.style.use("seaborn-v0_8-talk")
        else:
            plt.style.use("default")

        # Find relevant keys using JSON-based field registry
        format_def = magnet_data.field_registry
        primary_types = [
            FieldType.MAGNETIC_FIELD,
            FieldType.CURRENT,
            FieldType.VOLTAGE,
            FieldType.POWER,
        ]
        primary_keys = []

        for field_type in primary_types:
            for field_name, field in format_def.fields.items():
                if field.field_type == field_type and field_name in magnet_data.keys:
                    primary_keys.append(field_name)
                    break  # Only take first match per type

        # Fallback if no field types match
        if not primary_keys:
            all_keys = list(magnet_data.keys)
            primary_keys = [k for k in all_keys if k != "t"][:4]

        if primary_keys:
            DataPlotter.create_subplots(
                magnet_data,
                primary_keys,
                "t",
                False,
                2,
                file_path,
                save,
                show,
                output_dir,
            )

    @staticmethod
    def plot_unit_conversion_comparison(
        magnet_data: MagnetData,
        field_name: str,
        target_units: List[str],
        file_path: str = "",
        save: bool = False,
        show: bool = False,
        output_dir: Optional[Path] = None,
    ) -> None:
        """Plot field data in multiple units for comparison using JSON-based field definitions."""
        format_def = magnet_data.field_registry
        field = format_def.get_field(field_name)

        if not field:
            print(f"Warning: No field definition found for {field_name}")
            return

        # Check unit compatibility
        compatible_units = []
        for unit in target_units:
            if field.is_compatible_unit(unit, format_def.ureg):
                compatible_units.append(unit)
            else:
                print(
                    f"Warning: Unit '{unit}' not compatible with field '{field_name}'"
                )

        if not compatible_units:
            print(f"No compatible units found for field '{field_name}'")
            return

        # Get data
        try:
            data = magnet_data.get_data(["t", field_name])
            x_values = data["t"]
            x_label = magnet_data.get_field_label("t")
        except:
            data = magnet_data.get_data([field_name])
            x_values = data.index
            x_label = "Index"

        # Create subplots for each unit
        n_units = len(compatible_units)
        cols = min(2, n_units)
        rows = (n_units + cols - 1) // cols

        fig, axes = plt.subplots(rows, cols, figsize=(8 * cols, 4 * rows))
        if n_units == 1:
            axes = [axes]
        elif rows == 1 or cols == 1:
            axes = axes.flatten()
        else:
            axes = axes.flatten()

        for i, unit in enumerate(compatible_units):
            if i < len(axes):
                # Convert values to target unit
                converted_values = magnet_data.convert_field_values(
                    field_name, data[field_name], unit
                )

                axes[i].plot(x_values, converted_values, "b-", linewidth=1.5)
                axes[i].set_xlabel(x_label)
                axes[i].set_ylabel(f"{field.symbol} [{unit}]")
                axes[i].set_title(f"{field_name} in {unit}")
                axes[i].grid(True, alpha=0.3)

        # Hide unused subplots
        for i in range(n_units, len(axes)):
            axes[i].set_visible(False)

        plt.suptitle(
            f"{Path(file_path).stem} - Unit Conversion Comparison", fontsize=14
        )
        plt.tight_layout()

        if save:
            output_path = DataPlotter._get_output_path(
                file_path, f"_{field_name}_unit_comparison.png", output_dir
            )
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            print(f"Saved plot: {output_path}")

        if show:
            plt.show()

        plt.close()

    @staticmethod
    def plot_local_maxima(
        magnet_data: MagnetData,
        key: str,
        maxima_indices: np.ndarray,
        file_path: str = "",
        save: bool = False,
        show: bool = False,
        output_dir: Optional[Path] = None,
    ) -> None:
        """Plot data with local maxima marked using field information."""
        fig, ax = plt.subplots(figsize=(12, 6))

        try:
            data = magnet_data.get_data(["t", key])
            x_values = data["t"]
            x_label = magnet_data.get_field_label("t")
        except:
            data = magnet_data.get_data([key])
            x_values = data.index
            x_label = "Index"

        # Get field information for y-axis
        y_label = magnet_data.get_field_label(key)

        ax.plot(x_values, data[key], "b-", label=key)
        if len(maxima_indices) > 0:
            ax.plot(
                x_values.iloc[maxima_indices],
                data[key].iloc[maxima_indices],
                "r*",
                markersize=10,
                label="Local Maxima",
            )

        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.legend()
        ax.grid(True)
        ax.set_title(f"{Path(file_path).stem} - Local Maxima")

        if save:
            output_path = DataPlotter._get_output_path(
                file_path, f"_{key}_localmax.png", output_dir
            )
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            print(f"Saved plot: {output_path}")

        if show:
            plt.show()

        plt.close()

    @staticmethod
    def plot_format_comparison(
        magnet_data_list: List[MagnetData],
        field_name: str,
        file_path: str = "",
        save: bool = False,
        show: bool = False,
        output_dir: Optional[Path] = None,
    ) -> None:
        """Plot the same field from different formats for comparison."""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        for i, magnet_data in enumerate(magnet_data_list):
            if field_name in magnet_data.keys:
                try:
                    # Try to get time data
                    data = magnet_data.get_data(["t", field_name])
                    x_values = data["t"]
                    x_label = magnet_data.get_field_label("t")
                except:
                    # Fallback to index
                    data = magnet_data.get_data([field_name])
                    x_values = data.index
                    x_label = "Index"
                
                y_label = magnet_data.get_field_label(field_name)
                format_name = magnet_data.format_type
                
                color = colors[i % len(colors)]
                ax.plot(x_values, data[field_name], 
                       color=color, linewidth=1.5, 
                       label=f"{format_name} - {field_name}")
        
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_title(f"Format Comparison - {field_name}")
        
        if save:
            output_path = DataPlotter._get_output_path(
                file_path, f"_format_comparison_{field_name}.png", output_dir
            )
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            print(f"Saved plot: {output_path}")

        if show:
            plt.show()

        plt.close()

    @staticmethod
    def plot_field_metadata_summary(
        magnet_data: MagnetData,
        file_path: str = "",
        save: bool = False,
        show: bool = False,
        output_dir: Optional[Path] = None,
    ) -> None:
        """Plot summary of field metadata from JSON definitions."""
        format_def = magnet_data.field_registry
        
        # Collect field metadata
        field_info = []
        for key in magnet_data.keys:
            field = format_def.get_field(key)
            if field:
                field_info.append({
                    'name': key,
                    'type': field.field_type.value,
                    'unit': field.unit,
                    'symbol': field.symbol,
                    'has_description': bool(field.description)
                })
        
        if not field_info:
            print("No field definitions found for plotting")
            return
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
        
        # Field type distribution
        type_counts = {}
        for info in field_info:
            field_type = info['type']
            type_counts[field_type] = type_counts.get(field_type, 0) + 1
        
        ax1.pie(type_counts.values(), labels=type_counts.keys(), autopct='%1.1f%%')
        ax1.set_title('Field Type Distribution')
        
        # Unit distribution
        unit_counts = {}
        for info in field_info:
            unit = info['unit']
            unit_counts[unit] = unit_counts.get(unit, 0) + 1
        
        # Show top 10 units
        top_units = dict(sorted(unit_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        ax2.bar(range(len(top_units)), list(top_units.values()))
        ax2.set_xticks(range(len(top_units)))
        ax2.set_xticklabels(list(top_units.keys()), rotation=45, ha='right')
        ax2.set_title('Top 10 Units Used')
        ax2.set_ylabel('Count')
        
        # Symbol length distribution
        symbol_lengths = [len(info['symbol']) for info in field_info]
        ax3.hist(symbol_lengths, bins=10, alpha=0.7, color='skyblue')
        ax3.set_title('Symbol Length Distribution')
        ax3.set_xlabel('Symbol Length (characters)')
        ax3.set_ylabel('Count')
        
        # Description availability
        has_desc = sum(1 for info in field_info if info['has_description'])
        no_desc = len(field_info) - has_desc
        ax4.bar(['Has Description', 'No Description'], [has_desc, no_desc], 
               color=['green', 'red'], alpha=0.7)
        ax4.set_title('Description Availability')
        ax4.set_ylabel('Number of Fields')
        
        plt.suptitle(f"{Path(file_path).stem} - Field Metadata Summary", fontsize=14)
        plt.tight_layout()
        
        if save:
            output_path = DataPlotter._get_output_path(
                file_path, "_field_metadata_summary.png", output_dir
            )
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            print(f"Saved plot: {output_path}")

        if show:
            plt.show()

        plt.close()

    @staticmethod
    def _get_output_path(
        file_path: str, suffix: str, output_dir: Optional[Path] = None
    ) -> Path:
        """Generate output path for saved plots."""
        base_path = Path(file_path).with_suffix("")
        if output_dir:
            base_path = output_dir / base_path.name
        return base_path.with_suffix(suffix)
