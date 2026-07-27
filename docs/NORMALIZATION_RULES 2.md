# Normalization Rules

## Goals

- Eliminate false mismatches caused by type/format differences.
- Ensure identifiers compare consistently across sources.

## Part Number Rules

- Normalize before lookup, comparison, and report output.
- `2592002`, `2592002.0`, and `2592002.000` must compare equal.
- Preserve leading zeros only in approved display contexts.

Reference behavior:

```text
normalize_part_number("2592002.0") -> "2592002"
normalize_part_number("2592002")   -> "2592002"
normalize_part_number(2592002)       -> "2592002"
```

Implementation reference: `audits/unified_record_builder.py`.

## SKU Rules

- Normalize SKU keys consistently for dictionary insertion and retrieval.
- Do not mix raw and normalized keys in lookup paths.

## Missing Value Rules

- Normalize empty/null values to a consistent representation.
- Use explicit sentinel values only for display/reporting layers.

## Comparison Rules

- Never compare raw part number values.
- Normalize both sides before equality checks.
- Missing values should route to missing-reason paths, not mismatch paths.

## Reporting Rules

- Reports should display normalized identifiers to remove `.0` artifacts.
- If a display context requires leading zeros, preserve only in that context.
