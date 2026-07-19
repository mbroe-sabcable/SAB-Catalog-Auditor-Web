# SAB Catalog Auditor
## Audit Rules

---

# Purpose

This document defines every audit supported by the Catalog Auditor.

Each audit has a defined:

- Purpose
- Required input files
- Validation rules
- Output worksheets
- Expected behavior

Audit rules define what the application validates. The implementation defines how those rules are executed.

---

# General Audit Rules

All audits must follow these principles.

## Source Priority

Engineering specifications are always the source of truth.

Priority:

1. German Engineering
2. US Catalog
3. TrackVia
4. Directus

Exceptions must be explicitly documented.

---

## Normalization

Before any comparison:

- Normalize part numbers.
- Trim whitespace.
- Standardize numeric values.
- Normalize blank values.
- Normalize Yes/No values where applicable.

Raw values must never be compared directly.

---

## Missing Data

Blank values are considered valid only if blank is allowed for that field.

Missing required fields generate findings.

---

# Full Product Family Audit

## Purpose

Perform a complete comparison across every available source.

## Required Inputs

- German Engineering
- TrackVia
- Directus
- US Catalog

## Validation

### Product Existence

Verify every engineering product exists in:

- TrackVia
- Directus
- US Catalog

### Part Number

Normalized comparison only.

### Specifications

Compare all mapped specification fields.

Examples:

- Description
- AWG
- Conductors
- Jacket Material
- Shield
- Voltage
- Temperature
- Outer Diameter
- Copper Weight
- Approvals
- Search OD

### Missing Products

Identify products missing from any source.

### Field Differences

Identify mismatched values.

### Corrections

Generate recommended corrections.

## Outputs

- Dashboard
- Four-Way Comparison
- Missing Products
- Specification Mismatches
- Product Corrections
- German-US Mapping

---

# TrackVia vs Directus Audit

## Purpose

Verify synchronization between TrackVia and Directus.

## Required Inputs

- TrackVia
- Directus

## Validation

- Product existence
- Part numbers
- Product descriptions
- Marketing fields
- Search fields
- Metadata
- Downloads (if applicable)

## Outputs

- Dashboard
- Missing Products
- Field Mismatches
- Product Corrections

---

# Product Existence Audit

## Purpose

Determine whether every engineering SKU exists in every required system.

## Validation

Check presence only.

No field comparison.

## Outputs

- Missing Products
- Missing by Source
- Summary

---

# Directus QA Audit

## Purpose

Validate website data quality.

## Validation

Examples:

- Missing descriptions
- Missing images
- Missing downloads
- Missing SEO fields
- Missing search fields
- Missing specifications

## Outputs

- Dashboard
- QA Findings
- Corrections

---

# Catalog Verification Audit

## Purpose

Verify published catalog information against engineering data.

## Validation

Compare:

- Specifications
- Approvals
- Construction
- Ratings
- Dimensions

## Outputs

- Dashboard
- Specification Mismatches
- Corrections

---

# Finding Severity

## Critical

Engineering values differ.

Examples:

- AWG
- Conductors
- Voltage
- Temperature
- Part Number

---

## High

Product missing from a required source.

---

## Medium

Marketing information differs.

Examples:

- Description
- Search fields
- Keywords

---

## Low

Formatting differences.

Examples:

- Whitespace
- Capitalization
- Display formatting

---

# Product Corrections

Every correction should include:

- Part Number
- Source System
- Field Name
- Current Value
- Recommended Value
- Source of Truth

---

# Audit Completion

Every audit should report:

- Total products analyzed
- Products compared
- Missing products
- Mismatches
- Corrections generated
- Execution time

---

# Future Audits

Planned additions:

- Cross-family duplicate detection
- Orphan product detection
- Website filter validation
- Download validation
- Image validation
- PDF specification validation
- Category validation
