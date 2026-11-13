# WP05 — Acceptance and release gate

Date: 2026-11-13
Authority: ADR-0001 and ADR-0002 (Director Accepted).

| WP05 requirement | Status and evidence |
| --- | --- |
| Case/event/actor/document model | IMPLEMENTED in src/ideburen/decision_engine.py |
| Uppsala and Tierp pilots | DOCUMENTED at research-seed level in docs/WP05_PILOTS.md |
| All 27 source-record shape, 8 municipalities, 9 analytical cases | TESTED WITH SYNTHETIC PROFILE in tests/test_wp05_profile_27.py |
| Deterministic row-level provenance and checksums | IMPLEMENTED in engine |
| Multiple time precisions and strict non-causal chronology | IMPLEMENTED/TESTED |
| Distinguish policy requirement from observed implementation | IMPLEMENTED/TESTED |
| Missing process stages vs actual absence | IMPLEMENTED/TESTED |
| Explicit RefA-asserted relations only after human audit metadata | IMPLEMENTED/TESTED; does not independently prove claimed review |
| GraphML, CSV exports, actors, documents, gap and exceptions reports | IMPLEMENTED/TESTED |
| Full real 27-row private WP04 event engine execution | NOT VERIFIED IN GITHUB CI; execute locally using docs/WP05_DECISION_ENGINE.md |
| Full legal/primary source review of all municipal decisions | NOT COMPLETED — HARP RefA required |
| Public validated legal-decision release | BLOCKED pending human verification and Director approval |

Overall WP05 status: **technical Decision Engine implemented and tested**, pilot evidence index completed at inventory level, full source review and operational private-data execution outstanding. Do not report the municipal decision process as exhaustive.
