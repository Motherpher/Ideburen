"""WP08: read-only FF-Spatial normalized observation and provenance adapter.

No network, FF-Spatial writes, geometry production, job submission or public
release. Works only from a validated WP07 NON_SPATIAL_READY handoff.
This module pins and mirrors the relevant FF-Spatial consumer field contract
inspected from Motherpher/FF-Spatial/main (2026-11-15).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .cli import ROOT, read_csv
from .gis import validate_attributes

FF_FIELDS = (
    "provider_id","dataset_id","indicator_id","indicator_label",
    "geography_type","geography_id","geography_version",
    "reference_period","value","unit","population_definition",
    "retrieved_at","source_url","licence"
)
CONTRACT = "ideburen.ffspatial.observations.v1"
PROVIDER_ID = "ideburen"
DATASET_ID = "mchs_uppsala_seven_forms_2022"
GEOGRAPHY_VERSION = "SCB_2026_IDENTIFIER_LOOKUP_ONLY_NOT_2022_POLYGONS"
RIGHTS = "UNREVIEWED_NOT_CLEARED_FOR_REDISTRIBUTION"
REFS = {
    "observations": "Motherpher/FF-Spatial:qgis/materialize_observations.py",
    "normalized_model": "Motherpher/FF-Spatial:gateway/observations.py",
    "provenance": "Motherpher/FF-Spatial:provenance/schema.json",
    "job": "Motherpher/FF-Spatial:bridge/job.schema.json",
    "spatial_product": "Motherpher/FF-Spatial:registry/spatial-product.schema.json",
}
DEFAULT_SOURCE = "https://urn.kb.se/resolve?urn=urn:nbn:se:esh:diva-11246"


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _utc(value):
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value
    ):
        raise ValueError("Provide an explicit UTC generated-at timestamp YYYY-MM-DDTHH:MM:SSZ")
    d = datetime.fromisoformat(value.replace("Z","+00:00"))
    if d.tzinfo is None or d.utcoffset().total_seconds()!=0:
        raise ValueError("Adapter timestamp must be UTC")
    return value


def _safe_destination(output):
    dest = Path(output).resolve()
    if dest == ROOT or ROOT in dest.parents:
        try:
            dest.relative_to(ROOT / "build")
        except ValueError:
            raise ValueError("WP08 generated data must remain outside versioned source directories")
    return dest


def _write_csv(path, records):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FF_FIELDS, extrasaction="raise")
        writer.writeheader()
        writer.writerows(records)


def _validated_handoff(handoff_path, attributes_path, source_dir):
    handoff = json.loads(Path(handoff_path).read_text(encoding="utf-8"))
    expected = {
        "contract":"ideburen.wp07.qgis.v1",
        "status":"NON_SPATIAL_READY",
        "join_code":"municipality_code",
        "join_type":"four_character_text",
        "analysis_crs":"EPSG:3006",
        "observation_year":2022,
        "required_boundary_year_for_value_map":2022,
        "polygon_file":None,
        "polygon_checks":"NOT_RUN",
        "qgis_project":"NOT_CREATED",
        "release_gate":"BLOCKED_BY_POLYGON_TOPOLOGY_HARP_AND_DIRECTOR"
    }
    for k,v in expected.items():
        if handoff.get(k)!=v:
            raise ValueError("WP07 handoff contract mismatch: "+k)
    attr=validate_attributes(attributes_path,source_dir)
    if handoff.get("source_checksum")!=attr["package_sha256"]:
        raise ValueError("WP07 package checksum mismatch")
    for k,v in attr.items():
        if handoff.get("attribute_checks",{}).get(k)!=v:
            raise ValueError("WP07 attribute verification record mismatch: "+k)
    return handoff,attr


def build(handoff, gpkg, source_dir, out, *, generated_at, ff_spatial_commit):
    """Create an attribute-only, locally inspectable FF-Spatial consumer envelope."""
    timestamp = _utc(generated_at)
    if not re.fullmatch(r"[a-f0-9]{40}", ff_spatial_commit):
        raise ValueError("Pin a verified 40-character FF-Spatial commit")
    target = _safe_destination(out)
    if target.exists() and any(target.iterdir()):
        raise ValueError("Output directory is not empty (no implicit overwrites)")
    _handoff,attr = _validated_handoff(handoff,gpkg,source_dir)
    rows=read_csv(Path(source_dir)/"statistical_observations.csv")
    subset=[]
    ids=set()
    for r in rows:
        if r["geography_level"]=="country":
            if r["geography_code"]!="SE":
                raise ValueError("Invalid national geography")
            continue
        if (r["geography_level"]!="municipality" or r["source_id"]!="mchs_119_2025"
            or r["observation_year"]!="2022"
            or r["population_id"]!="ccf_7_legal_forms_2022"):
            raise ValueError("Unreviewed regional observation cannot enter FF-Spatial adapter")
        code=r["geography_code"]
        if not re.fullmatch(r"\d{4}",code) or code[:2]!="03" or code in ids:
            raise ValueError("Invalid or duplicated Uppsala municipality key")
        ids.add(code)
        if not re.fullmatch(r"(0|[1-9][0-9]*)",r["value"]):
            raise ValueError("Invalid numeric source value")
        if r["source_url"]!=DEFAULT_SOURCE or not r["source_locator"]:
            raise ValueError("Unexpected original report provenance")
        subset.append({
            "provider_id":PROVIDER_ID,
            "dataset_id":DATASET_ID,
            "indicator_id":r["metric_id"],
            "indicator_label":"Registered civil-society entities, seven legal forms",
            "geography_type":"municipality",
            "geography_id":code,
            "geography_version":GEOGRAPHY_VERSION,
            "reference_period":"2022",
            "value":str(int(r["value"])),
            "unit":"organisations",
            "population_definition":"seven_legal_forms_including_housing_associations",
            # This is the time the adapter read the local source file, NOT
            # the original SCB/source publication retrieval timestamp.
            "retrieved_at":timestamp,
            "source_url":r["source_url"],
            "licence":RIGHTS
        })
    if len(subset)!=8 or sum(int(r["value"]) for r in subset)!=10821:
        raise ValueError("Uppsala seven-form reference changed")
    target.mkdir(parents=True,exist_ok=True)
    file=target/"ffspatial_normalized_observations.csv"
    _write_csv(file, sorted(subset,key=lambda r:r["geography_id"]))
    provenance={
        "source_id":"mchs_119_2025",
        "dataset_id":DATASET_ID,
        "provider":"Marie Cederschiöld högskola / Ideburen derived",
        "retrieved_at":timestamp,
        "valid_from":"2022-01-01",
        "valid_to":"2022-12-31",
        "geography_version":GEOGRAPHY_VERSION,
        "crs":None,
        "license":RIGHTS,
        "source_url":DEFAULT_SOURCE,
        "checksum":sha256(file),
        "transformations":[
            "Read WP06 statistical_observations.csv after WP07 checksum validation",
            "Filter eight municipality observations (exclude four country-level rows)",
            "Map metric_id to indicator_id; geography_code to geography_id",
            "Preserve reference year and original report population definition",
            "No boundary polygon, CRS transform, FF-Spatial job or source file modification"
        ],
        "warnings":[
            "retrieved_at is adapter input read/export time, not publisher acquisition time",
            "Metadata checked; full original-source HARP RefA pending",
            "SCB 2026 administrative identifiers are not proven 2022 boundary polygons",
            "Not a spatial-product manifest: only non-spatial CSV observations",
            "Source re-use rights not cleared and no publication permitted"
        ]
    }
    prov=target/"ffspatial_provenance.json"
    prov.write_text(json.dumps(provenance,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    receipt={
        "contract":CONTRACT,
        "ffspatial_consumer_git_sha":ff_spatial_commit,
        "schema_refs":REFS,
        "created_at":timestamp,
        "status":"CONTRACT_MAPPED_NOT_CONSUMER_EXECUTED",
        "producer":"Motherpher/Ideburen",
        "consumer":"Motherpher/FF-Spatial",
        "workspace_write_policy":"ideburen_local_derived_only",
        "bridge_job_created":False,
        "bridge_job_approved":False,
        "ffspatial_repository_modified":False,
        "spatial_product_created":False,
        "qgis_project_created":False,
        "polygon_source_present":False,
        "observation_rows":len(subset),
        "observation_year":2022,
        "geography_identifier_reference":"SCB_2026_identifiers_not_historic_2022_polygon",
        "value_total":10821,
        "excluded_country_observations":4,
        "source_status":"curated_report_reference_full_HARP_pending",
        "source_rights":"not_cleared",
        "external_runtime_test":"NOT_RUN",
        "handoff_sha256":sha256(handoff),
        "attribute_gpkg_sha256":attr["package_sha256"],
        "normalized_csv_sha256":sha256(file),
        "provenance_sha256":sha256(prov),
        "release_status":"BLOCKED_HARP_RIGHTS_GEOMETRY_AND_DIRECTOR"
    }
    (target/"ffspatial_adapter_receipt.json").write_text(
        json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"
    )
    return receipt


def validate_output(out):
    p=Path(out)
    manifest=json.loads((p/"ffspatial_adapter_receipt.json").read_text(encoding="utf-8"))
    rows=read_csv(p/"ffspatial_normalized_observations.csv")
    if (len(rows)!=8 or tuple(rows[0])!=FF_FIELDS or
        len({r["geography_id"] for r in rows})!=8 or
        sum(int(r["value"]) for r in rows)!=10821):
        raise ValueError("FF-Spatial normalized row contract failed")
    if any(r["geography_type"]!="municipality" or
           r["geography_version"]!=GEOGRAPHY_VERSION or
           r["licence"]!=RIGHTS or r["reference_period"]!="2022"
           for r in rows):
        raise ValueError("Incompatible FF-Spatial observation metadata")
    for name,field in [
        ("ffspatial_normalized_observations.csv","normalized_csv_sha256"),
        ("ffspatial_provenance.json","provenance_sha256")
    ]:
        if sha256(p/name)!=manifest[field]:
            raise ValueError("FF-Spatial adapter artifact checksum mismatch")
    provenance=json.loads((p/"ffspatial_provenance.json").read_text(encoding="utf-8"))
    for key in ("source_id","retrieved_at","source_url","transformations"):
        if key not in provenance:
            raise ValueError("FF-Spatial provenance required field absent: "+key)
    if (manifest.get("bridge_job_created") is not False or
        manifest.get("spatial_product_created") is not False or
        manifest.get("release_status")!="BLOCKED_HARP_RIGHTS_GEOMETRY_AND_DIRECTOR"):
        raise ValueError("Unsafe adapter receipt/release claim")
    return {"result":"FFSPATIAL_CONSUMER_FIELD_CONTRACT_PASS",
            "rows":len(rows),"codes":len({r["geography_id"] for r in rows}),
            "bridged_runtime":"NOT_TESTED","release_authorized":False}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="cmd",required=True)
    b=sub.add_parser("build")
    b.add_argument("--handoff",required=True);b.add_argument("--gpkg",required=True)
    b.add_argument("--source-dir",required=True);b.add_argument("--out",required=True)
    b.add_argument("--generated-at",required=True)
    b.add_argument("--ff-spatial-commit",required=True)
    v=sub.add_parser("validate")
    v.add_argument("--out",required=True)
    a=p.parse_args(argv)
    if a.cmd=="build":
        result=build(a.handoff,a.gpkg,a.source_dir,a.out,
                     generated_at=a.generated_at,ff_spatial_commit=a.ff_spatial_commit)
    else:
        result=validate_output(a.out)
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__=="__main__":
    main()
