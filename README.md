# Ideburen — Sveriges civilsamhälle i data, beslut och geografi

**Status: implementation / pre-release.** National evidence infrastructure for Sweden's 21 counties and 290 municipalities (2000 onward).

## Scope
1. **Organisations**: registered entities, sector, activity, employment and geographic distribution.
2. **Institutions**: LÖK, RÖK, policy, guidelines, councils and partnership structures.
3. **Decision pathways**: initiative → consultation → preparation → decisions → implementation → follow-up.

Evidence is not a completed national census: initial Excel files are **research inventories**, not population data. Blank and unverified are never zero.

## Architecture
Google Drive stores original documents; this repository stores public metadata, scripts, curated tables, audits and versioned exports. QGIS consumes spatially referenced files; [FF-Spatial](https://github.com/Motherpher/FF-Spatial) remains a separate, read-only downstream integration target.

## Quick start
```bash
python -m pip install -e '.[dev]'
python -m ideburen.cli validate
python -m pytest -q
# When authorized local seed spreadsheets are available:
python -m ideburen.wp04 --municipal /secure/national_inventory.xlsx --uppsala /secure/uppsala_registry.xlsx --out build/wp04
python -m ideburen.cli package --input build --out build/ideburen_tables.gpkg
```

See `docs/ARCHITECTURE.md`, `docs/HARP.md`, `docs/QGIS.md` and `docs/RELEASE_STATUS.md`. The GeoPackage is **non-spatial until an authorized boundary dataset is supplied**; do not present it as a choropleth layer.

**Authority:** Director; Pius System Codex 5.0 Appendix O/HARP. No autonomous inference of missing evidence. No private data, tokens, unlicensed PDFs or organizational contact persons in this public repository.

## Source & publication registry (WP03)
`manifests/source_registry_v1.csv` maintains stable source IDs, Harvard-style references, provenance, HARP/rights and checksum states. `data/curated/publications/publication_registry_v1.csv` records publication editions; `study_family_registry_v1.csv` prevents duplicate counting of the same study. Validate using `python -m ideburen.sources validate`. Original documents and private Drive file identifiers are not published. See [WP03 documentation](docs/WP03_SOURCE_REGISTRY.md) and [acceptance](docs/WP03_ACCEPTANCE.md).

## WP04 – reproducible spreadsheet ingest
The canonical two-workbook inventory ingest is `python -m ideburen.wp04`; the earlier `ideburen.cli ingest` remains a legacy compatibility path and does **not** preserve all nine sheets. WP04 records all source rows locally, separates municipal profiles, supplements, historical association membership and decision-chain stages, and blocks false zero values or unknown municipality joins. All generated staging must remain private; **no original XLSX or raw row exports belong in Git**. See [WP04 acceptance](docs/WP04_ACCEPTANCE.md).
