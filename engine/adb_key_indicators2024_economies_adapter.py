"""Asian Development Bank Key Indicators 2024, economy workbook."""
import release_runtime
import argparse, hashlib, json, os, tempfile
from pathlib import Path
import openpyxl, requests
URL = 'https://www.adb.org/sites/default/files/publication/984521/ki-2024-economy-tables.xlsx'
PAGE = 'https://www.adb.org/publications/key-indicators-asia-and-pacific-2024'
SHA = '938e50abbabfb6f73fb732568eeca6e1f9fb3bc1693e3b8d344cc969100c5429'
CACHE = release_runtime.home() / '.cache' / 'zju-research-toolkit' / 'ADB_KI2024_economies.xlsx'

def _hash(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda: f.read(1048576), b''):
            h.update(c)
    return h.hexdigest()

def _file():
    if CACHE.is_file() and _hash(CACHE) == SHA:
        return CACHE
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(dir=CACHE.parent, prefix='.adb-ki2024-', delete=False) as f:
            tmp = Path(f.name)
            size = 0
            with requests.get(URL, stream=True, timeout=60) as r:
                r.raise_for_status()
                for c in r.iter_content(1048576):
                    size += len(c)
                    if size > 10000000:
                        raise ValueError('file exceeds size limit')
                    f.write(c)
        if _hash(tmp) != SHA:
            raise ValueError('source checksum changed; review manually')
        os.replace(tmp, CACHE)
        return CACHE
    finally:
        if tmp and tmp.exists():
            tmp.unlink()

def _rows(s):
    for n, r in enumerate(s.iter_rows(values_only=True), 1):
        yield {'row': n, 'cells': [v.isoformat() if hasattr(v, 'isoformat') else v for v in r]}

def catalog():
    w = openpyxl.load_workbook(_file(), read_only=True, data_only=True)
    try:
        return {'source': URL, 'publication_month': '2024-08', 'http_last_modified_observed': '2024-08-21T12:10:17Z', 'sha256': SHA, 'sheet_names': w.sheetnames, 'contents': list(_rows(w['Table of Contents'])), 'note': 'Workbook sheet codes are ADB codes, not necessarily ISO codes. The host date and 2024 edition label do not establish immutable historical bytes.'}
    finally:
        w.close()

def query(sheet, keyword, limit=10):
    if not isinstance(sheet, str) or len(sheet) > 50 or (not isinstance(keyword, str)) or (not keyword.strip()) or (len(keyword) > 100) or (type(limit) is not int) or (not 1 <= limit <= 50):
        raise ValueError('provide sheet, keyword, limit 1–50')
    w = openpyxl.load_workbook(_file(), read_only=True, data_only=True)
    try:
        if sheet not in w.sheetnames or sheet == 'Table of Contents':
            raise ValueError('unknown economy sheet; use catalog')
        rows = list(_rows(w[sheet]))
        matches = []
        footnote_start = next((i for i, r in enumerate(rows) if r['cells'][0] is not None and 'data not available' in str(r['cells'][0]).casefold()), None)
        footnotes = rows[footnote_start:] if footnote_start is not None else []
        for i, row in enumerate(rows):
            if any((keyword.casefold() in str(v).casefold() for v in row['cells'] if v is not None)):
                matches.append({'row': row, 'context_before': rows[max(0, i - 2):i], 'context_after': rows[i + 1:i + 3]})
        return {'source': URL, 'source_page': PAGE, 'edition': '2024', 'http_last_modified_observed': '2024-08-21T12:10:17Z', 'sha256': SHA, 'sheet': sheet, 'header_rows': rows[:8], 'footnotes': footnotes, 'footnote_start_detected': footnote_start is not None, 'matches': len(matches), 'results': matches[:limit], 'note': 'ADB economy tables, not the separate regional or SDG tables. Original sheet rows and text preserved; years may differ by sheet. When detected, all rows after the standard legend are preserved as footnotes; otherwise inspect the full workbook for footnotes. Definitions, breaks, provisional values and source notes require verification against the original workbook. Missing is not zero. Long-term comparability depends on methodology, units and notes. Server date is not proof current bytes are unchanged since 2024.'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['catalog', 'query'])
    p.add_argument('--sheet')
    p.add_argument('--keyword', default='')
    p.add_argument('--limit', type=int, default=10)
    a = p.parse_args()
    print(json.dumps(catalog() if a.action == 'catalog' else query(a.sheet, a.keyword, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
