import csv,json
from pathlib import Path
import pytest
from ideburen import statistics as s

def test_wp06_validated_source_data():
    result=s.validate()
    assert result["observations"]==12
    assert result["national_observations"]==4
    assert result["regional_municipalities"]==8
    assert result["uppsala_2022_observations_total"]==10821

def test_no_cross_population_or_geography_comparison():
    rows,_,methods=s.normalized()
    n=next(x for x in rows if x["geography_level"]=="country")
    m=next(x for x in rows if x["geography_level"]=="municipality")
    result=s.comparability(n,m,methods)
    assert not result["comparable"]
    assert {"geography_level","method_id","population_id"}.issubset(result["reasons"])

def test_no_fabricated_rate_or_extrapolation():
    with pytest.raises(ValueError,match="verified denominator"):
        s._rate(10,20)

def test_build_qgis_attributes_and_coverage(tmp_path):
    x=s.build(tmp_path/"out")
    assert not x["publication_approved"]
    assert not x["geometry_included"]
    with (tmp_path/"out/municipality_coverage.csv").open(encoding="utf-8") as f:
        coverage=list(csv.DictReader(f))
    assert len(coverage)==290
    assert sum(r["uppsala_2022_observation_status"]=="reported" for r in coverage)==8
    absent=[r for r in coverage if r["uppsala_2022_observation_status"]=="not_in_source_scope"]
    assert len(absent)==282
    assert all(r["uppsala_2022_value"]=="" for r in absent)
    with (tmp_path/"out/comparable_national_years.csv").open(encoding="utf-8") as f:
        comparisons=list(csv.DictReader(f))
    assert len(comparisons)==2
    assert {r["metric_id"]:int(r["reported_delta"]) for r in comparisons}=={
        "civil_society_organisations_total":700,
        "civil_society_ideella_foreningar":350}
    assert all("rounded" in r["caveat"] for r in comparisons)

def test_private_inventory_not_promoted(tmp_path):
    p=tmp_path/"private.csv"
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["row_id","municipality_code","organisation_count","count_status","source_id"])
        w.writeheader()
        w.writerow({"row_id":"x","municipality_code":"0380","organisation_count":"","count_status":"not_reported","source_id":"seed_290"})
    with pytest.raises(ValueError,match="290 distinct municipality"):
        s.build(tmp_path/"bad",p)
