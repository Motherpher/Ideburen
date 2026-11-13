# GIS contract: QGIS & FF-Spatial

Canonical join keys: `municipality_code` as **four-character text**; `county_code` as two-character text. Name-based joins are prohibited.

`python -m ideburen.cli package --input build --out build/ideburen_tables.gpkg` creates GeoPackage 1.2 **attribute tables only**, valid as QGIS data sources. Supply authoritative polygon data separately, with `boundary_vintage` and license before joining, and check 290 unique keys, invalid shapes, duplicate matches, temporal mismatches and unmatched codes. GeoPackage tables contain no fabricated geometry.

To create an interactive map, use `geo/qgis/load_ideburen.py` in QGIS Python console with a fully validated, locally available municipalities polygon layer. FF-Spatial consumes derived outputs only (no repo modifications, no bridge jobs by default).

Recommended CRS: EPSG:3006. Current boundaries must not be applied to 2000 statistics without documenting changed boundaries; prefer relevant annual boundaries.
