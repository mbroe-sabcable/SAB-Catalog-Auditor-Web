import pandas as pd


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
        german_value = str(row[german_column]).strip() if pd.notna(row[german_column]) else ""
        sku_value = str(row[sku_column]).strip() if pd.notna(row[sku_column]) else ""

        if not german_value:
            continue

        if german_value not in mapping:
            mapping[german_value] = sku_value

    return mapping
