# SAB Catalog Auditor
## Project Architecture

---

# Purpose

The SAB Catalog Auditor is a desktop application that validates and compares product information across multiple SAB North America data sources.

Its primary purpose is to identify:

- Missing products
- Specification mismatches
- Product synchronization issues
- Catalog inconsistencies
- Recommended data corrections

The application is designed to improve product data quality before information reaches customers through catalogs, websites, distributors, or internal systems.

---

# High-Level Architecture

```text
CSV Files
	|
	v
Import and Validation
	|
	v
Unified Record Builder
	|
	v
Data Normalization
	|
	v
Audit Engine
	|
	v
Comparison and Corrections
	|
	v
Excel Report Generator
```

Each stage has a single responsibility.

---

# Application Structure

```text
SAB-Catalog-Auditor/

app/
	User interface

audits/
	Audit engine
	Comparison logic
	Validation

importers/
	CSV loading
	File validation

reports/
	Excel report generation

assets/
	Logos
	Images

config/
	Configuration
	Field mappings

docs/
	Documentation

tests/
	Automated testing
```

---

# Data Sources

The Catalog Auditor compares information from four independent systems.

## German Engineering

Engineering source of truth.

Contains:

- Engineering specifications
- Construction details
- Approvals
- Dimensions
- Electrical properties

Engineering data always takes precedence when determining correct specifications.

---

## TrackVia

Internal product management system.

Contains:

- Product information
- Operational fields
- Internal product management data

---

## Directus

Website Content Management System.

Contains:

- Published website content
- Marketing fields
- Search fields
- Downloads
- Product metadata

---

## US Catalog

Customer-facing product catalog.

Contains published product information.

---

# Data Flow

Step 1

Load CSV exports.

v

Step 2

Validate required columns.

v

Step 3

Build unified product records.

v

Step 4

Normalize values.

v

Step 5

Execute selected audit.

v

Step 6

Generate corrections.

v

Step 7

Produce Excel report.

---

# Unified Record Builder

The Unified Record Builder combines information from every source into a single internal product record.

This eliminates duplicated comparison logic.

All audits operate on unified records rather than individual CSV rows.

---

# Normalization

Before any comparison occurs, data is normalized.

Examples include:

- Part numbers
- Blank values
- Numeric formatting
- Units
- Whitespace

Normalization ensures equivalent values compare correctly.

---

# Audit Engine

Each audit is independent.

Examples:

- Full Product Family Audit
- TrackVia vs Directus
- Product Existence
- Directus QA
- Catalog Verification

Each audit returns structured findings that are consumed by the reporting engine.

---

# Comparison Pipeline

Every comparison follows the same sequence.

Normalize

v

Compare

v

Record Difference

v

Generate Correction

v

Add to Report

No comparison should bypass normalization.

---

# Report Generation

Reports are generated as Excel workbooks.

Typical worksheets include:

- Dashboard
- Four-Way Comparison
- Missing Products
- Specification Mismatches
- Product Corrections
- German-US Mapping

The Dashboard provides an executive summary.

---

# Design Principles

The project follows these principles.

## Accuracy First

Correct results are more important than execution speed.

---

## Single Responsibility

Each module has one responsibility.

---

## Reusable Logic

Comparison logic should never be duplicated.

---

## Professional Output

Reports are intended for business users.

Formatting should reflect production-quality software.

---

## Engineering is the Source of Truth

Engineering specifications override other systems whenever conflicts occur.

---

# Future Architecture

Planned enhancements include:

- Settings screen
- Saved audit profiles
- Database support
- PDF reports
- Charts and analytics
- Health score
- Automated testing
- Installer
- Automatic updates

---

# Version

Architecture Version 1.0
