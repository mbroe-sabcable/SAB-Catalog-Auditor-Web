# SAB Catalog Auditor

A desktop application for validating and synchronizing product data across SAB North America's engineering, ERP, website, and catalog systems.

The Catalog Auditor helps identify missing products, specification mismatches, and data inconsistencies before information is published to customers.

By comparing product data from multiple sources, the application provides a single, comprehensive view of product quality and generates actionable correction reports to improve data accuracy and consistency.

---

# Key Capabilities

- Compare products across four independent data sources
- Detect missing products and synchronization issues
- Validate engineering specifications
- Identify field-level mismatches
- Generate recommended corrections
- Produce professional Excel audit reports
- Standardize part number comparisons through automatic normalization

---

# Supported Data Sources

The application compares information from four primary sources.

| Source | Purpose |
|---------|---------|
| German Engineering | Engineering source of truth |
| TrackVia | Internal product database |
| Directus | Website content management system |
| US Catalog | Published customer catalog |

---

# Supported Audit Types

## Full Product Family Audit

Compares all available product information across every source.

Outputs include:

- Dashboard
- Four-Way Comparison
- Missing Products
- Specification Mismatches
- Product Corrections
- German-US Mapping

---

## TrackVia vs Directus

Verifies synchronization between the internal product database and website.

---

## Product Existence

Determines whether products exist in every required system.

---

## Directus QA

Validates website product information.

---

## Catalog Verification

Verifies published catalog specifications against engineering data.

---

# Technology

- Python 3.12+
- PySide6
- pandas
- openpyxl
- NumPy

---

# Installation

Clone the repository

```bash
git clone https://github.com/<your-repository>/SAB-Catalog-Auditor.git
cd SAB-Catalog-Auditor
```

Create a virtual environment

```bash
python -m venv .venv
```

Activate

Windows

```bash
.venv\Scripts\activate
```

macOS / Linux

```bash
source .venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# Running the Application

```bash
python main.py
```

---

# Typical Workflow

1. Launch the application.
2. Select the desired audit type.
3. Load the required source files.
4. Run the audit.
5. Review the Excel report.
6. Correct data issues.
7. Repeat until all discrepancies are resolved.

---

# Project Structure

```text
SAB-Catalog-Auditor/

app/
	User interface

audits/
	Audit engine

config/
	Configuration files

importers/
	CSV import and validation

reports/
	Excel report generation

assets/
	Logos and images

docs/
	Project documentation

tests/
	Automated tests
```

---

# Report Output

Reports are generated as Microsoft Excel workbooks and include:

- Executive Dashboard
- Four-Way Comparison
- Missing Products
- Specification Mismatches
- Product Corrections
- German-US Mapping

---

# Development Principles

The project is built around the following priorities:

1. Accuracy over speed
2. Engineering data is the source of truth
3. Consistent normalization before comparison
4. Maintainable code
5. Professional reporting

---

# Documentation

Additional documentation is located in the `/docs` folder.

- PROJECT_ARCHITECTURE.md
- AUDIT_RULES.md
- NORMALIZATION_RULES.md
- REPORT_SPECIFICATION.md
- DEVELOPMENT_GUIDELINES.md
- ROADMAP.md

---

# Version

Current Version: **0.9.0**

---

# License

Copyright c SAB North America.

All rights reserved.
