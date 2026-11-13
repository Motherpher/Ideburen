# WP03 Acceptance record — 2026-11-13

| Requirement | Implementation | Status |
| --- | --- | --- |
| Stable source IDs and bibliographic references for seed corpus | `manifests/source_registry_v1.csv` | IMPLEMENTED |
| Archive references without exposing private Drive IDs | `manifests/source_archive_inventory_v1.csv` | IMPLEMENTED |
| Source, publication, study family identity separated | `publication_registry_v1.csv`, `study_family_registry_v1.csv` | IMPLEMENTED |
| Data-period/year and geography carried with publication | Publication registry columns | IMPLEMENTED WHERE KNOWN; blank if unknown |
| HARP evidence and publication rights not conflated | Separate columns; review gates | IMPLEMENTED |
| Source binary SHA-256 | Optional local tool, ledger not in public Git | 2 USER-UPLOADED XLSX SHA-256 VERIFIED; OTHER ORIGINALS PENDING |
| Uniqueness and referential integrity | `ideburen.sources validate` and CI tests | IMPLEMENTED, CI TO VERIFY |
| No false independent studies from editions/appendices | Värmland 2023 and Sörmland 2023 group validation | IMPLEMENTED |
| Source contents fully audited | Requires authorized original reads and RefA | NOT DONE — FOLLOW-UP |
| Entire 21-län/290-kommun 2000+ corpus complete | Discovery coverage not exhaustive | NOT CLAIMED |

**Overall WP03 status:** Seed metadata registry implementation complete; binary source checksums and comprehensive HARP evidence audit remain separately tracked. WP04/WP06 can use the catalogs as inputs without implying national completeness or a completed publication release.
