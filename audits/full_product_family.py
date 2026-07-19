from audits.four_way_comparison import FourWayComparison


class FullProductFamilyAudit:
    """Compatibility wrapper for the full product family audit flow."""

    def __init__(self):
        self._comparison = FourWayComparison()

    def run(self, records):
        return self._comparison.compare(records)
