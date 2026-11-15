"""WP09 Quality & Governance: evidence-first audit, RAG log and release gate.

The development/test pipeline can pass while public release remains BLOCKED.
This program never grants HARP RefA, a licence, privacy clearance, signed
Director approval or access to official polygon files.

HARP is Appendix O: ITR1, ITR2, ITR4, ITR5, ITR6 (NO ITR3).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .cli import ROOT, read_csv, digest, validate as base_validate
from .sources import validate as source_validate
from .statistics import validate as statistics_validate
from .gis import validate_attributes
from .ffspatial_adapter import validate_output as adapter_validate

HARP = ("ITR1","ITR2","ITR4","ITR5","ITR6")
ALLOWED_COLOURS = {"RED","AMBER","GREEN"}
SCANNABLE = {".py",".md",".rst",".csv",".json",".jsonl",".yml",".yaml",".toml",".txt",".sh"}
BINARY_BLOCK = {".xlsx",".xls",".xlsm",".pdf",".docx",".zip",".gpkg",".qgz",".sqlite",".db",".pem",".key"}
SECRET_PATTERN = re.compile(
    r"(?i)(?:ghp_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,}|"
    r"sk-[A-Za-z0-9_-]{24,}|"
    r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----)"
)
PERSONAL_EMAIL_PATTERN = re.compile(
    r"(?i)\b[A-Za-z0-9._%+\-]+@(?!example\.(?:org|com|net)\b)"
    r"[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)
RESTRICTED_PATH = re.compile(r"(?i)(?:^|/)(?:raw|staging|private|secrets|credentials)(?:/|$)")
SCHEMA_VERSION = "wp09.qa.v1"
CANONICAL = {
    "source_registry":"manifests/source_registry_v1.csv",
    "archive_registry":"manifests/source_archive_inventory_v1.csv",
    "publications":"data/curated/publications/publication_registry_v1.csv",
    "observations":"data/curated/observations/uppsala_2022.csv",
    "scb":"data/curated/statistics/scb_national_2023_2024.csv",
    "municipalities":"data/curated/dimensions/municipalities.csv",
    "counties":"data/curated/dimensions/counties.csv",
    "methods":"data/curated/statistics/methods.csv",
    "metrics":"data/curated/statistics/metrics.csv"
}


def issue(code, colour, scope, evidence, required_action="", owner="", gate="technical"):
    if colour not in ALLOWED_COLOURS:
        raise ValueError("Invalid RAG label")
    return {
        "issue_id":code,
        "rag":colour,
        "scope":scope,
        "evidence":evidence,
        "required_action":required_action,
        "owner":owner,
        "gate":gate,
    }


def _read_csv(path):
    return read_csv(ROOT/path)


def audit_sources():
    """Audit source claim *metadata*; never mark unreviewed PDFs as RefA."""
    src=_read_csv(CANONICAL["source_registry"])
    archive={r["source_id"]:r for r in _read_csv(CANONICAL["archive_registry"])}
    if len(src)!=len(archive):
        raise ValueError("Source and archive row coverage mismatch")
    report=[]
    for r in src:
        source_id=r["source_id"]
        if source_id not in archive:
            raise ValueError("Source without archive manifest: "+source_id)
        a=archive[source_id]
        # Metadata (ITR1/ITR4) are not proof of actually reading and checking
        # the entirety of the original document (ITR2/ITR5).
        itr1=bool(r["title"] and r["publisher"] and r["original_url"])
        itr4=bool(r["reference"] and r["original_url"])
        itr2=False
        itr5=False
        itr6=False
        rights=r["rights_status"]=="approved"
        original_hash=(r["checksum_status"]=="computed" and
                       re.fullmatch(r"[a-f0-9]{64}",r["checksum_sha256"] or "") is not None)
        claimed_refa=r["harp_level"]=="RefA_approved"
        if claimed_refa and not all((itr1,itr2,itr4,itr5,itr6)):
            raise ValueError("HARP RefA claimed without review evidence: "+source_id)
        report.append({
            "source_id":source_id,
            "ITR1_source_identity_metadata":"metadata_present" if itr1 else "not_checked",
            "ITR2_full_original_read":"not_verified_in_WP09",
            "ITR4_harvard_citation_metadata":"present_requires_review" if itr4 else "not_checked",
            "ITR5_manual_claim_crosscheck":"not_verified_in_WP09",
            "ITR6_validation_gate":"blocked_pending_ITR2_ITR5",
            "binary_sha256":"recorded" if original_hash else "not_computed",
            "original_binary_held_in_repo":"false",
            "redistribution_rights":"approved" if rights else "not_cleared",
            "publishable":"false",
            "current_source_status":r["source_status"]
        })
    return report


def scan_public_tree():
    """Conservative static scan of tracked *publishable source* only.

    No git execution or traversal of sibling projects; ignores build/ and
    runtime cache. A clean scan cannot replace a legal privacy review.
    """
    root=ROOT
    findings=[]
    count=0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel=path.relative_to(root)
        if any(p in {".git",".venv","__pycache__",".pytest_cache","build","dist",".mypy_cache"} for p in rel.parts):
            continue
        if rel.parts[0].startswith(".") and rel.parts[0] not in {".github"}:
            if rel.name not in {".gitignore"}:
                continue
        if any(p.endswith(".egg-info") for p in rel.parts):
            continue
        suffix=path.suffix.casefold()
        if RESTRICTED_PATH.search(rel.as_posix()) and rel.name not in {".gitkeep","README.md"}:
            findings.append(issue("RESTRICTED_PATH","RED","privacy",
                                  "Restricted-looking file path: "+rel.as_posix(),
                                  "Remove or explicitly justify public content",
                                  "Data steward"))
            continue
        if suffix in BINARY_BLOCK:
            findings.append(issue("BINARY_SOURCE_FILE","RED","privacy",
                                  "Non-cleared binary file in source tree: "+rel.as_posix(),
                                  "Remove binary; retain checksum only", "Data steward"))
            continue
        if suffix not in SCANNABLE or path.stat().st_size>2_000_000:
            continue
        count+=1
        body=path.read_text(encoding="utf-8",errors="replace")
        # Only return path; never echo a secret or email value into CI logs.
        if SECRET_PATTERN.search(body):
            findings.append(issue("CREDENTIAL_PATTERN","RED","security",
                                  "Potential credential in "+rel.as_posix(),
                                  "Revoke exposed credential and rotate immediately","Security maintainer"))
        if rel.as_posix().startswith(("data/curated/","manifests/")) and
           PERSONAL_EMAIL_PATTERN.search(body):
            findings.append(issue("PERSONAL_CONTACT_IN_PUBLIC_DATA","RED","privacy",
                                  "Email-like contact in published data: "+rel.as_posix(),
                                  "Review legal basis and remove sensitive contact fields","Data steward"))
    return count,findings


def _artifact_checks(source_dir):
    if source_dir is None:
        return {"status":"not_supplied","attribute_geopackage":"not_checked",
                "ffspatial":"not_checked"},[]
    src=Path(source_dir)
    output=[]
    package=src/"ideburen_tables.gpkg"
    if not package.is_file():
        output.append(issue("WP07_PACKAGE_MISSING","RED","build",
                     "Missing GeoPackage at expected build path",
                     "Build WP07 outputs","GIS maintainer","technical"))
        return {"status":"missing","attribute_geopackage":"not_checked"},output
    try:
        a=validate_attributes(package,src)
    except (ValueError,KeyError,FileNotFoundError,RuntimeError) as e:
        output.append(issue("WP07_PACKAGE_FAIL","RED","build",
                     "GeoPackage contract failed: "+type(e).__name__,
                     "Review failing package validator","GIS maintainer","technical"))
        return {"status":"failed","attribute_geopackage":"failed"},output
    adapter=src/"ffspatial_adapter"
    if adapter.is_dir():
        try:
            v=adapter_validate(adapter)
            status=v["result"]
        except (ValueError,KeyError,FileNotFoundError,RuntimeError):
            status="failed"
            output.append(issue("WP08_ADAPTER_FAIL","RED","build",
                          "Adapter output integrity failure",
                          "Rebuild producer adapter and recheck hashes",
                          "Maintainer","technical"))
    else:
        status="not_built"
    return {
        "status":"ok" if not output else "failed",
        "attribute_geopackage":"validated",
        "verified_municipalities":a["municipal_codes"],
        "source_scope_2022":a["uppsala_2022_reported"],
        "out_of_scope_null":a["uppsala_2022_not_in_scope_null"],
        "ffspatial":status,
        "geometry":0
    },output


def run(*,source_dir=None, extra_findings=()):
    """Run governance QA without turning incomplete evidence into approval."""
    # Existing automated checks must pass or WP09 engineering status turns red.
    technical=[]
    validations={}
    for label,fn in (("WP02",base_validate),("WP03",source_validate),
                     ("WP06",statistics_validate)):
        try:
            validations[label]=fn()
        except (AssertionError,ValueError,KeyError,FileNotFoundError) as e:
            technical.append(issue(label+"_VALIDATION_FAIL","RED","integrity",
                                   label+" validator failed: "+type(e).__name__,
                                   "Repair and rerun validator","Maintainer","technical"))
    try:
        source_audit=audit_sources()
    except (ValueError,KeyError,FileNotFoundError):
        technical.append(issue("HARP_SOURCE_AUDIT_INVALID","RED","sources",
                               "Source registry audit cannot be generated",
                               "Repair source metadata","Research reviewer","technical"))
        source_audit=[]
    counted,security=scan_public_tree()
    artifacts,artifact_errors=_artifact_checks(source_dir)
    technical.extend(security+artifact_errors+list(extra_findings))
    sources=_read_csv(CANONICAL["source_registry"])
    rights_ok=sum(x["rights_status"]=="approved" for x in sources)
    checksums=sum(x["checksum_status"]=="computed" for x in sources)
    publication_release=[
        issue("POLYGONS_UNAVAILABLE","RED","geography",
              "Lantmäteriet account application submitted; authorization and actual annual polygons unconfirmed",
              "Acquire authorized polygons and verify 2022 vintage separately",
              "GIS maintainer","release"),
        issue("QGIS_RUNTIME_PENDING","RED","geography",
              "No actual .qgz with validated annual 2022 polygons and topology receipt",
              "Execute QGIS geometry/topology audit on actual licensed 2022 polygons",
              "GIS maintainer","release"),
        issue("SOURCE_REFA_INCOMPLETE","RED","sources",
              "Full primary-source HARP RefA ITR1/ITR2/ITR4/ITR5/ITR6 not documented for public claims",
              "Review each original table/decision and attach source-located evidence",
              "Research reviewer","release"),
        issue("LICENSE_CLEARANCE_PENDING","RED","rights",
              f"{len(sources)-rights_ok} of {len(sources)} sources not marked redistribution-approved",
              "Record licence, rights holder, re-use terms and dated review for each released dataset",
              "Data steward","release"),
        issue("PRIVACY_REVIEW_PENDING","RED","privacy",
              "Automated static scan does not establish legitimate disclosure basis",
              "Approve privacy and disclosure impact review for released observations",
              "Data steward","release"),
        issue("DIRECTOR_RELEASE_APPROVAL_MISSING","RED","governance",
              "ADR approval is NOT approval to publish a public data/map release",
              "Record explicit Director release approval after other gates pass",
              "Director","release"),
        issue("FFSPATIAL_CONSUMER_NOT_RUN","AMBER","integration",
              "WP08 field mappings tested, local downstream FF-Spatial runtime not exercised",
              "Execute bounded consumer import after separate authorization",
              "GIS maintainer","release"),
        issue("SORM_LAN_ANNEXES_NOT_AUDITED","AMBER","coverage",
              "Nine Sörmland annexes indexed but not source-extracted and RefA-checked",
              "Review full source tables/period/legal forms before WP10 pilot",
              "Research reviewer","release"),
        issue("WP05_PRIMARY_DECISIONS_OPEN","AMBER","evidence",
              "27 seed events are not 27 independently verified legal decisions",
              "Primary audit of minutes and document specific assertions",
              "Research reviewer","release"),
        issue("SOURCE_CHECKSUM_COVERAGE","AMBER","provenance",
              f"{checksums}/{len(sources)} source binaries have recorded SHA-256",
              "Compute remaining original binary hashes through authorized source access",
              "Data steward","release")
    ]
    findings=technical+publication_release
    if not any(f["rag"]=="RED" and f["gate"]=="technical" for f in findings):
        findings.insert(0,issue("ENGINEERING_BASELINE_PASS","GREEN","engineering",
              "Core reference and source validators passed; build artifacts checked when supplied",
              "Continue source-specific audits","Maintainer","technical"))
    # Red release = no public release, not failed engineering CI.
    release_blocked=any(f["rag"]=="RED" for f in findings)
    technical_blocked=any(f["rag"]=="RED" and f["gate"]=="technical" for f in findings)
    summary={
        "contract":SCHEMA_VERSION,
        "audit_type":"automated_governance_preflight_not_human_RefA",
        "status":"TECHNICAL_FAIL" if technical_blocked else "ENGINEERING_PASS",
        "release_status":"BLOCKED" if release_blocked else "ELIGIBLE_FOR_HUMAN_DECISION",
        "director_release_approved":False,
        "harp_steps":list(HARP),
        "refa_automatically_approved":False,
        "source_count":len(sources),
        "source_reviewed_binary_sha256":checksums,
        "source_redistribution_rights_approved":rights_ok,
        "source_records_full_refa_approved":0,
        "source_audit_records":len(source_audit),
        "repository_files_scanned":counted,
        "artifact_integrity":artifacts,
        "checks":validations,
        "issue_counts":dict(Counter(f["rag"] for f in findings)),
        "technical_blocker_count":sum(f["rag"]=="RED" and f["gate"]=="technical" for f in findings),
        "release_blocker_count":sum(f["rag"]=="RED" and f["gate"]=="release" for f in findings),
        "findings":findings,
    }
    return summary,source_audit


def write_report(report,source_audit,out):
    path=Path(out)
    if path.resolve()==ROOT or (ROOT in path.resolve().parents and
                                ROOT/"build" not in path.resolve().parents):
        raise ValueError("QA reports must be written to build/ or an external analysis directory")
    path.mkdir(parents=True,exist_ok=True)
    (path/"wp09_audit.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
        encoding="utf-8")
    with (path/"wp09_qa_log.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=[
            "issue_id","rag","scope","gate","evidence","required_action","owner"
        ])
        w.writeheader()
        w.writerows(report["findings"])
    if source_audit:
        with (path/"wp09_harp_source_matrix.csv").open("w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(source_audit[0]))
            w.writeheader();w.writerows(source_audit)
    return path


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("command",choices=("audit","release-check"))
    p.add_argument("--source-dir",help="Built WP07/WP08 artifacts")
    p.add_argument("--out",default="build/wp09")
    a=p.parse_args(argv)
    report,source_audit=run(source_dir=a.source_dir)
    write_report(report,source_audit,a.out)
    print(json.dumps({
        "engineering":report["status"],
        "release":report["release_status"],
        "harp_refa":report["refa_automatically_approved"],
        "technical_blockers":report["technical_blocker_count"],
        "release_blockers":report["release_blocker_count"],
        "issue_counts":report["issue_counts"],
        "report_dir":a.out
    },ensure_ascii=False,indent=2))
    if report["technical_blocker_count"]:
        return 1
    if a.command=="release-check" and report["release_status"]!="ELIGIBLE_FOR_HUMAN_DECISION":
        return 2
    return 0


if __name__=="__main__":
    raise SystemExit(main())
