# WP01 clean-checkout and baseline acceptance

Requirements: Git, Python 3.11+ and network access for a one-time pip installation of dev tools. No QGIS runtime required for WP01. Do not copy local source spreadsheets into the Git repository.

```bash
git clone https://github.com/Motherpher/Ideburen.git
cd Ideburen
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
python -m ideburen.cli validate
python -m pytest -q
python -m ideburen.cli build --out build
python -m ideburen.cli package --input build --out build/ideburen_tables.gpkg
```

Expected output: 21 counties, 290 distinct municipal codes, 8 Uppsala observations totaling 10,821 for **2022**; 4 nonspatial attribute tables. Do **not** label the output an official current register or GIS polygon map. `build/` is ignored.

To ingest *authorized* local seed XLSX, run:

```bash
python -m ideburen.wp04 --municipal /secure/municipal.xlsx --uppsala /secure/uppsala.xlsx --out build/wp04
```

Ingestion creates staging and exception reports, not verified facts. Inspect the reports before curation.

CI: `.github/workflows/validate.yml` repeats the baseline checks on main and pull requests. It uploads a clearly marked nonspatial preview, not a public approved release. See `docs/RELEASE_STATUS.md` for gates.

The canonical WP04 run stages **all nine source worksheets** under `build/wp04/`. This is not the same as the legacy CLI's 362-row selection. Keep the private `original_sheet_rows.jsonl`, `exceptions.csv` and all normalized records outside any release asset. Do not run WP04 against CI build output intended for public artifact publication.
