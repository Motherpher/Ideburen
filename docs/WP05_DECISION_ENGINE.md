# WP05 Decision Engine — implementation contract

Date: 2026-11-13. Governing ADR-0001 and ADR-0002: Accepted.

## Objective
Trace civil-society policy and collaboration from initiative and dialogue through preparation, political decision, implementation and evaluation. Source-inventory incompleteness never proves non-occurrence of a municipal act.

## Inputs
Canonical private WP04 decision_events.csv (27 event records in eight Uppsala municipalities). Optionally the private WP04 raw_staging.jsonl to associate institutional actors. An optional third CSV may specify reviewed source relations. The original workbooks and raw/private event contents are not committed to this public repository.

## Graph entities
Case (case_id), event (event_id derived from original source row), municipality (four-character municipality_code), institutional actor (actor_id), document locator (document_id), typed edge (edge_id), missing-stage observation and review request. Every event preserves original row, workbook checksum, original Swedish stage, original period, source verification note, and release state.

An HTTPS document URL is a locator, not proof that the document has been read. An original worksheet note saying that an event is verified is NOT promoted to WP05 primary verification. WP05 event evidence_status is seed_claim_not_primary_reaudited; legal_decision_confirmed is not_in_wp05.

## Temporal and process logic
Event dates support YYYY-MM-DD, YYYY-MM, YYYY, a year range and unknown. Only strictly non-overlapping known date intervals can yield observed_temporal_precedence; edges do not imply causality or statutory dependence. Overlapping dates, unknown dates and same-day statements are not automatically ordered.

Normative rules requiring annual follow-up are NOT evidence that follow-up occurred. A policy's validity period is NOT a series of actions. These are classified as normative_requirement and document_validity_period and excluded from chronology edges and observed process-stage coverage.

Missing process stages are recorded as not_observed_in_seed, never as did_not_occur. Supplementary evidence_requests.csv lists missing original extracts, uncertain dates and source notes requiring follow-up.

## Explicit, document-reviewed decision relations
The engine can take a private relations CSV containing:
from_row_id,to_row_id,relation,source_url,source_locator,reviewer,audit_date,harp_status

Allowed relations include prepares, recommends, adopts, amends, supersedes, implements, follows_up, comments_on, reviews. Only asserted HARP RefA_approved relations with a named reviewer, audit date, HTTPS original-source URL and document locator are accepted. This is a software-level procedural check; it is not cryptographic proof or a substitute for human reading of the original.

## Run on private WP04 output
python -m ideburen.decision_engine --events /secure/wp04/decision_events.csv --raw /secure/wp04/raw_staging.jsonl --out /secure/wp05

Optional when a separate signed source review has been performed:
python -m ideburen.decision_engine --events /secure/wp04/decision_events.csv --raw /secure/wp04/raw_staging.jsonl --assertions /secure/verified_relations.csv --out /secure/wp05

## Output
decision_events.csv, cases.csv, decision_edges.csv, decision_graph.graphml, actors.csv, documents.csv, process_gaps.csv, evidence_requests.csv, exceptions.csv, manifest.json. Output must be outside the Git checkout. GraphML is interoperable with graph-analysis tools. The cases CSV can later be joined to QGIS using municipality_code, but does not contain geometry.

## Safety and acceptance
No private source documents, source-file contents or personnel information in public Git. Tests exercise synthetic datasets; they DO NOT constitute original-document auditing. Public legal/governance assertions require human HARP RefA and Director release approval.

See docs/WP05_PILOTS.md and docs/WP05_ACCEPTANCE.md.
