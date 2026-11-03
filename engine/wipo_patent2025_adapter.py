"""WIPO World Intellectual Property Indicators 2025 patent tables."""
import release_runtime
from pathlib import Path
import re
import openpyxl
ROOT = Path(__file__).parent / '数据' / 'WIPO2025'

def _path(code):
    if not isinstance(code, str) or not re.fullmatch('A(?:0[1-9]|[1-5][0-9]|6[0-3])', code):
        raise ValueError('code must be A01–A63')
    n = int(code[1:])
    return ROOT / ('pat.1.xlsx' if n <= 25 else 'pat.2.xlsx' if n <= 50 else 'pat.3.xlsx')

def catalog():
    out = []
    for n in range(1, 64):
        code = f'A{n:02}'
        w = openpyxl.load_workbook(_path(code), read_only=True, data_only=True)
        try:
            out.append({'sheet': code, 'title': w[code].cell(1, 1).value})
        finally:
            w.close()
    return out

def table(code):
    w = openpyxl.load_workbook(_path(code), read_only=True, data_only=True)
    try:
        return {'source': 'WIPO World Intellectual Property Indicators 2025', 'sheet': code, 'rows': [list(r) for r in w[code].iter_rows(values_only=True)], 'note': 'Raw cells, captions and notes; scope and units differ by table.'}
    finally:
        w.close()
