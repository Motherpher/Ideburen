# WP04 — Acceptance record (2026-11-13)

| Requirement | Result | Evidence |
| --- | --- | --- |
| Exact two-workbook version control | PASS | SHA-256 values in `config/wp04_seed_contract.json`; local QA manifest |
| All 9 worksheets and 421 nonblank source rows preserved in private staging | PASS | Local normalized ZIP (not committed) |
| Classification: 290 municipal profiles and 23 supplementary report entries | PASS | Separate normalized files, no supplements counted as measurements |
| Uppsala register sources 8 / historical associations 37 / decision events 27 / record requests 16 | PASS | Separate normalized files |
| Geographic mapping to SCB 2026 municipality key | PASS | 290 distinct identifiers, zero unmatched |
| Blank vs explicit numeric 0 | PASS | 280 unknown, 10 supplied counts, 0 zero; fixture tests cover explicit zero |
| Source versions / lineage | PASS | SHA-256 + sheet + source Excel row number in the local manifest |
| Formula execution / cached formulas / macros / external links | BLOCKED BY PARSER | Fail closed; tested formula rejection |
| Source evidence and public release | NOT APPROVED | Seed entries remain unverified; HARP and rights gates unchanged |
| National comprehensive population census | NOT CLAIMED | The source is a research inventory |

**WP04 technical implementation completed.** Files under build/staging remain unpublished; WP05/WP06 must curate evidence separately rather than automatically promoting any seed records to verified facts.
