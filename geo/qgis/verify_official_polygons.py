"""Run in the QGIS Python console to audit real authorized municipality polygons.

Boundaries must already be loaded as a valid QGIS QgsVectorLayer in EPSG:3006.
Raises on null/invalid geometries, duplicate/unmatched municipality codes, wrong CRS.
Does not approve license or publish map on its own.
"""
from qgis.core import QgsWkbTypes

def verify_official_municipal_polygons(layer,reference_codes,code_field="kommunkod",boundary_year=None):
    assert boundary_year is not None,"Year/vintage mandatory"
    assert layer and layer.isValid(),"Load an authorized vector polygon layer"
    assert layer.crs().authid()=="EPSG:3006","Wrong analytical CRS"
    assert QgsWkbTypes.geometryType(layer.wkbType())==QgsWkbTypes.PolygonGeometry,"Not polygon geometries"
    expected=set(reference_codes)
    assert len(expected)==290,"Expected 290 distinct official codes"
    seen=set();invalid=[];empty=[];duplicates=[]
    for feat in layer.getFeatures():
        key=str(feat[code_field]).zfill(4)
        if key in seen:duplicates.append(key)
        seen.add(key)
        geom=feat.geometry()
        if geom is None or geom.isNull() or geom.isEmpty():
            empty.append(key)
        elif not geom.isGeosValid():
            invalid.append(key)
    missing=sorted(expected-seen);unexpected=sorted(seen-expected)
    result={"boundary_year":int(boundary_year),"features":layer.featureCount(),
            "unique_codes":len(seen),"duplicate_codes":duplicates,
            "missing_codes":missing,"unexpected_codes":unexpected,
            "invalid_geometries":invalid,"empty_geometries":empty}
    if any([duplicates,missing,unexpected,invalid,empty]) or layer.featureCount()!=290:
        raise ValueError("Polygon QA failed: "+str(result))
    result["result"]="TOPOLOGY_AND_JOIN_PASS_WITHIN_QGIS"
    result["publication_approval"]=False
    return result
