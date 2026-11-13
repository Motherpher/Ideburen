# Architecture and boundaries

`Drive → source manifest → reproducible ingestion → staging → curation → CSV/GeoPackage → QGIS/FF-Spatial`.

Data model: `source`, `publication`, `geography`, `method`, `metric`, `observation`, `institution`, `decision_event`. Decision chains can branch; a missing recorded link is **not proof of a missing policy action**.

**Grain** for Uppsala sample: registered legal entities by municipality of registered seat, 2022, seven legal forms including housing associations, foundations and joint-property associations. NOT the number of grant-receiving clubs or currently active NGOs.

FF-Spatial inspected read-only: it has `registry/`, `gateway/`, `provenance/`, `qgis/` and `bridge/`; its QGIS policy uses EPSG:3006 for Swedish analysis and separates source acquisition from derived layers. No files in FF-Spatial should be changed by this repo.

**Spatial boundaries are NOT included**. They must come from an authorized documented Lantmäteriet (current/annual) GeoPackage. Never generate fictitious shapes/centroids or treat a nonspatial table as a map.
