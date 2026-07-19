from audits.unified_record_builder import UnifiedRecordBuilder


def test_normalize_part_number_equivalent_values():
    assert UnifiedRecordBuilder.normalize_part_number("2592002.0") == "2592002"
    assert UnifiedRecordBuilder.normalize_part_number("2592002") == "2592002"
    assert UnifiedRecordBuilder.normalize_part_number(2592002) == "2592002"
