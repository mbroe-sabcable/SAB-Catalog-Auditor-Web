from datetime import datetime

import pandas as pd

from audits.part_number import build_part_number_mapping
from audits.specifications import compare_specifications
from audits.unified_record_builder import AuditRecord, UnifiedRecordBuilder
from importers.field_mapper import FieldMapper
from reports.correction_report import build_correction_recommendations
from reports.excel_report import write_audit_report


class AuditEngine:
    def __init__(self, trackvia_df=None, directus_df=None, german_df=None, us_catalog_df=None, audit_type="Full Product Family Audit"):
        self.trackvia_df = trackvia_df
        self.directus_df = directus_df
        self.german_df = german_df
        self.us_catalog_df = us_catalog_df
        self.audit_type = audit_type
        self.field_mapper = FieldMapper()
        self.records = UnifiedRecordBuilder.build(trackvia_df, directus_df, german_df, us_catalog_df)

    def _normalize_column_name(self, column_name):
        return "".join(ch.lower() for ch in str(column_name) if ch.isalnum())

    def _unique_values(self, df, column_name):
        values = []
        seen = set()
        for value in df[column_name].dropna():
            text = str(value).strip()
            if text and text not in seen:
                seen.add(text)
                values.append(text)
        return values

    def _get_mapped_column(self, df, source_name):
        if df is None:
            return None

        expected_column = self.field_mapper.get_part_number_mapping(source_name)
        for column in df.columns:
            if self._normalize_column_name(column) == self._normalize_column_name(expected_column):
                return column
        return None

    def _get_column_by_expected_name(self, df, expected_column_name):
        if df is None or not expected_column_name:
            return None

        expected = self._normalize_column_name(expected_column_name)
        for column in df.columns:
            if self._normalize_column_name(column) == expected:
                return column
        return None

    def _get_german_value_for_field(self, sku, field_mapping):
        if not sku or self.german_df is None or self.trackvia_df is None or not field_mapping:
            return ""

        trackvia_sku_column = self._get_mapped_column(self.trackvia_df, "trackvia")
        trackvia_german_part_column = self._get_column_by_expected_name(self.trackvia_df, "part_german")
        german_part_number_column = self._get_column_by_expected_name(self.german_df, "item no.")
        german_field_column = self._get_column_by_expected_name(self.german_df, field_mapping.get("german"))

        if trackvia_sku_column is None or trackvia_german_part_column is None or german_part_number_column is None or german_field_column is None:
            return ""

        for _, row in self.trackvia_df.iterrows():
            current_sku = str(row[trackvia_sku_column]).strip() if pd.notna(row[trackvia_sku_column]) else ""
            if current_sku != sku:
                continue

            german_part_number = str(row[trackvia_german_part_column]).strip() if pd.notna(row[trackvia_german_part_column]) else ""
            if not german_part_number:
                return ""

            for _, german_row in self.german_df.iterrows():
                german_row_part_number = str(german_row[german_part_number_column]).strip() if pd.notna(german_row[german_part_number_column]) else ""
                if german_row_part_number != german_part_number:
                    continue

                value = german_row[german_field_column]
                return str(value).strip() if pd.notna(value) else ""

            break

        return ""

    def _build_recommendation_mismatches(self, mismatches):
        enriched_mismatches = []
        for mismatch in mismatches:
            field_mapping = self.field_mapper.get_mapping(mismatch.get("field_key")) if mismatch.get("field_key") else None
            source_of_truth = field_mapping.get("source_of_truth", "") if field_mapping else ""
            german_value = ""

            if source_of_truth == "German":
                german_value = self._get_german_value_for_field(mismatch.get("sku", ""), field_mapping)

            enriched_mismatches.append(
                {
                    **mismatch,
                    "source_of_truth": source_of_truth,
                    "german_value": german_value,
                }
            )

        return enriched_mismatches

    def _find_missing_part_numbers(self, trackvia_df, directus_df):
        trackvia_column = self._get_mapped_column(trackvia_df, "trackvia")
        directus_column = self._get_mapped_column(directus_df, "directus")

        if trackvia_column is None or directus_column is None:
            return [], []

        trackvia_values = self._unique_values(trackvia_df, trackvia_column)
        directus_values = self._unique_values(directus_df, directus_column)

        directus_lookup = set(directus_values)
        missing_from_directus = [value for value in trackvia_values if value not in directus_lookup]

        trackvia_lookup = set(trackvia_values)
        missing_from_trackvia = [value for value in directus_values if value not in trackvia_lookup]

        return missing_from_directus, missing_from_trackvia

    def _build_tier1_field_summary(self, mismatches):
        summary = {}
        trackvia_column = self._get_mapped_column(self.trackvia_df, "trackvia")
        directus_column = self._get_mapped_column(self.directus_df, "directus")

        common_sku_count = 0
        if trackvia_column is not None and directus_column is not None:
            trackvia_skus = set(self._unique_values(self.trackvia_df, trackvia_column))
            directus_skus = set(self._unique_values(self.directus_df, directus_column))
            common_sku_count = len(trackvia_skus & directus_skus)

        for field in self.field_mapper.get_specification_mappings():
            field_key = field.get("key")
            field_display = field.get("display")
            if not field_key or not field_display:
                continue

            field_mismatches = [mismatch for mismatch in mismatches if mismatch.get("field_key") == field_key]
            summary[field_display] = {
                "comparisons": common_sku_count,
                "mismatches": len(field_mismatches),
                "status": "PASS" if len(field_mismatches) == 0 else "FAIL",
            }

        return summary

    def _build_part_number_comparison_html(self):
        trackvia_column = self._get_mapped_column(self.trackvia_df, "trackvia")
        directus_column = self._get_mapped_column(self.directus_df, "directus")

        warnings = []
        if trackvia_column is None:
            available_columns = ", ".join(str(column) for column in self.trackvia_df.columns) if self.trackvia_df is not None else ""
            warnings.append(
                f"TrackVia expected column 'sku' is missing. Available columns: {available_columns or 'none'}"
            )
        if directus_column is None:
            available_columns = ", ".join(str(column) for column in self.directus_df.columns) if self.directus_df is not None else ""
            warnings.append(
                f"Directus expected column 'sku' is missing. Available columns: {available_columns or 'none'}"
            )

        if warnings:
            return (
                '<div class="alert alert-warning mt-4" role="alert">'
                + " ".join(warnings)
                + "</div>"
            )

        missing_from_directus, missing_from_trackvia = self._find_missing_part_numbers(self.trackvia_df, self.directus_df)
        matching_count = len(set(self._unique_values(self.trackvia_df, trackvia_column)) & set(self._unique_values(self.directus_df, directus_column)))
        mismatches = compare_specifications(self.trackvia_df, self.directus_df, self.field_mapper)
        part_number_mapping = build_part_number_mapping(self.trackvia_df)

        missing_from_directus_text = "\n".join(missing_from_directus) if missing_from_directus else "None"
        missing_from_trackvia_text = "\n".join(missing_from_trackvia) if missing_from_trackvia else "None"

        duplicate_german_numbers = []
        duplicate_german_lookup = {}
        duplicate_us_skus = []
        us_sku_lookup = {}

        german_column = None
        sku_column = None
        if self.trackvia_df is not None:
            german_column = next((column for column in self.trackvia_df.columns if self._normalize_column_name(column) == "partgerman"), None)
            sku_column = next((column for column in self.trackvia_df.columns if self._normalize_column_name(column) == "sku"), None)

        if german_column is not None and sku_column is not None:
            for _, row in self.trackvia_df.iterrows():
                german_value = str(row[german_column]).strip() if pd.notna(row[german_column]) else ""
                sku_value = str(row[sku_column]).strip() if pd.notna(row[sku_column]) else ""

                if not german_value:
                    continue

                if german_value in duplicate_german_lookup:
                    if german_value not in duplicate_german_numbers:
                        duplicate_german_numbers.append(german_value)
                else:
                    duplicate_german_lookup[german_value] = sku_value

                us_sku_lookup.setdefault(sku_value, []).append(german_value)

            for sku, german_numbers in us_sku_lookup.items():
                if sku and len(set(german_numbers)) > 1:
                    duplicate_us_skus.append((sku, sorted(set(german_numbers))))

        mapping_rows = "".join(
            f"<tr><td>{german_number}</td><td>{sku}</td></tr>"
            for german_number, sku in part_number_mapping.items()
        )

        tier1_summary = self._build_tier1_field_summary(mismatches)
        tier1_rows = "".join(
            f"<tr><td>{field_name}</td><td>{details['comparisons']}</td><td>{details['mismatches']}</td><td>{details['status']}</td></tr>"
            for field_name, details in tier1_summary.items()
        )
        tier1_table = (
            '<div class="card shadow-sm mt-4">'
            '<div class="card-body">'
            '<h2 class="h5 mb-3">Tier 1 Field Summary</h2>'
            + (f'<div class="table-responsive"><table class="table table-striped align-middle"><thead><tr><th>Field</th><th>Comparisons</th><th>Mismatches</th><th>Status</th></tr></thead><tbody>{tier1_rows}</tbody></table></div>' if tier1_rows else '<p class="mb-0">No tier 1 fields found.</p>')
            + '</div></div>'
        )

        recommendation_payload = self._build_recommendation_mismatches(mismatches)
        correction_rows = "".join(
            f"<tr><td>{recommendation['sku']}</td><td>{recommendation['system']}</td><td>{recommendation['field']}</td><td>{recommendation['current_value']}</td><td>{recommendation['correct_value']}</td><td>{recommendation['reason']}</td><td>{recommendation.get('source_of_truth', '')}</td></tr>"
            for recommendation in build_correction_recommendations(recommendation_payload)[:20]
        )
        correction_table = (
            '<div class="card shadow-sm mt-4">'
            '<div class="card-body">'
            '<h2 class="h5 mb-3">Recommended Corrections</h2>'
            + (f'<div class="table-responsive"><table class="table table-striped align-middle"><thead><tr><th>SKU</th><th>System</th><th>Field</th><th>Current Value</th><th>Correct Value</th><th>Reason</th><th>Source of Truth</th></tr></thead><tbody>{correction_rows}</tbody></table></div>' if correction_rows else '<p class="mb-0">No recommended corrections found.</p>')
            + '</div></div>'
        )

        mismatch_rows = "".join(
            f"<tr><td>{mismatch['sku']}</td><td>{mismatch['field_display']}</td><td>{mismatch['trackvia_value']}</td><td>{mismatch['directus_value']}</td></tr>"
            for mismatch in mismatches
        )
        mismatch_table = (
            '<div class="card shadow-sm mt-4">'
            '<div class="card-body">'
            '<h2 class="h5 mb-3">Specification Mismatches</h2>'
            f'<p class="mb-3"><strong>Total mismatches:</strong> {len(mismatches)}</p>'
            + (f'<div class="table-responsive"><table class="table table-striped align-middle"><thead><tr><th>SKU</th><th>Field</th><th>TrackVia</th><th>Directus</th></tr></thead><tbody>{mismatch_rows}</tbody></table></div>' if mismatch_rows else '<p class="mb-0">No specification mismatches found.</p>')
            + '</div></div>'
        )

        mapping_warning_html = ""
        if duplicate_german_numbers or duplicate_us_skus:
            warning_items = []
            if duplicate_german_numbers:
                warning_items.append(
                    f"Duplicate German part numbers found: {', '.join(duplicate_german_numbers)}"
                )
            if duplicate_us_skus:
                formatted_duplicates = ", ".join(
                    f"{sku} -> {', '.join(numbers)}" for sku, numbers in duplicate_us_skus
                )
                warning_items.append(f"Duplicate US SKUs mapped from different German numbers: {formatted_duplicates}")
            mapping_warning_html = (
                '<div class="alert alert-warning mt-3" role="alert">'
                + "<strong>Part number mapping warnings:</strong> "
                + " | ".join(warning_items)
                + "</div>"
            )

        mapping_table = (
            '<div class="card shadow-sm mt-4">'
            '<div class="card-body">'
            '<h2 class="h5 mb-3">German ↔ US Part Number Mapping</h2>'
            + mapping_warning_html
            + (f'<div class="table-responsive"><table class="table table-striped align-middle"><thead><tr><th>German Part Number</th><th>US Part Number</th></tr></thead><tbody>{mapping_rows}</tbody></table></div>' if mapping_rows else '<p class="mb-0">No part number mappings found.</p>')
            + '</div></div>'
        )

        return (
            '<div class="card shadow-sm mt-4">'
            '<div class="card-body">'
            '<h2 class="h5 mb-3">Part Number Comparison</h2>'
            '<div class="row g-3">'
            '<div class="col-12">'
            '<p class="mb-2"><strong>Matching part numbers:</strong> '
            + str(matching_count)
            + '</p>'
            '<p class="mb-2"><strong>Missing from Directus:</strong> '
            + str(len(missing_from_directus))
            + '</p>'
            '<p class="mb-2"><strong>Missing from TrackVia:</strong> '
            + str(len(missing_from_trackvia))
            + '</p>'
            '</div>'
            '<div class="col-md-6">'
            '<h3 class="h6">Missing from Directus</h3>'
            '<pre class="border rounded p-3 bg-light mb-0">'
            + missing_from_directus_text
            + '</pre></div>'
            '<div class="col-md-6">'
            '<h3 class="h6">Missing from TrackVia</h3>'
            '<pre class="border rounded p-3 bg-light mb-0">'
            + missing_from_trackvia_text
            + '</pre></div></div></div></div>'
            + mapping_table
            + tier1_table
            + correction_table
            + mismatch_table
        )

    def run(self):
        comparison_html = self._build_part_number_comparison_html()
        report_filename = ""

        if self.trackvia_df is not None and self.directus_df is not None:
            missing_from_directus, missing_from_trackvia = self._find_missing_part_numbers(self.trackvia_df, self.directus_df)
            mismatches = compare_specifications(self.trackvia_df, self.directus_df, self.field_mapper)
            part_number_mapping = build_part_number_mapping(self.trackvia_df)
            trackvia_column = self._get_mapped_column(self.trackvia_df, "trackvia")
            directus_column = self._get_mapped_column(self.directus_df, "directus")
            tier1_summary = self._build_tier1_field_summary(mismatches)
            recommendation_payload = self._build_recommendation_mismatches(mismatches)
            recommended_corrections = build_correction_recommendations(recommendation_payload)

            report_filename = write_audit_report(
                {
                    "audit_type": self.audit_type,
                    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "matching_count": len(
                        set(self._unique_values(self.trackvia_df, trackvia_column))
                        & set(self._unique_values(self.directus_df, directus_column))
                    ),
                    "missing_from_directus_count": len(missing_from_directus),
                    "missing_from_trackvia_count": len(missing_from_trackvia),
                    "total_mismatches": len(mismatches),
                    "missing_from_directus": missing_from_directus,
                    "missing_from_trackvia": missing_from_trackvia,
                    "mismatches": mismatches,
                    "part_number_mapping": part_number_mapping,
                    "tier1_summary": tier1_summary,
                    "recommended_corrections": recommended_corrections,
                }
            )

        return {
            "comparison_html": comparison_html,
            "report_filename": report_filename,
        }
