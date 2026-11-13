# WP06 — Statistical Pipeline v1.0

Status: engineering implemented; source-specific HARP RefA and nationwide municipal coverage NOT complete. Date: 2026-11-13.

## Data and definition contracts
- Seven-form Uppsala 2022 registered entity series: 8 municipalities, 10,821 total (working report 119, Table 2 p.26). This is NOT SCB X105 national population.
- SCB X105 national summary 2023: 265,700 organisations / 163,900 ideella föreningar. Official report corrected 2026-04-01.
- SCB X105 national summary 2024: 266,400 organisations / 164,250 ideella föreningar. Official report corrected 2026-08-14.
- National 2023→2024 differences +700 total, +350 ideella; values from rounded official summary, not a precisely estimated growth rate.
- Comparable observations must match metric ID, unit, population, geography and level, method/series. Refuse Uppsala seven-form versus SCB X105 direct comparisons.

## Source references
- Uppsala: https://urn.kb.se/resolve?urn=urn:nbn:se:esh:diva-11246
- SCB 2023 corrected: https://www.scb.se/hitta-statistik/statistik-efter-amne/naringsverksamhet-och-utrikeshandel/foretagens-produktion-forsaljning-och-ekonomi/civila-samhallet/pong/publikationer/det-civila-samhallet-2023/
- SCB 2024 corrected: https://www.scb.se/publikation/60046
- Sörmland 2024 report (2023 data), with nine municipal appendices: https://utvecklasormland.se/publikationer/kartlaggning-av-civilsamhallet-i-sormland/

## WP04 inventory handling
290 municipality research rows: 10 with counts entered, 280 missing. These counts are NOT a harmonised national statistical dataset; eight point to Uppsala and two to Sörmland. Only local private unverified_inventory_excluded.csv can contain the unverified inventory values. Missing is never zero.
Uppsala 2022 source covers eight municipalities. A 290-municipality coverage table therefore has eight reported and 282 out-of-source-scope, not 282 zeros.
Sörmland's nine municipal annexes belong to one study. No figures from those annexes are promoted until original table, seven-form frame, extraction and geographic assignment are reaudited.

## Reproducible commands
python -m ideburen.statistics validate
python -m ideburen.cli build --out build
python -m ideburen.statistics build --out build
python -m ideburen.cli package --input build --out build/ideburen_tables.gpkg
python -m ideburen.statistics build --out /secure/wp06 --inventory /secure/wp04/municipal_inventory.csv

## Outputs and GIS contract
statistical_observations.csv (12 facts), comparable_national_years.csv, municipality_coverage.csv (290 codes), statistical_manifest.json, and optional private unverified_inventory_excluded.csv.
When WP06 build precedes GeoPackage packaging, three extra attribute tables are included; counts are INTEGER columns, missing is NULL, country code SE remains distinct from four-character municipal code.
WP06 outputs have NO geometries. Boundary vintage and license are WP02 blockers pending Lantmäteriet account. A 2026 polygon geometry must not silently replace a 2022 observation's geography. No per-capita rate without year-matched population denominator.

## Governance and residual risk
Reject missing source locator, unknown metric/method, invalid count, duplicate observation grain, population/geography conflict and unsupported comparisons. Public source overview verification is not equivalent to full table-level HARP RefA. Director approval and rights review required before public data release.
