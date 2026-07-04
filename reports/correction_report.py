def build_correction_recommendations(mismatches):
    recommendations = []
    for mismatch in mismatches:
        source_of_truth = mismatch.get("source_of_truth", "")
        current_value = mismatch.get("directus_value", "")

        if source_of_truth == "German":
            correct_value = mismatch.get("german_value", "")
            reason = "German Engineering is the source of truth"
        elif source_of_truth == "TrackVia":
            correct_value = mismatch.get("trackvia_value", "")
            reason = "TrackVia is the source of truth"
        else:
            correct_value = ""
            reason = "Manual Review Required"

        if not correct_value:
            reason = "Manual Review Required"
            correct_value = ""

        recommendations.append(
            {
                "sku": mismatch.get("sku", ""),
                "system": "Directus",
                "field": mismatch.get("field_display", ""),
                "current_value": current_value,
                "correct_value": correct_value,
                "reason": reason,
                "source_of_truth": source_of_truth,
            }
        )
    return recommendations
