# API Ledger v1 — Ideburen / SCB AFR

Status: IMPLEMENTED METADATA/DRY-RUN; NO LIVE AUTHENTICATED FETCH.
Checked 2026-11-15 against SCB's current public API and legal-form variable descriptions.

## Critical correction to original proposal

The new SCB Allmänna företagsregistret API uses a PERSONAL API KEY, not the old client certificate. The current API returns JSON, permits pagination, maximum 5,000 rows/request and no more than 5 requests/second. A personal key is NOT a project secret to put in GitHub. Apply through https://registreraafr.scb.se and consult https://apiafr.scb.se/scalar/ . SCB API homepage: https://www.scb.se/vara-tjanster/bestall-data-och-statistik/foretagsregistret/avgiftsfria-uppgifter-i-foretagsregistret/ .

**Important contract gate:** OpenAPI endpoint and authentication/header/query/pagination parameters have NOT been independently parsed from the published machine-readable Swagger file in this implementation. Do not guess field names or send automated live requests until the specification and individual key are verified. The repository stores only the OpenAPI URL, not invented request bodies or keys.

## Ledger design

- config/api_ledger/sources.json: API identity, authority, documentation, auth, access, licence, rate, page size, current-versus-history semantics, release state
- config/api_ledger/civil_society_policy_v1.json: analytical **proposed** classification, distinct from SCB's standard/official definition
- src/ideburen/api_ledger.py: contract validation, dry-run selection plan, class mapping, append-only audit event writer, protection against credential values
- tests/test_api_ledger.py: no-network regression tests, no automatic authorization
- build/api_ledger/: local-only plans, snapshot run receipts and raw records only after signed source/rights controls; never checked into Git

## Juridisk form

Core: 61 (ideella föreningar), 72 (övriga stiftelser och fonder).
Review: 51 (ekonomiska föreningar), 63 (registrerade trossamfund), 71 (familjestiftelser).
Separate: 53 (bostadsrättsföreningar), 54 (kooperativa hyresrättsföreningar), 62 (samfälligheter).

The review tier is not automatically included or excluded. In particular 51 cannot reliably identify a social cooperative from legal form alone, and 72 may include foundations with substantially different purposes. The project must establish a substantive classification method and audit it.

## SNI 2025 and scope

SNI 93 and 94 are PRIORITY ANNOTATIONS and not hard inclusion or exclusion criteria. Associations active in social services, culture, education, humanitarian relief and other sectors may have other SNI. The source exposes SNI2025, up to five SNI values on each legal entity; legal form and SNI should be recorded separately with their version. SCB's business-active flag uses VAT/employer/F-tax criteria and cannot certify that an otherwise legitimate civil-society association is inactive.

## Data model and temporality

Use legal entity (JE) for organisation counts. Do NOT count establishments (AE) as organisations. Distinguish registered office municipality from actual operational local presence. Protect full person/organisation identity data according to rights and privacy clearance. Public repository stores definitions, code, source references, aggregated and authorized outputs only.

SCB AFR API is CURRENT SNAPSHOT: it has no historical endpoint and no free native change feed. A captured snapshot from 2026 cannot reconstruct all organisations active 2022. Capture run UTC, source metadata/as-of date, response schema version, page counts, record counts and SHA-256 of locally saved files. Never infer causality, founding/dissolution or substantive activities purely from two snapshot deltas.

## Local commands

    python -m ideburen.api_ledger validate
    python -m ideburen.api_ledger plan --out build/api_ledger/plan.json
    python -m ideburen.api_ledger classify --form 61 --sni 85.100 94.990

The plan explicitly states BLOCKED_PENDING_OPENAPI_REVIEW_AND_API_KEY. No live requests occur.

## Required steps for live integration

1. Register with BankID through the SCB portal, accept terms and obtain the personal API key.
2. Parse and pin the current SCB v2 OpenAPI document by SHA-256, endpoints, query filter names, paging, authentication header and return JSON schema. **No guessed authentication**.
3. Build a sealed local adapter using environment secret injection, request-size <=5000 and max 5 requests/second with conservative retry/backoff. Record the exact query plan, filters, pagination, hashes and failures. Never echo credentials to logs.
4. Pilot first by legal form 61/72 for a small, explicit geographic test. Validate entity identity, duplicate pages, cursor semantics, registered-office geography, and limits. Add categories 51/63/71 separately.
5. Independently review source reuse rights, protected fields, small-area disclosure and GDPR before publishing any individual organisation or aggregate product. Human HARP RefA and Director release approval remain binding under ADR-0001/WP09.

## HARP and governance

ITR1 source authority (official SCB service), ITR2 relevant documentation, ITR4 bibliographic/URL/version citation, ITR5 source-specific field/code verification, ITR6 refusal of unverified request schema, protected data or unsupported claims. No phantom ITR3.

The actual API credential is **not** available or connected; this ledger is not evidence that a single SCB record was retrieved.
