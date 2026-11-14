"""WP07: end-to-end attribute GeoPackage and defensive spatial contract checks.

Real polygon topology requires separately acquired licensed GeoPackage and
QGIS runtime. These tests must not fabricate an official polygon layer.
"""
import json
import sqlite3
from pathlib import Path
import pytest
from ideburen import gis
from ideburen.cli import build as core_build, gpkg
from ideburen.statistics import build as statistics_build


@pytest.fixture
def package(tmp_path):
    output = tmp_path / "wp07"
    core_build(output)
    statistics_build(output)
    target = output / "ideburen_tables.gpkg"
    gpkg(output, target)
    return output, target


def test_wp07_attribute_join_and_provenance(package):
    source, gpkg_path = package
    result = gis.validate_attributes(gpkg_path, source)
    assert result["municipal_codes"] == 290
    assert result["uppsala_2022_reported"] == 8
    assert result["uppsala_2022_not_in_scope_null"] == 282
    assert result["uppsala_total"] == 10821
    assert result["national_observations_not_spatially_joined"] == 4
    assert result["geometries"] == 0
    assert result["publication_approved"] is False


def test_wp07_prepared_nonspatial_handoff(package, tmp_path):
    source, gpkg_path = package
    handoff = tmp_path / "handoff.json"
    result = gis.prepare(gpkg_path, source, handoff)
    assert handoff.is_file()
    saved = json.loads(handoff.read_text())
    assert saved["status"] == "NON_SPATIAL_READY"
    assert saved["boundary_source"] == "authorized Lantmateriet/SCB annual polygon"
    assert saved["required_boundary_year_for_value_map"] == 2022
    assert saved["polygon_file"] is None
    assert saved["release_gate"].startswith("BLOCKED")


def test_wp07_no_2026_geometry_for_2022_statistics(package, tmp_path):
    with pytest.raises(ValueError, match="BOUNDARY_VINTAGE_MISMATCH"):
        gis.validate_spatial_handoff(
            tmp_path/"not_acquired.gpkg", "kommun",
            tmp_path/"not_acquired_manifest.json", 2026,
            intended_observation_year=2022
        )


def test_wp07_manifest_tampering_blocks_handoff(package):
    source, gpkg_path = package
    manifest = source / "statistical_manifest.json"
    meta = json.loads(manifest.read_text(encoding="utf-8"))
    meta["outputs"]["municipality_coverage.csv"] = "f" * 64
    manifest.write_text(json.dumps(meta), encoding="utf-8")
    with pytest.raises(ValueError, match="checksum mismatch"):
        gis.validate_attributes(gpkg_path, source)


def test_wp07_reject_missing_values_as_zero(package):
    source, gpkg_path = package
    db = sqlite3.connect(gpkg_path)
    try:
        db.execute(
            "UPDATE municipality_coverage SET uppsala_2022_value=0 "
            "WHERE municipality_code='0180'"
        )
        db.commit()
    finally:
        db.close()
    with pytest.raises(ValueError, match="imputed"):
        gis.validate_attributes(gpkg_path, source)


def test_wp07_no_national_value_on_polygon_join(package):
    source, gpkg_path = package
    db = sqlite3.connect(gpkg_path)
    try:
        total = db.execute(
            "SELECT count(*) FROM statistical_observations "
            "WHERE geography_level='country'"
        ).fetchone()[0]
        municipal = db.execute(
            "SELECT count(*) FROM municipality_coverage"
        ).fetchone()[0]
    finally:
        db.close()
    assert total == 4
    assert municipal == 290


def test_wp07_qgis_builder_python_syntax():
    import ast
    for path in (
        gis.ROOT/"geo/qgis/build_project.py",
        gis.ROOT/"geo/qgis/load_ideburen.py",
        gis.ROOT/"geo/qgis/verify_official_polygons.py",
    ):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_wp07_no_unverified_geometry_accepted(package):
    source, gpkg_path = package
    with pytest.raises(ValueError, match="Missing provenance key: source_authority"):
        gis.validate_spatial_handoff(
            gpkg_path, "municipalities", source/"statistical_manifest.json",
            2022
        )
