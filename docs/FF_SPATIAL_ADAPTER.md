# WP08 — FF-Spatial adapter, verified interface mapping

**Date:** 2026-11-15. **Producer:** `Motherpher/Ideburen`. **Target consumer:** `Motherpher/FF-Spatial` (read-only inspection of main commit `76dcadfb5d116e238d404ad106465b8a39111d6f`).

## Contracts inspected in the actual FF-Spatial repository

| Existing consumer contract | Implementation and compatibility |
| --- | --- |
| `gateway/observations.py` | `NormalizedObservation` fields used as read-only reference for the 14-field export. |
| `qgis/materialize_observations.py` | Exact `FIELDS` ordering used for `ffspatial_normalized_observations.csv`. |
| `provenance/schema.json` | A matching JSON provenance object, with `source_id`, `retrieved_at`, `source_url`, `transformations`. |
| `registry/spatial-product.schema.json` | **Not applicable**: this schema requires spatial product artifact/feature counts. WP08 does not fabricate spatial polygons. |
| `bridge/job.schema.json` | **Not submitted**: executable jobs must pass separate human governance and be merged to FF-Spatial `main/bridge/approved/`. |
| `docs/APPROVED_TRANSPORT.md` | Runtime transport is gated by FF-Spatial's main-branch approval and local Mac bridge. No use here. |
| `docs/LOCAL_BRIDGE.md` | Source read-only, project writes approved and no arbitrary shell actions. No bridge calls here. |
| `docs/ARCHITECTURE.md` | Derived-only, explicitly versioned, raw/derived/publish separation, EPSG:3006 only for actual geometries. |

**Source of truth:** FF-Spatial continues to own its consumer schema, bridge, QGIS and provenance; Ideburen owns only this producer adapter. Changes to FF-Spatial require a separately authorised review/commit.

## Adapter execution

```bash
python -m ideburen.cli build --out build
python -m ideburen.statistics build --out build
python -m ideburen.cli package --input build --out build/ideburen_tables.gpkg
python -m ideburen.gis prepare --gpkg build/ideburen_tables.gpkg --source-dir build --out build/gis_handoff.json
python -m ideburen.ffspatial_adapter build \
  --handoff build/gis_handoff.json \
  --gpkg build/ideburen_tables.gpkg \
  --source-dir build \
  --out build/ffspatial_adapter \
  --generated-at 2026-11-15T15:39:00Z \
  --ff-spatial-commit 76dcadfb5d116e238d404ad106465b8a39111d6f
python -m ideburen.ffspatial_adapter validate --out build/ffspatial_adapter
```

For a new real execution, set `--generated-at` to the actual UTC **local adapter input-read time**. It is not the publisher's original retrieval time; that is explicitly stated in provenance warnings. The target output directory must be empty to avoid silent overwrites.

## Output contract

`build/ffspatial_adapter/` contains:
1. `ffspatial_normalized_observations.csv`: eight municipality observations from Uppsala 2022, with exactly the FF-Spatial `qgis/materialize_observations.FIELDS` column names/order.
2. `ffspatial_provenance.json`: provenance object matching FF-Spatial's `provenance/schema.json` field contract, with source URL, observation period, checksum, transformation trail and explicit licensing/HARP warnings.
3. `ffspatial_adapter_receipt.json`: checksums, FF-Spatial reference commit, original WP07 handoff checksum and release gates.

**Not included:** country-level observations (four source rows, different geography), unverified WP04 inventory counts, inferred spatial features, new geometry, interactive QGIS project, bridge command or export rights approval.

## Data and time semantics

The producer uses `municipality_code` as a four-character text key and exports it to `geography_id`. It carries `reference_period=2022` and `geography_version=SCB_2026_IDENTIFIER_LOOKUP_ONLY_NOT_2022_POLYGONS`. This identifier reference does **not** prove source-matched 2022 polygon geometry. The adapter therefore **cannot** generate `registry/spatial-product.schema.json` compatible output and cannot submit a thematic map.

`licence=UNREVIEWED_NOT_CLEARED_FOR_REDISTRIBUTION` means source re-use terms are not yet approved. An original report's legal terms remain independent of the repository's MIT code license.

The FF-Spatial receiving runtime has **not** imported this package. CI tests direct consumer field equivalence and deterministic transformation, not a live FF-Spatial/QGIS/Mac integration. This distinction must not be hidden.

## Governance and bridge policy

- `bridge_job_created=false`; no file under FF-Spatial `bridge/approved/` or `bridge/queue/`.
- `ffspatial_repository_modified=false`; no push to FF-Spatial.
- `spatial_product_created=false`; no fabricated geometry.
- `release_status=BLOCKED_HARP_RIGHTS_GEOMETRY_AND_DIRECTOR`.
- Director authorises a future FF-Spatial downstream bridge/job separately, after source, vintage and privacy checks.
- HARP RefA and original legal attribution are required before public release.

## Next acceptance step

After real 2022 polygons are sourced under appropriate rights, WP02/WP07 boundary QA and a genuine QGIS `.qgz` runtime test must pass. Then test consumer import against the exact FF-Spatial commit pinned here, review any updated schema, and submit a separately approved integration request. The present adapter does not require modifying FF-Spatial.
