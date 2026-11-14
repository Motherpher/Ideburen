# WP07 — QGIS spatial integration and strict audit gates

**Date:** 2026-11-14. **Status:** reproducible non-spatial GeoPackage + strict, guarded spatial QGIS project builder. Final QGIS polygon/topology evaluation pending authorized annual boundary data. **No official polygon acquired or invented by WP07.**

## Design authority
Director-accepted ADR-0001 (originals, derived data, publication control) and ADR-0002 (SCB codes, EPSG:3006, source vintages and read-only FF-Spatial boundary). WP02 authoritative identifier registry and WP06 statistical coverage/method definitions are prerequisites.

### Two distinct GIS products

1. **Non-spatial research exchange** — seven attribute tables (municipalities, counties, Uppsala 2022, publications, statistical observations, municipality coverage, SCB year comparisons), inside `ideburen_tables.gpkg`. Intended for QGIS and subsequent spatial joins only. All four national observations with geography `SE` remain outside municipal polygon joins. Eight Uppsala 2022 municipality values are present; the other 282 municipality keys explicitly have `NULL` values because they are outside the report's regional scope.
2. **Spatial project builder** — `geo/qgis/build_project.py` can produce a real `.qgz` project only after a separately authorized, checksum-verified, *2022 vintage* municipal polygon GeoPackage is available. It validates all 290 geometries and joins to municipality coverage by a **four-character TEXT code**. It does not overwrite the user's current QGIS project, and styling/publication remains deliberately unapproved.

### Reproducible attribute build and inspection

```bash
python -m ideburen.cli build --out build
python -m ideburen.statistics build --out build
python -m ideburen.cli package --input build --out build/ideburen_tables.gpkg
python -m ideburen.gis validate-attributes --gpkg build/ideburen_tables.gpkg --source-dir build
python -m ideburen.gis prepare --gpkg build/ideburen_tables.gpkg --source-dir build --out build/gis_handoff.json
```

The last command emits a **non-spatial readiness receipt**, not a map or licensed polygon release. Its `status=NON_SPATIAL_READY` explicitly indicates `polygon_checks=NOT_RUN`, `qgis_project=NOT_CREATED` and `release_gate=BLOCKED_BY_POLYGON_TOPOLOGY_HARP_AND_DIRECTOR`.

### What the automated preflight tests

- Checks the GeoPackage application ID, table types, all seven required source tables and row counts.
- Checks the original statistical manifest and SHA-256 for each input CSV.
- Checks uniqueness, format and exhaustiveness of 290 municipal join keys against the official SCB 2026 dimension.
- Checks the **typed numeric** Uppsala value column, 8 observed rows, 10,821 total, and SQL `NULL` for 282 out-of-scope rows.
- Verifies the four national observations remain distinct from municipality-level data.
- Rejects accidental geometry in the attribute-only package, license-like release claims and source checksum tampering.

## Source-matched geometry — separate gate

Lantmäteriet access has been requested by the user, and remains unconfirmed. The intended 2026 annual polygon package may be used for **2026 administrative reference work**, but NOT silently for the **2022 statistical value map**. This WP07 pilot requires **annual 2022 boundaries** (SCB historical source or an authorized historical geospatial provider). A 2026 boundary dataset fails the `BOUNDARY_VINTAGE_MISMATCH` gate for the 2022 values. Crosswalking historic observations onto a different boundary vintage is a separate method/audit task requiring data and authorization; a disclaimer alone is insufficient.

When licensed 2022 boundaries are obtained:

1. Record the source, boundary year, license/rights approval, acquisition date, source CRS, layer name and original file SHA-256 in a private copy of `geo/boundaries/provenance.template.json`.
2. Inspect the actual polygon layer and its **TEXT** municipality code field; convert any numeric codes losslessly into an explicit four-character source text field in a **derived** working copy, without altering the original dataset.
3. Run `python -m ideburen.gis validate-boundary --gpkg /secure/2022_kommun.gpkg --layer ACTUAL_LAYER --code-field kommunkod --year 2022 --observation-year 2022 --manifest /secure/provenance.json`.
4. In an authorized QGIS Python environment, run `geo/qgis/build_project.py` using the call shown below. The script checks QGIS geometry type, polygon validity, original municipality code coverage and strict text joins, then writes a **local .qgz**.
5. Independently review multipart feature expectations, holes/overlaps between adjacent boundaries, gaps, topology and attribute join behaviour; record QGIS version and a source-specific QA receipt. The builder does not claim that all boundary-to-boundary topology invariants were tested.
6. Verify historical comparability, styling/legend, data rights, HARP RefA and Director sign-off before publishing any map.

```python
import sys
sys.path.insert(0, "/path/to/Ideburen/src")
exec(open("/path/to/Ideburen/geo/qgis/build_project.py", encoding="utf-8").read())
receipt = build_ideburen_project(
    "/secure/kommun_2022.gpkg",
    "ACTUAL_POLYGON_LAYER",
    "/secure/provenance_2022.json",
    "/path/to/Ideburen/build/ideburen_tables.gpkg",
    "/secure/ideburen_uppsala_2022.qgz",
    boundary_year=2022,
    code_field="kommunkod",
    source_dir="/path/to/Ideburen/build"
)
```

**This code has been syntax/contract checked in CI, but the PyQGIS runtime cannot be exercised without QGIS and the authorized polygon layer.** The prior `load_ideburen.py` routine that cleared existing QGIS project state and accepted unvalidated geometry has been disabled.

## Future WP08 contract

The statically versioned `gis_handoff.json` and the attribute GeoPackage form the producer-side handoff to FF-Spatial; FF-Spatial is a separate downstream consumer. No remote writes, bridge jobs, credentials or FF-Spatial repository changes occur in WP07.

## Scope exclusions

No nationwide municipality-level organisation measure beyond the eight-municipality Uppsala source. No 2000–2026 historical polygon inventory downloaded. No invented polygon/centroid, no automatic choropleth publication, no rates per inhabitant without denominator, no temporal boundary reconstruction, no full HARP RefA source release.
