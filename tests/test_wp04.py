"""WP04 controlled XLSX fixture, including typed zeros and all nine source sheets."""
from pathlib import Path
import csv,json,zipfile
from xml.sax.saxutils import escape
import pytest
from ideburen.wp04 import run,parse_xlsx,resolve,geocodes

SPR="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG="http://schemas.openxmlformats.org/package/2006/relationships"

def make(path,data,formula=False):
    book=[]; rels=[]; strings=[]; worksheets=[]
    for n,(name,rows) in enumerate(data.items(),start=1):
        book.append(f'<s:sheet name="{escape(name)}" sheetId="{n}" r:id="r{n}"/>')
        rels.append(f'<Relationship Id="r{n}" Target="/xl/worksheets/sheet{n}.xml" Type="{REL}/worksheet"/>')
        payload=[]
        for ix,row in enumerate(rows,start=1):
            cs=[]
            for j,v in enumerate(row):
                col=chr(65+j)
                if v is None:continue
                if isinstance(v,(int,float)):
                    cs.append(f'<s:c r="{col}{ix}" t="n"><s:v>{v}</s:v></s:c>')
                elif formula and ix==2 and j==1:
                    cs.append(f'<s:c r="{col}{ix}"><s:f>1+1</s:f><s:v>2</s:v></s:c>')
                else:
                    cs.append(f'<s:c r="{col}{ix}" t="inlineStr"><s:is><s:t>{escape(str(v))}</s:t></s:is></s:c>')
            payload.append(f'<s:row r="{ix}">{"".join(cs)}</s:row>')
        worksheets.append(f'<s:worksheet xmlns:s="{SPR}"><s:sheetData>{"".join(payload)}</s:sheetData></s:worksheet>')
    with zipfile.ZipFile(path,"w") as z:
        z.writestr("xl/workbook.xml",f'<s:workbook xmlns:s="{SPR}" xmlns:r="{REL}"><s:sheets>{"".join(book)}</s:sheets></s:workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",f'<Relationships xmlns="{PKG}">{"".join(rels)}</Relationships>')
        for n,xml in enumerate(worksheets,start=1):z.writestr(f"xl/worksheets/sheet{n}.xml",xml)

def test_wp04_all_sheets_and_null_zero(tmp_path):
    first=tmp_path/"national.xlsx";second=tmp_path/"uppsala.xlsx"
    make(first,{
     "Alla kommuner":[["Kommun","Län (kontrollerat)","Klassificering","Antal organisationer","Publicerad","Dataår","Därav ideella"],
                    ["Habo kommun","Jönköpings län","Ej verifierad",None,None,None,None],
                    ["Håbo kommun","Uppsala län","A – Kommunavsnitt",0,2022,2022,None],
                    ["Falu kommun","Dalarnas län","B – rapport",7,2023,2022,0]],
     "Kommunbilagor":[["Kommun","Klassificering"],["Habo kommun","B"]],
     "Viktiga källor":[["Nivå","Källa"],["SCB","Regional statistik"]],
     "Metod":[["Område","Princip"],["Täckning","Ej komplett"]]
    })
    make(second,{
     "Registerkällor":[["Kommun","System","Direktlänk till register"],["Enköping","Rbok","https://example.org"]],
     "Föreningar":[["Kommun","Föreningsnamn","Källår"],["Knivsta","Alsike IF","2023"]],
     "Beslutskedjor":[["Kommun","Datum / period","Steg","Handling / händelse"],["Tierp","2025-09","Beslut","LÖK"]],
     "Begär ut":[["Kommun","Handlingstyp"],["Heby","Föreningsregister"]],
     "Metod":[["Del","Avgränsning"],["Historik","Inte aktuellt register"]]
    })
    m=run(first,second,tmp_path/"output",strict=False)
    assert m["exceptions"]==0
    assert m["raw_rows"]==10
    assert m["metrics"]["reported_organisation_counts"]==2
    assert m["metrics"]["absent_organisation_counts"]==1
    assert m["metrics"]["zero_organisation_counts"]==1
    with (tmp_path/"output/municipal_inventory.csv").open(encoding="utf-8") as f:r=list(csv.DictReader(f))
    assert [x["municipality_code"] for x in r]==["0643","0305","2080"]
    assert [x["organisation_count"] for x in r]==["","0","7"]
    assert m["metrics"]["supplements_not_double_counted"]==1
    assert len((tmp_path/"output/original_sheet_rows.jsonl").read_text().splitlines())==10

def test_formula_rejected(tmp_path):
    file=tmp_path/"bad.xlsx"
    make(file,{"Alla kommuner":[["Kommun","Antal"],["Habo kommun","2"]]},formula=True)
    with pytest.raises(ValueError,match="Unsupported formula"):parse_xlsx(file)

def test_unknown_geography_never_default_zero():
    assert resolve("Ingen sådan kommun",geocodes())[0] is None
    assert resolve("Habo kommun",geocodes())[0]=="0643"
    assert resolve("Håbo kommun",geocodes())[0]=="0305"

def test_strict_row_count_drift_blocks(tmp_path):
    first=tmp_path/"national.xlsx";second=tmp_path/"uppsala.xlsx"
    make(first,{"Alla kommuner":[["Kommun","Län (kontrollerat)","Klassificering","Antal organisationer"],["Habo kommun","Jönköpings län","Ej verifierad",None]],"Kommunbilagor":[["Kommun","Klassificering"],["Habo kommun","B"]],"Viktiga källor":[["Nivå"],["Test"]],"Metod":[["Område"],["Test"]]})
    make(second,{"Registerkällor":[["Kommun","System","Direktlänk till register"],["Håbo","Rbok","https://example.org"]],"Föreningar":[["Kommun","Föreningsnamn","Källår"],["Knivsta","Alsike IF","2023"]],"Beslutskedjor":[["Kommun","Datum / period","Steg","Handling / händelse"],["Tierp","2025","Beslut","LÖK"]],"Begär ut":[["Kommun","Handlingstyp"],["Heby","Register"]],"Metod":[["Del"],["Test"]]})
    with pytest.raises(ValueError,match="exceptions"):
        run(first,second,tmp_path/"out",strict=True)
    with (tmp_path/"out/exceptions.csv").open(encoding="utf-8") as f:issues=list(csv.DictReader(f))
    assert any(x["code"]=="ROW_COUNT_DRIFT" for x in issues)
