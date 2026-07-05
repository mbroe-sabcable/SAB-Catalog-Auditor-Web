from typing import Any, Dict, Optional


class AuditRules:
    ENGINEERING_FIELDS = {
        "awg",
        "conductors",
        "ground_wire",
        "pair_count",
        "triple_count",
        "od_inches",
        "od_mm",
        "cable_weight",
    }

    @staticmethod
    def get_source_of_truth(field_key: str, german_record_exists: bool) -> str:
        if field_key == "part_number":
            return "TrackVia.sku"
        if field_key == "german_part_number":
            return "TrackVia.part_german"
        if field_key in AuditRules.ENGINEERING_FIELDS:
            return "German Engineering" if german_record_exists else "US Catalog"
        return ""

    @staticmethod
    def get_correction_recommendation(field_key: str, source_value: Any, system_value: Any, german_record_exists: bool) -> Optional[Dict[str, Any]]:
        if not field_key:
            return None

        source_of_truth = AuditRules.get_source_of_truth(field_key, german_record_exists)
        if not source_value:
            return {
                "status": "Manual Review Required",
                "source_of_truth": source_of_truth,
                "reason": "Manual Review Required",
            }

        if source_value == system_value:
            return None

        return {
            "status": "CORRECTION",
            "source_of_truth": source_of_truth,
            "correct_value": source_value,
            "reason": f"{source_of_truth} is the source of truth",
        }
