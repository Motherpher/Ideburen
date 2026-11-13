# WP03 — Source, publication and study-family registry

Status: **implemented for the registered seed corpus** (2026-11-13). This is not a claim that the entire 2000–2026 literature or all 290 municipalities have been comprehensively searched.

## Canonical files
- `manifests/source_registry_v1.csv`: **one source version/locator**, stable `source_id`, owner, citation, source URL, geographic scope, data-period, provenance note, metadata/HARP gate, rights status and checksum status.
- `data/curated/publications/publication_registry_v1.csv`: **one edition/report/web tool/appendix** per `publication_id`, foreign keys `source_id` and `study_id`.
- `data/curated/publications/study_family_registry_v1.csv`: **one underlying research programme/data collection** per `study_id` (not one row per PDF).
- `manifests/source_archive_inventory_v1.csv`: restricted Drive/local archival provenance classes and explicit **not_computed** checksums; private individual Google Drive file IDs are *not* committed.

These are metadata and research-discovery records. Some sources have no verified direct PDF URL; do not treat a landing page or secondary mention as a verified PDF. Original PDFs' bytes were **not reviewed exhaustively** during WP03; HARP RefA remains unsigned.

## De-duplication rules
Värmland 2023 region publication, academic 2025 reissue and online statistical tool are **one study**. Region Sörmland 2024 report plus its nine municipal appendices are **one study**. Studies that span multiple counties are not replicated as independent studies by county. A publication indexed under a municipality may be local/sectoral rather than a complete organisation count.

## Quality semantics
`primary_verified`: a source's specific claim/document has undergone a prior primary verification; **not equivalent to full RefA of every future extracted variable**.
`metadata_page_verified`: publication metadata visibly confirmed on an official publisher page; not a full PDF read.
`metadata_only`: source and title previously identified; attribution/URL and contents may still need primary checks.
`internal_inventory`: user-supplied research inventory, not official reference.
`secondary_pending`: existence grounded in non-primary evidence, cross-check pending.
`unverified`, `contradicted`, `unavailable`: retain as distinct states.

`checksum_status=not_computed` explicitly means original binary SHA-256 was not obtained, **not** that data are validated or file bytes verified. No guessed SHA values are in the register.

## Commands
```bash
python -m ideburen.sources validate
python -m ideburen.sources checksum --source-id varmland_2023 --file /secure/original.pdf --out /secure/ledger/varmland_2023.json
```

The checksum operation records filename, file size and SHA-256 outside the public repository; **it does not change HARP status** nor grant publication rights.

## HARP / next gate
Collect original source bytes through authorized access, record original-page evidentiary citations and complete ITR1/ITR2/ITR4/ITR5/ITR6 for each public-facing claim. Require rights determination, author/date and methodological comparability check. Source `mchs_119_2025` remains the existing Uppsala 2022 observation's source. Missing or duplicate sources must trigger QA failures, never silently become zero.

**WP03 acceptance:** Every registered seed has a unique source-ID, bibliographic reference, provenance note, archive/checksum status and source quality state; all publications link to registered sources and study families. The documented original-file checksum coverage remains outstanding until authorized files are audited.
