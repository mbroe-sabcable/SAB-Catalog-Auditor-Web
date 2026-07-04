class FieldMapper:
    def __init__(self):
        self.field_mapping = [
            {
                "key": "part_number",
                "display": "Part Number",
                "trackvia": "sku",
                "directus": "sku",
                "german": "item no.",
                "us_catalog": "Part #",
                "source_of_truth": "TrackVia",
            },
            {
                "key": "awg",
                "display": "AWG",
                "trackvia": "part_gauge",
                "directus": "part_gauge",
                "german": "AWG",
                "us_catalog": "AWG",
                "source_of_truth": "German",
            },
            {
                "key": "conductors",
                "display": "Conductors",
                "trackvia": "part_conductors",
                "directus": "part_conductors",
                "german": None,
                "us_catalog": None,
                "source_of_truth": "German",
            },
            {
                "key": "ground_wire",
                "display": "Ground Wire",
                "trackvia": "part_ground_wire",
                "directus": "part_ground_wire",
                "german": None,
                "us_catalog": None,
                "source_of_truth": "German",
            },
            {
                "key": "pair_count",
                "display": "Pair Count",
                "trackvia": "part_pair_count",
                "directus": "part_pair_count",
                "german": None,
                "us_catalog": None,
                "source_of_truth": "German",
            },
            {
                "key": "triple_count",
                "display": "Triple Count",
                "trackvia": "part_triples",
                "directus": "part_triples",
                "german": None,
                "us_catalog": None,
                "source_of_truth": "German",
            },
            {
                "key": "od_inches",
                "display": "OD (Inches)",
                "trackvia": "part_od_inches",
                "directus": "part_od_inches",
                "german": None,
                "us_catalog": "OD In",
                "source_of_truth": "German",
            },
            {
                "key": "od_mm",
                "display": "OD (mm)",
                "trackvia": "part_od_mm",
                "directus": "part_od_mm",
                "german": None,
                "us_catalog": "OD mm",
                "source_of_truth": "German",
            },
            {
                "key": "cable_weight",
                "display": "Cable Weight",
                "trackvia": "part_cable_weight",
                "directus": "part_cable_weight",
                "german": None,
                "us_catalog": None,
                "source_of_truth": "German",
            },
        ]

    def get_mapping(self, field_name):
        for field in self.field_mapping:
            if field["key"] == field_name:
                return field
        return None

    def get_part_number_mapping(self, source_name):
        return self.get_mapping("part_number")[source_name]

    def get_specification_mappings(self):
        return [field for field in self.field_mapping if field["key"] != "part_number"]
