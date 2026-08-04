# SAB Catalog Auditor

All notable changes to this project are documented in this file.

---

# Version 1.1
**Release Date:** July 27, 2026

## 🎉 Initial Production Release

The first production-ready version of the SAB Catalog Auditor.

### Added

#### Core Audits
- Four-way product comparison across:
	- TrackVia
	- Directus
	- German Engineering
	- US Catalog
- Missing Product audit
- Specification Mismatch audit
- German ↔ US mapping verification
- Rubicon Weight audit

#### Reporting
- Excel report generation
- Dashboard worksheet
- Missing Products worksheet
- Specification Mismatches worksheet
- German-US Mapping worksheet
- Four-Way Comparison worksheet
- Rubicon Weight Audit worksheet

#### Web Application
- Browser-based upload interface
- Four-file upload validation
- Progress logging
- Completion summary
- Downloadable Excel report

#### Dashboard Metrics
- Products Compared
- Missing Products
- Specification Mismatches
- Corrections Generated
- Rubicon Weight Matches
- Rubicon Weight Mismatches
- Not Found in Rubicon

### Fixed

- Corrected Rubicon lookup to use the US SKU instead of the German part number.
- Fixed Engineering Weight lookup using the correct German Engineering weight column.
- Improved column normalization for special characters and encoding differences.
- Removed all temporary Rubicon troubleshooting and debug logging.
- Added Rubicon metrics to the completion summary.
- Added application version tracking.

### Technical

- Git repository initialized.
- Production release tagged as **v1.1**.
- Development branch created for future work.

### Known Issues

- Dashboard Health Score calculation should be reviewed.
- Product Family filtering is planned for Version 1.2.

---

# Version 1.2
*(In Development)*

## Planned

### High Priority
- Product Family selector
- Health Score improvements
- Dashboard hyperlinks
- Enhanced mismatch grouping

### Medium Priority
- Dashboard charts
- Export corrections to CSV
- Configurable field mappings
- Audit history

### Future Ideas
- Batch auditing
- User preferences
- Saved configurations
- PDF executive summary
