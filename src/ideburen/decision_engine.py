"""WP05 Decision Engine: evidence-preserving institutional decision graphs.

Inputs: WP04 LOCAL (gitignored) decision_events.csv and optionally raw_staging.jsonl.
Outputs: local JSON/CSV, no public documents or private Drive data are transmitted.
Chronological edges are *not* legal/causal dependencies. Missing stage != absent event.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from .cli import ROOT, read_csv

CASE_BY_MUNICIPALITY = {
    "0380": "uppsala_cooperation",
    "0360": "tierp_cooperation",
    "0330": "knivsta_cooperation",
    "0382": "osthammar_cooperation",
    "0381": "enkoping_cooperation",
    "0305": "habo_iop",
    "0331": "heby_associations",
    "0319": "alvkarleby_associations",
}
# The separate Knivsta social-grant decision must not be merged into the
# municipal association council dialogue chain.
EXCEPTION_CASES = {"uppsala_register/Beslutskedjor/20": "knivsta_social_grants"}

STAGE_MAP = {
    "Beslut": "political_decision",
    "Överenskommelse": "adopted_instrument",
    "Beredning": "preparation",
    "Tjänsteskrivelse": "officer_report",
    "Politiskt yttrande": "political_statement",
    "Genomförande": "implementation",
    "Dialog": "dialogue",
    "Dialog och remiss": "dialogue",
    "Dialog och enkät": "dialogue",
    "Utvärdering och dialog": "evaluation_dialogue",
    "Styrdokument": "adopted_instrument",
    "Workshop": "dialogue",
    "Initiativ / uppdrag": "initiative",
    "Principbeslut / riktlinjer": "policy_instrument",
    "Riktlinjer": "policy_instrument",
}
CYCLE = (
    "initiative", "dialogue", "consultation", "preparation", "officer_report",
    "political_decision", "adopted_instrument", "implementation", "follow_up"
)
# Coverage means a category is documented by the *seed*, not a universal model
# of legally mandatory steps. Optional stage set, not a procedural mandate.
COVERAGE = {
    "initiative": {"initiative"},
    "dialogue": {"dialogue","evaluation_dialogue"},
    "preparation": {"preparation","officer_report"},
    "decision": {"political_decision","adopted_instrument","policy_instrument"},
    "implementation": {"implementation"},
    "follow_up": {"follow_up","evaluation_dialogue"},
}
VALID_CODES = set()
SOURCE_ID = "seed_uppsala"
SOURCE_CLASS = "secondary_seed_inventory"
EVIDENCE = "seed_claim_not_primary_reaudited"

def _write(path, rows, headers):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

def _json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+"\n", encoding="utf-8")

def _stable_actor_code(municipality_code, label):
    canonical = unicodedata.normalize("NFKC", label).casefold().strip()
    canonical = re.sub(r"\s+", " ", canonical)
    return "act_" + municipality_code + "_" + hashlib.sha256(canonical.encode()).hexdigest()[:12]

def _time(value):
    """Returns (earliest, latest, precision, ambiguous); no invented exact dates."""
    s = (value or "").strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        d = date.fromisoformat(s)
        return d.isoformat(), d.isoformat(), "day", False
    if re.fullmatch(r"\d{4}-\d{2}", s):
        y,m = map(int,s.split("-"))
        if not 1<=m<=12: raise ValueError("Invalid month "+s)
        end = (date(y+1,1,1) if m==12 else date(y,m+1,1)).toordinal()-1
        return date(y,m,1).isoformat(), date.fromordinal(end).isoformat(), "month", False
    if re.fullmatch(r"\d{4}", s):
        y=int(s)
        return f"{y}-01-01", f"{y}-12-31", "year", False
    if re.fullmatch(r"\d{4}\s*[–-]\s*\d{4}",s):
        y1,y2=map(int,re.split(r"\s*[–-]\s*",s))
        if y2<y1: raise ValueError("Reverse year range "+s)
        return f"{y1}-01-01", f"{y2}-12-31", "year_range", True
    if s in {"","Datum ej verifierat"}:
        return "", "", "unknown", True
    return "", "", "unparsed", True

def _load_raw_actors(path):
    """Link only by exact WP04 row id; never publish source JSON lines."""
    actors={}
    if path is None: return actors
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            record=json.loads(line)
            if record.get("sheet")!="Beslutskedjor":continue
            raw=record.get("values",{})
            actors[record["row_id"]]={
                "actor":str(raw.get("Besluts- eller dialogaktör") or "").strip(),
                "outcome":str(raw.get("Utfall / ordning") or "").strip()
            }
    return actors

def build(input_csv, output_dir, raw_jsonl=None, strict=True):
    """Produce linked nodes, documents, actors, provenance, temporal graph and gaps."""
    input_csv=Path(input_csv)
    if not input_csv.is_file():raise FileNotFoundError(input_csv)
    output=Path(output_dir).resolve()
    repo=ROOT.resolve()
    if output==repo or repo in output.parents:
        raise ValueError("Decision staging is private; output must be outside public repository")
    if output==input_csv.resolve().parent:
        raise ValueError("Do not write into original input folder")
    output.mkdir(parents=True,exist_ok=True)
    source_rows=read_csv(input_csv)
    if not source_rows:raise ValueError("Empty decision input")
    required={"row_id","source_id","municipality_code","period","event_stage","event_text",
              "verification_status","source_url","evidence_status","source_sha256"}
    if not required.issubset(source_rows[0]):
        raise ValueError("Missing columns: "+str(sorted(required-set(source_rows[0]))))
    municipality_codes={r["municipality_code"] for r in
                        read_csv(ROOT/"data/curated/dimensions/municipalities.csv")}
    actors_by_row=_load_raw_actors(raw_jsonl)
    events=[];actors={};documents={};issues=[];case_events=defaultdict(list);requests=[]
    seen_rows=set()
    for r in source_rows:
        rid=r["row_id"]
        if rid in seen_rows:
            issues.append({"severity":"BLOCKING","issue":"duplicate_input_row","event_id":rid,"detail":""})
            continue
        seen_rows.add(rid)
        code=r["municipality_code"]
        if code not in municipality_codes or code not in CASE_BY_MUNICIPALITY:
            issues.append({"severity":"BLOCKING","issue":"invalid_geography","event_id":rid,"detail":code})
            continue
        if r["source_id"]!=SOURCE_ID or r["evidence_status"]!="seed_unverified":
            issues.append({"severity":"BLOCKING","issue":"source_status_mismatch","event_id":rid,"detail":r["source_id"]})
            continue
        if not re.fullmatch(r"[a-f0-9]{64}",r["source_sha256"]):
            issues.append({"severity":"BLOCKING","issue":"invalid_workbook_checksum","event_id":rid,"detail":""})
            continue
        stage=STAGE_MAP.get(r["event_stage"])
        if not stage:
            issues.append({"severity":"BLOCKING","issue":"unclassified_stage","event_id":rid,"detail":r["event_stage"]})
            continue
        try:start,end,precision,uncertain=_time(r["period"])
        except ValueError:
            issues.append({"severity":"BLOCKING","issue":"invalid_time","event_id":rid,"detail":r["period"]})
            continue
        case=EXCEPTION_CASES.get(rid,CASE_BY_MUNICIPALITY[code])
        event_id="evt_"+hashlib.sha256(rid.encode("utf-8")).hexdigest()[:16]
        actor_label=actors_by_row.get(rid,{}).get("actor","")
        actor_id=_stable_actor_code(code,actor_label) if actor_label else ""
        if actor_id:
            actors[actor_id]={"actor_id":actor_id,"municipality_code":code,
                              "actor_label":actor_label,"actor_type":"institution_or_group",
                              "entity_evidence_status":EVIDENCE}
        url=r["source_url"].strip()
        doc_id=""
        if url:
            u=urlsplit(url)
            if u.scheme!="https" or not u.netloc:
                issues.append({"severity":"BLOCKING","issue":"unsafe_source_link","event_id":rid,"detail":"not HTTPS"})
                continue
            doc_id="doc_"+hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
            documents[doc_id]={"document_id":doc_id,"url":url,
                               "link_status":"locator_not_read_or_page_verified",
                               "document_type":"unknown","source_id":SOURCE_ID}
        # Distinguish observed-event claims from a document's normative
        # requirements or validity period; neither is proof of implementation.
        normalized_description=r["event_text"].casefold()
        claim_kind=("normative_requirement" if stage=="implementation" and
                    any(t in normalized_description for t in ("kräver","ska följas","bör följas"))
                    else "document_validity_period" if stage=="adopted_instrument" and precision=="year_range"
                    else "event_claim")
        event={
            "event_id":event_id,"case_id":case,"municipality_code":code,
            "source_row_id":rid,"source_id":r["source_id"],
            "source_sha256":r["source_sha256"],
            "event_type":stage,"original_stage":r["event_stage"],
            "claim_kind":claim_kind,
            "original_period":r["period"],"date_earliest":start,"date_latest":end,
            "time_precision":precision,"temporal_uncertainty":str(uncertain).lower(),
            "description":r["event_text"],"actor_id":actor_id,
            "document_id":doc_id,"original_verification_note":r["verification_status"],
            "evidence_status":EVIDENCE,"primary_source_reaudited":"false",
            "legal_decision_confirmed":"not_in_wp05",
            "is_publication_cleared":"false"
        }
        events.append(event)
        case_events[case].append(event)
        note=r["verification_status"].casefold()
        requires_review=any(t in note for t in
                            ("återstår","måste inhämtas","behöver","saknas","ej inhämtade",
                             "dubbelt", "dubbelkontroll", "förarbete"))
        if requires_review or not doc_id or not start:
            reason = ("document_or_procedural_followup" if requires_review
                      else "missing_document_locator" if not doc_id
                      else "unverified_time")
            requests.append({
                "request_id":"req_"+event_id,"event_id":event_id,"case_id":case,
                "municipality_code":code,"request_type":reason,
                "source_verification_note":r["verification_status"],
                "request_status":"research_needed",
                "evidence_status":"inferred_review_task_from_seed_not_official_absence"
            })
    if strict and len(source_rows)!=27:
        issues.append({"severity":"BLOCKING","issue":"source_row_count_drift","event_id":"","detail":str(len(source_rows))})
    edges=[];gaps=[];cases=[]
    for case,group in sorted(case_events.items()):
        code=group[0]["municipality_code"]
        # Only strictly non-overlapping, unambiguous time windows create
        # precedence edges. A timeline edge is not an inferred causal edge.
        ordered=sorted([r for r in group if r["date_earliest"]
                        and r["claim_kind"]=="event_claim"],
                       key=lambda x:(x["date_earliest"],x["date_latest"],x["event_id"]))
        for i,src in enumerate(ordered):
            nxt=next((dst for dst in ordered[i+1:] if
                      src["date_latest"] < dst["date_earliest"]),None)
            if nxt:
                edges.append({
                    "edge_id":"edge_"+hashlib.sha256((src["event_id"]+nxt["event_id"]).encode()).hexdigest()[:16],
                    "case_id":case,"from_event_id":src["event_id"],"to_event_id":nxt["event_id"],
                    "relation":"observed_temporal_precedence",
                    "evidence_status":"computed_from_unverified_seed_dates",
                    "causal_claim":"false","verification_required":"true"
                })
        observed={r["event_type"] for r in group if r["claim_kind"]=="event_claim"}
        for required_stage,alternatives in COVERAGE.items():
            if observed.isdisjoint(alternatives):
                gaps.append({"case_id":case,"municipality_code":code,
                             "stage":required_stage,"gap_status":"not_observed_in_seed",
                             "not_a_claim_of_absence":"true",
                             "request":"Locate original documents or minutes for this stage"})
        uncertain=sum(x["temporal_uncertainty"]=="true" for x in group)
        cases.append({"case_id":case,"municipality_code":code,"event_count":len(group),
                      "unverified_time_count":uncertain,
                      "case_evidence_status":"research_inventory_not_primary_reaudited",
                      "complete_decision_chain":"false",
                      "causal_chain_evidenced":"false"})
    event_ids={e["event_id"] for e in events}
    for e in edges:
        if e["from_event_id"] not in event_ids or e["to_event_id"] not in event_ids:
            issues.append({"severity":"BLOCKING","issue":"orphan_edge","event_id":"","detail":e["edge_id"]})
    _write(output/"decision_events.csv",events,[
       "event_id","case_id","municipality_code","source_row_id","source_id","source_sha256",
       "event_type","original_stage","claim_kind","original_period","date_earliest","date_latest",
       "time_precision","temporal_uncertainty","description","actor_id","document_id",
       "original_verification_note","evidence_status","primary_source_reaudited",
       "legal_decision_confirmed","is_publication_cleared"])
    _write(output/"decision_edges.csv",edges,["edge_id","case_id","from_event_id",
       "to_event_id","relation","evidence_status","causal_claim","verification_required"])
    _write(output/"cases.csv",cases,["case_id","municipality_code","event_count",
       "unverified_time_count","case_evidence_status","complete_decision_chain",
       "causal_chain_evidenced"])
    _write(output/"actors.csv",list(actors.values()),["actor_id","municipality_code",
       "actor_label","actor_type","entity_evidence_status"])
    _write(output/"documents.csv",list(documents.values()),["document_id","url",
       "link_status","document_type","source_id"])
    _write(output/"process_gaps.csv",gaps,["case_id","municipality_code","stage",
       "gap_status","not_a_claim_of_absence","request"])
    _write(output/"evidence_requests.csv",requests,["request_id","event_id","case_id",
       "municipality_code","request_type","source_verification_note","request_status","evidence_status"])
    _write(output/"exceptions.csv",issues,["severity","issue","event_id","detail"])
    # Portable GraphML: chronological edges only, without fictional causal edges.
    graphml=ET.Element("graphml",xmlns="http://graphml.graphdrawing.org/xmlns")
    for key_id,context,name in [
        ("case","node","case_id"),("municipality","node","municipality_code"),
        ("type","node","event_type"),("source","node","source_row_id"),
        ("relation","edge","relation")]:
        ET.SubElement(graphml,"key",id=key_id,**{"for":context,"attr.name":name,"attr.type":"string"})
    graph=ET.SubElement(graphml,"graph",id="ideburen_decisions",edgedefault="directed")
    for node in events:
        n=ET.SubElement(graph,"node",id=node["event_id"])
        for key_id,col in (("case","case_id"),("municipality","municipality_code"),
                           ("type","event_type"),("source","source_row_id")):
            ET.SubElement(n,"data",key=key_id).text=str(node[col])
    for edge in edges:
        el=ET.SubElement(graph,"edge",id=edge["edge_id"],source=edge["from_event_id"],
                         target=edge["to_event_id"])
        ET.SubElement(el,"data",key="relation").text=edge["relation"]
    ET.ElementTree(graphml).write(output/"decision_graph.graphml",encoding="utf-8",
                                  xml_declaration=True)
    manifest={
       "contract":"wp05.v1","input":"WP04 decision_events.csv",
       "input_sha256":hashlib.sha256(input_csv.read_bytes()).hexdigest(),
       "raw_actor_metadata_joined":bool(raw_jsonl),
       "events":len(events),"cases":len(cases),"actors":len(actors),
       "documents":len(documents),"chronological_edges":len(edges),
       "missing_stage_flags":len(gaps),"evidence_followup_requests":len(requests),
       "blocking_exceptions":len(issues),
       "relation_semantics":"temporal_only_not_causal",
       "normative_or_period_claims_excluded_from_temporal_graph":sum(
         e["claim_kind"]!="event_claim" for e in events),
       "primary_decisions_validated":False,"release_approval":False,
       "coverage":"research_seed_not_all_municipal_decisions",
       "files":sorted(p.name for p in output.iterdir() if p.suffix in (".csv",".graphml"))
    }
    _json(output/"manifest.json",manifest)
    if issues:
        raise ValueError(f"{len(issues)} decision graph exceptions. See {output/'exceptions.csv'}")
    return manifest

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--events",required=True)
    p.add_argument("--raw",help="WP04 raw_staging.jsonl, optional actor names")
    p.add_argument("--out",required=True)
    p.add_argument("--allow-nonstandard-row-count",action="store_true")
    a=p.parse_args(argv)
    result=build(a.events,a.out,a.raw,strict=not a.allow_nonstandard_row_count)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
