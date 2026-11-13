# ADR-0002: Geographic keys and FF-Spatial boundary

- Status: **Accepted**
- Date: 2026-11-13
- Scope: WP01 foundation / WP02 and WP07 follow-on

## Context
The project must compare all 290 municipalities and 21 counties over time, while preserving FF-Spatial's external architecture.

## Decision
Use four-character text municipality codes and two-character text county codes. Record observation year, boundary vintage and source. Use EPSG:3006 for analysis, with source CRS preserved. Do not derive polygon geometry, centroid, or spatial claims from an attribute spreadsheet. GeoPackage attribute tables remain explicitly non-spatial until authoritative licensed geometry has been joined and validated.

## Alternatives
Join by normalized names (rejected because of ambiguity and administrative changes); copy geospatial orchestration from FF-Spatial (rejected to avoid dual ownership and interference).

## Consequences
Historical comparisons require versioned geography; a complete spatial pilot cannot be claimed until official boundaries and a local QGIS test exist.

## Verification
Automated tests for key uniqueness and attribute packaging; manual/QGIS tests remain release gates.

## Decision record
- Decision: **Accepted**
- Authority: **Director** (explicit instruction in the Ideburen project conversation)
- Approval date: **2026-11-13**
- Scope of approval: This ADR only; no approval of downstream releases, data rights or other work packages.
- Implementation note: Existing safeguards and outstanding verification gates remain in force.
