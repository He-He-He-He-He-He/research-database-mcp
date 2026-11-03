"""WIPO World Intellectual Property Indicators 2025 design workbook snapshot."""
import release_runtime
from pathlib import Path
import re
import openpyxl
FILE = Path(__file__).parent / '数据' / 'WIPO2025' / 'design.xlsx'

def catalog():
    w = openpyxl.load_workbook(FILE, read_only=True, data_only=True)
    try:
        return [{'sheet': s.title, 'title': s.cell(1, 2).value} for s in w.worksheets if re.fullmatch('C\\d\\d', s.title)]
    finally:
        w.close()

def table(code):
    if not isinstance(code, str) or not re.fullmatch('C(?:0[1-9]|[123][0-9])', code):
        raise ValueError('sheet code must be C01–C39')
    w = openpyxl.load_workbook(FILE, read_only=True, data_only=True)
    try:
        s = w[code]
        rows = [list(r) for r in s.iter_rows(values_only=True)]
        return {'source': 'WIPO World Intellectual Property Indicators 2025', 'sheet': code, 'rows': rows, 'note': 'Raw cells, notes and headings retained; each table has its own scope and units.'}
    finally:
        w.close()
