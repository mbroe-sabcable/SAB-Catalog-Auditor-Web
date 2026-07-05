from typing import Any, Dict, List

from audits.value_normalizer import ValueNormalizer


class OutlierDetector:
    @staticmethod
    def _get_debug_value(values: List[Dict[str, Any]], key: str) -> str:
        for item in values:
            if key in item and item.get(key) not in (None, ""):
                return str(item.get(key))
        return ""

    @staticmethod
    def analyze(values: List[Dict[str, Any]]) -> Dict[str, Any]:
        sku = OutlierDetector._get_debug_value(values, "sku")
        german_part_number = OutlierDetector._get_debug_value(values, "german_part_number")
        german_item = next((item for item in values if str(item.get("system", "")).lower() == "german"), None)
        german_record_found = bool(german_item is not None)
        if german_item is not None and "record_found" in german_item:
            german_record_found = bool(german_item.get("record_found"))

        source_system = None
        source_value = ""
        source_reason = "No source value found from German or US Catalog"
        for system_name in ["German", "US Catalog"]:
            matching_value = next((item for item in values if str(item.get("system", "")).lower() == system_name.lower()), None)
            if matching_value is None:
                continue

            normalized_value = ValueNormalizer.normalize(matching_value.get("value", ""))
            if normalized_value:
                source_system = system_name
                source_value = matching_value.get("value", "")
                if system_name == "German":
                    source_reason = "German selected because a normalized German value is present"
                else:
                    source_reason = "US Catalog selected because German is missing/blank and a normalized US Catalog value is present"
                break

        if not source_value:
            return {
                "status": "Manual Review Required",
                "source_of_truth": "",
                "systems_out_of_sync": [],
                "correct_value": "",
                "recommended_updates": [],
                "confidence": "Low",
                "recommendation": "Manual Review Required",
            }

        systems_out_of_sync = []
        recommended_updates = []
        for item in values:
            system_name = item.get("system", "")
            if not system_name or str(system_name).lower() == source_system.lower():
                continue

            normalized_value = ValueNormalizer.normalize(item.get("value", ""))
            if normalized_value and normalized_value != ValueNormalizer.normalize(source_value):
                systems_out_of_sync.append(system_name)
                recommended_updates.append(f"Update {system_name} to {source_value}")

        if not systems_out_of_sync:
            return {
                "status": "PASS",
                "source_of_truth": source_system,
                "systems_out_of_sync": [],
                "correct_value": source_value,
                "recommended_updates": [],
                "confidence": "High",
                "recommendation": "All values align with the source of truth.",
            }

        return {
            "status": "OUTLIER",
            "source_of_truth": source_system,
            "systems_out_of_sync": systems_out_of_sync,
            "correct_value": source_value,
            "recommended_updates": recommended_updates,
            "confidence": "High",
            "recommendation": "; ".join(recommended_updates),
        }
