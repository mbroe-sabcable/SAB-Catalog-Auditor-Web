import math

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


def _construction_record(german_row, trackvia_row, directus_row, us_catalog_row):
    return AuditRecord(
        sku="6542202",
        trackvia_row=trackvia_row,
        directus_row=directus_row,
        german_row=german_row,
        us_catalog_row=us_catalog_row,
    )


def _construction_results(record):
    comparisons = FourWayComparison().compare([record])
    return {
        item["field"]: item
        for item in comparisons
        if item["field"] in {"Conductors", "Pairs"}
    }


def test_pairs_and_conductors_are_equivalent_for_construction():
    results = _construction_results(
        _construction_record(
            {"Pairs": "2", "No. of cores": ""},
            {"part_cond_no_ground": "4"},
            {"part_cond_no_ground": "4"},
            {"Conductors": "4"},
        )
    )

    assert results["Conductors"]["german"] is None
    assert results["Pairs"]["german"] == 2
    assert results["Conductors"]["status"] == "PASS"
    assert results["Pairs"]["status"] == "PASS"


def test_conflicting_pairs_and_conductors_fail_construction_comparison():
    results = _construction_results(
        _construction_record(
            {"Pairs": "2", "No. of cores": ""},
            {"part_cond_no_ground": "6"},
            {"part_cond_no_ground": "6"},
            {"Conductors": "6"},
        )
    )

    assert results["Conductors"]["status"] == "FAIL"
    assert results["Pairs"]["status"] == "FAIL"


def test_conductor_only_construction_remains_consistent():
    results = _construction_results(
        _construction_record(
            {"No. of cores": "4"},
            {"part_cond_no_ground": "4"},
            {"part_cond_no_ground": "4"},
            {"Conductors": "4"},
        )
    )

    assert results["Conductors"]["status"] == "PASS"
    assert results["Pairs"]["status"] == "PASS"


def test_pair_only_construction_remains_consistent():
    results = _construction_results(
        _construction_record(
            {"Pairs": "4", "No. of cores": ""},
            {"part_pair_count": "4"},
            {"part_pair_count": "4"},
            {"Conductors": float("nan"), "Pairs": "4"},
        )
    )

    assert all(
        value is None or (isinstance(value, float) and math.isnan(value))
        for value in [
            results["Conductors"]["german"],
            results["Conductors"]["trackvia"],
            results["Conductors"]["directus"],
            results["Conductors"]["us_catalog"],
        ]
    )
    assert [
        results["Pairs"][source]
        for source in ["german", "trackvia", "directus", "us_catalog"]
    ] == [4, 4, 4, 4]
    assert results["Conductors"]["status"] == "PASS"
    assert results["Pairs"]["status"] == "PASS"
