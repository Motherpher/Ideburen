# WP04 — Source workbook import and normalization

**Completed technical pilot:** 2026-11-13. Public GitHub code and contract; original workbooks and their row-level staging remain in the private analyst workspace.

## Input contract (source versions)
Two user-provided XLSX workbooks, exact SHA-256 checksums pinned in `config/wp04_seed_contract.json`:
1. `seed_290`: nation-wide **research inventory**, not an official register of 290 complete municipal reports.
2. `seed_uppsala`: eight municipal register portals, 37 historical Knivsta association memberships and 27 municipal decision-chain entries (not complete current memberships or fully audited decisions).

The XML parser reads all nine sheets, preserves actual row numbers, source SHA-256, numeric-versus-string cells, explicit zero and blank/null distinctly, and rejects formula cells (even where Excel caches a value), macros and external links.

## Canonical command

```bash
python -m ideburen.wp04 \
 --municipal /secure/Ideburen_kommuninventering_290_2026-11-13.xlsx \
 --uppsala /secure/Barnombudet_Foreningsregister_och_Beslutskedjor_Uppsala_Lan_2026-11-13.xlsx \
 --out build/wp04
```

Files under `build/wp04/` are local staging only:
- `original_sheet_rows.jsonl`: entire content of all nonblank worksheet rows, with source-sheet and row provenance.
- `municipal_inventory.csv`: one record per municipality (290).
- `municipal_supplements.csv`: separately indexed 23 local/municipal report entries, **not independent observations**.
- `historical_associations.csv`: 37 Knivsta 2023 historical council members, not a complete municipal list.
- `association_register_sources.csv`: eight registry portals, not fetched organization membership.
- `decision_events.csv`: 27 events with original dates and verification text preserved.
- `records_requests.csv`: 16 drafted document requests, not submitted requests.
- `reference_links.csv`, `method_notes_national.csv`, `method_notes_uppsala.csv`: provenance links and limitations.
- `exceptions.csv`: blocking errors (unknown geography, row drift, unsafe counts).
- `manifest.json`: input hashes, counts, coverage, empty-vs-zero, source/release status.

## Local acceptance result
| Category | Rows |
| --- | ---: |
| National municipality inventory | 290 |
| Municipal supplements | 23 |
| National key source links | 5 |
| National method notes | 6 |
| Uppsala municipality registry portals | 8 |
| Historical Knivsta member organizations | 37 |
| Decision events | 27 |
| Document-request templates | 16 |
| Uppsala method notes | 9 |
| **Original preserved source rows** | **421** |

Local source audit: **290 unique SCB 2026 municipality code mappings** and **0 geographic exceptions**. In the national seed, 10 municipalities have an explicit `Antal organisationer` value and **280 have it blank/unknown**. No explicit numeric zero occurs in those 290 rows. Missing counts are never interpreted as zero and no fictional national completeness is inferred.

## Method limits
The reference is **SCB 2026 geography**, not year-specific polygons for pre-2026 observations. The source workbook is a research index; reported organisation counts must not become verified measures without independent HARP source, population and methodology audits. A year marked “2022” in the index is not necessarily the study's publication year.

## Security
Public Git contains code, schema, expected row counts and SHA-256 digests of authorized user-supplied inputs, **not** raw XLSX, private Drive IDs, personal contact data or the original row JSON. Github Actions tests only synthetic XLSX fixtures and static nonspatial public datasets.

## Acceptance gate
`python -m pytest -q` and `python -m ideburen.wp04 --help` on clean checkout, plus the local run against the exact input hashes. Original reports' claim validation and release permissions remain WP03/WP09 and Director gates.
