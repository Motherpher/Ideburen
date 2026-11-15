"""SCB AFR API ledger - do not need real credentials or live calls."""
import csv
import pytest
from ideburen import api_ledger as a

def test_config_restrictions():
    sources,policy=a.config()
    assert len(sources["apis"])==2
    assert policy["publication_authorized"] is False
    assert a.plan()["schema_verified"] is False
    assert a.plan()["max_page_rows"]==5000

def test_civil_society_classes_not_assumed_from_sni():
    assert a.classify("61",["85.100"])["tier"]=="core"
    assert a.classify("72",["88.999"])["tier"]=="core"
    assert a.classify("63",["94.910"])["tier"]=="review"
    assert a.classify("51",["93.120"])["tier"]=="review"
    assert a.classify("53",["68.200"])["tier"]=="separate"
    assert a.classify("61",["85.100"])["sni_hard_exclusion"] is False
    assert a.classify("61",["85.100"])["organisational_membership_verified"] is False

def test_plan_is_local_and_unapproved(tmp_path):
    p=a.write_plan(tmp_path/"plan.json")
    assert p.exists()
    assert a.plan()["live_requests"]==0
    with pytest.raises(ValueError,match="Writes allowed"):
        a.write_plan(a.ROOT/"manifests/scb_private_plan.json")

def test_audit_log_append_and_secret_rejection(tmp_path):
    record={k:"" for k in a.COLUMNS}
    record.update(event_id="test-001",utc="2026-11-15T17:00:00Z",
       api_id="scb_afr_v2",action="contract_review",status="pending",
       count="0",rights="not_cleared",harp="MinRA",note="Await OpenAPI verification")
    target=tmp_path/"ledger.csv"
    a.append_event(target,record)
    with pytest.raises(ValueError,match="Duplicate"):a.append_event(target,record)
    assert len(list(csv.DictReader(target.open())))==1
    record["event_id"]="test-002"
    record["note"]="api_key=SECRET"
    with pytest.raises(ValueError,match="secrets"):a.append_event(target,record)
