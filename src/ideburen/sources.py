"""WP03: deterministic source/publication register QA and private checksum ledger.

No network requests; never copies private Drive originals into the public repository.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"manifests/source_registry_v1.csv"
PUBLICATION=ROOT/"data/curated/publications/publication_registry_v1.csv"
FAMILY=ROOT/"data/curated/publications/study_family_registry_v1.csv"
ARCHIVE=ROOT/"manifests/source_archive_inventory_v1.csv"
LEGACY=ROOT/"manifests/sources.csv"
ACCESS={"public","internal","restricted"}
STATUS={"primary_verified","metadata_page_verified","metadata_only","internal_inventory","secondary_pending","unverified","contradicted","unavailable"}
RIGHTS={"not_reviewed_for_redistribution","approved","restricted","denied"}
CLASS={"A","B","C","P","reference","legacy"}

def rows(path):
    with Path(path).open(newline="",encoding="utf-8-sig") as f:return list(csv.DictReader(f))

def _unique(rows_,field):
    values=[r[field] for r in rows_]
    if any(not v for v in values):raise ValueError("blank "+field)
    if len(values)!=len(set(values)):raise ValueError("duplicate "+field)
    return set(values)

def validate():
    sources=rows(SOURCE); pubs=rows(PUBLICATION); fam=rows(FAMILY); archive=rows(ARCHIVE)
    ids=_unique(sources,"source_id")
    pubids=_unique(pubs,"publication_id")
    families=_unique(fam,"study_id")
    archive_ids=_unique(archive,"source_id")
    if ids!=archive_ids:raise ValueError("archive inventory coverage mismatch")
    legacy=_unique(rows(LEGACY),"source_id")
    if not legacy.issubset(ids):raise ValueError("legacy seed sources are missing from WP03")
    if len(sources)<len(legacy) or not pubs:raise ValueError("registry not populated")
    for r in sources:
        for field in ["title","publisher","reference","provenance_note","study_id","harp_level","rights_status"]:
            if not r[field]:raise ValueError("missing "+field+" for "+r["source_id"])
        if r["access"] not in ACCESS:raise ValueError("invalid access")
        if r["source_status"] not in STATUS:raise ValueError("invalid status")
        if r["rights_status"] not in RIGHTS:raise ValueError("invalid rights status")
        if r["source_type"] not in CLASS:raise ValueError("invalid classification")
        if r["study_id"] not in families:raise ValueError("unregistered study family")
        if r["checksum_status"]=="not_computed" and r["checksum_sha256"]:
            raise ValueError("checksum present but not computed")
        if r["checksum_status"]=="computed" and not re.fullmatch(r"[a-f0-9]{64}",r["checksum_sha256"]):
            raise ValueError("invalid checksum")
        if r["access"]!="public" and ("drive.google.com/" in r["original_url"] or "file/d/" in r["original_url"]):
            raise ValueError("private Drive identifier exposed")
        if r["source_status"] in ("metadata_only","metadata_page_verified","unverified","secondary_pending") and r["harp_level"]=="RefA_approved":
            raise ValueError("HARP cannot be approved on metadata alone")
    group_count={}
    for p in pubs:
        if p["source_id"] not in ids:raise ValueError("orphan publication "+p["publication_id"])
        if p["study_id"] not in families:raise ValueError("orphan study "+p["study_id"])
        if p["study_id"] != next(s["study_id"] for s in sources if s["source_id"]==p["source_id"]):
            raise ValueError("source/publication study mismatch")
        if p["publication_kind"] not in CLASS:raise ValueError("unexpected publication class")
        group_count[p["study_id"]]=group_count.get(p["study_id"],0)+1
    for f in fam:
        if int(f["publication_count"])!=group_count.get(f["study_id"],0):
            raise ValueError("incorrect family edition count "+f["study_id"])
    for a in archive:
        if a["file_sha256"] and a["sha256_status"]!="computed":
            raise ValueError("archive file checksum not marked computed")
        if a["sha256_status"] not in ("not_computed","computed"):
            raise ValueError("bad archive checksum status")
        if re.search(r"drive\.google\.com/file/d/|1[A-Za-z0-9_-]{30,}",a["location_publication"]):
            raise ValueError("internal Drive file ID leaked")
    duplicate_groups=sorted(k for k,v in group_count.items() if v>1)
    assert "study_varmland_2023" in duplicate_groups
    assert "study_sormland_2023" in duplicate_groups
    return {"source_records":len(sources),"publication_records":len(pubs),
            "study_families":len(families),"archive_inventory_records":len(archive),
            "legacy_sources_covered":len(legacy),
            "multi_publication_studies":duplicate_groups,
            "binary_checksums_computed":sum(a["sha256_status"]=="computed" for a in archive),
            "binary_checksum_status":"PENDING_SOURCE_FILE_ACCESS",
            "harp_refa_publication_gate":"NOT_APPROVED",
            "validation":"PASS_METADATA_INTEGRITY"}

def local_sha256(source_id,filename,out):
    ids=_unique(rows(SOURCE),"source_id")
    if source_id not in ids:raise ValueError("unknown source_id")
    source=Path(filename)
    if not source.is_file():raise FileNotFoundError(source)
    h=hashlib.sha256()
    with source.open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):h.update(chunk)
    output=Path(out)
    if ROOT in output.resolve().parents or output.resolve()==ROOT:
        raise ValueError("Private checksum ledger must be written outside the git repo")
    entry={"source_id":source_id,"original_basename":source.name,"sha256":h.hexdigest(),
           "size_bytes":source.stat().st_size,"verification":"local_binary_sha256_only",
           "rights_status":"pending_separate_review"}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(entry,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return entry

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    s=p.add_subparsers(dest="command",required=True)
    s.add_parser("validate")
    c=s.add_parser("checksum")
    c.add_argument("--source-id",required=True)
    c.add_argument("--file",required=True)
    c.add_argument("--out",required=True)
    a=p.parse_args(argv)
    v=validate() if a.command=="validate" else local_sha256(a.source_id,a.file,a.out)
    print(json.dumps(v,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
