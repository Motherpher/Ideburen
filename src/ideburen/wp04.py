"""WP04: fail-closed, reproducible import for the two user-supplied inventory XLSX files.

Original Excel bytes are never committed or copied to a publishable dataset.
Outputs belong in gitignored, non-public staging only. Zero != missing.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,re,unicodedata,zipfile
import xml.etree.ElementTree as ET
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path

from .cli import ROOT, read_csv, digest

M="{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R="{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
P="{http://schemas.openxmlformats.org/package/2006/relationships}"
EXPECTED={
 "national_inventory":{"Alla kommuner","Kommunbilagor","Viktiga källor","Metod"},
 "uppsala_register":{"Registerkällor","Föreningar","Beslutskedjor","Begär ut","Metod"}
}
FIELDS={
 "Alla kommuner":{"Kommun","Län (kontrollerat)","Klassificering","Antal organisationer"},
 "Kommunbilagor":{"Kommun","Klassificering"},
 "Registerkällor":{"Kommun","System","Direktlänk till register"},
 "Föreningar":{"Kommun","Föreningsnamn","Källår"},
 "Beslutskedjor":{"Kommun","Datum / period","Steg","Handling / händelse"},
 "Begär ut":{"Kommun","Handlingstyp"}
}
DATASET_MAP={
 ("national_inventory","Alla kommuner"):"municipal_inventory",
 ("national_inventory","Kommunbilagor"):"municipal_supplements",
 ("national_inventory","Viktiga källor"):"reference_links",
 ("national_inventory","Metod"):"method_notes_national",
 ("uppsala_register","Registerkällor"):"association_register_sources",
 ("uppsala_register","Föreningar"):"historical_associations",
 ("uppsala_register","Beslutskedjor"):"decision_events",
 ("uppsala_register","Begär ut"):"records_requests",
 ("uppsala_register","Metod"):"method_notes_uppsala"
}
COUNTS={
 "municipal_inventory":290,"municipal_supplements":23,"reference_links":5,
 "method_notes_national":6,"association_register_sources":8,
 "historical_associations":37,"decision_events":27,"records_requests":16,
 "method_notes_uppsala":9
}
def _coord(col):
    n=0
    for c in col:n=n*26+ord(c)-64
    return n-1

def _safe_target(name):
    target=name.lstrip("/")
    if target.startswith("../") or "/../" in target:raise ValueError("Unsafe XLSX worksheet path")
    return target if target.startswith("xl/") else "xl/"+target

def parse_xlsx(path):
    """Return ALL sheets and actual XML rows (sheet,row,dict,cell type map).

    Formula cells abort import, as cached formula values cannot be trusted.
    Numeric cells retain integer vs float; empty cells remain None.
    """
    path=Path(path)
    if path.suffix.lower()!=".xlsx":raise ValueError("Only .xlsx supported")
    result=defaultdict(list)
    with zipfile.ZipFile(path) as z:
        entries=z.infolist()
        if len(entries)>2000 or sum(x.file_size for x in entries)>80_000_000:
            raise ValueError("XLSX ZIP exceeds safe size or entry limits")
        if any(x.filename.endswith("vbaProject.bin") or x.filename.startswith("xl/externalLinks/") for x in entries):
            raise ValueError("Macros/external linked data are not accepted")
        book=ET.fromstring(z.read("xl/workbook.xml"))
        rel=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        targets={x.attrib["Id"]:_safe_target(x.attrib["Target"]) for x in rel.findall(f"{P}Relationship")}
        shared=[]
        if "xl/sharedStrings.xml" in z.namelist():
            raw=ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared=["".join(n.text or "" for n in si.iter(f"{M}t")) for si in raw.findall(f"{M}si")]
        for sheet in book.find(f"{M}sheets"):
            name=sheet.attrib["name"]
            result[name]=[]
            target=targets[sheet.attrib[f"{R}id"]]
            root=ET.fromstring(z.read(target))
            grid=root.find(f"{M}sheetData")
            if grid is None:continue
            headers=None;last_row=0
            for row in grid.findall(f"{M}row"):
                number=int(row.attrib.get("r",last_row+1));last_row=number
                cells={};types={}
                for cell in row.findall(f"{M}c"):
                    m=re.match(r"([A-Z]+)",cell.attrib.get("r",""))
                    if m is None:raise ValueError("Invalid cell coordinate")
                    index=_coord(m.group(1))
                    if cell.find(f"{M}f") is not None:
                        raise ValueError(f"Unsupported formula at {name}!{cell.attrib['r']}")
                    typ=cell.attrib.get("t","n")
                    v=cell.find(f"{M}v")
                    inline=cell.find(f"{M}is")
                    if typ=="inlineStr":
                        value="".join(t.text or "" for t in inline.iter(f"{M}t")) if inline is not None else ""
                    elif v is None or v.text is None:value=None
                    elif typ=="s":value=shared[int(v.text)]
                    elif typ=="b":value=v.text=="1"
                    elif typ in ("str","e"):value=v.text
                    elif typ=="n":
                        try:
                            d=float(v.text)
                            value=int(d) if d.is_integer() else d
                        except (ValueError,OverflowError):value=v.text
                    else:raise ValueError(f"Unexpected XLSX cell type {typ} at {name}!{cell.attrib['r']}")
                    cells[index]=value;types[index]=typ
                if not cells:continue
                width=max(cells)+1
                arr=[cells.get(i) for i in range(width)]
                if headers is None:
                    headers=[str(v).strip() if v is not None else "" for v in arr]
                    nonblank=[x for x in headers if x]
                    if len(nonblank)!=len(set(nonblank)):raise ValueError("Duplicate header in "+name)
                    continue
                if any(v is not None and v!="" for v in arr):
                    record={h:(arr[i] if i<len(arr) else None) for i,h in enumerate(headers) if h}
                    kinds={h:types.get(i,"blank") for i,h in enumerate(headers) if h}
                    result[name].append((number,record,kinds))
    return dict(result)

def _diacritics(x):
    x=unicodedata.normalize("NFKD",str(x or "").casefold().strip())
    return "".join(c for c in x if not unicodedata.combining(c))

def _place_aliases(name):
    stem=name
    return [stem,stem+" kommun",stem+"s kommun",stem+" stad",stem+"s stad","Region "+stem]

def geocodes():
    exact=defaultdict(set);loose=defaultdict(set)
    for row in read_csv(ROOT/"data/curated/dimensions/municipalities.csv"):
        for alias in _place_aliases(row["municipality_name"]):
            exact[alias.casefold().strip()].add(row["municipality_code"])
            loose[_diacritics(alias)].add(row["municipality_code"])
    return exact,loose

def resolve(place,maps):
    exact,loose=maps;label=str(place or "").strip()
    exact_match=exact.get(label.casefold(),set())
    if len(exact_match)==1:return next(iter(exact_match)),"exact"
    fallback=loose.get(_diacritics(label),set())
    if len(fallback)==1:return next(iter(fallback)),"normalized"
    return None,"ambiguous" if len(exact_match)>1 or len(fallback)>1 else "unmatched"

def _write_csv(path,values,headers):
    with Path(path).open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=headers,extrasaction="ignore")
        w.writeheader();w.writerows(values)

def _jsonl(path,rows):
    with Path(path).open("w",encoding="utf-8") as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False,sort_keys=True)+"\n")

def _blank(v):
    return v is None or v==""

def _number(v,where,issues):
    if _blank(v):return ""
    if isinstance(v,bool) or not isinstance(v,(int,float)) or v<0 or int(v)!=v:
        issues.append({"severity":"BLOCKING","code":"INVALID_NONNEGATIVE_INTEGER","at":where,"detail":str(v)})
        return ""
    return str(int(v))

def run(national,uppsala,out,strict=True):
    output=Path(out).resolve();output.mkdir(parents=True,exist_ok=True)
    if output==ROOT or output in (ROOT/"data/curated",ROOT/"manifests"):
        raise ValueError("Do not stage sensitive data in curated/public directories")
    if any(output==Path(p).resolve().parent for p in (national,uppsala)):
        raise ValueError("Do not write staging next to original seed workbooks")
    bundles={"national_inventory":Path(national),"uppsala_register":Path(uppsala)}
    originals={};inputs=[];issues=[];raw=[];transformed=defaultdict(list)
    map_codes=geocodes()
    for label,path in bundles.items():
        if not path.is_file():raise FileNotFoundError(path)
        sheets=parse_xlsx(path)
        if set(sheets)!=EXPECTED[label]:
            raise ValueError(f"Sheet mismatch {label}: missing={sorted(EXPECTED[label]-set(sheets))}; extra={sorted(set(sheets)-EXPECTED[label])}")
        inputs.append({"source_id":"seed_290" if label=="national_inventory" else "seed_uppsala",
                       "label":label,"file_basename":path.name,"sha256":digest(path),
                       "sheets":{k:len(v) for k,v in sheets.items()}})
        for sheet,items in sheets.items():
            if sheet in FIELDS and items:
                missing=FIELDS[sheet]-set(items[0][1])
                if missing:raise ValueError(f"{label}:{sheet} required headers missing: {sorted(missing)}")
            group=DATASET_MAP[label,sheet]
            for n,fields,types in items:
                row_id=f"{label}/{sheet}/{n}"
                where=f"{label}!{sheet}!{n}"
                raw.append({"row_id":row_id,"source_id":inputs[-1]["source_id"],
                            "source_sha256":inputs[-1]["sha256"],"sheet":sheet,"excel_row":n,
                            "values":fields,"cell_types":types})
                if group in ("method_notes_national","method_notes_uppsala","reference_links"):
                    transformed[group].append({"row_id":row_id,"source_id":inputs[-1]["source_id"],
                                               "raw_only":True})
                    continue
                name=fields.get("Kommun")
                code,resolution=resolve(name,map_codes)
                if not code:issues.append({"severity":"BLOCKING","code":"UNRESOLVED_MUNICIPALITY",
                                          "at":where,"detail":str(name)})
                item={"row_id":row_id,"source_id":inputs[-1]["source_id"],
                      "municipality_code":code or "","municipality_input":str(name or ""),
                      "geocode_method":resolution,"evidence_status":"seed_unverified"}
                if group in ("municipal_inventory","municipal_supplements"):
                    item.update({"report_title":fields.get("Rapporttitel") or "",
                                 "classification":fields.get("Klassificering") or "",
                                 "report_year":_number(fields.get("Publicerad"),where+":Publicerad",issues),
                                 "data_year":_number(fields.get("Dataår"),where+":Dataår",issues),
                                 "organisation_count":_number(fields.get("Antal organisationer"),where+":Antal organisationer",issues),
                                 "association_count":_number(fields.get("Därav ideella"),where+":Därav ideella",issues),
                                 "original_source_url":fields.get("Källänk") or "",
                                 "count_status":"reported_number_unverified" if not _blank(fields.get("Antal organisationer")) else "not_reported",
                                 "geography_status":"SCB_2026_code_lookup_not_historical_geography",
                                 "study_status":"municipal_index" if group=="municipal_inventory" else "supplement_not_independent_observation"})
                elif group=="historical_associations":
                    item.update({"organisation_name":fields.get("Föreningsnamn") or "",
                                 "list_type":fields.get("Register/listtyp") or "",
                                 "relation":fields.get("Relation/status") or "",
                                 "list_year":str(fields.get("Källår") or ""),
                                 "source_url":fields.get("Primärkälla") or "",
                                 "population":"historical_membership_list_not_municipal_register"})
                elif group=="association_register_sources":
                    item.update({"registry_system":fields.get("System") or "",
                                 "registry_url":fields.get("Direktlänk till register") or "",
                                 "extraction_status":fields.get("Extraktionsstatus") or "",
                                 "population":"register_locator_not_extracted_membership"})
                elif group=="decision_events":
                    item.update({"period_original":str(fields.get("Datum / period") or ""),
                                 "event_stage":fields.get("Steg") or "",
                                 "event_text":fields.get("Handling / händelse") or "",
                                 "actor":fields.get("Besluts- eller dialogaktör") or "",
                                 "verification_original":fields.get("Verifikationsstatus") or "",
                                 "source_url":fields.get("Primärkälla") or "",
                                 "event_status":"discovered_not_legally_approved"})
                elif group=="records_requests":
                    item.update({"record_type":fields.get("Handlingstyp") or "",
                                 "source_url":fields.get("Registerkälla") or "",
                                 "request_status":"draft_not_submitted"})
                transformed[group].append(item)
    counts={k:len(v) for k,v in transformed.items()}
    if strict:
        for key,expected in COUNTS.items():
            if counts.get(key)!=expected:issues.append({"severity":"BLOCKING","code":"ROW_COUNT_DRIFT",
                "at":key,"detail":f"expected {expected} observed {counts.get(key,0)}"})
        codes=[x["municipality_code"] for x in transformed["municipal_inventory"]]
        if len(set(codes))!=290:issues.append({"severity":"BLOCKING","code":"NATIONAL_COVERAGE", "at":"municipal_inventory",
                                               "detail":f"unique codes {len(set(codes))} expected 290"})
    supplement_codes={r["municipality_code"] for r in transformed["municipal_supplements"]}
    primary_codes={r["municipality_code"] for r in transformed["municipal_inventory"]}
    if not supplement_codes.issubset(primary_codes):
        issues.append({"severity":"BLOCKING","code":"ORPHAN_SUPPLEMENT","at":"municipal_supplements","detail":"Missing national parent"})
    # Raw data only to ignored local JSONL, never in committed curated tables or CI artifact.
    _jsonl(output/"original_sheet_rows.jsonl",raw)
    for group,items in sorted(transformed.items()):
        if items:
            _write_csv(output/(group+".csv"),items,list(items[0]))
    _write_csv(output/"exceptions.csv",issues,["severity","code","at","detail"])
    numeric=transformed["municipal_inventory"]
    stats={"reported_organisation_counts":sum(x["count_status"]=="reported_number_unverified" for x in numeric),
           "absent_organisation_counts":sum(x["count_status"]=="not_reported" for x in numeric),
           "zero_organisation_counts":sum(x["organisation_count"]=="0" for x in numeric),
           "supplements_not_double_counted":len(transformed["municipal_supplements"])}
    manifest={"schema":"ideburen_wp04_v1","inputs":inputs,"sheet_counts":counts,
              "raw_rows":len(raw),"normalized_rows":sum(counts.values()),"metrics":stats,
              "exceptions":len(issues),"blocking_exceptions":sum(i["severity"]=="BLOCKING" for i in issues),
              "geography_basis":"SCB 2026 IDs (not historical boundaries)",
              "source_status":"research_seed_not_primary_audited",
              "release_status":"BLOCKED_HARP_AND_RIGHTS",
              "no_original_files_committed":True,"originals_preserved_outside_git":True}
    (output/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if issues:raise ValueError(f"WP04 import found {len(issues)} exceptions; see {output/'exceptions.csv'}")
    return manifest

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--municipal",required=True);p.add_argument("--uppsala",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--allow-different-row-counts",action="store_true")
    a=p.parse_args(argv)
    result=run(a.municipal,a.uppsala,a.out,strict=not a.allow_different_row_counts)
    print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=="__main__":main()
