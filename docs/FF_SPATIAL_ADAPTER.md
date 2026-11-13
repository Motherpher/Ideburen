# FF-Spatial adapter contract (read-only discovery 2026-11-13)

Inspected private FF-Spatial README and qgis/README in read-only mode. This project will not write to that repository. FF-Spatial presently separates registry, gateway, provenance, QGIS and local bridge; its own README does NOT assert fully working end-to-end operation.

**Producer**: Ideburen deterministic build emits `municipalities.csv`, `counties.csv`, `uppsala_2022.csv`, `manifest.json` and optional non-spatial `ideburen_tables.gpkg`.

**Consumer contract**: FF-Spatial may consume metadata and deliver polygons only after establishing a compatible boundary vintage; join on 4-digit string code and validate 290 distinct codes, EPSG:3006, geometry integrity and licensing. No automatic network bridge jobs, remote filesystem access, private credentials or writes to FF-Spatial.

**Current state**: data contract drafted; end-to-end binding unverified. `geo/qgis/load_ideburen.py` supplies an explicit, guarded QGIS route requiring real polygon input.
