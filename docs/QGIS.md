# QGIS user guide — Ideburen

**WP07 baseline:** the QGIS-compatible **non-spatial** data product can already be opened in QGIS through `Layer > Add Layer > Add Vector Layer`, pointing at the generated `build/ideburen_tables.gpkg`. Select `municipality_coverage` (290 rows) and `statistical_observations` (12 rows). The table `statistical_observations` includes four national `SE` references, not municipal data.

**Real municipality polygons:** join by four-character `municipality_code` TEXT, not by names or integers. Use authorized historic **2022 polygons** for the Uppsala 2022 value map. Current/2026 polygons are only suitable for same-vintage administrative reference until a legally and methodologically accepted historical crosswalk is available.

`geo/qgis/build_project.py` provides a guarded PyQGIS builder for the annual 2022 polygon input with a separate provenance file. It validates exact 290 municipality keys, geometry validity, EPSG:3006 and code-field type. It uses a standalone `QgsProject()`, preserving the user's open project. An unvalidated, unlicensed or mismatched boundary is rejected.

Commands and complete acceptance gates: [WP07 implementation](WP07_QGIS_INTEGRATION.md), [acceptance](WP07_ACCEPTANCE.md).

**No geometry has been downloaded, fabricated or included in CI.** The QGIS project builder requires external data and an actual QGIS runtime; it does not imply an existing certified 2022 map.
