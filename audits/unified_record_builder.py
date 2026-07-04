from dataclasses import dataclass
from typing import Optional


@dataclass
class AuditRecord:
    sku: Optional[str] = None
    german_part: Optional[str] = None
    trackvia: Optional[str] = None
    directus: Optional[str] = None
    german: Optional[str] = None
    us_catalog: Optional[str] = None


class UnifiedRecordBuilder:
    @staticmethod
    def build(trackvia_df, directus_df, german_df, us_catalog_df):
        records = []

        trackvia_column = None
        directus_column = None
        german_column = None
        us_catalog_column = None

        if trackvia_df is not None:
            trackvia_column = next((column for column in trackvia_df.columns if str(column).lower() == "sku"), None)
        if directus_df is not None:
            directus_column = next((column for column in directus_df.columns if str(column).lower() == "sku"), None)
        if german_df is not None:
            german_column = next((column for column in german_df.columns if str(column).lower() == "item no."), None)
        if us_catalog_df is not None:
            us_catalog_column = next((column for column in us_catalog_df.columns if str(column).lower() == "part #"), None)

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
            part_german_value = str(row["part_german"]).strip() if "part_german" in row and row["part_german"] is not None else None
            directus_value = None
            german_value = None
            us_catalog_value = None

            if sku in directus_lookup:
                directus_row = directus_lookup[sku]
                directus_value = str(directus_row[directus_column]).strip() if directus_column is not None and directus_row[directus_column] is not None else None

            if part_german_value and part_german_value in german_lookup:
                german_value = str(german_lookup[part_german_value][german_column]).strip() if german_column is not None else None

            if trackvia_value and trackvia_value in us_catalog_lookup:
                us_catalog_value = str(us_catalog_lookup[trackvia_value][us_catalog_column]).strip() if us_catalog_column is not None else None

            records.append(
                AuditRecord(
                    sku=sku,
                    german_part=part_german_value,
                    trackvia=trackvia_value,
                    directus=directus_value,
                    german=german_value,
                    us_catalog=us_catalog_value,
                )
            )

        return records
