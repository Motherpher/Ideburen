"""Decision engine: non-causal graph, links, evidence gates and source integrity."""
import csv
import json
from pathlib import Path
import pytest
from ideburen.decision_engine import build,_time,STAGE_MAP,EXCEPTION_CASES

def fake_event(row_id,code,period,stage,desc,source_url="https://example.org/minutes"):
    return {
        "row_id":row_id,"source_id":"seed_uppsala","municipality_code":code,
        "evidence_status":"seed_unverified","source_sha256":"a"*64,
        "period":period,"event_stage":stage,"event_text":desc,
        "verification_status":"unverified seed claim","source_url":source_url
    }

def fixture(path,records):
    fields=["row_id","source_id","municipality_code","evidence_status",
            "source_sha256","period","event_stage","event_text",
            "verification_status","source_url"]
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records)

def read(path):
    with path.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))

def test_time_precision_and_uncertainty():
    assert _time("2025-09-08")==("2025-09-08","2025-09-08","day",False)
    assert _time("2025-09")==("2025-09-01","2025-09-30","month",False)
    assert _time("2026")==("2026-01-01","2026-12-31","year",False)
    assert _time("2018–2023")[3]
    assert _time("Datum ej verifierat")==("","","unknown",True)
    with pytest.raises(ValueError):_time("2025-13")
    with pytest.raises(ValueError):_time("2026–2023")

def test_all_expected_swedish_stages_mapped():
    assert STAGE_MAP["Beredning"]=="preparation"
    assert STAGE_MAP["Beslut"]=="political_decision"
    assert STAGE_MAP["Politiskt yttrande"]=="political_statement"
    assert STAGE_MAP["Utvärdering och dialog"]=="evaluation_dialogue"
    assert EXCEPTION_CASES["uppsala_register/Beslutskedjor/20"]=="knivsta_social_grants"

def test_graph_does_not_invent_causality_or_legal_verification(tmp_path):
    fixture(tmp_path/"events.csv",[
        fake_event("uppsala_register/Beslutskedjor/4","0380","2025-06-10","Beredning","AU"),
        fake_event("uppsala_register/Beslutskedjor/5","0380","2025-06-18","Beredning","KS"),
        fake_event("uppsala_register/Beslutskedjor/7","0380","2025-09-08","Beslut","KF"),
        fake_event("uppsala_register/Beslutskedjor/8","0380","2025-09-08","Politiskt yttrande","Statement"),
        fake_event("uppsala_register/Beslutskedjor/10","0360","2022-06-08","Beslut","Tierp KF"),
        fake_event("uppsala_register/Beslutskedjor/13","0360","2025-09","Beslut","Tierp KF later"),
        fake_event("uppsala_register/Beslutskedjor/23","0381","Datum ej verifierat","Principbeslut / riktlinjer","Enköping")
    ])
    result=build(tmp_path/"events.csv",tmp_path/"out",strict=False)
    assert result["events"]==7 and result["cases"]==3
    assert result["primary_decisions_validated"] is False
    edges=read(tmp_path/"out/decision_edges.csv")
    assert edges and all(x["causal_claim"]=="false" for x in edges)
    assert all(x["relation"]=="observed_temporal_precedence" for x in edges)
    events=read(tmp_path/"out/decision_events.csv")
    assert all(e["legal_decision_confirmed"]=="not_in_wp05" for e in events)
    assert all(e["primary_source_reaudited"]=="false" for e in events)
    assert {e["time_precision"] for e in events}>={"unknown","day","month"}
    same_day=[e for e in events if e["original_period"]=="2025-09-08"]
    assert len(same_day)==2
    for edge in edges:
        byid={e["event_id"]:e for e in events}
        assert byid[edge["from_event_id"]]["date_latest"] < byid[edge["to_event_id"]]["date_earliest"]
    gaps=read(tmp_path/"out/process_gaps.csv")
    assert all(g["not_a_claim_of_absence"]=="true" for g in gaps)

def test_actor_and_document_lineage(tmp_path):
    rid="uppsala_register/Beslutskedjor/7"
    fixture(tmp_path/"events.csv",[
        fake_event(rid,"0380","2025-09-08","Beslut","Verified? Not by WP05")
    ])
    raw=tmp_path/"raw.jsonl"
    raw.write_text(json.dumps({"row_id":rid,"sheet":"Beslutskedjor",
        "values":{"Besluts- eller dialogaktör":"Kommunfullmäktige","Utfall / ordning":"Policy"}})+"\n",encoding="utf-8")
    result=build(tmp_path/"events.csv",tmp_path/"out",raw,strict=False)
    assert result["actors"]==1 and result["documents"]==1
    assert result["raw_actor_metadata_joined"] is True
    actor=read(tmp_path/"out/actors.csv")[0]
    assert actor["actor_label"]=="Kommunfullmäktige"
    assert read(tmp_path/"out/documents.csv")[0]["link_status"]=="locator_not_read_or_page_verified"

def test_duplicate_unsafe_url_and_unknown_geography_rejected(tmp_path):
    rid="uppsala_register/Beslutskedjor/7"
    fixture(tmp_path/"events.csv",[
        fake_event(rid,"0380","2025-09-08","Beslut","A"),
        fake_event(rid,"0380","2025-09-09","Beslut","B"),
        fake_event("uppsala_register/Beslutskedjor/9","9999","2026","Genomförande","C"),
        fake_event("uppsala_register/Beslutskedjor/10","0360","2022","Beslut","D","http://example.org/unsafe")
    ])
    with pytest.raises(ValueError,match="3 decision graph exceptions"):
        build(tmp_path/"events.csv",tmp_path/"out",strict=False)
    issues={i["issue"] for i in read(tmp_path/"out/exceptions.csv")}
    assert {"duplicate_input_row","invalid_geography","unsafe_source_link"}==issues

def test_no_raw_artifact_in_public_repository(tmp_path):
    fixture(tmp_path/"events.csv",[fake_event("x","0380","2025","Beslut","A")])
    from ideburen.decision_engine import ROOT
    with pytest.raises(ValueError,match="outside public repository"):
        build(tmp_path/"events.csv",ROOT/"build/decisions",strict=False)

def test_strict_counter_gate(tmp_path):
    fixture(tmp_path/"events.csv",[fake_event("x","0380","2025","Beslut","A")])
    with pytest.raises(ValueError,match="1 decision graph exceptions"):
        build(tmp_path/"events.csv",tmp_path/"out",strict=True)


def test_normative_policy_not_counted_as_implemented(tmp_path):
    fixture(tmp_path/"events.csv",[
        fake_event("uppsala_register/Beslutskedjor/7","0380","2025-09-08","Beslut","Policy adopted"),
        fake_event("uppsala_register/Beslutskedjor/9","0380","2026","Genomförande",
                   "Policyn kräver årlig uppföljning tillsammans med civilsamhället"),
        fake_event("uppsala_register/Beslutskedjor/14","0360","2025–2031","Styrdokument","LÖK giltig i perioden")
    ])
    result=build(tmp_path/"events.csv",tmp_path/"out",strict=False)
    assert result["normative_or_period_claims_excluded_from_temporal_graph"]==2
    events=read(tmp_path/"out/decision_events.csv")
    kinds={x["source_row_id"]:x["claim_kind"] for x in events}
    assert kinds["uppsala_register/Beslutskedjor/9"]=="normative_requirement"
    assert kinds["uppsala_register/Beslutskedjor/14"]=="document_validity_period"
    gaps=read(tmp_path/"out/process_gaps.csv")
    assert any(g["case_id"]=="uppsala_cooperation" and g["stage"]=="implementation" for g in gaps)
    assert not read(tmp_path/"out/decision_edges.csv")  # No chronological inference from norms

def test_graphml_export_integrity(tmp_path):
    from xml.etree import ElementTree as ET
    fixture(tmp_path/"events.csv",[
        fake_event("uppsala_register/Beslutskedjor/4","0380","2025-06-10","Beredning","AU"),
        fake_event("uppsala_register/Beslutskedjor/7","0380","2025-09-08","Beslut","KF")
    ])
    result=build(tmp_path/"events.csv",tmp_path/"out",strict=False)
    tree=ET.parse(tmp_path/"out/decision_graph.graphml")
    uri={"g":"http://graphml.graphdrawing.org/xmlns"}
    assert len(tree.findall(".//g:node",uri))==2
    assert len(tree.findall(".//g:edge",uri))==1
    assert result["chronological_edges"]==1


def test_refa_edge_requires_claim_specific_evidence(tmp_path):
    records=[
       fake_event("uppsala_register/Beslutskedjor/4","0380","2025-06-10","Beredning","AU"),
       fake_event("uppsala_register/Beslutskedjor/7","0380","2025-09-08","Beslut","KF")
    ]
    fixture(tmp_path/"events.csv",records)
    assertions=tmp_path/"relations.csv"
    fields=["from_row_id","to_row_id","relation","source_url",
            "source_locator","reviewer","audit_date","harp_status"]
    def write(items):
        with assertions.open("w",encoding="utf-8",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=fields)
            writer.writeheader();writer.writerows(items)
    valid={
      "from_row_id":records[0]["row_id"],"to_row_id":records[1]["row_id"],
      "relation":"prepares","source_url":"https://example.org/municipal-protocol.pdf",
      "source_locator":"p. 4, § 12","reviewer":"Human research reviewer",
      "audit_date":"2026-11-13","harp_status":"RefA_approved"
    }
    invalid=dict(valid,source_locator="",harp_status="metadata_only")
    write([invalid])
    with pytest.raises(ValueError,match="decision graph exceptions"):
        build(tmp_path/"events.csv",tmp_path/"fail",strict=False,assertions_csv=assertions)
    write([valid])
    result=build(tmp_path/"events.csv",tmp_path/"pass",strict=False,assertions_csv=assertions)
    assert result["explicit_refa_relation_edges"]==1
    edges=read(tmp_path/"pass/decision_edges.csv")
    assert len([r for r in edges if r["relation"]=="prepares"])==1
    assert all(r["causal_claim"]!="true" for r in edges)
