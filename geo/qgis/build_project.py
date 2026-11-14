"""WP07 PyQGIS project builder (run in the QGIS Python console).

Requires a user-supplied AUTHORIZED municipality polygon GeoPackage for the
SAME year as the statistical observation (2022 for this pilot). This script
never downloads boundaries, never creates fake polygons and never publishes.
Do not use the 2026 reference polygons as if they were historic 2022 geometry.

Usage from QGIS:
  import sys
  sys.path.insert(0, "/path/to/Ideburen")
  exec(open("/path/to/Ideburen/geo/qgis/build_project.py").read())
  result = build_ideburen_project(
      "/secure/2022_municipal_boundaries.gpkg", "ACTUAL_POLYGON_LAYER",
      "/secure/boundary_manifest.json",
      "/path/to/Ideburen/build/ideburen_tables.gpkg",
      "/secure/ideburen_uppsala_2022.qgz",
      code_field="kommunkod", boundary_year=2022)
"""
from __future__ import annotations

from pathlib import Path
import json
from ideburen.gis import validate_spatial_handoff, validate_attributes
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsVectorLayerJoinInfo,
    QgsWkbTypes, QgsMapLayerType
)
from qgis.PyQt.QtCore import QVariant


def _check_polygon_layer(layer, code_field, expected):
    if not layer.isValid():
        raise ValueError("Unable to load authorized polygon layer")
    if layer.crs().authid() != "EPSG:3006":
        raise ValueError("Boundary polygon layer must be EPSG:3006")
    if QgsWkbTypes.geometryType(layer.wkbType()) != QgsWkbTypes.PolygonGeometry:
        raise ValueError("Polygon geometry required")
    idx = layer.fields().indexFromName(code_field)
    if idx < 0:
        raise ValueError("Missing polygon join field: " + code_field)
    field = layer.fields().at(idx)
    if field.type() != QVariant.String:
        # A numeric field cannot preserve leading zeroes safely; create an
        # explicit text field through the source preparation workflow.
        raise ValueError("Boundary code field must be TEXT, not numeric")
    codes = []
    invalid = []
    for feature in layer.getFeatures():
        code = feature[code_field]
        if not isinstance(code, str) or len(code) != 4 or not code.isdecimal():
            raise ValueError("Non-4-digit text polygon municipality key")
        codes.append(code)
        shape = feature.geometry()
        if shape is None or shape.isNull() or shape.isEmpty() or not shape.isGeosValid():
            invalid.append(code)
    if invalid:
        raise ValueError("Invalid or empty polygon geometries: " + str(invalid))
    if len(codes) != 290 or set(codes) != set(expected) or len(set(codes)) != 290:
        raise ValueError("Missing, surplus or duplicated municipality geometries")
    return {"polygon_count": len(codes), "invalid_geometry_count": 0}


def build_ideburen_project(
    boundary_gpkg, boundary_layer, boundary_manifest,
    attributes_gpkg, project_path,
    *, code_field="kommunkod", boundary_year=2022,
    source_dir=None
):
    """Create a guarded QGIS project, only with verified and year-matched data.

    In-memory project uses *separate layers* for references and observations.
    A successful save does NOT clear the HARP/Director publication gate.
    """
    if source_dir is None:
        source_dir = str(Path(attributes_gpkg).parent)
    attr = validate_attributes(attributes_gpkg, source_dir)
    boundary = validate_spatial_handoff(
        boundary_gpkg, boundary_layer, boundary_manifest, boundary_year,
        code_field=code_field, intended_observation_year=2022
    )
    polygon = QgsVectorLayer(
        str(Path(boundary_gpkg).resolve()) + "|layername=" + boundary_layer,
        "Municipalities / authorized 2022 polygons", "ogr"
    )
    coverage = QgsVectorLayer(
        str(Path(attributes_gpkg).resolve()) + "|layername=municipality_coverage",
        "Uppsala 2022 / source coverage", "ogr"
    )
    observations = QgsVectorLayer(
        str(Path(attributes_gpkg).resolve()) + "|layername=statistical_observations",
        "Statistical observations / 2022 + national refs", "ogr"
    )
    if not coverage.isValid() or not observations.isValid():
        raise ValueError("QGIS could not open attribute tables")
    keys = set()
    coverage_count = 0
    for row in coverage.getFeatures():
        code = row["municipality_code"]
        if not isinstance(code, str) or len(code) != 4 or not code.isdecimal():
            raise ValueError("Coverage code must be four-character text")
        if code in keys:
            raise ValueError("Duplicate coverage municipality code")
        keys.add(code)
        coverage_count += 1
    if coverage_count != 290:
        raise ValueError("Coverage requires all 290 municipality keys")
    result = _check_polygon_layer(polygon, code_field, keys)
    if coverage.fields().indexFromName("municipality_code") < 0:
        raise ValueError("Missing coverage join field")
    # Attach an exact key-to-key attribute join. NO foreign-year conversion.
    join = QgsVectorLayerJoinInfo()
    join.setJoinLayer(coverage)
    join.setJoinFieldName("municipality_code")
    join.setTargetFieldName(code_field)
    join.setUsingMemoryCache(True)
    join.setPrefix("ideburen_")
    polygon.addJoin(join)
    # The QGIS project is deliberately not treated as a released thematic
    # map and uses neutral/default polygon styling until human review.
    project = QgsProject()
    project.setCrs(polygon.crs())
    project.addMapLayer(polygon)
    project.addMapLayer(coverage)
    project.addMapLayer(observations)
    output = Path(project_path).resolve()
    if output.suffix.lower() != ".qgz":
        raise ValueError("Project must be saved as .qgz")
    output.parent.mkdir(parents=True, exist_ok=True)
    project.setFileName(str(output))
    if not project.write():
        raise ValueError("QGIS project could not be written")
    receipt = {
        "project": str(output),
        "project_exists": output.is_file(),
        "boundary_year": 2022,
        "attribute_sha256": attr["package_sha256"],
        "polygon_sha256": boundary["boundary_metadata"]["geopackage_sha256"],
        "join_type": "strict_text_municipality_code",
        "geometry_validation": result,
        "qgis_runtime_verified": True,
        "public_release": False,
        "next_gate": "HARP_REFA_AND_DIRECTOR",
    }
    output.with_suffix(".qgis_receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return receipt
