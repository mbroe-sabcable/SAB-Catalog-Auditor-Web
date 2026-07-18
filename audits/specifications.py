import pandas as pd

from audits.unified_record_builder import UnifiedRecordBuilder


def _normalize_column_name(column_name):
    return "".join(ch.lower() for ch in str(column_name) if ch.isalnum())


def _get_mapped_column(df, source_name, field_mapper):
    if df is None:
        return None

    expected_column = field_mapper.get_part_number_mapping(source_name)
    for column in df.columns:
        if _normalize_column_name(column) == _normalize_column_name(expected_column):
            return column
    return None


def compare_specifications(trackvia_df, directus_df, field_mapper):
    normalize_part_number = UnifiedRecordBuilder.normalize_part_number

    trackvia_column = _get_mapped_column(trackvia_df, "trackvia", field_mapper)
    directus_column = _get_mapped_column(directus_df, "directus", field_mapper)

    if trackvia_column is None or directus_column is None:
        return []

    trackvia_lookup = {}
    for _, row in trackvia_df.iterrows():
        sku = normalize_part_number(row[trackvia_column])
        if not sku:
            continue
        trackvia_lookup[sku] = row

    mismatches = []
    directus_skus = [normalize_part_number(value) for value in directus_df[directus_column].tolist()]
    for sku, row in trackvia_lookup.items():
        if sku not in directus_skus:
            continue

        directus_row = directus_df.loc[directus_df[directus_column].apply(normalize_part_number) == sku].iloc[0]
        for field in field_mapper.get_specification_mappings():
            trackvia_field = field.get("trackvia")
            directus_field = field.get("directus")
            if trackvia_field is None or directus_field is None:
                continue

            trackvia_value = row.get(trackvia_field)
            directus_value = directus_row.get(directus_field)
            if pd.isna(trackvia_value) and pd.isna(directus_value):
                continue

            normalized_trackvia = str(trackvia_value).strip() if pd.notna(trackvia_value) else ""
            normalized_directus = str(directus_value).strip() if pd.notna(directus_value) else ""
            if normalized_trackvia == normalized_directus:
                continue

            mismatches.append(
                {
                    "sku": sku,
                    "field_key": field.get("key"),
                    "field_display": field.get("display"),
                    "trackvia_value": normalized_trackvia,
                    "directus_value": normalized_directus,
                }
            )

    return mismatches
