"""Integration test for exact structure of user-exported XLSX (shared strings + /xl/ targets)."""
import csv
from pathlib import Path
import tempfile
import zipfile

from ideburen.cli import ingest, xlsx_rows

PKG="http://schemas.openxmlformats.org/package/2006/relationships"
SPR="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL="http://schemas.openxmlformats.org/officeDocument/2006/relationships"

def make_workbook(path, sheetname, rows):
    strings=[]
    for row in rows:
        for cell in row:
            if cell not in strings:strings.append(cell)
    indices={value:i for i,value in enumerate(strings)}
    cells=[]
    for y,row in enumerate(rows,1):
        inner=[]
        for x,val in enumerate(row):
            inner.append(f'<x:c r="{chr(65+x)}{y}" t="s"><x:v>{indices[val]}</x:v></x:c>')
        cells.append(f'<x:row r="{y}">{"".join(inner)}</x:row>')
    shared="".join(f'<x:si><x:t>{s}</x:t></x:si>' for s in strings)
    with zipfile.ZipFile(path,"w") as z:
        z.writestr("xl/workbook.xml",f'<x:workbook xmlns:x="{SPR}" xmlns:r="{REL}"><x:sheets><x:sheet name="{sheetname}" sheetId="1" r:id="r1"/></x:sheets></x:workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",f'<Relationships xmlns="{PKG}"><Relationship Id="r1" Target="/xl/worksheets/sheet1.xml" Type="{REL}/worksheet"/></Relationships>')
        z.writestr("xl/sharedStrings.xml",f'<x:sst xmlns:x="{SPR}">{shared}</x:sst>')
        z.writestr("xl/worksheets/sheet1.xml",f'<x:worksheet xmlns:x="{SPR}"><x:sheetData>{"".join(cells)}</x:sheetData></x:worksheet>')

def test_seed_xlsx_reader_and_diacritics():
    with tempfile.TemporaryDirectory() as d:
        d=Path(d)
        first=d/"national.xlsx";second=d/"uppsala.xlsx"
        make_workbook(first,"Alla kommuner",[["Kommun","Klassificering"],["Habo kommun","Ej verifierad"],["Håbo kommun","Ej verifierad"],["Östhammars kommun","Ej verifierad"],["Stockholms stad","Ej verifierad"],["Falu kommun","Ej verifierad"],["Region Gotland","Ej verifierad"]])
        make_workbook(second,"Beslutskedjor",[["Kommun","Datum / period","Handling / händelse"],["Tierp","2025-09","LÖK"],["Uppsala","2025-09-08","Policy"]])
        assert len(list(xlsx_rows(first)))==6
        result=ingest(first,second,d/"out")
        assert result["staged_rows"]==8
        assert result["geocode_exceptions"]==0
        with open(d/"out/staging.csv",encoding="utf-8",newline="") as f:
            rows=list(csv.DictReader(f))
        assert [r["municipality_code"] for r in rows]==["0643","0305","0382","0180","2080","0980","0360","0380"]
