from importers.field_mapper import FieldMapper
import math
import re


class FourWayComparison:
    def _to_number(self, value):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return value

        text = str(value).strip()
        if not text:
            return None

        normalized = text.replace(",", "")
        match = re.search(r"-?\d+(?:\.\d+)?", normalized)
        if not match:
            return None

        number_text = match.group(0)
        if "." in number_text:
            try:
                return float(number_text)
            except ValueError:
                return None

        try:
            return int(number_text)
        except ValueError:
            return None

    def _first_populated_numeric(self, row, field_names):
        if row is None:
            return None

        for field_name in field_names:
            if field_name not in row:
                continue

            value = row.get(field_name)

            if value is None:
                continue

            if isinstance(value, float) and math.isnan(value):
                continue

            if isinstance(value, str) and not value.strip():
                continue

            try:
                if value != value:
                    continue
            except Exception:
                pass

            resolved = self._to_number(value)
            if resolved is not None:
                return resolved

        return None

    def _first_populated_raw(self, row, field_names):
        if row is None:
            return None

        for field_name in field_names:
            if field_name not in row:
                continue
            candidate = row.get(field_name)
            if candidate is None:
                continue

            if isinstance(candidate, float) and math.isnan(candidate):
                continue

            if isinstance(candidate, str) and not candidate.strip():
                continue

            # pandas-style missing scalar (e.g., pd.NA) can compare unequal to itself
            # but may not produce a plain bool; guard conversion errors.
            try:
                is_nan_like = candidate != candidate
                if isinstance(is_nan_like, bool) and is_nan_like:
                    continue
            except Exception:
                pass

            return candidate
        return None

    def _parse_german_cores(self, value):
        parsed = {
            "conductors": None,
            "pair_count": None,
            "triples": None,
        }

        if value is None:
            return parsed

        text = str(value).strip()
        if not text:
            return parsed

        lower_text = text.lower()
        leading_number = self._to_number(text)
        if leading_number is None:
            return parsed

        # German business rules for No. of cores:
        # - "x2" => pairs
        # - "x3" => triples
        # - otherwise => conductors
        if re.search(r"x\s*2\b", lower_text):
            parsed["pair_count"] = leading_number
        elif re.search(r"x\s*3\b", lower_text):
            parsed["triples"] = leading_number
        else:
            parsed["conductors"] = leading_number

        return parsed

    def _normalize_for_comparison(self, value):
        if value is None:
            return None

        if isinstance(value, bool):
            return str(value)

        if isinstance(value, (int, float)):
            return value

        text = str(value)
        if not text.strip():
            return text

        normalized = text.strip().replace(",", "")
        try:
            return float(normalized)
        except ValueError:
            return text

    def compare(self, records):
        mapper = FieldMapper()
        comparisons = []

        field_definitions = [
            ("part_number", "Part Number"),
            ("awg", "AWG"),
            ("conductors", "Conductors"),
            ("pair_count", "Pairs"),
            ("triples", "Triples"),
            ("od_inches", "OD (in.)"),
            ("od_mm", "OD (mm.)"),
            ("cable_weight", "Cable Weight (lbs/mft)"),
        ]

        for record in records:
            for field_key, field_name in field_definitions:
                trackvia_row = record.trackvia_row
                directus_row = record.directus_row

                mapping = mapper.get_mapping(field_key) or {}

                german_column = mapping.get("german")
                trackvia_column = mapping.get("trackvia")
                directus_column = mapping.get("directus")
                us_catalog_column = mapping.get("us_catalog")

                german_row = record.german_row
                us_catalog_row = record.us_catalog_row

                if field_key == "awg":
                    german_value = german_row.get(german_column) if german_row is not None and german_column else None
                    trackvia_value = trackvia_row.get("part_gauge") if trackvia_row is not None else None
                    directus_value = directus_row.get("part_gauge") if directus_row is not None else None
                    us_catalog_value = us_catalog_row.get(us_catalog_column) if us_catalog_row is not None and us_catalog_column else None
                elif field_key in {"conductors", "pair_count", "triples"}:
                    german_cores_value = german_row.get("No. of cores") if german_row is not None else None
                    german_parsed = self._parse_german_cores(german_cores_value)
                    german_value = german_parsed.get(field_key)

                    if field_key == "conductors":
                        conductor_fields = [
                            "part_cond_no_ground",
                            "part_cond_with_ground",
                        ]

                        trackvia_value = self._first_populated_numeric(
                            trackvia_row,
                            conductor_fields,
                        )

                        directus_value = self._first_populated_numeric(
                            directus_row,
                            conductor_fields,
                        )
                    elif field_key == "pair_count":
                        trackvia_value = self._first_populated_numeric(trackvia_row, ["part_pair_count"])
                        directus_value = self._first_populated_numeric(directus_row, ["part_pair_count"])
                    else:
                        trackvia_value = self._first_populated_numeric(trackvia_row, ["part_triples"])
                        directus_value = self._first_populated_numeric(directus_row, ["part_triples"])

                    us_catalog_value = self._to_number(us_catalog_row.get(us_catalog_column)) if us_catalog_row is not None and us_catalog_column else None
                elif field_key == "od_inches":
                    german_value = self._first_populated_raw(german_row, ["Outer-Ø- in", "Outer-¿- in"])
                    trackvia_value = self._first_populated_raw(trackvia_row, ["part_od_inches", "part_od_inches_10", "part_od_inches_range"])
                    directus_value = self._first_populated_raw(directus_row, ["part_od_inches", "part_od_inches_10", "part_od_inches_range"])
                    us_catalog_value = us_catalog_row.get("OD In") if us_catalog_row is not None else None
                elif field_key == "od_mm":
                    german_value = self._first_populated_raw(german_row, ["Outer-Ø- mm", "Outer-¿- mm"])
                    trackvia_value = self._first_populated_raw(trackvia_row, ["part_od_mm", "part_od_mm_10", "part_od_mm_range"])
                    directus_value = self._first_populated_raw(directus_row, ["part_od_mm", "part_od_mm_10", "part_od_mm_range"])
                    us_catalog_value = us_catalog_row.get("OD mm") if us_catalog_row is not None else None
                elif field_key == "cable_weight":
                    german_value = german_row.get("Cable weight Ålb/1000 ft") if german_row is not None else None
                    trackvia_value = trackvia_row.get("part_cable_weight") if trackvia_row is not None else None
                    directus_value = directus_row.get("part_cable_weight") if directus_row is not None else None
                    us_catalog_value = us_catalog_row.get("Cable weight Lbs") if us_catalog_row is not None else None
                else:
                    german_value = german_row.get(german_column) if german_row is not None and german_column else None
                    trackvia_value = trackvia_row.get(trackvia_column) if trackvia_row is not None and trackvia_column else None
                    directus_value = directus_row.get(directus_column) if directus_row is not None and directus_column else None
                    us_catalog_value = us_catalog_row.get(us_catalog_column) if us_catalog_row is not None and us_catalog_column else None

                populated_values = [
                    self._normalize_for_comparison(value)
                    for value in [german_value, trackvia_value, directus_value, us_catalog_value]
                    if value is not None
                ]
                status = "PASS" if len(set(populated_values)) <= 1 else "FAIL"

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
