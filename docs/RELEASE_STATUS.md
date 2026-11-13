# Implementation status — 2026-11-13

- **WP00** Partial: FF-Spatial README and QGIS integration contracts checked read-only; broader architecture review pending.
- **WP01** Technical baseline complete; ADR-0001 and ADR-0002 formally **Accepted** by Director.
- **WP02** **PARTIAL**: all 290 municipality identifiers, names, 21 county codes verified **exactly** against SCB official 2026 enumeration (0 discrepancies). 2000–2026 boundary-vintage requirements and geography validation infrastructure installed. Lantmäteriet 2026 polygon acquisition **blocked by Geotorget entitlement**; QGIS topology not run. See `docs/WP02_ACCEPTANCE.md`.
- **WP03** **SEED CATALOG IMPLEMENTED**: 50 source records, 41 publication editions, 39 study families; 50 archive-index records, two user-uploaded XLSX binary SHA-256 checksums verified. Referential integrity, deduplication and HARP/rights status gates enforced by CI. Full original-PDF checksum/HARP RefA audit and comprehensive national archive discovery remain pending. See `docs/WP03_ACCEPTANCE.md`.
- **WP04** XLSX source-inventory staging import implemented; raw workbooks not committed.
- **WP05** Decision-event staging and sample institutions; full primary audit incomplete.
- **WP06** Uppsala 2022 eight-municipality sample (10,821 across seven legal forms); comparison research incomplete.
- **WP07** Nonspatial GeoPackage attributes and QGIS loader; official spatial map blocked pending polygons.
- **WP08** FF-Spatial adapter contract drafted; no remote binding verified and no FF-Spatial writes.
- **WP09** CI baseline QA passing; RefA human verification pending.
- **WP10** Public release remains **BLOCKED**.

Distinguish implemented code, verified evidence, sourced real geometry and Director-authorized publication.
