SAB Catalog Auditor Business Rules v1.0
1. Source of Truth
Part Number

If a German Engineering record exists:

German Engineering is the Source of Truth

If no German Engineering record exists:

US Catalog is the Source of Truth

TrackVia and Directus are compared against the Source of Truth.

2. Four-Way Comparison Fields

The Four-Way Comparison compares only:

Part Number
AWG
Conductors
Pairs
OD (in.)
OD (mm.)
Cable Weight (lbs/mft)

Nothing else belongs in the Four-Way Comparison.

3. Conductors

The comparison is based on the numeric conductor count only.

The comparison engine retrieves the correct value from each source according to the business rules for that source.

No string parsing or guessing is performed during comparison.

4. Pairs

Pairs are compared only when the product family contains pairs.

If a product family does not have pairs, blank values across all systems are acceptable and are not considered a mismatch.

5. OD (in.)
Source of Truth

German Engineering

Column:

Outer-Ø- in
TrackVia

Uses the engineering OD (in.) value according to the TrackVia business rules.

Directus Engineering Fields

Exactly one of these fields must contain a value:

part_od_inches
part_od_inches_10
part_od_inches_range

Rules:

Exactly one field populated.
The populated value must exactly match the German Engineering value.
No calculations.
No conversions.
Compare the stored value exactly.
Directus Search Field
od_in

Rules:

Must always be populated.
Must exactly match the German Engineering value.
6. OD (mm.)
Source of Truth

German Engineering

Column:

Outer-Ø- mm
TrackVia

Uses the engineering OD (mm.) value according to the TrackVia business rules.

Directus Engineering Fields

Exactly one of these fields must contain a value:

part_od_mm
part_od_mm_10
part_od_mm_range

Rules:

Exactly one field populated.
Must exactly match German Engineering.
Compare stored value exactly.
7. Cable Weight

Source of Truth:

German Engineering when available.

Otherwise US Catalog.

Comparison uses the engineering value only.

(We'll add the exact TrackVia/Directus field precedence once we document those fields.)

8. Directus QA Rules

These are not Four-Way Comparison rules.

OD (in.)

Fail if:

More than one engineering OD (in.) field is populated.
No engineering OD (in.) field is populated.
od_in is blank.
od_in does not match the German Engineering value.
OD (mm.)

Fail if:

More than one engineering OD (mm.) field is populated.
No engineering OD (mm.) field is populated.
9. Four-Way Comparison Output

Each comparison row contains:

SKU
Field
German Engineering
TrackVia
Directus
US Catalog
Status (PASS/FAIL)

No corrections.

No QA issues.

No recommendations.

10. Correction Engine

Runs after the Four-Way Comparison.

Uses the Source of Truth to recommend updates for:

TrackVia
Directus
11. QA Engine

Runs independently of the Four-Way Comparison.

Validates:

Directus publishing fields
Directus search fields
Required field population
Business-rule violations