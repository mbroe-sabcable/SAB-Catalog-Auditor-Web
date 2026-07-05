from dataclasses import dataclass
from typing import Optional


@dataclass
class AuditRecord:
    sku: Optional[str] = None
    german_part: Optional[str] = None
    trackvia_row: Optional[dict] = None
    directus_row: Optional[dict] = None
    german_row: Optional[dict] = None
    us_catalog_row: Optional[dict] = None


class UnifiedRecordBuilder:
    @staticmethod
    def build(trackvia_df, directus_df, german_df, us_catalog_df):
        records = []

        def _normalize_column_name(column_name):
            return "".join(ch.lower() for ch in str(column_name) if ch.isalnum())

        def _get_column_by_expected_name(df, expected_column_name):
            if df is None or not expected_column_name:
                return None

            expected = _normalize_column_name(expected_column_name)
            for column in df.columns:
                if _normalize_column_name(column) == expected:
                    return column
            return None

        trackvia_column = None
        directus_column = None
        german_column = None
        us_catalog_column = None

        if trackvia_df is not None:
            trackvia_column = next((column for column in trackvia_df.columns if str(column).lower() == "sku"), None)
        if directus_df is not None:
            directus_column = next((column for column in directus_df.columns if str(column).lower() == "sku"), None)
        if german_df is not None:
            german_column = _get_column_by_expected_name(german_df, "item no.")
        if us_catalog_df is not None:
            us_catalog_column = _get_column_by_expected_name(us_catalog_df, "part #")

        if trackvia_df is None:
            return records

        trackvia_lookup = {}
        for _, row in trackvia_df.iterrows():
            sku = str(row[trackvia_column]).strip() if trackvia_column is not None and row[trackvia_column] is not None else ""
            trackvia_lookup[sku] = row

        directus_lookup = {}
        if directus_df is not None and directus_column is not None:
            for _, row in directus_df.iterrows():
                sku = str(row[directus_column]).strip() if row[directus_column] is not None else ""
                directus_lookup[sku] = row

        german_lookup = {}
        if german_df is not None and german_column is not None:
            for _, row in german_df.iterrows():
                german_part = str(row[german_column]).strip() if row[german_column] is not None else ""
                german_lookup[german_part] = row

        us_catalog_lookup = {}
        if us_catalog_df is not None and us_catalog_column is not None:
            for _, row in us_catalog_df.iterrows():
                us_part_number = str(row[us_catalog_column]).strip() if row[us_catalog_column] is not None else ""
                us_catalog_lookup[us_part_number] = row

        for sku, row in trackvia_lookup.items():
            if not sku:
                continue

            trackvia_value = str(row[trackvia_column]).strip() if trackvia_column is not None and row[trackvia_column] is not None else None
            trackvia_row_dict = row.to_dict() if hasattr(row, "to_dict") else None
            part_german_column = _get_column_by_expected_name(trackvia_df, "part_german")
            part_german_raw = row[part_german_column] if part_german_column is not None else None
            if part_german_raw is None:
                part_german_value = None
            else:
                part_german_text = str(part_german_raw).strip()
                part_german_value = part_german_text if part_german_text and part_german_text.lower() != "nan" else None
            directus_row_dict = None
            german_row_dict = None
            us_catalog_row_dict = None

            if sku in directus_lookup:
                directus_row = directus_lookup[sku]
                directus_row_dict = directus_row.to_dict() if hasattr(directus_row, "to_dict") else None

            german_lookup_key = part_german_value if part_german_value else sku
            if german_lookup_key and german_lookup_key in german_lookup:
                german_row = german_lookup[german_lookup_key]
                german_row_dict = german_row.to_dict() if hasattr(german_row, "to_dict") else None

            if trackvia_value and trackvia_value in us_catalog_lookup:
                us_catalog_row = us_catalog_lookup[trackvia_value]
                us_catalog_row_dict = us_catalog_row.to_dict() if hasattr(us_catalog_row, "to_dict") else None

            audit_record = AuditRecord(
                sku=sku,
                german_part=part_german_value,
                trackvia_row=trackvia_row_dict,
                directus_row=directus_row_dict,
                german_row=german_row_dict,
                us_catalog_row=us_catalog_row_dict,
            )

            records.append(audit_record)

        return records
