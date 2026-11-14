"""WP07 GIS delivery and provenance gates.

There is no polygon data in this repository. This module validates the
attribute-only GeoPackage and prepares a strictly non-spatial QGIS handoff.
Spatial validation requires separate, authorised, vintage-appropriate boundary
data and the existing WP02 geography.qa() checks.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from .cli import ROOT, read_csv
from .geography import qa as validate_geography

EXPECTED_TABLES = {
    "municipalities": 290,
    "counties": 21,
    "uppsala_2022": 8,
    "statistical_observations": 12,
    "municipality_coverage": 290,
    "comparable_national_years": 2,
}
SOURCE_OBSERVATION_YEAR = 2022


def _sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def _require_municipal_codes(codes, label):
    if len(codes) != 290 or any(not re.fullmatch(r"\d{4}", k) for k in codes):
        raise ValueError(f"{label}: expected 290 four-digit municipality codes")
    if len(set(codes)) != 290:
        raise ValueError(f"{label}: duplicate municipality codes")


def validate_attributes(gpkg, source_dir):
    """Validate a QGIS-ready attribute package, never pretend it has geometries.

    Cross-checks CSV checksums against WP06 statistics manifest, verifies all
    national and regional grains, and confirms missing=SQL NULL, not zero.
    """
    source = Path(source_dir).resolve()
    package = Path(gpkg).resolve()
    if not package.is_file() or package.suffix.casefold() != ".gpkg":
        raise ValueError("An existing attribute GeoPackage (.gpkg) is required")
    statistical_manifest = source / "statistical_manifest.json"
    if not statistical_manifest.is_file():
        raise ValueError("Missing WP06 statistical_manifest.json")
    metadata = json.loads(statistical_manifest.read_text(encoding="utf-8"))
    if metadata.get("publication_approved") is not False:
        raise ValueError("Unexpected public-release claim")
    if metadata.get("geometry_included") is not False:
        raise ValueError("Unexpected claim of included geometry")
    for name, checksum in metadata.get("outputs", {}).items():
        filename = source / name
        if not filename.is_file() or _sha256(filename) != checksum:
            raise ValueError("Statistical input checksum mismatch: " + name)
    required_sources = ("statistical_observations.csv", "municipality_coverage.csv")
    if any(x not in metadata.get("outputs", {}) for x in required_sources):
        raise ValueError("WP06 source manifest lacks required statistical tables")
    db = sqlite3.connect(f"file:{package.as_posix()}?mode=ro", uri=True)
    try:
        if db.execute("PRAGMA application_id").fetchone()[0] != 1196444487:
            raise ValueError("GeoPackage application id does not match specification")
        if db.execute("SELECT count(*) FROM sqlite_master WHERE name='gpkg_contents'").fetchone()[0] != 1:
            raise ValueError("Not a valid GeoPackage contents registry")
        contents = {
            name: typ for name, typ in
            db.execute("SELECT table_name,data_type FROM gpkg_contents").fetchall()
        }
        if any(typ == "features" for typ in contents.values()):
            raise ValueError("WP07 attribute package must NOT include unverified polygons")
        for name, count in EXPECTED_TABLES.items():
            if contents.get(name) != "attributes":
                raise ValueError("Missing or non-attribute QGIS table: " + name)
            actual = db.execute(f'SELECT count(*) FROM "{name}"').fetchone()[0]
            if actual != count:
                raise ValueError(f"{name}: expected {count}, got {actual}")
        ref_codes = [x["municipality_code"] for x in
                     read_csv(ROOT / "data/curated/dimensions/municipalities.csv")]
        _require_municipal_codes(ref_codes, "official codes")
        actual_codes = [
            r[0] for r in db.execute("SELECT municipality_code FROM municipality_coverage")
        ]
        _require_municipal_codes(actual_codes, "QGIS coverage")
        if set(ref_codes) != set(actual_codes):
            raise ValueError("Municipality coverage differs from the official SCB 2026 reference")
        gpkg_count = db.execute(
            "SELECT count(*) FROM municipality_coverage "
            "WHERE uppsala_2022_observation_status='reported'"
        ).fetchone()[0]
        if gpkg_count != 8:
            raise ValueError("WP06 Uppsala coverage must contain exactly eight reported rows")
        reported = db.execute(
            "SELECT municipality_code, uppsala_2022_value FROM municipality_coverage "
            "WHERE uppsala_2022_observation_status='reported'"
        ).fetchall()
        if any(not isinstance(val, int) for code, val in reported):
            raise ValueError("Report values must be INTEGER in GeoPackage")
        if sum(val for code, val in reported) != 10821:
            raise ValueError("Uppsala 2022 total differs from the source")
        nulls = db.execute(
            "SELECT count(*) FROM municipality_coverage "
            "WHERE uppsala_2022_observation_status='not_in_source_scope' "
            "AND uppsala_2022_value IS NULL"
        ).fetchone()[0]
        if nulls != 282:
            raise ValueError("Missing values were imputed or misrepresented")
        country = db.execute(
            "SELECT count(*) FROM statistical_observations "
            "WHERE geography_level='country' AND geography_code='SE'"
        ).fetchone()[0]
        if country != 4:
            raise ValueError("National observations must remain separate from municipal geometry")
        wrong = db.execute(
            "SELECT count(*) FROM statistical_observations "
            "WHERE geography_level='municipality' AND "
            "(observation_year != '2022' OR substr(geography_code,1,2) != '03')"
        ).fetchone()[0]
        if wrong:
            raise ValueError("Unapproved municipality observation geography/year")
        numeric_type = {r[1]:r[2] for r in db.execute("PRAGMA table_info('municipality_coverage')")}
        if numeric_type.get("uppsala_2022_value") != "INTEGER":
            raise ValueError("GeoPackage numeric measure was exported as text")
    finally:
        db.close()
    return {
        "package_sha256": _sha256(package),
        "package_type": "GeoPackage 1.2 / attribute tables only",
        "geometries": 0,
        "municipal_codes": 290,
        "uppsala_2022_reported": 8,
        "uppsala_2022_not_in_scope_null": 282,
        "uppsala_total": 10821,
        "national_observations_not_spatially_joined": 4,
        "statistical_manifest_verified": True,
        "result": "ATTRIBUTE_PACKAGE_VALIDATED",
        "publication_approved": False,
    }


def validate_spatial_handoff(
    polygon_gpkg, layer, manifest, boundary_year, code_field="kommunkod",
    intended_observation_year=SOURCE_OBSERVATION_YEAR
):
    """Reject any analytic map that mixes observation and polygon vintages.

    The WP02 standard-library validator checks the original geometries' file
    envelope and codes; it explicitly does not replace QGIS topology checks.
    """
    year = int(boundary_year)
    if year != int(intended_observation_year):
        raise ValueError(
            "BOUNDARY_VINTAGE_MISMATCH: observations and polygon vintage differ; "
            "source-specific historic crosswalk + independent approval required"
        )
    validation = validate_geography(
        polygon_gpkg, layer, field=code_field, year=year, manifest=manifest
    )
    if validation.get("result") != "METADATA_KEYS_PASS":
        raise ValueError("Original polygon metadata did not pass WP02")
    return {
        "boundary_metadata": validation,
        "analytic_observation_year": intended_observation_year,
        "vintage_status": "MATCHED",
        "qgis_geometry_topology": "REQUIRED_IN_QGIS_NOT_YET_VERIFIED",
        "publication_approved": False,
    }


def prepare(gpkg, source_dir, out):
    """Create a reusable NON-SPATIAL handoff record for downstream FF-Spatial."""
    result = validate_attributes(gpkg, source_dir)
    destination = Path(out).resolve()
    if ROOT == destination or ROOT in destination.parents:
        if not (ROOT / "build" in destination.parents):
            raise ValueError("GIS handoff is a derived build artifact, not canonical data")
    destination.parent.mkdir(parents=True, exist_ok=True)
    handoff = {
        "contract": "ideburen.wp07.qgis.v1",
        "status": "NON_SPATIAL_READY",
        "attribute_checks": result,
        "join_code": "municipality_code",
        "join_type": "four_character_text",
        "analysis_crs": "EPSG:3006",
        "observation_year": SOURCE_OBSERVATION_YEAR,
        "required_boundary_year_for_value_map": SOURCE_OBSERVATION_YEAR,
        "boundary_source": "authorized Lantmateriet/SCB annual polygon",
        "polygon_file": None,
        "polygon_checks": "NOT_RUN",
        "qgis_project": "NOT_CREATED",
        "release_gate": "BLOCKED_BY_POLYGON_TOPOLOGY_HARP_AND_DIRECTOR",
        "source_checksum": result["package_sha256"],
    }
    destination.write_text(json.dumps(handoff, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    return handoff


def main(argv=None):
    p = argparse.ArgumentParser(prog="ideburen.gis")
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate-attributes")
    v.add_argument("--gpkg", required=True)
    v.add_argument("--source-dir", required=True)
    h = sub.add_parser("prepare")
    h.add_argument("--gpkg", required=True)
    h.add_argument("--source-dir", required=True)
    h.add_argument("--out", required=True)
    s = sub.add_parser("validate-boundary")
    s.add_argument("--gpkg", required=True)
    s.add_argument("--layer", required=True)
    s.add_argument("--manifest", required=True)
    s.add_argument("--year", type=int, required=True)
    s.add_argument("--code-field", default="kommunkod")
    s.add_argument("--observation-year", type=int, default=2022)
    a = p.parse_args(argv)
    if a.cmd == "validate-attributes":
        result = validate_attributes(a.gpkg, a.source_dir)
    elif a.cmd == "prepare":
        result = prepare(a.gpkg, a.source_dir, a.out)
    else:
        result = validate_spatial_handoff(
            a.gpkg, a.layer, a.manifest, a.year,
            code_field=a.code_field,
            intended_observation_year=a.observation_year
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
