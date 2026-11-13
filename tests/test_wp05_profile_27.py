"""Structural integration test with 27 *synthetic, non-sensitive* WP04-shaped rows.

Reproduces the observed municipality/stage/date profile only. It is not a
republication of the user's private workbook and NOT a source-authenticity test.
"""
import csv
import json
from pathlib import Path
from collections import Counter
from ideburen.decision_engine import build

PROFILE=[
 ("0380","2013","Beslut"),("0380","2018–2023","Överenskommelse"),
 ("0380","2025-06-10","Beredning"),("0380","2025-06-18","Beredning"),
 ("0380","2025-08-22","Tjänsteskrivelse"),("0380","2025-09-08","Beslut"),
 ("0380","2025-09-08","Politiskt yttrande"),("0380","2026","Genomförande"),
 ("0360","2022-06-08","Beslut"),("0360","2024-03","Dialog"),
 ("0360","2025","Utvärdering och dialog"),("0360","2025-09","Beslut"),
 ("0360","2025–2031","Styrdokument"),
 ("0330","2019","Dialog och remiss"),("0330","2022-04-19","Workshop"),
 ("0330","2022-09-04","Dialog"),("0330","2023","Dialog och remiss"),
 ("0330","2023-12","Dialog och enkät"),("0330","2021-11-25","Beslut"),
 ("0382","2017–2019","Initiativ / uppdrag"),("0382","2020-12-03","Beslut"),
 ("0381","Datum ej verifierat","Principbeslut / riktlinjer"),
 ("0381","2026","Genomförande"),("0305","2025-04-07","Beslut"),
 ("0331","2024-10-07","Beslut"),("0331","2026","Genomförande"),
 ("0319","Datum ej verifierat","Riktlinjer")
]
def test_twenty_seven_record_profile(tmp_path):
    p=tmp_path/"seed_shape.csv"
    keys=["row_id","source_id","municipality_code","evidence_status","source_sha256",
          "period","event_stage","event_text","verification_status","source_url"]
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
        for n,(code,period,stage) in enumerate(PROFILE,start=2):
            # Synthetic descriptions intentionally omit private source content.
            description=("Policyn kräver årlig uppföljning" if n==9 else f"Synthetic test event {n}")
            w.writerow({"row_id":f"uppsala_register/Beslutskedjor/{n}",
                "source_id":"seed_uppsala","municipality_code":code,
                "evidence_status":"seed_unverified","source_sha256":"a"*64,
                "period":period,"event_stage":stage,"event_text":description,
                "verification_status":"Test fixture, not audited","source_url":""})
    result=build(p,tmp_path/"out",strict=True)
    assert result["events"]==27
    assert result["cases"]==9
    assert result["normative_or_period_claims_excluded_from_temporal_graph"]>=2
    assert result["explicit_refa_relation_edges"]==0
    assert not result["primary_decisions_validated"]
    assert not result["release_approval"]
    with (tmp_path/"out/cases.csv").open(encoding="utf-8") as f:
        records=list(csv.DictReader(f))
    counts={r["case_id"]:int(r["event_count"]) for r in records}
    assert counts["uppsala_cooperation"]==8
    assert counts["tierp_cooperation"]==5
    assert counts["knivsta_cooperation"]==5
    assert counts["knivsta_social_grants"]==1
    assert len({r["municipality_code"] for r in records})==8
    assert (tmp_path/"out/decision_graph.graphml").exists()
    assert (tmp_path/"out/evidence_requests.csv").exists()
