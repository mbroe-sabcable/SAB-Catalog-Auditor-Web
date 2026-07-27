from audits.comparison.specifications import compare_specifications


class TrackViaVsDirectusAudit:
    """Runs TrackVia vs Directus specification checks."""

    def run(self, trackvia_df, directus_df, field_mapper):
        return compare_specifications(trackvia_df, directus_df, field_mapper)
