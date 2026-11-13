# Data dictionary v0.1
**Geographies:** `municipality_code` = text, four digits; `county_code` = two-digit text. Source geographic pack is 2025 and must be checked against 2026 SCB.

**Observations:** `metric_id` must specify statistical population, `value_year` refers to measurement year, not publication year, `method_id` identifies source method, `source_id` traces a verifiable report, `evidence_status` gates publication. `registered_civil_society_entities_7_legal_forms` includes 7 organizational forms, not the same as clubs in a municipality's association register.

**Institutions:** An institutional document is a versioned policy, agreement, declaration, council or instrument. It does not automatically prove implementation.

**Decision events:** Events are discrete steps; `date_or_period` may remain a textual period when exact date is unavailable. `metadata_only` records discovery, not full primary-source validation. Multiple chains or detours are permitted.

**Source rights:** Private Drive binaries are not committed here. Original materials require own rights assessment.

**Null semantics:** null/not checked, not found, contradicted, not applicable and verified zero remain separate. Do not silently fill null with zero.
