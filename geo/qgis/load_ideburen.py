"""Paste into QGIS Python console with an authoritative EPSG:3006 municipal polygon layer."""
from qgis.core import QgsProject,QgsVectorLayer,QgsVectorLayerJoinInfo
from pathlib import Path

def create_project(boundaries,gpkg_path,project_path,code_field="kommunkod"):
    assert boundaries and boundaries.isValid()
    assert boundaries.crs().authid()=="EPSG:3006"
    codes=[str(f[code_field]).zfill(4) for f in boundaries.getFeatures()]
    assert len(codes)==290 and len(set(codes))==290
    obs=QgsVectorLayer(str(Path(gpkg_path).resolve())+"|layername=uppsala_2022","Uppsala 2022: 7 legal forms","ogr")
    assert obs.isValid()
    assert all(str(f["municipality_code"]).zfill(4) in codes for f in obs.getFeatures())
    project=QgsProject.instance();project.clear()
    project.addMapLayer(boundaries);project.addMapLayer(obs)
    join=QgsVectorLayerJoinInfo()
    join.setJoinLayer(obs);join.setJoinFieldName("municipality_code")
    join.setTargetFieldName(code_field);join.setUsingMemoryCache(True)
    boundaries.addJoin(join)
    project.setFileName(str(Path(project_path).resolve()))
    assert project.write()
    return project_path
