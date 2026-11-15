"""WP10 pilot / freeze: no fictitious figures, no public release without gates."""
import csv
import json
from pathlib import Path

import pytest

from ideburen import pilot_release as p


def test_pilot_exact_seventeen_and_study_deduplication():
    rows=p.make_pilot()
    assert len(rows)==17
    assert len({r["municipality_code"] for r in rows})==17
    assert {r["study_id"] for r in rows}=={"study_uppsala_2022","study_sormland_2023"}
    u=[r for r in rows if r["area"]=="Uppsala län"]
    s=[r for r in rows if r["area"]=="Södermanlands län"]
    assert len(u)==8 and sum(int(r["value"]) for r in u)==10821
    assert len(s)==9 and {r["municipality_name"] for r in s}==p.SORM_NAMES
    assert all(r["value"]=="" and r["metric_id"]=="" for r in s)
    assert all(r["value_status"]=="not_extracted_not_zero" for r in s)
    assert all(r["geography_reference_year"]=="2026_identifier_only" for r in rows)
    assert all(r["harp_refa_status"]=="pending" for r in rows)


def test_freeze_manifest_hashes_verify_and_no_release(tmp_path):
    target=tmp_path/"candidate"
    manifest=p.freeze(
        target,"2026-11-15T17:00:00Z",
        "a"*40
    )
    assert manifest["candidate_state"]=="FROZEN_INTERNAL_NOT_RELEASED"
    assert manifest["pilot"]["sormland_numeric_observations"]==0
    assert manifest["pilot"]["underlying_studies"]==2
    assert manifest["geometry"]["available"] is False
    assert manifest["release"]["github_release_created"] is False
    assert manifest["quality"]["publication"]=="BLOCKED"
    assert p.verify(target)["publication_authorized"] is False
    with pytest.raises(ValueError,match="overwrite"):
        p.freeze(target,"2026-11-15T17:00:00Z","a"*40)


def test_freeze_fails_on_modified_pilot(tmp_path):
    target=tmp_path/"candidate"
    p.freeze(target,"2026-11-15T17:00:00Z","a"*40)
    path=target/"wp10_pilot_17.csv"
    path.write_text(path.read_text(encoding="utf-8").replace("not_extracted_not_zero","0",1),encoding="utf-8")
    with pytest.raises(ValueError,match="checksum mismatch"):
        p.verify(target)


def test_no_unapproved_git_tracking_or_fake_commit(tmp_path):
    from ideburen.cli import ROOT
    with pytest.raises(ValueError,match="tracked source"):
        p.freeze(ROOT/"data/curated/wp10","2026-11-15T17:00:00Z","a"*40)
    with pytest.raises(ValueError,match="40-char"):
        p.freeze(tmp_path/"candidate","2026-11-15T17:00:00Z","main")


def test_sormland_source_family_integrity():
    rows=p.make_pilot()
    s=[r for r in rows if r["area"]=="Södermanlands län"]
    assert len({r["publication_id"] for r in s})==9
    assert {r["publication_year"] for r in s}=={"2024"}
    assert {r["observation_year"] for r in s}=={"2023"}
    assert {r["study_id"] for r in s}=={"study_sormland_2023"}


def test_candidate_qa_gates_remain_red(tmp_path):
    target=tmp_path/"candidate"
    p.freeze(target,"2026-11-15T17:00:00Z","a"*40)
    with (target/"wp10_acceptance_gates.csv").open(encoding="utf-8") as f:
        gates=list(csv.DictReader(f))
    reds=[x for x in gates if x["result"]=="BLOCKED"]
    assert len(reds)>=4
    assert any(x["gate"]=="director_public_release" for x in reds)
    assert not any(x["gate"]=="qgis_map_2022" and x["result"]=="PASS" for x in gates)
