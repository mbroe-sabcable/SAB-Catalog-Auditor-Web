from importers.field_mapper import FieldMapper


class FourWayComparison:
    def compare(self, records):
        mapper = FieldMapper()
        comparisons = []
        first_comparison_printed = False

        field_definitions = [
            ("part_number", "Part Number"),
            ("awg", "AWG"),
            ("conductors", "Conductors"),
            ("pair_count", "Pairs"),
            ("od_inches", "OD (in.)"),
            ("od_mm", "OD (mm.)"),
            ("cable_weight", "Cable Weight (lbs/mft)"),
        ]

        for record in records:
            for field_key, field_name in field_definitions:
                mapping = mapper.get_mapping(field_key) or {}

                german_column = mapping.get("german")
                trackvia_column = mapping.get("trackvia")
                directus_column = mapping.get("directus")
                us_catalog_column = mapping.get("us_catalog")

                german_row = record.german_row
                trackvia_row = record.trackvia_row
                directus_row = record.directus_row
                us_catalog_row = record.us_catalog_row

                german_value = german_row.get(german_column) if german_row is not None and german_column else None
                trackvia_value = trackvia_row.get(trackvia_column) if trackvia_row is not None and trackvia_column else None
                directus_value = directus_row.get(directus_column) if directus_row is not None and directus_column else None
                if field_key == "od_inches":
                    directus_value = None
                    populated_directus_od_values = []
                    if directus_row is not None:
                        for directus_od_field in ["part_od_inches", "part_od_inches_10", "part_od_inches_range"]:
                            candidate = directus_row.get(directus_od_field)
                            if candidate is not None:
                                populated_directus_od_values.append(candidate)

                    if len(populated_directus_od_values) == 1:
                        directus_value = populated_directus_od_values[0]
                    elif len(populated_directus_od_values) == 0:
                        directus_value = None
                    else:
                        directus_value = populated_directus_od_values[0]
                us_catalog_value = us_catalog_row.get(us_catalog_column) if us_catalog_row is not None and us_catalog_column else None

                populated_values = [
                    value
                    for value in [german_value, trackvia_value, directus_value, us_catalog_value]
                    if value is not None
                ]
                status = "PASS" if len(set(populated_values)) <= 1 else "FAIL"

                if field_key == "part_number" and not first_comparison_printed:
                    print("================ FIRST COMPARISON ================")
                    print()
                    print("sku:")
                    print(record.sku)
                    print()
                    print("field:")
                    print(field_name)
                    print()
                    print("german:")
                    print(german_value)
                    print()
                    print("trackvia:")
                    print(trackvia_value)
                    print()
                    print("directus:")
                    print(directus_value)
                    print()
                    print("us_catalog:")
                    print(us_catalog_value)
                    print()
                    print("status:")
                    print(status)
                    print()
                    print("==================================================")
                    first_comparison_printed = True

                comparisons.append(
                    {
                        "sku": record.sku,
                        "field": field_name,
                        "german": german_value,
                        "trackvia": trackvia_value,
                        "directus": directus_value,
                        "us_catalog": us_catalog_value,
                        "status": status,
                    }
                )

        return comparisons
