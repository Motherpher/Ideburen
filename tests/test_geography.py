import json,hashlib,sqlite3,tempfile
from pathlib import Path
import pytest
from ideburen.geography import qa,ROOT

def test_scb_reference_manifest():
    m=json.loads((ROOT/"data/reference/scb_2026_identifiers_verification.json").read_text(encoding="utf-8"))
    assert m["checked_municipalities"]==290 and m["checked_counties"]==21
    assert m["missing_codes"]==m["extra_codes"]==m["name_code_mismatches"]==0
    assert not m["verified_geometry"]

def test_provenance_required_even_if_file_exists():
    with tempfile.TemporaryDirectory() as d:
        path=Path(d)/"dummy.gpkg";path.write_bytes(b"not a gpkg")
        with pytest.raises(ValueError,match="Boundary provenance manifest is required"):
            qa(path,"kommun",year=2026)

def test_rights_gate_before_reading_polygons():
    with tempfile.TemporaryDirectory() as d:
        path=Path(d)/"dummy.gpkg";path.write_bytes(b"not a gpkg")
        source={"source_authority":"Lantmäteriet","source_url":"https://example.org",
                "boundary_year":2026,"license":"not approved","acquisition_date":"2026-11-13",
                "source_crs":"EPSG:3006","sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                "usage_rights_reviewed":False}
        manifest=Path(d)/"manifest.json";manifest.write_text(json.dumps(source))
        with pytest.raises(ValueError,match="not approved"):
            qa(path,"kommun",year=2026,manifest=manifest)
