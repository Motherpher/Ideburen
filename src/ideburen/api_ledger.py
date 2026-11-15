"""SCB AFR v2 API ledger, local-only plans and append-only audit events.

No live requests until the current OpenAPI specification and auth contract
have been verified, and the personal API key has been supplied securely.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,re
from datetime import datetime
from pathlib import Path
from .cli import ROOT

BASE=ROOT/"config/api_ledger"
COLUMNS=("event_id","utc","api_id","action","status","input_sha256","output_sha256","count","rights","harp","note")

def config():
    sources=json.loads((BASE/"sources.json").read_text(encoding="utf-8"))
    policy=json.loads((BASE/"civil_society_policy_v1.json").read_text(encoding="utf-8"))
    api=next(x for x in sources["apis"] if x["id"]=="scb_afr_v2")
    if api["auth"]!="personal_api_key" or api["max_page_rows"]>5000 or api["max_requests_per_second"]>5:
        raise ValueError("SCB rate/auth mismatch")
    groups=[set(policy[x]) for x in ("core","review","separate")]
    if any(groups[i]&groups[j] for i,j in ((0,1),(0,2),(1,2))):
        raise ValueError("Overlapping legal-form groups")
    if set.union(*groups)!={"51","53","54","61","62","63","71","72"}:
        raise ValueError("Unknown legal-form coverage")
    if policy["publication_authorized"] is not False:
        raise ValueError("No automatic release approval")
    return sources,policy

def classify(form,sni=()):
    _,policy=config()
    form=str(form or "").strip()
    if form in policy["core"]: tier="core"
    elif form in policy["review"]: tier="review"
    elif form in policy["separate"]: tier="separate"
    else: tier="outside_configured_scope"
    codes=[re.sub(r"[^0-9]","",str(x)) for x in (sni or [])]
    return {"legal_form":form,"tier":tier,
            "sni_focus":any(x.startswith(("93","94")) for x in codes),
            "sni_hard_exclusion":False,
            "organisational_membership_verified":False}

def plan():
    sources,policy=config()
    api=next(x for x in sources["apis"] if x["id"]=="scb_afr_v2")
    return {"schema":"ideburen.api-ledger.plan.v1","api_id":api["id"],
            "status":"BLOCKED_PENDING_OPENAPI_REVIEW_AND_API_KEY",
            "live_requests":0,"source_snapshot":"current_only",
            "operations":[{"legal_form":k,"selection":group,"mode":"planned_not_executed"}
              for group in ("core","review") for k in policy[group]],
            "max_page_rows":api["max_page_rows"],
            "max_requests_per_second":api["max_requests_per_second"],
            "schema_verified":False,"credential_stored":False,
            "raw_data_public":False,"release_authorized":False}

def safe_path(name):
    p=Path(name).resolve()
    if p==ROOT or ROOT in p.parents:
        if p!=ROOT/"build" and ROOT/"build" not in p.parents:
            raise ValueError("Writes allowed only to local build directory or outside repo")
    return p

def write_plan(name):
    p=safe_path(name)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(plan(),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return p

def append_event(filename,entry):
    if set(entry)!=set(COLUMNS):raise ValueError("Ledger schema mismatch")
    if entry["action"] not in ("contract_review","dry_run","snapshot","failure"):
        raise ValueError("Unsupported ledger action")
    if entry["status"] not in ("pending","blocked","success","failure"):
        raise ValueError("Unsupported event status")
    if entry["api_id"] not in {x["id"] for x in config()[0]["apis"]}:
        raise ValueError("Unregistered API id")
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z",entry["utc"]):
        raise ValueError("UTC timestamp required")
    datetime.fromisoformat(entry["utc"].replace("Z","+00:00"))
    for key in ("input_sha256","output_sha256"):
        if entry[key] and not re.fullmatch(r"[a-f0-9]{64}",entry[key]):
            raise ValueError("Invalid SHA-256")
    if not re.fullmatch(r"(0|[1-9][0-9]*)",str(entry["count"])):
        raise ValueError("Invalid count")
    note=str(entry["note"])
    if re.search(r"(?i)(?:api.?key|token|password|authorization|bearer)\s*[:=]",note):
        raise ValueError("No secrets in audit log")
    if len(note)>500:raise ValueError("Too much free text")
    p=safe_path(filename)
    p.parent.mkdir(parents=True,exist_ok=True)
    existed=p.exists()
    if existed:
        with p.open(encoding="utf-8",newline="") as f:rows=list(csv.DictReader(f))
        if rows and list(rows[0])!=list(COLUMNS):raise ValueError("Ledger columns changed")
        if any(x["event_id"]==entry["event_id"] for x in rows):
            raise ValueError("Duplicate event ID")
    with p.open("a",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=COLUMNS)
        if not existed:w.writeheader()
        w.writerow(entry)
    return p

def main(argv=None):
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="action",required=True)
    sub.add_parser("validate")
    a=sub.add_parser("plan");a.add_argument("--out",default="build/api_ledger/plan.json")
    a=sub.add_parser("classify");a.add_argument("--form",required=True);a.add_argument("--sni",nargs="*",default=[])
    args=p.parse_args(argv)
    if args.action=="validate":
        config();res={"result":"API_LEDGER_CONTRACT_PASS","live_connection":"NOT_CONFIGURED","release":False}
    elif args.action=="plan":res={"file":str(write_plan(args.out)),"live_connection":"NOT_CONFIGURED"}
    else:res=classify(args.form,args.sni)
    print(json.dumps(res,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
