# ADR-0001: Source of truth and publication boundaries

- Status: **Accepted**
- Date: 2026-11-13
- Scope: WP01 / future WP03–WP10

## Context
The research work uses original reports in Drive, public government publications, local inventory spreadsheets and a public GitHub repository. Their access and reuse terms differ. FF-Spatial is a separate repository.

## Decision
1. Google Drive and publishers' public URLs retain the original documents.
2. `Ideburen` stores traceable metadata, scripts, non-personal curated facts and derived outputs with explicit reuse rights.
3. Raw uploads, unpublished Drive contents, personal data and tokens never enter the public git history.
4. QGIS/FF-Spatial consumes versioned derived products; no automatic changes are authorized to FF-Spatial.
5. Release requires documented source rights, HARP review, source lineage and Director approval. An automated build is not publication approval.

## Alternatives
Commit all original reports to Git (rejected due to copyright/privacy and repository size risk); use QGIS as canonical database (rejected due to weaker source traceability and dependence on a GIS runtime).

## Consequences
Original reports are referenced not duplicated; reproducible internal ingestion may require authorized local access. This is an accepted governance decision under Director authority.

## Verification
CI checks package/tests; rights and human approvals remain outside CI.

## Decision record
- Decision: **Accepted**
- Authority: **Director** (explicit instruction in the Ideburen project conversation)
- Approval date: **2026-11-13**
- Scope of approval: This ADR only; no approval of downstream releases, data rights or other work packages.
- Implementation note: Existing safeguards and outstanding verification gates remain in force.
