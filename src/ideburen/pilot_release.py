"""WP10 internal pilot / frozen release-candidate inventory (NOT public release).

Validates exactly 8 Uppsala observations and 9 Sörmland appendices.
Freezes versions and hashes of source-controlled inputs; no invented Sörmland
numeric observations, no fabricated polygons, no Director approval.
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
from .governance import run as governance_run

VERSION="v0.1.0-rc1"
CONTRACT="ideburen.wp10.pilot.v1"
UPPSALA_CODES={"0305","0319","0330","0331","0360","0380","0381","0382"}
SORM_NAMES={"Eskilstuna","Flen","Gnesta","Katrineholm","Nyköping",
            "Oxelösund","Strängnäs","Trosa","Vingåker"}
SOURCE_FILES={
    "municipalities":"data/curated/dimensions/municipalities.csv",
    "counties":"data/curated/dimensions/counties.csv",
    "uppsala_observations":"data/curated/observations/uppsala_2022.csv",
    "publication_registry":"data/curated/publications/publication_registry_v1.csv",
    "study_registry":"data/curated/publications/study_family_registry_v1.csv",
    "source_registry":"manifests/source_registry_v1.csv",
    "method_dictionary":"data/curated/statistics/methods.csv",
    "metric_dictionary":"data/curated/statistics/metrics.csv",
    "scb_national":"data/curated/statistics/scb_national_2023_2024.csv",
    "decision_case_index":"data/curated/decisions/wp05_seed_case_scope.csv",
    "governance_rules":"src/ideburen/governance.py",
}
COLUMNS=[
    "pilot_id","area","municipality_code","municipality_name","source_id",
    "publication_id","study_id","observation_year","publication_year",
    "metric_id","method_id","population","value","value_status",
    "source_review_status","source_locator","geography_reference_year",
    "polygon_status","harp_refa_status","release_status"
]


def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def _write_csv(path,items,fields):
    with Path(path).open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction="raise")
        writer.writeheader()
        writer.writerows(items)


def make_pilot():
    places={r["municipality_code"]:r for r in
            read_csv(ROOT/"data/curated/dimensions/municipalities.csv")}
    names={r["municipality_name"]:r for r in places.values()}
    sources={r["source_id"]:r for r in
             read_csv(ROOT/"manifests/source_registry_v1.csv")}
    pub=read_csv(ROOT/"data/curated/publications/publication_registry_v1.csv")
    rows=[]
    obs=read_csv(ROOT/"data/curated/observations/uppsala_2022.csv")
    if len(obs)!=8 or {r["municipality_code"] for r in obs}!=UPPSALA_CODES:
        raise ValueError("WP10 Uppsala 8-municipality coverage mismatch")
    if sum(int(r["value"]) for r in obs)!=10821:
        raise ValueError("WP10 seven-form source total mismatch")
    for r in sorted(obs,key=lambda v:v["municipality_code"]):
        code=r["municipality_code"]
        if (places[code]["county_code"]!="03" or r["value_year"]!="2022" or
            r["source_id"]!="mchs_119_2025" or
            r["population"]!="seven_legal_forms_including_housing_associations" or
            not re.fullmatch(r"(0|[1-9][0-9]*)",r["value"])):
            raise ValueError("Uppsala metric, provenance or year drift")
        if r["source_id"] not in sources:
            raise ValueError("Missing Uppsala report source")
        rows.append(dict(
            pilot_id="uppsala_"+code,area="Uppsala län",municipality_code=code,
            municipality_name=places[code]["municipality_name"],
            source_id=r["source_id"],publication_id="pub_mchs_119_2025",
            study_id="study_uppsala_2022",observation_year=r["value_year"],
            publication_year="2025",metric_id=r["metric_id"],
            method_id=r["method_id"],population=r["population"],value=r["value"],
            value_status="existing_curated_report_table_pending_full_RefA",
            source_review_status="source_seed_not_reaudited_in_WP10",
            source_locator="Table 2 p. 26 in working report 119",
            geography_reference_year="2026_identifier_only",polygon_status="not_acquired",
            harp_refa_status="pending",release_status="internal_candidate_not_public"
        ))
    sorm=[p for p in pub if p["study_id"]=="study_sormland_2023"
          and p["edition_role"]=="municipal_appendix"]
    if len(sorm)!=9 or {p["geography"] for p in sorm}!=SORM_NAMES:
        raise ValueError("WP10 Sörmland nine-annex catalog mismatch")
    if len({p["publication_id"] for p in sorm})!=9:
        raise ValueError("Duplicated appendix identifier")
    parent=[p for p in pub if p["study_id"]=="study_sormland_2023"
            and p["edition_role"]=="main_or_single"]
    if len(parent)!=1 or parent[0]["source_id"]!="sormland_2024":
        raise ValueError("Missing Sörmland primary study family")
    for p in sorted(sorm,key=lambda v:v["geography"]):
        name=p["geography"]
        if name not in names or names[name]["county_code"]!="04":
            raise ValueError("Sörmland name cannot resolve to 2026 SCB municipal ID")
        if p["source_id"] not in sources or p["data_period"]!="2023" or p["publication_year"]!="2024":
            raise ValueError("Annex provenance mismatch")
        ref=names[name]
        rows.append(dict(
            pilot_id="sormland_"+ref["municipality_code"],
            area="Södermanlands län",municipality_code=ref["municipality_code"],
            municipality_name=name,source_id=p["source_id"],
            publication_id=p["publication_id"],study_id="study_sormland_2023",
            observation_year="2023",publication_year="2024",
            metric_id="",method_id="",population="",value="",
            value_status="not_extracted_not_zero",
            source_review_status=p["review_status"],
            source_locator="regional report annex catalog; original numeric table not checked",
            geography_reference_year="2026_identifier_only",polygon_status="not_acquired",
            harp_refa_status="pending",release_status="internal_candidate_not_public"
        ))
    if len(rows)!=17 or len({r["municipality_code"] for r in rows})!=17:
        raise ValueError("Pilot missing one of 17 target municipalities")
    if any(r["value"]=="0" for r in rows[8:]):
        raise ValueError("Missing Sörmland data imputed to zero")
    return rows


def freeze(out,generated_at,code_revision,build_dir=None):
    target=Path(out).resolve()
    if ROOT==target or ROOT in target.parents:
        if ROOT/"build" not in target.parents:
            raise ValueError("Release-candidate build must not be committed to tracked source")
    if target.exists() and any(target.iterdir()):
        raise ValueError("Refusing to overwrite frozen candidate")
    if not re.fullmatch(r"[a-f0-9]{40}",code_revision):
        raise ValueError("Freeze requires explicit 40-char source commit id")
    stamp=datetime.fromisoformat(generated_at.replace("Z","+00:00"))
    if not generated_at.endswith("Z") or stamp.utcoffset().total_seconds()!=0:
        raise ValueError("Freeze timestamp must be explicit UTC")
    rows=make_pilot()
    gov,_=governance_run(source_dir=build_dir)
    if gov["status"]!="ENGINEERING_PASS" or gov["technical_blocker_count"]:
        raise ValueError("Technical QA failed: cannot freeze pilot candidate")
    if gov["release_status"]!="BLOCKED" or gov["director_release_approved"]:
        raise ValueError("Unexpected governance release status; stop and review")
    target.mkdir(parents=True,exist_ok=True)
    pilot=target/"wp10_pilot_17.csv"
    _write_csv(pilot,rows,COLUMNS)
    studies={r["study_id"] for r in rows}
    checklist=[
        {"gate":"uppsala_eight","result":"PASS","detail":"8/8; sum 10821; 2022 seven-form report"},
        {"gate":"sormland_nine_annexes","result":"PASS_METADATA_ONLY",
         "detail":"9/9 distinct municipality appendices; no figures fabricated"},
        {"gate":"independent_study_count","result":"PASS",
         "detail":"2 studies; 17 municipal record slots; Sormland annexes one study"},
        {"gate":"source_trace","result":"PASS_INDEX_ONLY",
         "detail":"Each row traces source_id and 2026 SCB code; source content RefA outstanding"},
        {"gate":"historic_polygon_2022","result":"BLOCKED","detail":"No approved 2022 polygon source"},
        {"gate":"qgis_map_2022","result":"BLOCKED","detail":"No real QGIS .qgz/topology acceptance"},
        {"gate":"original_claim_harp","result":"BLOCKED","detail":"Full HARP RefA not verified"},
        {"gate":"legal_reuse_and_privacy","result":"BLOCKED","detail":"Dataset rights and privacy pending"},
        {"gate":"director_public_release","result":"BLOCKED","detail":"No Director signoff for public data release"}
    ]
    _write_csv(target/"wp10_acceptance_gates.csv",checklist,["gate","result","detail"])
    source_hashes={label:{"path":path,"sha256":digest(ROOT/path)} for label,path in SOURCE_FILES.items()}
    artifact_hashes={
        "wp10_pilot_17.csv":digest(pilot),
        "wp10_acceptance_gates.csv":digest(target/"wp10_acceptance_gates.csv")
    }
    manifest={
        "manifest_contract":CONTRACT,"candidate_version":VERSION,
        "candidate_state":"FROZEN_INTERNAL_NOT_RELEASED",
        "created_at_utc":generated_at,"git_commit":code_revision,
        "source_files":source_hashes,"generated_artifacts":artifact_hashes,
        "pilot":{"uppsala_municipalities":8,"uppsala_2022_total":10821,
                 "uppsala_population":"seven_legal_forms_including_housing_associations",
                 "sormland_annex_municipalities":9,"sormland_numeric_observations":0,
                 "unique_municipalities":17,"underlying_studies":len(studies)},
        "geometry":{"available":False,"spatial_project_produced":False,
                    "identifier_reference_year":2026,"observation_vintages":[2022,2023],
                    "historical_2022_geometry_needed":True},
        "quality":{"technical":gov["status"],"publication":gov["release_status"],
                   "release_blockers":gov["release_blocker_count"],
                   "harp_refa_complete":False,"rights_cleared":False,
                   "director_authorized":False},
        "release":{"github_tag_created":False,"github_release_created":False,
                   "public_artifacts_uploaded":False,"can_publish":False},
        "interpretation":"Engineering pilot freeze only; never a released map or dataset."
    }
    (target/"wp10_manifest.json").write_text(
        json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
        encoding="utf-8")
    return manifest


def verify(path):
    path=Path(path)
    manifest=json.loads((path/"wp10_manifest.json").read_text(encoding="utf-8"))
    if manifest["manifest_contract"]!=CONTRACT or manifest["candidate_version"]!=VERSION:
        raise ValueError("Wrong WP10 candidate contract")
    for x in ("wp10_pilot_17.csv","wp10_acceptance_gates.csv"):
        if digest(path/x)!=manifest["generated_artifacts"][x]:
            raise ValueError("Frozen artifact checksum mismatch: "+x)
    for v in manifest["source_files"].values():
        if digest(ROOT/v["path"])!=v["sha256"]:
            raise ValueError("Source file changed after freeze: "+v["path"])
    rows=read_csv(path/"wp10_pilot_17.csv")
    if len(rows)!=17 or len({x["municipality_code"] for x in rows})!=17:
        raise ValueError("Frozen pilot scope invalid")
    if len([x for x in rows if x["area"]=="Uppsala län"])!=8:
        raise ValueError("Uppsala coverage changed")
    sorm=[x for x in rows if x["area"]=="Södermanlands län"]
    if len(sorm)!=9 or any(x["value"]!="" or x["value_status"]!="not_extracted_not_zero" for x in sorm):
        raise ValueError("Sörmland values invented or modified")
    if (manifest["release"]["can_publish"] is not False or
        manifest["quality"]["director_authorized"] is not False):
        raise ValueError("Candidate contains unauthorized release claim")
    return {"result":"FROZEN_INTERNAL_CANDIDATE_VALIDATED","version":VERSION,
            "pilot_rows":17,"sormland_values_extracted":0,
            "publication_authorized":False}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="command",required=True)
    b=sub.add_parser("freeze")
    b.add_argument("--out",required=True)
    b.add_argument("--generated-at",required=True)
    b.add_argument("--code-revision",required=True)
    b.add_argument("--build-dir")
    v=sub.add_parser("verify");v.add_argument("--path",required=True)
    a=p.parse_args(argv)
    if a.command=="freeze":
        result=freeze(a.out,a.generated_at,a.code_revision,a.build_dir)
    else:result=verify(a.path)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
