# WP10 Pilot and Internal Release Candidate

Date: 2026-11-15. Version: v0.1.0-rc1. STATUS: FROZEN INTERNAL CANDIDATE; NOT A PUBLIC RELEASE.

## Pilot scope

Uppsala: 8 municipal observations, report reference year 2022, seven legal forms, aggregate 10,821, drawn from curated source mchs_119_2025, Table 2 p.26. This existing extract is NOT a new complete RefA re-audit. Source identifiers are SCB 2026 code references, not historic 2022 polygons.

Sörmland: 9 municipality annex metadata records, report published 2024, observation year 2023, one source study study_sormland_2023. Municipality list: Eskilstuna, Flen, Gnesta, Katrineholm, Nyköping, Oxelösund, Strängnäs, Trosa, Vingåker. All nine numeric values are BLANK/NOT EXTRACTED, not zero and not comparable estimates.

## Local build and freeze

Commands:

    python -m ideburen.cli build --out build
    python -m ideburen.statistics build --out build
    python -m ideburen.cli package --input build --out build/ideburen_tables.gpkg
    python -m ideburen.governance audit --source-dir build --out build/wp09
    python -m ideburen.pilot_release freeze --out build/wp10_candidate --generated-at ACTUAL_UTC_ISO_TIMESTAMP --code-revision EXACT_40_CHARACTER_GIT_SHA --build-dir build
    python -m ideburen.pilot_release verify --path build/wp10_candidate

Outputs local only: wp10_pilot_17.csv, wp10_acceptance_gates.csv, wp10_manifest.json. Version and source SHA-256 checksums are fixed and verified. Never overwrite a candidate: freeze into a new directory. GitHub CI uses its actual checkout commit and UTC timestamp. No WP10 data artifact, tag or release is automatically published.

## QGIS map boundary

WP07 can produce an attribute-only GeoPackage, no geometry. The spatial 2022 value map needs legally obtained historical 2022 municipality polygons, exact join keys, QGIS geometry/topology checks and human review. User applied for a Lantmäteriet account; approval and 2022 polygon availability remain unconfirmed. A 2026 boundary dataset must not be mislabeled as a 2022 polygon layer.

## Release policy

The development build may pass while public release remains BLOCKED under WP09. Original evidence RefA, source reuse rights, privacy audit, historical polygons, QGIS runtime and explicit Director release acceptance are mandatory. The candidate does not satisfy the work-order requirement of a public v0.1 release or demonstrated real QGIS maps. ADR acceptance is not public release authorization.
