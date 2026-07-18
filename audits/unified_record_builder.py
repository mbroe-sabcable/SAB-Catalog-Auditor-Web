from dataclasses import dataclass
from typing import Optional
import re


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
    def normalize_part_number(value, preserve_leading_zeros=False):
        if value is None:
            return ""

        try:
            if value != value:
                return ""
        except Exception:
            pass

        text = str(value).strip()
        if not text:
            return ""

        normalized = text.replace(",", "")
        if re.fullmatch(r"[+-]?\d+(?:\.\d+)?", normalized):
            if (
                preserve_leading_zeros
                and isinstance(value, str)
                and re.fullmatch(r"\d+", normalized)
                and len(normalized) > 1
                and normalized.startswith("0")
            ):
                return normalized

            sign = ""
            number = normalized
            if number.startswith(("+", "-")):
                sign = number[0]
                number = number[1:]

            if "." in number:
                whole, fraction = number.split(".", 1)
                if not fraction or set(fraction) <= {"0"}:
                    number = whole
                else:
                    number = f"{whole}.{fraction.rstrip('0')}"

            if "." not in number:
                number = number.lstrip("0") or "0"

            return f"{sign}{number}"

        return text

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

        normalize_part_number = UnifiedRecordBuilder.normalize_part_number

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
            sku = normalize_part_number(row[trackvia_column]) if trackvia_column is not None else ""
            trackvia_lookup[sku] = row

        directus_lookup = {}
        if directus_df is not None and directus_column is not None:
            for _, row in directus_df.iterrows():
                sku = normalize_part_number(row[directus_column])
                directus_lookup[sku] = row

        german_lookup = {}
        if german_df is not None and german_column is not None:
            for _, row in german_df.iterrows():
                german_part = normalize_part_number(row[german_column])
                german_lookup[german_part] = row

        us_catalog_lookup = {}
        if us_catalog_df is not None and us_catalog_column is not None:
            for _, row in us_catalog_df.iterrows():
                us_part_number = normalize_part_number(row[us_catalog_column])
                us_catalog_lookup[us_part_number] = row

        for sku, row in trackvia_lookup.items():
            if not sku:
                continue

            trackvia_value = normalize_part_number(row[trackvia_column]) if trackvia_column is not None else ""
            trackvia_row_dict = row.to_dict() if hasattr(row, "to_dict") else None
            part_german_column = _get_column_by_expected_name(trackvia_df, "part_german")
            part_german_raw = row[part_german_column] if part_german_column is not None else None
            part_german_value = normalize_part_number(part_german_raw)
            if not part_german_value or part_german_value.lower() == "nan":
                part_german_value = None
            directus_row_dict = None
            german_row_dict = None
            us_catalog_row_dict = None

            if sku in directus_lookup:
                directus_row = directus_lookup[sku]
                directus_row_dict = directus_row.to_dict() if hasattr(directus_row, "to_dict") else None

            german_lookup_key = part_german_value if part_german_value else normalize_part_number(sku)
            german_lookup_contains_key = bool(german_lookup_key and german_lookup_key in german_lookup)

            us_lookup_key = normalize_part_number(trackvia_value)
            us_lookup_contains_key = bool(us_lookup_key and us_lookup_key in us_catalog_lookup)

            german_row_dict = german_lookup.get(german_lookup_key)
            if german_row_dict is not None:
                german_row_dict = german_row_dict.to_dict() if hasattr(german_row_dict, "to_dict") else german_row_dict

            if us_lookup_contains_key:
                us_catalog_row = us_catalog_lookup[us_lookup_key]
                us_catalog_row_dict = us_catalog_row.to_dict() if hasattr(us_catalog_row, "to_dict") else None

            audit_record = AuditRecord(
                sku=sku,
                german_part=part_german_value,
                trackvia_row=trackvia_row_dict,
                directus_row=directus_row_dict,
                german_row=german_row_dict,
                us_catalog_row=us_catalog_row_dict,
            )

            print("Assigned german_row:")
            print(german_row_dict is not None)
            print()
            print("Assigned us_catalog_row:")
            print(us_catalog_row_dict is not None)
            print()

            records.append(audit_record)

        return records
