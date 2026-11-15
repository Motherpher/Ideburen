"""WP08 FF-Spatial adapter: contract equivalence and fail-closed boundaries."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import pytest

from ideburen.cli import build as core_build, gpkg
from ideburen.statistics import build as statistics_build
from ideburen.gis import prepare
from ideburen.ffspatial_adapter import (
    FF_FIELDS, build, validate_output, GEOGRAPHY_VERSION, RIGHTS
)

COMMIT="76dcadfb5d116e238d404ad106465b8a39111d6f"
TIMESTAMP="2026-11-15T15:39:00Z"


@pytest.fixture
def inputs(tmp_path):
    source=tmp_path/"source"
    core_build(source)
    statistics_build(source)
    gpkg(source,source/"ideburen_tables.gpkg")
    prepare(source/"ideburen_tables.gpkg",source,source/"gis_handoff.json")
    return source


def export(source, out):
    return build(
        source/"gis_handoff.json",
        source/"ideburen_tables.gpkg",
        source,out,
        generated_at=TIMESTAMP,
        ff_spatial_commit=COMMIT
    )


def test_wp08_canonical_normalized_fields_and_license_gates(inputs,tmp_path):
    result=export(inputs,tmp_path/"product")
    assert result["observation_rows"]==8
    assert result["excluded_country_observations"]==4
    assert result["value_total"]==10821
    assert result["bridge_job_created"] is False
    assert result["spatial_product_created"] is False
    assert result["ffspatial_repository_modified"] is False
    assert result["external_runtime_test"]=="NOT_RUN"
    with (tmp_path/"product/ffspatial_normalized_observations.csv").open(
        encoding="utf-8",newline=""
    ) as f:
        r=csv.DictReader(f)
        assert tuple(r.fieldnames)==FF_FIELDS
        rows=list(r)
    assert len(rows)==8
    assert all(x["geography_version"]==GEOGRAPHY_VERSION for x in rows)
    assert all(x["licence"]==RIGHTS for x in rows)
    assert all(len(x["geography_id"])==4 for x in rows)
    assert all(x["retrieved_at"]==TIMESTAMP for x in rows)
    assert validate_output(tmp_path/"product")["release_authorized"] is False


def test_wp08_provenance_schema_original_fields(inputs,tmp_path):
    export(inputs,tmp_path/"product")
    p=json.loads((tmp_path/"product/ffspatial_provenance.json").read_text())
    for key in ("source_id","retrieved_at","source_url","transformations"):
        assert key in p
    assert p["crs"] is None
    assert p["license"]==RIGHTS
    assert any("not publisher" in v for v in p["warnings"])


def test_wp08_reject_gpkg_tampering(inputs,tmp_path):
    handoff=inputs/"gis_handoff.json"
    info=json.loads(handoff.read_text())
    info["source_checksum"]="a"*64
    handoff.write_text(json.dumps(info))
    with pytest.raises(ValueError,match="WP07 package checksum mismatch"):
        export(inputs,tmp_path/"product")


def test_wp08_reject_2026_polygons_claim(inputs,tmp_path):
    handoff=inputs/"gis_handoff.json"
    info=json.loads(handoff.read_text())
    info["polygon_checks"]="PASS"
    handoff.write_text(json.dumps(info))
    with pytest.raises(ValueError,match="handoff contract mismatch"):
        export(inputs,tmp_path/"product")


def test_wp08_refuse_overwrite_and_invalid_commit(inputs,tmp_path):
    target=tmp_path/"product"
    export(inputs,target)
    with pytest.raises(ValueError,match="not empty"):
        export(inputs,target)
    with pytest.raises(ValueError,match="40-character"):
        build(inputs/"gis_handoff.json",inputs/"ideburen_tables.gpkg",
              inputs,tmp_path/"other",generated_at=TIMESTAMP,
              ff_spatial_commit="main")


def test_wp08_reject_export_tampering(inputs,tmp_path):
    output=tmp_path/"product"
    export(inputs,output)
    data=output/"ffspatial_normalized_observations.csv"
    original=data.read_text(encoding="utf-8")
    data.write_text(original.replace("7088","9999"),encoding="utf-8")
    with pytest.raises(ValueError,match="row contract failed"):
        validate_output(output)


def test_wp08_reject_release_claim_without_review(inputs,tmp_path):
    output=tmp_path/"product"
    export(inputs,output)
    p=output/"ffspatial_adapter_receipt.json"
    receipt=json.loads(p.read_text())
    receipt["bridge_job_created"]=True
    p.write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match="Unsafe adapter receipt"):
        validate_output(output)
