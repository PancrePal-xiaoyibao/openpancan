# Technical Specifications

This directory contains detailed technical specifications for OpenPanCan Gene Base components.

## What Goes Here

- **Data Schema Specifications** — Precise field definitions, data types, allowed values, validation rules, and constraints for all database tables and data structures. Includes JSON Schema definitions for API payloads.
- **ETL Pipeline Specifications** — Detailed specifications for Extract-Transform-Load pipelines: source systems, extraction methods, transformation rules, data quality checks, error handling, and loading procedures.
- **API Endpoint Specifications** — Complete OpenAPI/Swagger specifications for REST endpoints or GraphQL schema definitions. Includes request/response formats, status codes, error handling, and rate limits.
- **Gene Annotation Specifications** — Standards and rules for gene annotation: naming conventions, evidence levels, confidence scoring, and conflict resolution between sources.
- **Variant Classification Specifications** — ACMG/AMP variant classification rules adapted for somatic variants, tier systems (I-IV), and clinical actionability criteria.
- **AI Model Specifications** — Model architecture specifications, input/output tensor shapes, preprocessing requirements, inference parameters, and performance benchmarks.
- **File Format Specifications** — Definitions of all data file formats used in the system: TSV/CSV schemas, JSON structure, Parquet column definitions, and binary formats.

## File Naming Convention

```
YYYY-MM-DD_component-spec.md
```

Example: `2026-07-01_gene-entity-schema-spec.md`

## Template

Each specification document should include:

1. **Overview** — Brief description of what is being specified.
2. **Scope** — Boundaries of this specification.
3. **Requirements** — Functional and non-functional requirements.
4. **Detailed Specification** — The actual spec content (schemas, rules, contracts).
5. **Examples** — Concrete examples illustrating the specification.
6. **Validation** — How to verify conformance to this specification.
7. **Changelog** — History of changes to this specification.
