from audits.unified_record_builder import UnifiedRecordBuilder


def normalize_part_number(value, preserve_leading_zeros=False):
    return UnifiedRecordBuilder.normalize_part_number(
        value,
        preserve_leading_zeros=preserve_leading_zeros,
    )
