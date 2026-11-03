"""WIPO World Intellectual Property Indicators 2025 trademark tables."""
import release_runtime
from pathlib import Path
import re
import openpyxl
ROOT = Path(__file__).parent / '数据' / 'WIPO2025'

def _path(code):
    if not isinstance(code, str) or not re.fullmatch('b(?:[1-9]|[1-3][0-9]|4[0-6])', code):
        raise ValueError('code must be b1–b46')
    return ROOT / ('marks-1.xlsx' if int(code[1:]) <= 30 else 'marks-2.xlsx')

def catalog():
    items = []
    for f in ('marks-1.xlsx', 'marks-2.xlsx'):
        w = openpyxl.load_workbook(ROOT / f, read_only=True, data_only=True)
        try:
            for s in w.worksheets:
                if re.fullmatch('b\\d+', s.title):
                    items.append({'sheet': s.title, 'title': s.cell(1, 1).value})
        finally:
            w.close()
    return items

def table(code):
    w = openpyxl.load_workbook(_path(code), read_only=True, data_only=True)
    try:
        return {'source': 'WIPO World Intellectual Property Indicators 2025', 'sheet': code, 'rows': [list(row) for row in w[code].iter_rows(values_only=True)], 'note': 'Original cells and notes; table scope and units vary.'}
    finally:
        w.close()
