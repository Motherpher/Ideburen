from pathlib import Path
import json,tempfile
import pytest
from ideburen import sources

def test_source_catalog_integrity():
    summary=sources.validate()
    assert summary["source_records"]>=40
    assert summary["publication_records"]>=30
    assert summary["legacy_sources_covered"]>=10
    assert summary["binary_checksums_computed"]==2
    assert summary["harp_refa_publication_gate"]=="NOT_APPROVED"

def test_editions_deduplicate_to_common_study():
    entries=sources.rows(sources.PUBLICATION)
    varmland=[x for x in entries if x["study_id"]=="study_varmland_2023"]
    assert len(varmland)==3
    assert {"academic_reissue","interactive_data"}.issubset({x["edition_role"] for x in varmland})
    sormland=[x for x in entries if x["study_id"]=="study_sormland_2023"]
    assert len(sormland)==10
    assert sum(x["edition_role"]=="municipal_appendix" for x in sormland)==9

def test_private_checksum_not_committed(tmp_path):
    doc=tmp_path/"input.pdf"
    doc.write_bytes(b"this is test data")
    ledger=tmp_path/"private"/"checksum.json"
    output=sources.local_sha256("sormland_2024",doc,ledger)
    assert len(output["sha256"])==64
    assert output["rights_status"]=="pending_separate_review"
    assert json.loads(ledger.read_text())["original_basename"]=="input.pdf"

def test_unknown_checksum_source(tmp_path):
    p=tmp_path/"a.txt";p.write_text("x")
    with pytest.raises(ValueError,match="unknown source_id"):
        sources.local_sha256("not_a_source",p,tmp_path/"out.json")

def test_checksummed_source_cannot_write_inside_repository():
    with pytest.raises(ValueError,match="outside"):
        sources.local_sha256("sormland_2024", sources.SOURCE, sources.ROOT/"build/private_checksum.json")
