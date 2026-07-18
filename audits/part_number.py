import pandas as pd
import re

from audits.unified_record_builder import UnifiedRecordBuilder


def _normalize_column_name(column_name):
    return "".join(ch.lower() for ch in str(column_name) if ch.isalnum())


def _find_column(df, expected_columns):
    if df is None:
        return None

    expected_names = {_normalize_column_name(column) for column in expected_columns}
    for column in df.columns:
        if _normalize_column_name(column) in expected_names:
            return column
    return None


def build_part_number_mapping(trackvia_df):
    if trackvia_df is None:
        return {}

    german_column = _find_column(trackvia_df, ["part_german"])
    sku_column = _find_column(trackvia_df, ["sku"])

    if german_column is None or sku_column is None:
        return {}

    mapping = {}
    for _, row in trackvia_df.iterrows():
        german_value = UnifiedRecordBuilder.normalize_part_number(row[german_column]) if pd.notna(row[german_column]) else ""
        sku_value = UnifiedRecordBuilder.normalize_part_number(row[sku_column]) if pd.notna(row[sku_column]) else ""

        # Preserve leading zeros in the exported German mapping when available in
        # the textual record identifier while still using normalized join values.
        record_id_column = _find_column(trackvia_df, ["Record ID"])
        if record_id_column is not None and pd.notna(row[record_id_column]):
            record_id_text = str(row[record_id_column]).strip()
            match = re.search(r"\d+", record_id_text)
            if match:
                record_id_digits = match.group(0)
                if (
                    record_id_digits.startswith("0")
                    and UnifiedRecordBuilder.normalize_part_number(record_id_digits) == german_value
                ):
                    german_value = UnifiedRecordBuilder.normalize_part_number(
                        record_id_digits,
                        preserve_leading_zeros=True,
                    )

        if not german_value:
            continue

        if german_value not in mapping:
            mapping[german_value] = sku_value

    return mapping
