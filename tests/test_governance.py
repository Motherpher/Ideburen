"""WP09 governance checks: engineering can pass but release must remain blocked."""
import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest
from ideburen import governance as gov
from ideburen.cli import build as core_build, gpkg
from ideburen.statistics import build as statistics_build
from ideburen.gis import prepare
from ideburen.ffspatial_adapter import build as adapter_build


def test_governance_baseline_and_harp_order():
    result,matrix=gov.run()
    assert result["status"]=="ENGINEERING_PASS"
    assert result["release_status"]=="BLOCKED"
    assert result["technical_blocker_count"]==0
    assert result["release_blocker_count"]>=6
    assert result["harp_steps"]==["ITR1","ITR2","ITR4","ITR5","ITR6"]
    assert "ITR3" not in result["harp_steps"]
    assert result["director_release_approved"] is False
    assert not result["refa_automatically_approved"]
    assert len(matrix)==result["source_count"]>=50
    assert all(r["publishable"]=="false" for r in matrix)
    assert all(r["ITR2_full_original_read"]=="not_verified_in_WP09" for r in matrix)


def test_source_binary_hash_does_not_imply_rights_or_harp():
    matrix=gov.audit_sources()
    checked=[r for r in matrix if r["binary_sha256"]=="recorded"]
    assert len(checked)==2
    assert all(r["redistribution_rights"]=="not_cleared" for r in checked)
    assert all(r["ITR6_validation_gate"]=="blocked_pending_ITR2_ITR5" for r in checked)


def test_release_gate_not_conflated_with_ci():
    assert gov.main(["audit","--out","build/wp09-test-audit"])==0
    assert gov.main(["release-check","--out","build/wp09-test-release"])==2


def test_evidence_report_structure(tmp_path):
    report,matrix=gov.run()
    gov.write_report(report,matrix,tmp_path/"qa")
    r=json.loads((tmp_path/"qa/wp09_audit.json").read_text())
    assert r["release_status"]=="BLOCKED"
    assert (tmp_path/"qa/wp09_qa_log.csv").is_file()
    issues=list(csv.DictReader((tmp_path/"qa/wp09_qa_log.csv").open(encoding="utf-8")))
    assert {x["rag"] for x in issues}=={"GREEN","AMBER","RED"}
    assert all(x["required_action"] or x["rag"]=="GREEN" for x in issues)
    matrix_file=list(csv.DictReader(
        (tmp_path/"qa/wp09_harp_source_matrix.csv").open(encoding="utf-8")))
    assert len(matrix_file)==len(matrix)


def test_restricted_binary_detected_without_leaking_payload(tmp_path,monkeypatch):
    fake=tmp_path/"repo";fake.mkdir()
    (fake/"private").mkdir()
    (fake/"private"/"identifiers.xlsx").write_bytes(b"private contact")
    monkeypatch.setattr(gov,"ROOT",fake)
    n,issues=gov.scan_public_tree()
    assert issues
    assert issues[0]["rag"]=="RED"
    assert "private contact" not in repr(issues)


def test_embedded_credential_detected_without_logging_it(tmp_path,monkeypatch):
    fake=tmp_path/"repo";fake.mkdir()
    token="ghp_"+"Z"*35
    (fake/"unsafe.py").write_text("secret="+repr(token),encoding="utf-8")
    monkeypatch.setattr(gov,"ROOT",fake)
    n,issues=gov.scan_public_tree()
    assert any(x["issue_id"]=="CREDENTIAL_PATTERN" for x in issues)
    assert token not in repr(issues)


def test_manifest_tampering_is_a_red_technical_issue(tmp_path):
    source=tmp_path/"build"
    core_build(source)
    statistics_build(source)
    gpkg(source,source/"ideburen_tables.gpkg")
    meta=source/"statistical_manifest.json"
    m=json.loads(meta.read_text())
    m["outputs"]["municipality_coverage.csv"]="0"*64
    meta.write_text(json.dumps(m))
    result,_=gov.run(source_dir=source)
    assert result["technical_blocker_count"]>=1
    assert any(f["issue_id"]=="WP07_PACKAGE_FAIL" for f in result["findings"])


def test_full_build_metadata_audit_still_blocks_release(tmp_path):
    source=tmp_path/"build"
    core_build(source)
    statistics_build(source)
    gpkg(source,source/"ideburen_tables.gpkg")
    prepare(source/"ideburen_tables.gpkg",source,source/"gis_handoff.json")
    adapter_build(
        source/"gis_handoff.json",
        source/"ideburen_tables.gpkg",
        source,
        source/"ffspatial_adapter",
        generated_at="2026-11-15T16:00:00Z",
        ff_spatial_commit="76dcadfb5d116e238d404ad106465b8a39111d6f"
    )
    result,_=gov.run(source_dir=source)
    assert result["technical_blocker_count"]==0
    assert result["status"]=="ENGINEERING_PASS"
    assert result["release_status"]=="BLOCKED"
    assert result["artifact_integrity"]["ffspatial"]=="FFSPATIAL_CONSUMER_FIELD_CONTRACT_PASS"


def test_no_claim_of_full_archival_audit():
    r,_=gov.run()
    assert r["source_records_full_refa_approved"]==0
    assert r["source_redistribution_rights_approved"]==0
    required={"POLYGONS_UNAVAILABLE","SOURCE_REFA_INCOMPLETE",
              "LICENSE_CLEARANCE_PENDING","DIRECTOR_RELEASE_APPROVAL_MISSING"}
    assert required.issubset({i["issue_id"] for i in r["findings"]})
