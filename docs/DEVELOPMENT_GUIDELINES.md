# Development Guidelines

## Purpose

This document defines coding standards and AI/Copilot rules for this codebase.

## Coding Standards

- Prefer small, focused functions.
- Keep one responsibility per module/function.
- Avoid duplicated comparison or normalization logic.
- Use explicit reason messages for audit failures.
- Preserve current behavior unless changes are explicitly requested.

## Architecture Rules

- Keep audit logic in `audits/`.
- Keep source parsing/mapping in `importers/`.
- Keep workbook generation in `reports/`.
- Keep UI and routing concerns out of core audit modules.

## Normalization Rules

- Normalize before lookup and comparison.
- Use `UnifiedRecordBuilder.normalize_part_number(...)` for part-number logic.
- Do not compare raw part number values.
- Avoid direct `str(part_number)` conversions in comparison paths.

## Reporting Rules

- Maintain required worksheet set.
- Keep Dashboard first.
- Ensure normalized identifiers in output.
- Include reason columns for missing/mismatch rows.

## Refactoring Rules

- Refactoring must preserve audit outcomes.
- Prefer incremental changes over large rewrites.
- Validate behavior against known edge cases after refactoring.

## Git Workflow

- Use focused feature branches.
- Keep commits small and cohesive.
- Use clear commit messages describing functional impact.
- Avoid combining unrelated changes in a single commit.

## Copilot Operating Rules

- Accuracy over speed.
- Do not simplify logic if it changes results.
- Keep recommendations actionable and test-backed when possible.
