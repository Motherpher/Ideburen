# WP09 — Acceptance and Release Decision

Date: 2026-11-15. Governing Codex: Pius System Codex 5.0, Appendix O. Director-approved ADR-0001 and ADR-0002.

| Definition of Done / control | Evidence | Result |
| --- | --- | --- |
| Source registry audit, one row per source | WP09 HARP audit matrix | IMPLEMENTED; original full RefA NOT APPROVED |
| Harvard/ITR workflow ITR1, ITR2, ITR4, ITR5, ITR6 | `governance.py` and Codex Appendix O | IMPLEMENTED AS VERIFICATION CHECKLIST |
| Privacy and forbidden source binary pattern checks | Source tree static scan and synthetic tests | IMPLEMENTED; legal assessment PENDING |
| Data integrity and reproducibility | WP02/WP03/WP06 validators, WP07 GeoPackage SHA, WP08 adapter receipt | AUTOMATED IN CI |
| RAG log with accountability | `wp09_qa_log.csv`, `docs/WP09_RAG_REGISTER.md` | IMPLEMENTED |
| Internal vs external disclosure separation | Engineering audit separate from `release-check` | IMPLEMENTED; RELEASE BLOCKED |
| Original sources and binary rights cleared | Source register rights and HARP audit | BLOCKED |
| National polygon and 2022 historical geometry | Lantmäteriet approval outstanding / distinct 2022 source | BLOCKED |
| FF-Spatial local runtime / QGIS topology | No actual authorized runtime or .qgz | NOT TESTED |
| No blocking defects IN RELEASE | `release-check` nonzero on red | SAFETY ENFORCED; **NO RELEASE OCCURRED** |
| Authorized public v0.1 release | Requires named Director signoff | NOT AUTHORISED |

## Operational commands

- `python -m ideburen.governance audit --source-dir build --out build/wp09` passes when the engineering controls pass but records red release blockers.
- `python -m ideburen.governance release-check --source-dir build --out build/wp09-release` exits nonzero if release conditions are unsatisfied.
- Github Actions never runs `release-check` to **approve** data; it runs development preflight and publishes only a QA audit log.

**Verdict:** WP09 governance control plane and automated audit implemented. Release acceptance is RED (fail-closed) pending source/rights/geometry/Director review. WP10 must not be presented as a public release until all blockers are resolved.
