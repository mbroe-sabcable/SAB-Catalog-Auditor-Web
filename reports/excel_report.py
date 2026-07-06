from datetime import datetime
from pathlib import Path

from openpyxl import Workbook


def _build_output_dir():
    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _append_product_corrections_sheet(workbook, product_corrections):
    product_sheet = workbook.create_sheet("Product Corrections")
    product_sheet.append(["SKU", "Total Corrections", "Category", "System", "Field", "Current Value", "Correct Value", "Reason"])

    for product in product_corrections:
        sku = product.get("sku", "")
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
                        correction.get("current_value", ""),
                        correction.get("correct_value", ""),
                        correction.get("reason", ""),
                    ]
                )
                first_row_for_sku = False


def write_audit_report(summary_data):
    print("ENTERED write_audit_report")
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
        missing_products_sheet.append([sku, "Directus"])
    for sku in summary_data.get("missing_from_trackvia", []):
        missing_products_sheet.append([sku, "TrackVia"])

    mismatches_sheet = workbook.create_sheet("Specification Mismatches")
    mismatches_sheet.append(["SKU", "Field", "TrackVia Value", "Directus Value"])
    for mismatch in summary_data.get("mismatches", []):
        mismatches_sheet.append(
            [
                mismatch.get("sku", ""),
                mismatch.get("field_display", ""),
                mismatch.get("trackvia_value", ""),
                mismatch.get("directus_value", ""),
            ]
        )

    mapping_sheet = workbook.create_sheet("German-US Mapping")
    mapping_sheet.append(["German Part Number", "US Part Number"])
    for german_number, us_number in summary_data.get("part_number_mapping", {}).items():
        mapping_sheet.append([german_number, us_number])

    four_way_sheet = workbook.create_sheet("Four-Way Comparison")
    four_way_sheet.append(["SKU", "Field", "German Engineering", "TrackVia", "Directus", "US Catalog", "Status"])
    four_way_comparisons = summary_data.get("four_way_comparisons", [])
    if four_way_comparisons:
        print("================ EXCEL INPUT ================")
        print()
        print("Number of comparisons:")
        print(len(summary_data["four_way_comparisons"]))
        print()
        print("First comparison:")
        print(summary_data["four_way_comparisons"][0])
        print()
        print("=============================================")
    for comparison in summary_data.get("four_way_comparisons", []):
        four_way_sheet.append(
            [
                comparison.get("sku", ""),
                comparison.get("field", ""),
                comparison.get("german", ""),
                comparison.get("trackvia", ""),
                comparison.get("directus", ""),
                comparison.get("us_catalog", ""),
                comparison.get("status", ""),
            ]
        )

    workbook.save(report_path)
    return report_path.name
