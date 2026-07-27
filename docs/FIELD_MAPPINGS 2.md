# Field Mappings

This document maps source fields to canonical audit fields used by comparison logic.

## Canonical Field Naming

- Use one canonical name per logical attribute.
- Canonical names should remain stable across audits and report versions.

Core canonical identifiers:
- `sku`
- `us_part_number`
- `german_part_number`

## Source Mapping Matrix

### German Engineering -> Canonical

- Item No. -> german_part_number
- Engineering specification fields -> canonical spec fields
- Approval fields -> approvals

### TrackVia -> Canonical

- SKU -> sku
- part_german -> german_part_number
- Operational product fields -> canonical product/spec fields

### Directus -> Canonical

- sku -> sku
- Published content fields -> canonical description/content fields
- Filter/facet fields -> canonical filter fields

### US Catalog -> Canonical

- Part # -> us_part_number
- Customer-visible specification fields -> canonical spec fields

## Mapping Rules

- Normalize source header names during lookup to avoid case/punctuation drift.
- Keep parsing/transformation logic documented beside mapping entries.
- Record known source quirks (missing columns, alternate names, type drift).
- Do not embed business comparison rules inside mapping code.

## Mapping Conventions

- Keep one canonical name per logical field.
- Document transformation or parsing rules beside each mapping.
- Mark source-specific quirks explicitly.
