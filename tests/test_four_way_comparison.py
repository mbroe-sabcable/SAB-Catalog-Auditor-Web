import pytest

from audits.four_way_comparison import FourWayComparison
from audits.unified_record_builder import AuditRecord


@pytest.mark.skip(reason="Pending four-way comparison regression coverage")
def test_four_way_comparison_placeholder():
    assert True


@pytest.mark.parametrize(
    "header",
    [
        "Cable weight ≈ lbs/mft",
        "Cable weight Ålb/1000 ft",
        "Cable weight Alb/1000 ft",
        "Cable weight approx.lb/mft",
    ],
)
def test_cable_weight_resolves_german_engineering_header_variants(header):
    comparisons = FourWayComparison().compare(
        [
            AuditRecord(
                sku="SABIX A 146 FRNC",
                german_row={header: "42"},
                trackvia_row={"part_cable_weight": "42"},
                directus_row={"part_cable_weight": "42"},
                us_catalog_row={"Cable weight Lbs": "42"},
            )
        ]
    )

    cable_weight = next(item for item in comparisons if item["field"] == "Cable Weight (lbs/mft)")
    assert cable_weight["german"] == "42"


@pytest.mark.parametrize(
    ("header", "field", "value"),
    [
        ("Outer-�- in", "OD (in.)", "0.083"),
        ("Outer-�- mm", "OD (mm.)", "2.1"),
    ],
)
def test_od_resolves_german_engineering_encoding_variant(header, field, value):
    comparisons = FourWayComparison().compare(
        [
            AuditRecord(
                sku="SABIX A 146 FRNC",
                german_row={header: value},
                trackvia_row={},
                directus_row={},
                us_catalog_row={},
            )
        ]
    )

    comparison = next(item for item in comparisons if item["field"] == field)
    assert comparison["german"] == value
