from datetime import datetime
from pathlib import Path

from openpyxl import Workbook

from audits.unified_record_builder import UnifiedRecordBuilder


def _build_output_dir():
    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _append_product_corrections_sheet(workbook, product_corrections):
    product_sheet = workbook.create_sheet("Product Corrections")
    product_sheet.append(["SKU", "Total Corrections", "Category", "System", "Field", "Current Value", "Correct Value", "Reason"])

    for product in product_corrections:
        sku = UnifiedRecordBuilder.normalize_part_number(product.get("sku", ""))
        total = product.get("total_corrections", 0)
        categories = [
            ("Product Identity corrections", product.get("product_identity_corrections", [])),
            ("Engineering corrections", product.get("engineering_corrections", [])),
            ("Website QA corrections", product.get("website_qa_corrections", [])),
            ("Directus QA corrections", product.get("directus_qa_corrections", [])),
        ]

        if total == 0:
            product_sheet.append([sku, 0, "No Corrections", "", "", "", "", "No Corrections"])
            continue

        first_row_for_sku = True
        for category_name, corrections in categories:
            if not corrections:
                product_sheet.append([
                    sku if first_row_for_sku else "",
                    total if first_row_for_sku else "",
                    category_name,
                    "",
                    "",
                    "",
                    "",
                    "No Corrections",
                ])
                first_row_for_sku = False
                continue

            for correction in corrections:
                product_sheet.append(
                    [
                        sku if first_row_for_sku else "",
                        total if first_row_for_sku else "",
                        category_name,
                        correction.get("system", ""),
                        correction.get("field", ""),
                        UnifiedRecordBuilder.normalize_part_number(correction.get("current_value", "")),
                        UnifiedRecordBuilder.normalize_part_number(correction.get("correct_value", "")),
                        correction.get("reason", ""),
                    ]
                )
                first_row_for_sku = False


def write_audit_report(summary_data):
    normalize_part_number = UnifiedRecordBuilder.normalize_part_number

    output_dir = _build_output_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"Audit_{timestamp}.xlsx"

    workbook = Workbook()
    workbook.remove(workbook.active)

    summary_sheet = workbook.create_sheet("Summary")
    summary_sheet.append(["Field", "Value"])
    summary_sheet.append(["Audit Type", summary_data.get("audit_type", "")])
    summary_sheet.append(["Date/Time", summary_data.get("generated_at", "")])
    summary_sheet.append(["Matching SKUs", summary_data.get("matching_count", 0)])
    summary_sheet.append(["Missing from Directus", summary_data.get("missing_from_directus_count", 0)])
    summary_sheet.append(["Missing from TrackVia", summary_data.get("missing_from_trackvia_count", 0)])
    summary_sheet.append(["Total Specification Mismatches", summary_data.get("total_mismatches", 0)])
    summary_sheet.append([])
    summary_sheet.append(["Tier 1 Field Summary", ""])
    for field_name, details in summary_data.get("tier1_summary", {}).items():
        summary_sheet.append(
            [
                field_name,
                f"comparisons={details.get('comparisons', 0)}; mismatches={details.get('mismatches', 0)}; status={details.get('status', 'PASS')}",
            ]
        )

    missing_products_sheet = workbook.create_sheet("Missing Products")
    missing_products_sheet.append(["SKU", "Missing From"])
    for sku in summary_data.get("missing_from_directus", []):
        missing_products_sheet.append([normalize_part_number(sku), "Directus"])
    for sku in summary_data.get("missing_from_trackvia", []):
        missing_products_sheet.append([normalize_part_number(sku), "TrackVia"])

    mismatches_sheet = workbook.create_sheet("Specification Mismatches")
    mismatches_sheet.append(["SKU", "Field", "TrackVia Value", "Directus Value"])
    for mismatch in summary_data.get("mismatches", []):
        mismatches_sheet.append(
            [
                normalize_part_number(mismatch.get("sku", "")),
                mismatch.get("field_display", ""),
                normalize_part_number(mismatch.get("trackvia_value", "")),
                normalize_part_number(mismatch.get("directus_value", "")),
            ]
        )

    mapping_sheet = workbook.create_sheet("German-US Mapping")
    mapping_sheet.append(["German Part Number", "US Part Number"])
    for german_number, us_number in summary_data.get("part_number_mapping", {}).items():
        mapping_sheet.append([
            normalize_part_number(german_number, preserve_leading_zeros=True),
            normalize_part_number(us_number),
        ])

    four_way_sheet = workbook.create_sheet("Four-Way Comparison")
    four_way_sheet.append(["SKU", "Field", "German Engineering", "TrackVia", "Directus", "US Catalog", "Status", "Reason"])
    four_way_comparisons = summary_data.get("four_way_comparisons", [])
    awg_comparison = next((comparison for comparison in four_way_comparisons if comparison.get("field") == "AWG"), None)
    if awg_comparison is not None:
        print(awg_comparison)

    conductors_comparison = next((comparison for comparison in four_way_comparisons if comparison.get("field") == "Conductors"), None)
    if conductors_comparison is not None:
        print(conductors_comparison)

    for comparison in summary_data.get("four_way_comparisons", []):
        field_name = comparison.get("field", "")
        is_part_number_field = field_name in {"Part Number", "US Part Number", "German Part Number"}

        sku_value = comparison.get("sku", "")
        german_value = comparison.get("german", "")
        trackvia_value = comparison.get("trackvia", "")
        directus_value = comparison.get("directus", "")
        us_catalog_value = comparison.get("us_catalog", "")

        if is_part_number_field:
            sku_value = normalize_part_number(sku_value)
            german_value = normalize_part_number(german_value, preserve_leading_zeros=True)
            trackvia_value = normalize_part_number(trackvia_value, preserve_leading_zeros=True)
            if normalize_part_number(directus_value, preserve_leading_zeros=True) != "N/A":
                directus_value = normalize_part_number(directus_value)
            if normalize_part_number(us_catalog_value, preserve_leading_zeros=True) != "N/A":
                us_catalog_value = normalize_part_number(us_catalog_value)

        four_way_sheet.append(
            [
                sku_value,
                field_name,
                german_value,
                trackvia_value,
                directus_value,
                us_catalog_value,
                comparison.get("status", ""),
                comparison.get("reason", ""),
            ]
        )

    workbook.save(report_path)
    return report_path.name
