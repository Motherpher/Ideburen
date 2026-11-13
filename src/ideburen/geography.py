"""WP02 official-geography gates; validates a supplied polygon GeoPackage.

Python standard library only: verifies metadata, codes, feature counts, binary
envelopes and declared CRS. Full topology requires GDAL/QGIS verification.
No network access, no source acquisition or credential handling.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,re,sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def codes():
    with (ROOT/"data/curated/dimensions/municipalities.csv").open(encoding="utf-8",newline="") as f:
        return {r["municipality_code"] for r in csv.DictReader(f)}

def qa(path,layer,field="kommunkod",year=None,manifest=None):
    src=Path(path)
    if not src.is_file() or src.suffix.casefold()!=".gpkg":
        raise ValueError("An existing .gpkg polygon file is required")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*",layer):raise ValueError("Unsafe layer name")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*",field):raise ValueError("Unsafe join field")
    if year is None or not 2000<=int(year)<=2100:
        raise ValueError("Boundary reference year is mandatory (2000–2100)")
    if manifest is None or not Path(manifest).is_file():
        raise ValueError("Boundary provenance manifest is required")
    prov=json.loads(Path(manifest).read_text(encoding="utf-8"))
    for key in ("source_authority","source_url","boundary_year","license","acquisition_date","source_crs","sha256","usage_rights_reviewed"):
        if key not in prov:raise ValueError("Missing provenance key: "+key)
    if not prov["usage_rights_reviewed"]:
        raise ValueError("Boundary license/rights not approved for analysis")
    if int(prov["boundary_year"])!=int(year):raise ValueError("Boundary year mismatch")
    checksum=hashlib.sha256(src.read_bytes()).hexdigest()
    if checksum!=prov["sha256"]:raise ValueError("GeoPackage checksum mismatch")
    db=sqlite3.connect(f"file:{src.as_posix()}?mode=ro",uri=True)
    try:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='gpkg_geometry_columns'").fetchone():
            raise ValueError("Missing GeoPackage geometry metadata")
        record=db.execute("SELECT table_name,column_name,geometry_type_name,srs_id FROM gpkg_geometry_columns WHERE table_name=?",(layer,)).fetchone()
        if not record:raise ValueError("No registered feature layer: "+layer)
        _,geom,typ,srid=record
        if srid!=3006:raise ValueError("Expected native Swedish analysis CRS EPSG:3006; reproject first with QGIS/GDAL and preserve source CRS")
        if "POLYGON" not in typ.upper() and typ.upper()!="GEOMETRY":
            raise ValueError("Municipality boundaries must be polygons")
        pragma=db.execute(f'PRAGMA table_info("{layer}")').fetchall()
        cols=[r[1] for r in pragma]
        if field not in cols or geom not in cols:raise ValueError("Join or geometry column missing")
        cur=db.execute(f'SELECT "{field}", "{geom}" FROM "{layer}"')
        found=[]
        for code,geometry in cur:
            k=str(code or "")
            if not re.fullmatch(r"\d{4}",k):raise ValueError("Bad code: "+k)
            if geometry is None or not isinstance(geometry,bytes) or not geometry.startswith(b"GP"):
                raise ValueError("Null or invalid GeoPackage geometry header: "+k)
            found.append(k)
        if len(found)!=290 or len(set(found))!=290:
            raise ValueError("Expected exactly 290 unique municipality polygon records")
        unknown=set(found)-codes()
        omitted=codes()-set(found)
        if unknown or omitted:raise ValueError("Geographic join failure: unknown="+str(sorted(unknown))+" missing="+str(sorted(omitted)))
        return {"boundary_year":int(year),"geopackage_sha256":checksum,"feature_count":len(found),
                "unique_codes":len(set(found)),"expected_codes":290,
                "crs":"EPSG:3006","result":"METADATA_KEYS_PASS",
                "topology_validation":"REQUIRED_IN_QGIS",
                "status":"NOT_A_RELEASE_APPROVAL"}
    finally:db.close()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--gpkg",required=True);p.add_argument("--layer",required=True)
    p.add_argument("--code-field",default="kommunkod");p.add_argument("--year",type=int,required=True)
    p.add_argument("--manifest",required=True)
    a=p.parse_args()
    print(json.dumps(qa(a.gpkg,a.layer,a.code_field,a.year,a.manifest),ensure_ascii=False,indent=2))

if __name__=="__main__":main()
