"""MagnetRun class for high-level data operations with updated field management."""

from typing import Optional, List, Dict, Any
import numpy as np
import pandas as pd
from .magnet_data import MagnetData

# CORRECTED: Import from new locations
from ..formats import FormatDefinition
from ..core.fields import Field, FieldType

from ..config.housing_configs import get_housing_config, HousingConfig
from ..exceptions import DataFormatError


class MagnetRun:
    """High-level interface for magnet run data analysis with updated field management."""

    def __init__(self, housing: str, site: str, data: Optional[MagnetData] = None):
        self.housing = housing
        self.site = site
        self.magnet_data = data
        self._housing_config = get_housing_config(housing)

    @property
    def housing_config(self) -> Optional[HousingConfig]:
        """Get housing configuration."""
        return self._housing_config

    @property
    def field_registry(self) -> Optional[FormatDefinition]:
        """Get format definition from MagnetData."""
        if self.magnet_data:
            return self.magnet_data.field_registry
        return None

    @property
    def format_definition(self) -> Optional[FormatDefinition]:
        """Get format definition from MagnetData."""
        return self.field_registry

    def get_data(self, key: Optional[str] = None) -> pd.DataFrame:
        """Get data from MagnetData."""
        if self.magnet_data is None:
            raise DataFormatError("No MagnetData associated")
        return self.magnet_data.get_data(key)

    def get_keys(self) -> list:
        """Get available data keys."""
        if self.magnet_data is None:
            raise DataFormatError("No MagnetData associated")
        return self.magnet_data.keys

    def prepare_data(self, debug: bool = False) -> None:
        """Prepare data according to housing configuration."""
        if self.magnet_data is None or self._housing_config is None:
            if debug:
                print("No MagnetData or housing configuration available")
            return

        format_def = self.magnet_data.field_registry

        # Add reference calculations with proper field definitions
        if self._housing_config.ih_ref_channels:
            formula = self._housing_config.get_ih_formula()
            if debug:
                print(f"Adding IH_ref with formula: {formula}")

            # Add calculated field with proper field type
            self.magnet_data.add_data(
                "IH_ref", formula, field_type="current", unit="ampere", symbol="I_H"
            )

        if self._housing_config.ib_ref_channels:
            formula = self._housing_config.get_ib_formula()
            if debug:
                print(f"Adding IB_ref with formula: {formula}")

            # Add calculated field with proper field type
            self.magnet_data.add_data(
                "IB_ref", formula, field_type="current", unit="ampere", symbol="I_B"
            )

        # Apply field mappings (rename existing fields)
        if self._housing_config.field_mappings:
            if debug:
                print(f"Applying field mappings: {self._housing_config.field_mappings}")

            # Update field definitions for renamed fields
            mappings = self._housing_config.field_mappings
            for old_name, new_name in mappings.items():
                if old_name in self.magnet_data.keys:
                    # Get existing field definition
                    old_field = format_def.get_field(old_name)
                    if old_field:
                        # Create new field with updated name
                        new_field = Field(
                            name=new_name,
                            field_type=old_field.field_type,
                            unit=old_field.unit,
                            symbol=old_field.symbol,
                            description=f"Renamed from {old_name}: {old_field.description}",
                        )
                        format_def.add_field(new_field)

            # Apply the rename operation
            self.magnet_data.rename_data(mappings)

        # Remove specified channels
        if self._housing_config.remove_channels:
            if debug:
                print(f"Removing channels: {self._housing_config.remove_channels}")

            existing_channels = [
                ch
                for ch in self._housing_config.remove_channels
                if ch in self.magnet_data.keys
            ]
            if existing_channels:
                self.magnet_data.remove_data(existing_channels)

    def validate_all_fields(self) -> dict:
        """Validate all fields in the dataset."""
        if self.magnet_data is None:
            return {"error": "No MagnetData associated"}

        return self.magnet_data.get_field_validation_summary()

    def validate_housing_requirements(self) -> dict:
        """Validate that required fields for this housing are present and valid."""
        if self.magnet_data is None:
            return {"error": "No MagnetData associated"}

        if self._housing_config is None:
            return {"error": f"No configuration found for housing: {self.housing}"}

        validation_result = {
            "housing": self.housing,
            "site": self.site,
            "required_fields_status": {},
            "reference_calculations": {},
            "overall_status": "unknown",
        }

        # Check reference current requirements
        if self._housing_config.ih_ref_channels:
            ih_channels = self._housing_config.ih_ref_channels
            ih_status = {
                "required_channels": ih_channels,
                "available_channels": [],
                "missing_channels": [],
                "can_calculate": False,
            }

            for channel in ih_channels:
                if channel in self.magnet_data.keys:
                    ih_status["available_channels"].append(channel)
                else:
                    ih_status["missing_channels"].append(channel)

            ih_status["can_calculate"] = len(ih_status["missing_channels"]) == 0
            validation_result["reference_calculations"]["IH_ref"] = ih_status

        if self._housing_config.ib_ref_channels:
            ib_channels = self._housing_config.ib_ref_channels
            ib_status = {
                "required_channels": ib_channels,
                "available_channels": [],
                "missing_channels": [],
                "can_calculate": False,
            }

            for channel in ib_channels:
                if channel in self.magnet_data.keys:
                    ib_status["available_channels"].append(channel)
                else:
                    ib_status["missing_channels"].append(channel)

            ib_status["can_calculate"] = len(ib_status["missing_channels"]) == 0
            validation_result["reference_calculations"]["IB_ref"] = ib_status

        # Check field mappings
        if self._housing_config.field_mappings:
            mapping_status = {}
            for old_name, new_name in self._housing_config.field_mappings.items():
                mapping_status[f"{old_name} -> {new_name}"] = (
                    old_name in self.magnet_data.keys
                )
            validation_result["field_mappings"] = mapping_status

        # Determine overall status
        can_calculate_ih = (
            validation_result["reference_calculations"]
            .get("IH_ref", {})
            .get("can_calculate", True)
        )
        can_calculate_ib = (
            validation_result["reference_calculations"]
            .get("IB_ref", {})
            .get("can_calculate", True)
        )

        if can_calculate_ih and can_calculate_ib:
            validation_result["overall_status"] = "complete"
        elif can_calculate_ih or can_calculate_ib:
            validation_result["overall_status"] = "partial"
        else:
            validation_result["overall_status"] = "incomplete"

        return validation_result

    def get_field_summary(self) -> dict:
        """Get comprehensive field summary for this magnet run."""
        if self.magnet_data is None:
            return {"error": "No MagnetData associated"}

        # Get basic field statistics
        format_stats = self.magnet_data.get_format_statistics()

        # Get validation summary
        validation_summary = self.validate_all_fields()

        # Get housing-specific validation
        housing_validation = self.validate_housing_requirements()

        # Combine all information
        summary = {
            "run_info": {
                "housing": self.housing,
                "site": self.site,
                "format_type": self.magnet_data.format_type,
                "filename": self.magnet_data.filename,
            },
            "format_statistics": format_stats,
            "field_validation": validation_summary,
            "housing_validation": housing_validation,
            "data_shape": None,
        }

        # Add data shape if available
        try:
            data = self.magnet_data.get_data()
            summary["data_shape"] = data.shape
        except:
            pass

        return summary

    def get_measurement_overview(self) -> dict:
        """Get overview of measurements available in this run."""
        if self.magnet_data is None:
            return {"error": "No MagnetData associated"}

        format_def = self.magnet_data.field_registry
        measurements = {
            "magnetic_fields": [],
            "currents": [],
            "voltages": [],
            "temperatures": [],
            "pressures": [],
            "flow_rates": [],
            "powers": [],
            "others": [],
        }

        # Categorize available measurements
        for key in self.magnet_data.keys:
            field = format_def.get_field(key)
            if field:
                field_type = field.field_type
                label = field.get_label(format_def.ureg)

                measurement_info = {
                    "key": key,
                    "symbol": field.symbol,
                    "unit": field.unit,
                    "label": label,
                    "description": field.description,
                }

                if field_type == FieldType.MAGNETIC_FIELD:
                    measurements["magnetic_fields"].append(measurement_info)
                elif field_type == FieldType.CURRENT:
                    measurements["currents"].append(measurement_info)
                elif field_type == FieldType.VOLTAGE:
                    measurements["voltages"].append(measurement_info)
                elif field_type == FieldType.TEMPERATURE:
                    measurements["temperatures"].append(measurement_info)
                elif field_type == FieldType.PRESSURE:
                    measurements["pressures"].append(measurement_info)
                elif field_type == FieldType.FLOW_RATE:
                    measurements["flow_rates"].append(measurement_info)
                elif field_type == FieldType.POWER:
                    measurements["powers"].append(measurement_info)
                else:
                    measurements["others"].append(measurement_info)
            else:
                # Unknown field
                measurements["others"].append(
                    {
                        "key": key,
                        "symbol": key,
                        "unit": "unknown",
                        "label": key,
                        "description": "Field definition not found",
                    }
                )

        # Add summary counts
        measurements["summary"] = {
            "total_measurements": len(self.magnet_data.keys),
            "magnetic_fields_count": len(measurements["magnetic_fields"]),
            "currents_count": len(measurements["currents"]),
            "voltages_count": len(measurements["voltages"]),
            "temperatures_count": len(measurements["temperatures"]),
            "pressures_count": len(measurements["pressures"]),
            "flow_rates_count": len(measurements["flow_rates"]),
            "powers_count": len(measurements["powers"]),
            "others_count": len(measurements["others"]),
        }

        return measurements

    def get_data_quality_report(self) -> dict:
        """Get comprehensive data quality report."""
        if self.magnet_data is None:
            return {"error": "No MagnetData associated"}

        report = {
            "run_info": {
                "housing": self.housing,
                "site": self.site,
                "format_type": self.magnet_data.format_type,
                "filename": self.magnet_data.filename,
            },
            "data_completeness": {},
            "field_validation": {},
            "housing_compliance": {},
            "data_statistics": {},
            "recommendations": [],
        }

        # Data completeness analysis
        try:
            data = self.magnet_data.get_data()
            total_rows = len(data)

            completeness = {}
            for key in self.magnet_data.keys:
                column_data = data[key] if key in data.columns else pd.Series()
                null_count = column_data.isnull().sum()
                completeness[key] = {
                    "total_values": total_rows,
                    "valid_values": total_rows - null_count,
                    "null_values": null_count,
                    "completeness_percent": (
                        ((total_rows - null_count) / total_rows * 100)
                        if total_rows > 0
                        else 0
                    ),
                }

            report["data_completeness"] = completeness

            # Overall data statistics
            numeric_data = data.select_dtypes(include=[np.number])
            if not numeric_data.empty:
                report["data_statistics"] = {
                    "total_rows": total_rows,
                    "numeric_columns": len(numeric_data.columns),
                    "total_columns": len(data.columns),
                    "memory_usage_mb": data.memory_usage(deep=True).sum() / 1024 / 1024,
                }

        except Exception as e:
            report["data_completeness"]["error"] = str(e)

        # Field validation
        validation_summary = self.validate_all_fields()
        report["field_validation"] = validation_summary

        # Housing compliance
        housing_validation = self.validate_housing_requirements()
        report["housing_compliance"] = housing_validation

        # Generate recommendations
        recommendations = []

        # Check field coverage
        field_coverage = validation_summary.get("summary", {}).get(
            "coverage_percent", 0
        )
        if field_coverage < 50:
            recommendations.append(
                {
                    "type": "field_coverage",
                    "priority": "high",
                    "message": f"Low field definition coverage ({field_coverage:.1f}%). Consider updating format definition.",
                }
            )
        elif field_coverage < 80:
            recommendations.append(
                {
                    "type": "field_coverage",
                    "priority": "medium",
                    "message": f"Moderate field definition coverage ({field_coverage:.1f}%). Some fields may need definitions.",
                }
            )

        # Check data quality
        quality_percent = validation_summary.get("summary", {}).get(
            "quality_percent", 0
        )
        if quality_percent < 90:
            recommendations.append(
                {
                    "type": "data_quality",
                    "priority": "medium",
                    "message": f"Data quality issues detected ({quality_percent:.1f}% valid). Check field validation results.",
                }
            )

        # Check housing compliance
        housing_status = housing_validation.get("overall_status", "unknown")
        if housing_status == "incomplete":
            recommendations.append(
                {
                    "type": "housing_compliance",
                    "priority": "high",
                    "message": f"Housing '{self.housing}' requirements not met. Missing required measurement channels.",
                }
            )
        elif housing_status == "partial":
            recommendations.append(
                {
                    "type": "housing_compliance",
                    "priority": "medium",
                    "message": f"Housing '{self.housing}' partially compliant. Some reference calculations may not be available.",
                }
            )

        # Check data completeness
        if "data_completeness" in report and isinstance(
            report["data_completeness"], dict
        ):
            low_completeness_fields = []
            for field, stats in report["data_completeness"].items():
                if (
                    isinstance(stats, dict)
                    and stats.get("completeness_percent", 100) < 95
                ):
                    low_completeness_fields.append(field)

            if low_completeness_fields:
                recommendations.append(
                    {
                        "type": "data_completeness",
                        "priority": "medium",
                        "message": f"Fields with missing data: {', '.join(low_completeness_fields[:5])}{'...' if len(low_completeness_fields) > 5 else ''}",
                    }
                )

        report["recommendations"] = recommendations

        # Overall assessment
        critical_issues = len([r for r in recommendations if r["priority"] == "high"])
        medium_issues = len([r for r in recommendations if r["priority"] == "medium"])

        if critical_issues == 0 and medium_issues == 0:
            overall_status = "excellent"
        elif critical_issues == 0:
            overall_status = "good"
        elif critical_issues <= 1:
            overall_status = "fair"
        else:
            overall_status = "poor"

        report["overall_assessment"] = {
            "status": overall_status,
            "critical_issues": critical_issues,
            "medium_issues": medium_issues,
            "total_recommendations": len(recommendations),
        }

        return report

    def export_field_definitions(self, filepath: str) -> None:
        """Export current field definitions to file."""
        if self.magnet_data is None:
            raise DataFormatError("No MagnetData associated")

        self.magnet_data.save_format_definition(filepath)

    def import_field_definitions(self, filepath: str) -> None:
        """Import field definitions from file."""
        if self.magnet_data is None:
            raise DataFormatError("No MagnetData associated")

        self.magnet_data.load_format_definition(filepath)

    def get_field_conversion_table(self, target_units: Dict[str, str]) -> pd.DataFrame:
        """Get a table showing field conversions to target units."""
        if self.magnet_data is None:
            raise DataFormatError("No MagnetData associated")

        format_def = self.magnet_data.field_registry
        conversion_data = []

        for field_name, target_unit in target_units.items():
            field = format_def.get_field(field_name)
            if field:
                try:
                    conversion_factor = field.get_conversion_factor(
                        target_unit, format_def.ureg
                    )
                    is_compatible = field.is_compatible_unit(
                        target_unit, format_def.ureg
                    )

                    conversion_data.append(
                        {
                            "field_name": field_name,
                            "current_unit": field.unit,
                            "target_unit": target_unit,
                            "conversion_factor": conversion_factor,
                            "compatible": is_compatible,
                            "symbol": field.symbol,
                            "field_type": field.field_type.value,
                        }
                    )
                except Exception as e:
                    conversion_data.append(
                        {
                            "field_name": field_name,
                            "current_unit": field.unit,
                            "target_unit": target_unit,
                            "conversion_factor": None,
                            "compatible": False,
                            "symbol": field.symbol,
                            "field_type": field.field_type.value,
                            "error": str(e),
                        }
                    )
            else:
                conversion_data.append(
                    {
                        "field_name": field_name,
                        "current_unit": "unknown",
                        "target_unit": target_unit,
                        "conversion_factor": None,
                        "compatible": False,
                        "symbol": field_name,
                        "field_type": "unknown",
                        "error": "Field definition not found",
                    }
                )

        return pd.DataFrame(conversion_data)

    def create_measurement_dashboard_data(self) -> Dict[str, Any]:
        """Create data structure suitable for measurement dashboard."""
        if self.magnet_data is None:
            return {"error": "No MagnetData associated"}

        dashboard_data = {
            "metadata": {
                "housing": self.housing,
                "site": self.site,
                "format_type": self.magnet_data.format_type,
                "filename": self.magnet_data.filename,
                "total_measurements": len(self.magnet_data.keys),
            },
            "measurements": self.get_measurement_overview(),
            "data_quality": {
                "field_validation": self.validate_all_fields()["summary"],
                "housing_compliance": self.validate_housing_requirements()[
                    "overall_status"
                ],
            },
            "plot_ready_data": {},
        }

        # Prepare plot-ready data for common measurement types
        try:
            format_def = self.magnet_data.field_registry

            # Get time series data if available
            time_fields = [
                key
                for key in self.magnet_data.keys
                if format_def.get_field(key)
                and format_def.get_field(key).field_type == FieldType.TIME
            ]

            if time_fields:
                dashboard_data["plot_ready_data"]["time_field"] = time_fields[0]

            # Get main measurement fields
            main_measurements = {}
            for measurement_type in [
                "magnetic_fields",
                "currents",
                "voltages",
                "temperatures",
                "powers",
            ]:
                measurements = dashboard_data["measurements"].get(measurement_type, [])
                if measurements:
                    # Get first few measurements of each type for quick plotting
                    main_measurements[measurement_type] = measurements[
                        :3
                    ]  # Limit to first 3

            dashboard_data["plot_ready_data"]["main_measurements"] = main_measurements

            # Add summary statistics for numeric fields
            summary_stats = self.magnet_data.get_data_summary()
            if summary_stats and "error" not in summary_stats:
                dashboard_data["plot_ready_data"]["summary_statistics"] = summary_stats

        except Exception as e:
            dashboard_data["plot_ready_data"]["error"] = str(e)

        return dashboard_data

    def optimize_for_analysis(self) -> Dict[str, Any]:
        """Optimize data and field definitions for analysis workflows."""
        if self.magnet_data is None:
            return {"error": "No MagnetData associated"}

        optimization_report = {
            "actions_taken": [],
            "warnings": [],
            "recommendations": [],
            "performance_metrics": {},
        }

        # Prepare data according to housing configuration
        try:
            self.prepare_data(debug=False)
            optimization_report["actions_taken"].append(
                "Applied housing-specific data preparation"
            )
        except Exception as e:
            optimization_report["warnings"].append(f"Housing preparation failed: {e}")

        # Check for common analysis requirements
        format_def = self.magnet_data.field_registry

        # Check for time field
        time_fields = [
            key
            for key in self.magnet_data.keys
            if format_def.get_field(key)
            and format_def.get_field(key).field_type == FieldType.TIME
        ]

        if not time_fields:
            optimization_report["recommendations"].append(
                {
                    "type": "missing_time_field",
                    "message": "No time field detected. Consider adding a time reference for time-series analysis.",
                }
            )

        # Check for main measurement fields
        field_types_present = set()
        for key in self.magnet_data.keys:
            field = format_def.get_field(key)
            if field:
                field_types_present.add(field.field_type)

        important_types = {
            FieldType.MAGNETIC_FIELD,
            FieldType.CURRENT,
            FieldType.VOLTAGE,
        }
        missing_types = important_types - field_types_present

        if missing_types:
            missing_names = [ft.value for ft in missing_types]
            optimization_report["recommendations"].append(
                {
                    "type": "missing_measurement_types",
                    "message": f"Missing important measurement types: {', '.join(missing_names)}",
                }
            )

        # Performance metrics
        try:
            data = self.magnet_data.get_data()
            optimization_report["performance_metrics"] = {
                "data_shape": data.shape,
                "memory_usage_mb": data.memory_usage(deep=True).sum() / 1024 / 1024,
                "numeric_columns": len(data.select_dtypes(include=[np.number]).columns),
                "field_coverage_percent": self.magnet_data._get_field_coverage(),
            }
        except Exception as e:
            optimization_report["warnings"].append(
                f"Could not compute performance metrics: {e}"
            )

        return optimization_report
