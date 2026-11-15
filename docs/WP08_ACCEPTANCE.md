# WP08 — Adapter acceptance record

**Date:** 2026-11-15. **Target FF-Spatial commit:** `76dcadfb5d116e238d404ad106465b8a39111d6f`.

| Requirement | Evidence | Status |
| --- | --- | --- |
| Read current registry/gateway/provenance/QGIS/bridge contracts | Verified read-only from FF-Spatial | PASS |
| Versioned adapter with exact FF-Spatial normalized field order | `src/ideburen/ffspatial_adapter.py` | IMPLEMENTED |
| Input gate for WP07 attribute package | SHA, 290 codes, eight Uppsala values, 282 NULLs, no geometry | IMPLEMENTED |
| Explicit geographic vintage separation | 2022 observations vs SCB 2026 identifiers | IMPLEMENTED |
| Eight municipality rows; exclude four nationwide rows | 8/8 and 4 excluded; no fake observation | IMPLEMENTED |
| FF-Spatial provenance metadata / checksum | Source URL, transformation audit, file SHA-256 | IMPLEMENTED |
| Safe local export and validation | Non-overwriting export + CLI validator | IMPLEMENTED |
| Bridge job, remote QGIS job, FF-Spatial repository mutation | Explicitly absent | PASS SAFETY |
| Original source legal rights / full HARP RefA | Unresolved source rights and review | BLOCKED |
| Real municipality polygons, vintage 2022 | Lantmäteriet account pending; historic source outstanding | BLOCKED |
| FF-Spatial consumer Python runtime import | Separate private repository and local bridge; not executed | NOT VERIFIED |
| Physical end-to-end QGIS project and map | No source-matched polygons or runtime | NOT VERIFIED |

**WP08 verdict:** Adapter implemented and internally testable against **actual inspected consumer interface definitions**. A complete runtime integration is **not** verified. No changes were made to the FF-Spatial repository. Automated tests cannot grant Director authorization, legal data reuse rights or map publication approval.
