"""WP06: lossless statistical observation processing and comparability gates.

Sources are evidence tables, not interchangeable estimates of a single population.
No network access, extrapolation, interpolation or fabricated observations.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
import sqlite3
from collections import Counter,defaultdict
from pathlib import Path
from .cli import ROOT, read_csv

BASE=ROOT/"data/curated"
METRICS=BASE/"statistics/metrics.csv"
METHODS=BASE/"statistics/methods.csv"
NATIONAL=BASE/"statistics/scb_national_2023_2024.csv"
UPPSALA=BASE/"observations/uppsala_2022.csv"
MUNICIPAL=BASE/"dimensions/municipalities.csv"

def _exact_int(value,which):
    if isinstance(value,bool) or not re.fullmatch(r"(0|[1-9][0-9]*)",str(value)):
        raise ValueError("Invalid nonnegative integer for "+which+": "+str(value))
    return int(value)

def normalized():
    """Return canonical observations at source grain; preserves rounded precision."""
    metrics={x["metric_id"]:x for x in read_csv(METRICS)}
    methods={x["method_id"]:x for x in read_csv(METHODS)}
    places={x["municipality_code"]:x for x in read_csv(MUNICIPAL)}
    if len(metrics)!=3 or len(methods)!=2 or len(places)!=290:
        raise ValueError("Unexpected registry/reference scope")
    obs=[]
    for r in read_csv(UPPSALA):
        code=r["municipality_code"]
        if code not in places or places[code]["county_code"]!="03":
            raise ValueError("Uppsala 2022 municipality outside known Uppsala län")
        if r["population"]!="seven_legal_forms_including_housing_associations":
            raise ValueError("Uppsala statistical population changed")
        obs.append({
            "geography_code":code,"geography_level":"municipality",
            "metric_id":r["metric_id"],"value":str(_exact_int(r["value"],code)),
            "unit":r["unit"],"observation_year":r["value_year"],"source_id":r["source_id"],
            "method_id":r["method_id"],"population_id":"ccf_7_legal_forms_2022",
            "source_version":"working_report_119_2025",
            "source_locator":"table_2_p26",
            "source_url":"https://urn.kb.se/resolve?urn=urn:nbn:se:esh:diva-11246",
            "evidence_status":r["evidence_status"],"precision_status":"integer_table_count",
            "publication_status":"curated_source_extract_pending_fullaudit"
        })
    obs.extend(read_csv(NATIONAL))
    ids=set();national_years=set()
    for x in obs:
        if x["metric_id"] not in metrics or x["method_id"] not in methods:
            raise ValueError("Unknown metric or method")
        m=metrics[x["metric_id"]];method=methods[x["method_id"]]
        if m["population_id"]!=x["population_id"] or method["population_id"]!=x["population_id"]:
            raise ValueError("Statistical population conflict")
        if m["geography_level"]!=x["geography_level"]:
            raise ValueError("Metric geography mismatch")
        if x["unit"]!=m["unit"]:
            raise ValueError("Unit mismatch")
        if not re.fullmatch(r"20[0-9]{2}",x["observation_year"]):
            raise ValueError("Invalid observation year")
        _exact_int(x["value"],x["metric_id"])
        if x["geography_level"]=="country":
            if x["geography_code"]!="SE":raise ValueError("Unsupported national geography")
            if x["precision_status"]!="rounded_reported":
                raise ValueError("National summaries must retain rounding")
            national_years.add(x["observation_year"])
        elif x["geography_code"] not in places:
            raise ValueError("Unknown municipality")
        grain=(x["geography_code"],x["metric_id"],x["observation_year"],x["population_id"])
        if grain in ids:raise ValueError("Duplicate statistical observation grain")
        ids.add(grain)
        if not x["source_id"] or not x["source_locator"] or not x["source_url"]:
            raise ValueError("Missing source provenance")
    if len(obs)!=12 or len([x for x in obs if x["geography_level"]=="municipality"])!=8:
        raise ValueError("WP06 seed scope drift")
    if national_years!={"2023","2024"}:raise ValueError("National years missing")
    sums=sum(_exact_int(x["value"],"uppsala") for x in obs
             if x["geography_level"]=="municipality")
    if sums!=10821:raise ValueError("Uppsala 2022 reference total changed")
    return obs,metrics,methods

def comparability(a,b,methods):
    """Only direct year-on-year for identical metric, unit, method, geography and population."""
    checks=("metric_id","unit","population_id","geography_code",
            "geography_level","method_id")
    reasons=[k for k in checks if a[k]!=b[k]]
    if a["method_id"] not in methods or b["method_id"] not in methods:
        reasons.append("method_not_registered")
    elif methods[a["method_id"]]["comparability_group"]!=methods[b["method_id"]]["comparability_group"]:
        reasons.append("method_series_different")
    if a["source_id"]==b["source_id"] and a["observation_year"]==b["observation_year"]:
        reasons.append("duplicate_source_year")
    return {"comparable":not reasons,"reasons":sorted(set(reasons))}

def _write_csv(path,items,cols=None):
    cols=cols or list(items[0])
    with Path(path).open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore")
        w.writeheader();w.writerows(items)

def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _rate(a,b):
    """Do not calculate false precision or a rate without an explicit denominator."""
    raise ValueError("Rate computation requires a separately verified denominator, vintage and population")

def validate():
    obs,metrics,methods=normalized()
    nat=[x for x in obs if x["geography_level"]=="country"]
    totals={(x["metric_id"],x["observation_year"]):int(x["value"]) for x in nat}
    assert totals[("civil_society_organisations_total","2023")]==265700
    assert totals[("civil_society_organisations_total","2024")]==266400
    assert totals[("civil_society_ideella_foreningar","2023")]==163900
    assert totals[("civil_society_ideella_foreningar","2024")]==164250
    a=next(x for x in nat if x["metric_id"]=="civil_society_organisations_total" and x["observation_year"]=="2023")
    b=next(x for x in nat if x["metric_id"]=="civil_society_organisations_total" and x["observation_year"]=="2024")
    assert comparability(a,b,methods)["comparable"]
    c=next(x for x in obs if x["geography_level"]=="municipality")
    assert not comparability(a,c,methods)["comparable"]
    return {"observations":len(obs),"regional_municipalities":8,
            "national_observations":len(nat),"statistical_populations":2,
            "uppsala_2022_observations_total":10821,
            "national_2023_2024_different_population":"enforced",
            "cross_population_aggregation":"blocked","municipal_missing_is_not_zero":"enforced",
            "national_summary_precision":"rounded_reported",
            "public_release":"not_authorized"}

def build(out, inventory=None):
    output=Path(out).resolve()
    if output==ROOT or ROOT in output.parents:
        # Allow only build/ outside checked-in paths; source files and private inventory are never auto-published.
        if not str(output).startswith(str(ROOT/"build")):
            raise ValueError("WP06 output inside git repository; use local build/ only")
    output.mkdir(parents=True,exist_ok=True)
    obs,metrics,methods=normalized()
    _write_csv(output/"statistical_observations.csv",obs)
    report=[]
    nat=[x for x in obs if x["geography_level"]=="country"]
    for metric in ("civil_society_organisations_total","civil_society_ideella_foreningar"):
        old=next(x for x in nat if x["metric_id"]==metric and x["observation_year"]=="2023")
        new=next(x for x in nat if x["metric_id"]==metric and x["observation_year"]=="2024")
        verdict=comparability(old,new,methods)
        if not verdict["comparable"]:raise ValueError("National series not comparable")
        delta=int(new["value"])-int(old["value"])
        report.append({"comparison_id":metric+"_2023_2024",
                       "metric_id":metric,"from_year":"2023","to_year":"2024",
                       "from_value":old["value"],"to_value":new["value"],"reported_delta":str(delta),
                       "caveat":"rounded_source_values_not_precise_growth_estimate",
                       "comparison_status":"within_same_scb_series",
                       "source_ids":"scb_2023;scb_2024_corr_20260814"})
    _write_csv(output/"comparable_national_years.csv",report)
    coverage=[]
    mun={r["municipality_code"]:r for r in read_csv(MUNICIPAL)}
    measured={r["geography_code"] for r in obs if r["geography_level"]=="municipality"}
    for code,ref in sorted(mun.items()):
        coverage.append({"municipality_code":code,"county_code":ref["county_code"],
                        "municipality_name":ref["municipality_name"],
                        "uppsala_2022_observation_status":"reported" if code in measured else "not_in_source_scope",
                        "uppsala_2022_value":next((r["value"] for r in obs if
                             r["geography_level"]=="municipality" and r["geography_code"]==code),""),
                        "zero_inference":"forbidden"})
    _write_csv(output/"municipality_coverage.csv",coverage)
    if inventory is not None:
        source=read_csv(inventory)
        if len(source)!=290 or len({x["municipality_code"] for x in source})!=290:
            raise ValueError("WP04 inventory must contain 290 distinct municipality codes")
        staging=[]
        for r in source:
            if r["count_status"] not in ("not_reported","reported_number_unverified"):
                raise ValueError("Invalid source inventory count status")
            if r["count_status"]=="not_reported" and str(r["organisation_count"]).strip():
                raise ValueError("Missing inventory value was imputed")
            if r["count_status"]=="reported_number_unverified":
                _exact_int(r["organisation_count"],r["municipality_code"])
            staging.append({"row_id":r["row_id"],"municipality_code":r["municipality_code"],
                "organisation_count":r["organisation_count"],
                "count_status":r["count_status"],"source_id":r["source_id"],
                "harmonization_status":"NOT_COMPARABLE_UNTIL_METRIC_METHOD_SOURCE_AUDIT"})
        _write_csv(output/"unverified_inventory_excluded.csv",staging)
    manifest={"contract":"wp06.v1","reference_observation_count":len(obs),
        "national_comparisons":len(report),"municipalities":len(coverage),
        "reporting_2022_uppsala_count":len(measured),
        "wp04_inventory_loaded":inventory is not None,
        "national_data_status":"official_SCb_summary_sources_with_version_dates",
        "uppsala_data_status":"existing_curated_report_table_unrechecked_in_WP06",
        "unverified_wp04_counts_not_promoted":True,
        "sormland_annexes":"metadata_only_not_extracted",
        "geometry_included":False,"reference_year_geography":"2026_SCb_codes_not_2022_boundary",
        "publication_approved":False,
        "outputs":{p.name:_sha(p) for p in output.glob("*.csv")}}
    (output/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return manifest

def main(argv=None):
    p=argparse.ArgumentParser()
    a=p.add_subparsers(dest="cmd",required=True)
    a.add_parser("validate")
    b=a.add_parser("build");b.add_argument("--out",required=True)
    b.add_argument("--inventory",help="Private WP04 municipal_inventory.csv")
    args=p.parse_args(argv)
    print(json.dumps(validate() if args.cmd=="validate" else build(args.out,args.inventory),ensure_ascii=False,indent=2))

if __name__=="__main__":main()
