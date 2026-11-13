# WP02 acceptance — 2026-11-13

## Objective
Establish authoritative Swedish geographic identifiers (21 län, 290 kommuner) with strict time-validity and ready-to-validate QGIS/Lantmäteriet geometry contracts.

## Results
| Gate | Result | Evidence |
| --- | --- | --- |
| Full 2026 SCB code/name audit, 290 municipalities | **PASS** | `docs/WP02_SCB_VERIFICATION.md`, `data/reference/scb_2026_codes_snapshot.csv` |
| 21 counties, correct code prefixes | **PASS** | `data/curated/dimensions/counties.csv` |
| Reproducible code snapshots and tests | **PASS** | `tests/test_geography.py`, CI |
| Temporal vintage inventory 2000–2026 | **INDEXED, DATA NOT ACQUIRED** | `geo/boundaries/historical_vintage_inventory.csv` |
| Governance-approved GIS interface contract | **PASS** | `docs/adr/0002-geography-qgis-contract.md` (Accepted) |
| Source/rights/authentication requirements | **SPECIFIED** | `docs/WP02_GEODATA.md`, `geo/boundaries/provenance.template.json` |
| Countrywide real municipal polygons (2026) | **BLOCKED** | Lantmäteriet Geotorget access ordering/authentication not connected |
| Historical polygons 2000–2025 | **BLOCKED / NOT SOURCED** | SCB historical source and Lantmäteriet annual series identified |
| Geometry topology valid in QGIS | **NOT RUN** | Requires actual polygon layer and QGIS runtime |

**Overall state: PARTIAL — identifier gate accepted, spatial boundary gate blocked.**

No official polygons have been invented or substituted with SCB visualization-only simplified borders. Public map release remains blocked, even though nonspatial GeoPackage preview builds successfully.

## Next unblocking action
Authorize Lantmäteriet Geotorget *Kommun, län och rike Nedladdning* access outside GitHub and supply an original **2026 annual polygon GeoPackage** plus source rights and metadata. Then run python `ideburen.geography` package QA and the `geo/qgis/verify_official_polygons.py` topology audit in QGIS. Historical data should use temporally appropriate boundaries.
