# Report Specification

## Workbook Requirements

Required worksheets:
- Dashboard
- Four-Way Comparison
- Specification Mismatches
- Missing Products
- German-US Mapping
- Product Corrections

Dashboard should be first.

## Worksheet Requirements

### Dashboard

Required sections:
- Audit type
- Date and time
- Input source file names
- Summary counts (pass/fail/missing)
- Worksheet index/navigation list

### Four-Way Comparison

Required columns:
- SKU
- Field name
- TrackVia value
- Directus value
- German Engineering value
- US Catalog value
- Status
- Reason

### Specification Mismatches

Required columns:
- SKU
- Field
- Source value
- Target value
- Reason

### Missing Products

Required columns:
- SKU or identifier
- Missing in system
- Source context
- Reason

### German-US Mapping

Required columns:
- German part number
- US part number
- Mapping source

### Product Corrections

Required columns:
- SKU
- Target system
- Field
- Current value
- Recommended value
- Reason

## Formatting Requirements

- Header row styling with SAB visual identity
- Freeze top row
- Auto filter
- Auto-size columns
- Thin borders

## Content Requirements

- Use normalized identifiers in output
- Include reason fields for missing/mismatch outcomes
- Keep correction rows actionable and traceable to source values

## Validation Requirements

- Workbook must contain all required worksheets.
- Dashboard must be the first sheet.
- Header row must be present for every worksheet.
- Identifier columns must not contain float-string artifacts for integer-like values.
