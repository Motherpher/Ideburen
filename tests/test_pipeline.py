import csv,sqlite3,tempfile
from pathlib import Path
from ideburen.cli import validate,build,gpkg,ROOT,read_csv,normalize

def test_geo():
    assert validate()["municipalities"]==290
    assert len(read_csv(ROOT/"data/curated/dimensions/counties.csv"))==21
    assert normalize("Östhammars kommun")=="osthammar"

def test_upland_metric():
    obs=read_csv(ROOT/"data/curated/observations/uppsala_2022.csv")
    assert len(obs)==8
    assert sum(int(r["value"]) for r in obs)==10821
    assert all(r["value_year"]=="2022" and "seven_legal_forms" in r["population"] for r in obs)

def test_gpkg_nonspatial():
    with tempfile.TemporaryDirectory() as tmp:
        build(tmp)
        path=Path(tmp)/"tables.gpkg"
        result=gpkg(tmp,path)
        assert result["tables"]["municipalities"]==290
        c=sqlite3.connect(path)
        try:
            assert c.execute("SELECT count(*) FROM gpkg_contents WHERE data_type='features'").fetchone()[0]==0
        finally:c.close()
