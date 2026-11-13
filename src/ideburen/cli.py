"""Ideburen CLI: research staging, HARP gates and nonspatial QGIS exports."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,csv,hashlib,json,re,sqlite3,unicodedata,zipfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
S="{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R="{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
P="{http://schemas.openxmlformats.org/package/2006/relationships}"

def read_csv(path):
    with open(path,encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def save_csv(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with open(path,"w",encoding="utf-8",newline="") as f:
        if rows:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        else:f.write("dataset,sheet,row_number,municipality,issue\n")

def digest(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()

def normalize(x):
    x=unicodedata.normalize("NFKD",str(x or "").casefold().strip())
    x="".join(c for c in x if not unicodedata.combining(c))
    x=re.sub(r"^region ","",x)
    x=re.sub(r"(s)? (kommun|stad)$","",x).strip()
    return "falun" if x=="falu" else x

def xlsx_rows(path):
    """Yield (sheet,row_number,{column:value}) using stdlib, without macros."""
    with zipfile.ZipFile(path) as z:
        book=ET.fromstring(z.read("xl/workbook.xml"))
        rel=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        paths={r.attrib["Id"]:r.attrib["Target"].lstrip("/") for r in rel.findall(f"{P}Relationship")}
        ss=[]
        if "xl/sharedStrings.xml" in z.namelist():
            sroot=ET.fromstring(z.read("xl/sharedStrings.xml"))
            ss=["".join(t.text or "" for t in si.iter(f"{S}t")) for si in sroot.findall(f"{S}si")]
        for sheet in book.find(f"{S}sheets"):
            target=paths[sheet.attrib[f"{R}id"]]
            if not target.startswith("xl/"):target="xl/"+target
            root=ET.fromstring(z.read(target))
            grid=root.find(f"{S}sheetData")
            if grid is None:continue
            headers=None
            for row in grid.findall(f"{S}row"):
                cells={}
                for c in row.findall(f"{S}c"):
                    code=re.match(r"[A-Z]+",c.attrib["r"]).group()
                    index=0
                    for letter in code:index=index*26+ord(letter)-64
                    index-=1
                    typ=c.attrib.get("t")
                    node=c.find(f"{S}v")
                    inline=c.find(f"{S}is")
                    if typ=="inlineStr":value="".join(t.text or "" for t in inline.iter(f"{S}t")) if inline is not None else ""
                    elif node is None or node.text is None:value=None
                    elif typ=="s":value=ss[int(node.text)]
                    elif typ=="b":value=(node.text=="1")
                    elif typ in ("str","e"):value=node.text
                    else:
                        try:
                            value=float(node.text)
                            if value.is_integer():value=int(value)
                        except (TypeError,ValueError):value=node.text
                    cells[index]=value
                if not cells:continue
                arr=[cells.get(i) for i in range(max(cells)+1)]
                if headers is None:headers=[str(v or "").strip() for v in arr];continue
                if any(v is not None and v!="" for v in arr):
                    yield sheet.attrib["name"],int(row.attrib["r"]),{h:(arr[i] if i<len(arr) else None) for i,h in enumerate(headers) if h}

def validate():
    base=ROOT/"data/curated"
    counties=read_csv(base/"dimensions/counties.csv")
    cities=read_csv(base/"dimensions/municipalities.csv")
    obs=read_csv(base/"observations/uppsala_2022.csv")
    assert len(counties)==21 and len(cities)==290 and len(obs)==8
    ids={v["county_code"] for v in counties};keys=[v["municipality_code"] for v in cities]
    assert len(set(keys))==290
    assert all(re.fullmatch(r"\d{4}",k) for k in keys)
    assert all(v["county_code"] in ids and v["municipality_code"][:2]==v["county_code"] for v in cities)
    assert all(v["value_year"]=="2022" and v["source_id"] and v["population"] and v["method_id"] for v in obs)
    assert len({o["municipality_code"] for o in obs})==8 and all(o["municipality_code"] in keys for o in obs)
    assert sum(int(v["value"]) for v in obs)==10821
    return {"municipalities":290,"counties":21,"uppsala_2022_total":10821,
            "geography_validation":"PROVISIONAL_OFFICIAL_SCB_RECHECK_REQUIRED",
            "spatial_boundaries":"NOT_ACQUIRED","public_release":"BLOCKED_DIRECTOR_REFA"}

def ingest(municipal,uppsala,out):
    validate()
    lookup={}
    exact={}
    for r in read_csv(ROOT/"data/curated/dimensions/municipalities.csv"):
        for alias in (r["municipality_name"],r["municipality_name"]+" kommun",r["municipality_name"]+"s kommun",
                      r["municipality_name"]+" stad",r["municipality_name"]+"s stad","Region "+r["municipality_name"]):
            lookup.setdefault(normalize(alias),set()).add(r["municipality_code"])
            exact.setdefault(alias.casefold().strip(),set()).add(r["municipality_code"])
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    now=datetime.now(timezone.utc).isoformat();staged=[];errors=[];inputs=[]
    for label,path in (("national_inventory",municipal),("uppsala_decisions",uppsala)):
        sha=digest(path);inputs.append({"dataset":label,"filename":Path(path).name,"sha256":sha})
        for sheet,n,data in xlsx_rows(path):
            if label=="national_inventory" and sheet!="Alla kommuner":continue
            if label=="uppsala_decisions" and sheet not in ("Beslutskedjor","Föreningar","Registerkällor"):continue
            place=str(data.get("Kommun") or "")
            # Accent-preserving exact match first: Habo and Håbo MUST remain distinct.
            options=exact.get(place.casefold().strip(),set()) or lookup.get(normalize(place),set())
            code=next(iter(options)) if len(options)==1 else ""
            staged.append({"dataset":label,"sheet":sheet,"row_number":n,"municipality":place,
                "municipality_code":code,"source_sha256":sha,"status":"staging_unverified",
                "raw_json":json.dumps(data,ensure_ascii=False,sort_keys=True,default=str)})
            if not code:errors.append({"dataset":label,"sheet":sheet,"row_number":n,"municipality":place,"issue":"unresolved_geocode"})
    save_csv(out/"staging.csv",staged)
    save_csv(out/"exceptions.csv",errors)
    manifest={"run_utc":now,"inputs":inputs,"staged_rows":len(staged),"geocode_exceptions":len(errors),
              "publication_status":"NOT_VERIFIED"}
    (out/"ingestion_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return manifest

FILES={"municipalities":"dimensions/municipalities.csv","counties":"dimensions/counties.csv",
       "uppsala_2022":"observations/uppsala_2022.csv","publications":"publications/registry.csv"}
def build(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    outputs=[]
    for name,location in FILES.items():
        target=out/(name+".csv");target.write_bytes((ROOT/"data/curated"/location).read_bytes())
        outputs.append({"name":name,"file":target.name,"sha256":digest(target)})
    metadata={"outputs":outputs,"format":"attribute_tables","geometries":False,
              "release_status":"INTERNAL_NOT_CLEARED","target_crs":"EPSG:3006"}
    (out/"manifest.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return metadata

def gpkg(src,destination):
    src=Path(src);dest=Path(destination);dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():dest.unlink()
    db=sqlite3.connect(dest)
    try:
        db.execute("PRAGMA application_id=1196444487")
        db.execute("PRAGMA user_version=10200")
        db.execute("""CREATE TABLE gpkg_spatial_ref_sys(srs_name TEXT NOT NULL,srs_id INTEGER PRIMARY KEY,
             organization TEXT NOT NULL,organization_coordsys_id INTEGER NOT NULL,definition TEXT NOT NULL,description TEXT)""")
        db.execute("""CREATE TABLE gpkg_contents(table_name TEXT NOT NULL PRIMARY KEY,data_type TEXT NOT NULL,
             identifier TEXT UNIQUE,description TEXT DEFAULT '',last_change DATETIME NOT NULL DEFAULT
             (strftime('%Y-%m-%dT%H:%M:%fZ','now')),min_x DOUBLE,min_y DOUBLE,max_x DOUBLE,max_y DOUBLE,srs_id INTEGER)""")
        db.execute("INSERT INTO gpkg_spatial_ref_sys VALUES ('Undefined cartesian',-1,'NONE',-1,'undefined','undefined'),('Undefined geographic',0,'NONE',0,'undefined','undefined')")
        counts={}
        for table in FILES:
            rows=read_csv(src/(table+".csv"))
            if not rows:raise ValueError("Missing rows: "+table)
            columns=list(rows[0])
            assert all(re.fullmatch(r"[a-zA-Z_][a-zA-Z_0-9]*",c) for c in columns)
            sqlcols=",".join('"'+k+'" TEXT' for k in columns)
            db.execute('CREATE TABLE "'+table+'" (fid INTEGER PRIMARY KEY AUTOINCREMENT,'+sqlcols+')')
            keys=",".join('"'+k+'"' for k in columns)
            marks=",".join("?" for _ in columns)
            db.executemany('INSERT INTO "'+table+'" ('+keys+') VALUES ('+marks+')',[[r[c] for c in columns] for r in rows])
            db.execute("INSERT INTO gpkg_contents(table_name,data_type,identifier,description) VALUES (?,?,?,?)",
                       (table,"attributes",table,"No polygons: attribute data only"))
            counts[table]=len(rows)
        db.commit()
    finally:db.close()
    return {"tables":counts,"features_layers":0,"usable_in_qgis":"attribute_tables_only"}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest="command",required=True)
    s.add_parser("validate")
    a=s.add_parser("ingest");a.add_argument("--municipal",required=True);a.add_argument("--uppsala",required=True);a.add_argument("--out",default="build")
    a=s.add_parser("build");a.add_argument("--out",default="build")
    a=s.add_parser("package");a.add_argument("--input",default="build");a.add_argument("--out",default="build/ideburen_tables.gpkg")
    x=p.parse_args(argv)
    if x.command=="validate":result=validate()
    elif x.command=="ingest":result=ingest(x.municipal,x.uppsala,x.out)
    elif x.command=="build":result=build(x.out)
    else:
        if not (Path(x.input)/"manifest.json").exists():build(x.input)
        result=gpkg(x.input,x.out)
    print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=="__main__":main()
