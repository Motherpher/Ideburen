# WP02 — Geospatial foundation and Lantmäteriet intake

## Identifier reference — PASSED (2026-11-13)
SCB's official **Län och kommuner 2026 i kodnummerordning** lists exactly 290 municipality codes and 21 county codes. All 290 code/name pairs were compared bidirectionally against the previously staged reference and **all match**. Source: https://www.scb.se/hitta-statistik/regional-statistik-och-kartor/regionala-indelningar/lan-och-kommuner/lan-och-kommuner-i-kodnummerordning/. See `data/reference/scb_2026_identifiers_verification.json` and `docs/WP02_SCB_VERIFICATION.md`.

## Geographical boundary sourcing
**Official intended source:** Lantmäteriet, *Kommun, län och rike Nedladdning*, https://geotorget.lantmateriet.se/geodataprodukter/kommun-lan-rike-nedladdning-api

Official endpoint: `https://api.lantmateriet.se/stac-vektor/v1` (STAC, GeoPackage). Data are described as free of charge under the high-value dataset usage terms, but the Geotorget product page requires login/ordering of access. Do not assert that anonymous download or local QGIS connectivity works without an actual credentialed test.

According to Lantmäteriet, present boundaries update weekly; **annual boundaries** are updated at the turn of the year. Lantmäteriet produces annual versions for **2025 onward**, and SCB is the producer of older annual versions. The national exchange specification was marked **Test**; inspect package schema dynamically instead of assuming fixed layer names. <https://geotorget.lantmateriet.se/dokument/projects/kommun-laen-och-rike-nedladdning/released/1/>

Alternative direct endpoint (for future investigation): `https://api.lantmateriet.se/ogc-features/v1/administrativ-indelning`; requires separate rights/authorization.

## Manual acquisition and validation workflow
1. Obtain user-authorized Lantmäteriet Geotorget credentials/access, outside the public repository. Never commit credentials.
2. Order/download the **2026 annual** countrywide municipality polygons as GeoPackage (prefer SWEREF 99 TM/EPSG:3006).
3. Preserve original GeoPackage outside the repository, record file checksum, license, source URL, boundary date, reference CRS and acquisition date in a **local copy** of `geo/boundaries/provenance.template.json`.
4. Run `python -m ideburen.geography --gpkg /secure/municipal_2026.gpkg --layer <actual_layer> --year 2026 --manifest /secure/provenance.json`. This checks the package metadata, declared CRS, geometry headers, exact 290 code matches, unique join keys, and checksum. It does **not** certify topology.
5. In QGIS/GDAL, independently verify all polygons' geometry type, `isGeosValid`, spatial relations, missing/null geometries, duplicates, unexpected multipart features and boundary topology. Record evidence (QGIS version, job output, 290/290 geometry validations and exclusions).
6. Export a **derived, clearly attributed** geopackage to the analyst workspace, and test joining 2022 Uppsala observations to the 2022 boundary vintage or explicitly document re-expression of 2022 data on 2026 administrative geometry.
7. Do not release a thematic map until Director and HARP RefA gates pass.

## Historical geography (2000–2026)
The file `geo/boundaries/historical_vintage_inventory.csv` is a **coverage requirements inventory**, not a claim that 27 polygon packages are downloaded. Annual vintages prior to 2025 must be sourced and reconciled through SCB/REGINA or designated archived datasets. Never back-cast a 2026 municipality's existence or boundaries to 2000.

## Decision
**WP02 reference and engineering controls implemented.** Physical polygon acquisition, end-to-end QGIS topology verification and annual historical crosswalk coverage remain **blocked/pending**. The full WP02 spatial acceptance gate cannot be marked complete until those tasks are verified.
